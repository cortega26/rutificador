import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO
from rutificador.cli import main


def test_cli_validate_json_file(tmp_path, capsys):
    f = tmp_path / "ruts.txt"
    f.write_text("12345678-5\n8.765.432-1\ninvalido")

    main(["validar", str(f), "--format", "json"])
    out, _ = capsys.readouterr()

    data = json.loads(out)
    assert len(data) == 3
    assert data[0]["valido"] is True
    assert data[0]["resultado"] == "12345678-5"
    assert data[2]["valido"] is False
    assert "codigo_error" in data[2]


def test_cli_format_csv_file(tmp_path, capsys):
    f = tmp_path / "ruts.txt"
    # Usar RUTs válidos: 12.345.678-5 y 1 (DV=9)
    f.write_text("12345678-5\n1-9")

    main(["formatear", str(f), "--format", "csv", "--separador-miles"])
    out, _ = capsys.readouterr()

    reader = csv.DictReader(StringIO(out))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["resultado"] == "12.345.678-5"
    assert rows[1]["resultado"] == "1-9"


def test_cli_validate_xml_file(tmp_path, capsys):
    f = tmp_path / "ruts.txt"
    f.write_text("12345678-5")

    main(["validar", str(f), "--format", "xml"])
    out, _ = capsys.readouterr()

    root = ET.fromstring(out)
    assert root.tag == "rutificador"
    assert root.find("registro/valido").text == "True"
