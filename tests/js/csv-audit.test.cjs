"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const csv = require("../../docs/javascripts/csv-audit.js");

function resultados() {
  return [
    { estado: "valido", normalizado: "12345678-5", errores: [] },
    { estado: "valido", normalizado: "12345678-5", errores: [] },
    { estado: "invalido", normalizado: "12345678-9", errores: ["DV_DISCORDANTE"] },
    { estado: "incompleto", normalizado: "", errores: ["RUT_VACIO"] },
    { estado: "posible", normalizado: "1-", errores: [] }
  ];
}

test("BOM UTF-8, comas, comillas escapadas, saltos de línea y columnas ajenas", () => {
  const entrada = "\uFEFFRUT,Nombre,Comentario\r\n" +
    '"12.345.678-5","Ana, María","Dijo ""hola""' + "\n" + 'ayer"\r\n' +
    "12345678-5,Bea,=2+2\r\n" +
    "12345678-9,C,@SUM(A1)\r\n" +
    ",D,  -2+3\r\n" +
    "1-,E,Texto\r\n";
  const inspeccion = csv.inspeccionar(entrada, "auto");
  assert.equal(inspeccion.delimitador, ",");
  assert.equal(inspeccion.filas.length, 6);
  assert.equal(inspeccion.filas[1][2], 'Dijo "hola"\nayer');
  const informe = csv.auditar(inspeccion, "RUT", resultados());
  assert.deepEqual(informe.resumen, {
    total: 5, validos: 2, invalidos: 1, incompletos: 1, posibles: 1,
    normalizados: 1, filas_en_grupos_duplicados: 2, duplicados_adicionales: 1
  });
  const filasSalida = csv.leerCSV(informe.csv, ",");
  assert.equal(filasSalida.length, 6);
  assert.equal(filasSalida[1][0], "12.345.678-5");
  assert.equal(filasSalida[1][2], 'Dijo "hola"\nayer');
  assert.equal(filasSalida[2][2], "'=2+2");
  assert.equal(filasSalida[3][2], "'@SUM(A1)");
  assert.equal(filasSalida[4][2], "'  -2+3");
  assert.equal(filasSalida[1][3], "2");
  assert.equal(filasSalida[5][3], "6");
  assert.equal(filasSalida[1][7], "si");
  assert.equal(filasSalida[2][7], "si");
  assert.equal(filasSalida[3][7], "no");
  assert.equal(filasSalida[3][6], "DV_DISCORDANTE");
});

test("separador punto y coma, preservación de orden y salto citado", () => {
  const inspeccion = csv.inspeccionar('RUT;Referencia\r\n"1-9";"A;B"\r\n"2-7";"Línea 1\nLínea 2"\r\n', "auto");
  assert.equal(inspeccion.delimitador, ";");
  assert.deepEqual(inspeccion.cabeceras, ["RUT", "Referencia"]);
  assert.equal(inspeccion.filas[2][1], "Línea 1\nLínea 2");
  const informe = csv.auditar(inspeccion, "RUT", [
    { estado: "valido", normalizado: "1-9", errores: [] },
    { estado: "invalido", normalizado: "2-7", errores: ["DV_DISCORDANTE"] }
  ]);
  assert.equal(informe.resumen.total, 2);
  assert.equal(csv.leerCSV(informe.csv, ";")[2][1], "Línea 1\nLínea 2");
});

test("rechaza filas irregulares sin perder registros", () => {
  assert.throws(() => csv.inspeccionar("RUT,Nombre\n1-9,Ana\n2-7\n", ","), /Fila 3/);
  assert.throws(() => csv.inspeccionar("RUT;Nombre\n1-9;Ana;Extra\n", ";"), /Fila 2/);
});

test("rechaza entradas sin cabecera, cabeceras repetidas y columnas reservadas", () => {
  assert.throws(() => csv.inspeccionar("12345678-5,Juan\n1-9,Ana\n", ","), /faltar la cabecera/);
  assert.throws(() => csv.inspeccionar("RUT,RUT\n1-9,1-9\n", ","), /duplicadas/);
  assert.throws(() => csv.inspeccionar("RUT,rutificador_estado\n1-9,a\n", ","), /reservadas/);
  assert.throws(() => csv.inspeccionar("RUT,\n1-9,a\n", ","), /sin nombre/);
});

test("rechaza sintaxis CSV malformada y bytes NUL", () => {
  assert.throws(() => csv.inspeccionar('RUT,Nombre\n"1-9,Juan', ","), /sin cerrar/);
  assert.throws(() => csv.inspeccionar('RUT,Nombre\n"1-9"x,Ana', ","), /después de comillas/);
  assert.throws(() => csv.inspeccionar('RUT,Nombre\n1-9,Ju"an', ","), /sin escapar/);
  assert.throws(() => csv.inspeccionar("RUT,Nombre\n\0,Juan", ","), /NUL/);
});

test("fórmulas CSV: neutraliza prefijos peligrosos sin alterar texto corriente", () => {
  for (const formula of ["=2+2", "+1", "-1", "@SUM(1)", " \t=CMD", "\n=CMD", "\t@CMD"]) {
    assert.ok(csv.neutralizarFormula(formula).startsWith("'"), formula);
  }
  assert.equal(csv.neutralizarFormula("12345678-5"), "12345678-5");
  assert.equal(csv.neutralizarFormula("Hola; mundo"), "Hola; mundo");
});

test("no se aceptan resultados inexistentes ni una columna no seleccionada", () => {
  const d = csv.inspeccionar("RUT,Nombre\n1-9,Juan\n", ",");
  assert.throws(() => csv.auditar(d, "RUN", [{ estado: "valido", normalizado: "1-9", errores: [] }]), /Selecciona/);
  assert.throws(() => csv.auditar(d, "RUT", []), /no coincide/);
  assert.throws(() => csv.auditar(d, "RUT", [{ estado: "desconocido", errores: [] }]), /inválido/);
});

test("límites de registros y delimitadores ambiguos", () => {
  const demasiado = "RUT,Nombre\n" + "1-9,Juan\n".repeat(15001);
  assert.throws(() => csv.inspeccionar(demasiado, ","), /15.000/);
  assert.throws(() => csv.inspeccionar("RUT,Nombre;Edad\n1-9,Juan;24\n", "auto"), /ambiguo/);
});

test("el JS del playground tiene sintaxis válida y no envía datos por red", () => {
  const vm = require("node:vm");
  const pagina = fs.readFileSync(path.resolve(__dirname, "../../docs/guia/playground.md"), "utf8");
  const scripts = [...pagina.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  new vm.Script(scripts[0][1]);
  assert.match(pagina, /rutificador==2\.3\.0/);
  assert.match(pagina, /p\.globals\.set\("rutificador_csv_json"/);
  assert.doesNotMatch(pagina, /fetch\(|XMLHttpRequest|sendBeacon|localStorage|sessionStorage/);
});
