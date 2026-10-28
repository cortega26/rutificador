"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const raiz = path.resolve(__dirname, "../..");
const leer = (nombre) => fs.readFileSync(path.join(raiz, nombre), "utf8");
const landing = leer("docs/empresas/auditoria-rut.md");

test("navegación B2B está disponible desde inicio, playground y README", () => {
  assert.match(leer("mkdocs.yml"), /empresas\/auditoria-rut\.md/);
  assert.match(leer("docs/index.md"), /\]\(empresas\/auditoria-rut\.md\)/);
  assert.match(leer("docs/guia/playground.md"), /\]\(\.\.\/empresas\/auditoria-rut\.md\)/);
  assert.match(leer("README.md"), /tooltician\.com\/rutificador\/empresas\/auditoria-rut\//);
  assert.match(landing, /\]\(\.\.\/guia\/playground\.md\)/);
});

test("los CTAs B2B contienen únicamente etiquetas UTM fijas y el fragmento de contacto real", () => {
  const enlaces = [...landing.matchAll(/\]\((https:\/\/tooltician\.com\/es\/\?[^)]+)\)/g)]
    .map((match) => new URL(match[1]));
  assert.ok(enlaces.length >= 3, "debe haber CTAs con variantes de intención");
  const variantes = new Set();
  for (const url of enlaces) {
    assert.equal(url.origin, "https://tooltician.com");
    assert.equal(url.pathname, "/es/");
    assert.equal(url.hash, "#contact");
    assert.deepEqual(
      [...url.searchParams.keys()].sort(),
      ["utm_campaign", "utm_content", "utm_medium", "utm_source"]
    );
    assert.equal(url.searchParams.get("utm_source"), "rutificador");
    assert.equal(url.searchParams.get("utm_medium"), "referral");
    assert.equal(url.searchParams.get("utm_campaign"), "auditoria_rut_b2b");
    assert.ok(["diagnostico", "recurrente"].includes(url.searchParams.get("utm_content")));
    variantes.add(url.searchParams.get("utm_content"));
    // Ningún registro, RUT individual o nombre viaja por el enlace.
    assert.doesNotMatch(url.search, /\b\d{7,8}-[0-9k]\b|@|nombre|archivo|rut_entrada/i);
  }
  assert.deepEqual([...variantes].sort(), ["diagnostico", "recurrente"]);
});

test("la oferta separa producto gratuito de servicios aún no implementados", () => {
  assert.match(landing, /2 MiB y 15\.000 registros/);
  assert.match(landing, /no sube su contenido/);
  assert.match(landing, /no una función ya disponible/);
  assert.match(landing, /no existe todavía una tarifa cerrada/i);
  assert.match(landing, /no.*identidad.*estado tributario.*SII/);
  assert.match(landing, /3 UF/);
  assert.match(landing, /6 UF\/mes/);
  assert.match(landing, /no adjuntes listas de RUT/i);
  assert.doesNotMatch(landing, /<script|<form|<iframe|fetch\(|localStorage|sendBeacon/i);
});

test("la modalidad de contacto permite identificar respuestas sin SDK analítico", () => {
  assert.match(landing, /mailto:carlos@tooltician\.com\?subject=Rutificador/);
  assert.match(landing, /menciona «Rutificador»/i);
  assert.match(landing, /formulario y el correo son canales externos/);
});
