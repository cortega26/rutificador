# ruff: noqa
# mypy: ignore-errors
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import mannwhitneyu, spearmanr

BASE = "https://github.com/Johnbrick123/sp500-data/releases/download/data"
FILES = {
    "prices": "prices.parquet",
    "intervals": "membership_intervals.parquet",
    "recycled": "recycled_tickers.csv",
}
CUTS = [pd.Timestamp("2016-10-06"), pd.Timestamp("2021-10-06")]
BEAR_START = pd.Timestamp("2022-01-03")
BEAR_END = pd.Timestamp("2022-10-12")
MAX_HV = 1.20
MIN_HV = 0.20
MIN_PRICE = 5.0
MIN_BETA = 0.80
SCORER_LIQ_USD = 2_000_000.0
UNIVERSE_LIQ_USD = 50_000_000.0


def download(name: str) -> Path:
    fn = FILES[name]
    path = Path("/tmp") / fn
    if path.exists() and path.stat().st_size > 0:
        return path
    url = f"{BASE}/{fn}"
    print(f"DOWNLOAD {fn} ...", flush=True)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"DOWNLOADED {fn} bytes={path.stat().st_size}", flush=True)
    return path


def log_returns(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").dropna()
    s = s[s > 0]
    return np.log(s / s.shift(1)).dropna()


def max_drawdown(s: pd.Series, window: int = 252) -> float:
    x = pd.to_numeric(s, errors="coerce").dropna().tail(window)
    if len(x) < 20:
        return float("nan")
    roll = x.cummax()
    dd = (x - roll) / roll
    return float(abs(dd.min()))


def beta(asset_r: pd.Series, spy_r: pd.Series) -> float:
    a = pd.concat([asset_r.rename("a"), spy_r.rename("s")], axis=1).dropna().tail(252)
    if len(a) < 84:
        return float("nan")
    var = a["s"].var()
    if not np.isfinite(var) or var < 1e-10:
        return float("nan")
    return float(a["a"].cov(a["s"]) / var)


def zigzag_reversals(prices: pd.Series, delta: float) -> int:
    x = pd.to_numeric(prices, errors="coerce").dropna().to_numpy(dtype=float)
    x = x[np.isfinite(x) & (x > 0)]
    if len(x) < 2:
        return 0
    direction = 0
    extreme = x[0]
    reversals = 0
    for p in x[1:]:
        if direction == 0:
            if p >= extreme * (1 + delta):
                direction = 1
                extreme = p
            elif p <= extreme * (1 - delta):
                direction = -1
                extreme = p
            else:
                # Expand the potential excursion anchor only in the favorable direction
                # once a direction is established; before then keep the initial anchor.
                pass
        elif direction > 0:
            if p > extreme:
                extreme = p
            elif p <= extreme * (1 - delta):
                reversals += 1
                direction = -1
                extreme = p
        else:
            if p < extreme:
                extreme = p
            elif p >= extreme * (1 + delta):
                reversals += 1
                direction = 1
                extreme = p
    return reversals


def period_stats(g: pd.DataFrame) -> dict[str, float]:
    g = g.sort_values("date").dropna(subset=["adj_close"])
    if len(g) < 40:
        return {"n": float(len(g)), "hv": math.nan, "hor2": math.nan, "hor3": math.nan, "er": math.nan}
    r = log_returns(g["adj_close"])
    hv = float(r.std() * np.sqrt(252)) if len(r) >= 20 else math.nan
    years = max(len(g) / 252.0, 1e-9)
    hor2 = float(zigzag_reversals(g["adj_close"], 0.02) / years)
    hor3 = float(zigzag_reversals(g["adj_close"], 0.03) / years)
    path = float(r.abs().sum())
    er = float(abs(np.log(g["adj_close"].iloc[-1] / g["adj_close"].iloc[0])) / path) if path > 0 else math.nan
    return {"n": float(len(g)), "hv": hv, "hor2": hor2, "hor3": hor3, "er": er}


def snapshot_candidates(prices: pd.DataFrame, intervals: pd.DataFrame, recycled: set[str], t0: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    active = intervals[
        (intervals["start"] <= t0)
        & (intervals["end"].isna() | (intervals["end"] > t0))
        & (~intervals["ticker"].isin(recycled))
    ]["ticker"].dropna().astype(str).unique().tolist()

    # Keep enough history to reproduce 252d beta / 1y drawdown.
    lb = t0 - pd.Timedelta(days=550)
    hist = prices[(prices["ticker"].isin(active + ["SPY"])) & (prices["date"] >= lb) & (prices["date"] <= t0)].copy()
    spy = hist[hist["ticker"] == "SPY"].sort_values("date")
    spy_r = log_returns(spy.set_index("date")["adj_close"])

    recs = []
    with_price = 0
    for tk in active:
        g = hist[hist["ticker"] == tk].sort_values("date")
        if g.empty or g["date"].max() < t0 - pd.Timedelta(days=7):
            continue
        with_price += 1
        ar = log_returns(g.set_index("date")["adj_close"])
        if len(g) < 126 or len(ar) < 20:
            continue
        hv20 = float(ar.tail(20).std() * np.sqrt(252))
        b = beta(ar, spy_r)
        px = float(g["close"].dropna().iloc[-1]) if g["close"].notna().any() else math.nan
        recent20 = g.dropna(subset=["close", "volume"]).tail(20)
        adv = float((recent20["close"] * recent20["volume"]).mean()) if len(recent20) else math.nan
        mdd = max_drawdown(g["adj_close"])
        recs.append({
            "ticker": tk,
            "hv20": hv20,
            "beta": b,
            "price": px,
            "avg_dollar_vol": adv,
            "max_drawdown_1y": mdd,
        })
    df = pd.DataFrame(recs)
    mask_base = (
        df["hv20"].between(MIN_HV, MAX_HV, inclusive="both")
        & (df["price"] >= MIN_PRICE)
        & (df["beta"] >= MIN_BETA)
        & ((df["max_drawdown_1y"].isna()) | (df["max_drawdown_1y"] <= 0.70))
    )
    runtime = df[mask_base & ((df["avg_dollar_vol"].isna()) | (df["avg_dollar_vol"] >= SCORER_LIQ_USD))].copy()
    strict = df[mask_base & (df["avg_dollar_vol"] >= UNIVERSE_LIQ_USD)].copy()
    runtime = runtime.sort_values(["hv20", "ticker"], ascending=[False, True]).reset_index(drop=True)
    strict = strict.sort_values(["hv20", "ticker"], ascending=[False, True]).reset_index(drop=True)
    meta = {
        "active_members": len(active),
        "members_with_recent_price": with_price,
        "coverage_pct": round(100 * with_price / len(active), 2) if active else None,
        "eligible_runtime_2m": len(runtime),
        "eligible_liq50m": len(strict),
        "top10_overlap_2m_vs_50m": len(set(runtime.head(10)["ticker"]) & set(strict.head(10)["ticker"])),
    }
    return strict, meta


def cohort_period(prices: pd.DataFrame, cohort: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, min_bars: int) -> pd.DataFrame:
    sub = prices[
        (prices["ticker"].isin(cohort["ticker"]))
        & (prices["date"] >= start)
        & (prices["date"] <= end)
    ][["date", "ticker", "adj_close"]].copy()
    rows = []
    for tk, g in sub.groupby("ticker"):
        s = period_stats(g)
        if s["n"] < min_bars:
            continue
        rows.append({"ticker": tk, **s})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.merge(cohort[["ticker", "hv20"]], on="ticker", how="left")
    for col in ["hv", "hor2", "hor3"]:
        out[f"{col}_pctile"] = out[col].rank(pct=True, method="average")
    # Lower ER is better / more oscillatory.
    out["er_pctile_osc"] = (-out["er"]).rank(pct=True, method="average")
    return out


def summarize_period(df: pd.DataFrame, top: set[str]) -> dict:
    if df.empty:
        return {}
    df = df.copy()
    df["is_top"] = df["ticker"].isin(top)
    a = df[df["is_top"]]
    b = df[~df["is_top"]]
    out = {
        "n_cohort": int(len(df)),
        "n_top_available": int(len(a)),
        "median_top_hv_pctile": float(a["hv_pctile"].median()) if len(a) else math.nan,
        "median_top_hor2_pctile": float(a["hor2_pctile"].median()) if len(a) else math.nan,
        "median_top_hor3_pctile": float(a["hor3_pctile"].median()) if len(a) else math.nan,
        "median_top_er_osc_pctile": float(a["er_pctile_osc"].median()) if len(a) else math.nan,
        "top_share_hv_top_quartile": float((a["hv_pctile"] >= 0.75).mean()) if len(a) else math.nan,
        "top_share_hor2_top_quartile": float((a["hor2_pctile"] >= 0.75).mean()) if len(a) else math.nan,
    }
    valid = df[["hv20", "hv", "hor2", "hor3"]].dropna()
    if len(valid) >= 10:
        out["spearman_initial_hv20_future_hv"] = float(spearmanr(valid["hv20"], valid["hv"]).statistic)
        out["spearman_initial_hv20_future_hor2"] = float(spearmanr(valid["hv20"], valid["hor2"]).statistic)
        out["spearman_initial_hv20_future_hor3"] = float(spearmanr(valid["hv20"], valid["hor3"]).statistic)
    if len(a) >= 3 and len(b) >= 3:
        for col in ["hv", "hor2", "hor3"]:
            aa = a[col].dropna()
            bb = b[col].dropna()
            if len(aa) >= 3 and len(bb) >= 3:
                out[f"mw_p_top_vs_rest_{col}"] = float(mannwhitneyu(aa, bb, alternative="greater").pvalue)
    return out


def main() -> None:
    p_prices = download("prices")
    p_intervals = download("intervals")
    p_recycled = download("recycled")

    print("READ parquet ...", flush=True)
    prices = pd.read_parquet(p_prices, columns=["date", "ticker", "close", "volume", "adj_close"])
    intervals = pd.read_parquet(p_intervals)
    recycled = set(pd.read_csv(p_recycled)["ticker"].dropna().astype(str))
    prices["date"] = pd.to_datetime(prices["date"]).dt.tz_localize(None)
    intervals["start"] = pd.to_datetime(intervals["start"]).dt.tz_localize(None)
    intervals["end"] = pd.to_datetime(intervals["end"]).dt.tz_localize(None)
    prices["ticker"] = prices["ticker"].astype(str)
    intervals["ticker"] = intervals["ticker"].astype(str)
    data_end = prices["date"].max()

    result = {
        "dataset_end": str(data_end.date()),
        "method": {
            "score": "quant_invest current score: HV20 pure, descending",
            "filters_reconstructed": "PIT S&P membership; HV20 20-120%; price >=5; beta>=0.8; 1y DD<=70%; 20d dollar volume>=50M",
            "market_cap_limitation": "Historical market cap >=20B unavailable in source; S&P 500 PIT membership used as large-cap proxy.",
            "fundamental_health": "Not used retrospectively because quant_invest itself forbids current yfinance fundamentals in walk-forward.",
            "selection_frozen": True,
            "hor_definition": "Annualized zig-zag reversals of at least 2% / 3% on adjusted daily closes.",
        },
        "cuts": {},
    }

    for t0 in CUTS:
        cohort, meta = snapshot_candidates(prices, intervals, recycled, t0)
        top10 = cohort.head(10).copy()
        top_set = set(top10["ticker"])
        cut = {
            "selection_date": str(t0.date()),
            "meta": meta,
            "top10": top10[["ticker", "hv20", "beta", "price", "avg_dollar_vol", "max_drawdown_1y"]].round(6).to_dict("records"),
            "annual": {},
        }

        first_year = t0.year + 1
        for year in range(first_year, data_end.year + 1):
            start = pd.Timestamp(year=year, month=1, day=1)
            end = min(pd.Timestamp(year=year, month=12, day=31), data_end)
            min_bars = 100 if end.month >= 6 else 50
            yr = cohort_period(prices, cohort, start, end, min_bars=min_bars)
            cut["annual"][str(year)] = summarize_period(yr, top_set)

        bear = cohort_period(prices, cohort, BEAR_START, BEAR_END, min_bars=100)
        cut["bear_2022_peak_to_trough"] = summarize_period(bear, top_set)
        if not bear.empty:
            cut["bear_2022_top_details"] = bear[bear["ticker"].isin(top_set)][
                ["ticker", "hv", "hor2", "hor3", "er", "hv_pctile", "hor2_pctile", "hor3_pctile", "er_pctile_osc"]
            ].sort_values("hor2_pctile", ascending=False).round(6).to_dict("records")

        overall = cohort_period(prices, cohort, t0 + pd.Timedelta(days=1), data_end, min_bars=252)
        cut["full_forward"] = summarize_period(overall, top_set)
        if not overall.empty:
            cut["top10_forward_details"] = overall[overall["ticker"].isin(top_set)][
                ["ticker", "n", "hv", "hor2", "hor3", "er", "hv_pctile", "hor2_pctile", "hor3_pctile", "er_pctile_osc"]
            ].sort_values("hor2_pctile", ascending=False).round(6).to_dict("records")

        # Data survival / availability of frozen names.
        tails = prices[prices["ticker"].isin(top_set)].groupby("ticker")["date"].max()
        cut["top10_last_price_date"] = {tk: str(dt.date()) for tk, dt in tails.items()}
        result["cuts"][str(t0.date())] = cut

    # SPY return over the canonical 2022 bear peak-to-trough window.
    spy = prices[(prices["ticker"] == "SPY") & (prices["date"] >= BEAR_START) & (prices["date"] <= BEAR_END)].sort_values("date")
    if len(spy) >= 2:
        result["spy_2022_bear_return"] = float(spy["adj_close"].iloc[-1] / spy["adj_close"].iloc[0] - 1)

    Path("forward_test_result.json").write_text(json.dumps(result, indent=2, allow_nan=True), encoding="utf-8")

    for cut_name, cut in result["cuts"].items():
        print("\n=== CUT", cut_name, "===")
        print("META", json.dumps(cut["meta"], sort_keys=True))
        print("TOP10")
        for row in cut["top10"]:
            print(row)
        print("BEAR2022", json.dumps(cut["bear_2022_peak_to_trough"], sort_keys=True))
        print("FULL_FORWARD", json.dumps(cut["full_forward"], sort_keys=True))
        print("ANNUAL_MEDIANS")
        for year, s in cut["annual"].items():
            if s:
                print(year, json.dumps(s, sort_keys=True))
        print("TOP10_FORWARD_DETAILS")
        for row in cut.get("top10_forward_details", []):
            print(row)
    print("\nFORWARD_TEST_RESULT_JSON=" + json.dumps(result, separators=(",", ":"), allow_nan=True))


if __name__ == "__main__":
    main()
