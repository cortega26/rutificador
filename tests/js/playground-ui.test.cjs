"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const motorCSV = require("../../docs/javascripts/csv-audit.js");

function construirPagina() {
  const elementos = new Map();
  const descargas = [];
  const scriptsExternos = [];
  const pythonGlobals = new Map();

  class Elemento {
    constructor(tag) {
      this.tagName = tag;
      this.children = [];
      this.listeners = new Map();
      this.value = "";
      this._textContent = "";
      this.disabled = false;
      this.files = [];
    }
    get textContent() {
      return this._textContent + this.children.map((child) => child.textContent).join("");
    }
    set textContent(texto) {
      this._textContent = String(texto);
      this.children = [];
    }
    addEventListener(nombre, manejador) {
      this.listeners.set(nombre, manejador);
    }
    async trigger(nombre) {
      const manejador = this.listeners.get(nombre);
      assert.ok(manejador, "falta manejador: " + nombre);
      return manejador();
    }
    appendChild(nodo) {
      this.children.push(nodo);
      if (this.tagName === "select" && this.children.length === 1) this.value = nodo.value;
    }
    replaceChildren() { this.children = []; this.value = ""; this._textContent = ""; }
    click() { /* descarga disparada localmente */ }
    remove() { /* descarga disparada localmente */ }
  }

  const ids = [
    "rut-input", "rut-salida", "rut-csv-archivo", "rut-csv-separador",
    "rut-csv-columna", "rut-csv-auditar", "rut-csv-descargar",
    "rut-csv-estado", "rut-csv-resumen", "rut-validar"
  ];
  ids.forEach((id) => elementos.set(id, new Elemento(id === "rut-csv-columna" ? "select" : "input")));
  elementos.get("rut-csv-separador").value = "auto";
  elementos.get("rut-input").value = "12.345.678-5";

  const fakePyodide = {
    globals: {
      set: (clave, valor) => pythonGlobals.set(clave, valor),
      delete: (clave) => pythonGlobals.delete(clave)
    },
    loadPackage: async () => undefined,
    pyimport: () => ({ install: async () => undefined }),
    runPython(programa) {
      if (programa.startsWith("globals().pop")) return null;
      if (programa.includes("_version_paquete('rutificador')")) return "2.4.0";
      assert.ok(programa.includes("Rut.parse"));
      return {
        toJs: () => ["valido", "12345678-5", ""],
        destroy: () => undefined
      };
    },
    async runPythonAsync(programa) {
      assert.ok(programa.includes("Rut.parse"));
      const valores = JSON.parse(pythonGlobals.get("rutificador_csv_json"));
      return JSON.stringify(valores.map((rut) =>
        rut === "12.345.678-5" || rut === "12345678-5"
          ? { estado: "valido", normalizado: "12345678-5", errores: [] }
          : { estado: "invalido", normalizado: "12345678-9", errores: ["DV_DISCORDANTE"] }
      ));
    }
  };
  const document = {
    getElementById: (id) => {
      assert.ok(elementos.has(id), "missing DOM node " + id);
      return elementos.get(id);
    },
    createElement: (tag) => new Elemento(tag),
    head: {
      appendChild(nodo) {
        scriptsExternos.push(nodo.src);
        nodo.onload();
      }
    },
    body: new Elemento("body")
  };
  let blob = null;
  const sandbox = {
    document,
    RutificadorCSV: motorCSV,
    TextDecoder,
    Blob,
    URL: {
      createObjectURL(b) {
        blob = b;
        descargas.push(b);
        return "blob:fake-local";
      },
      revokeObjectURL: () => undefined
    },
    loadPyodide: async () => fakePyodide,
    setTimeout: (callback) => callback(),
    console: {
      log: () => { throw new Error("no loguear datos personales"); }
    }
  };

  const md = fs.readFileSync(path.resolve(__dirname, "../../docs/guia/playground.md"), "utf8");
  const script = [...md.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
  vm.runInNewContext(script, sandbox);
  return { elementos, descargas, scriptsExternos, pythonGlobals, blob: () => blob };
}

test("flujo UI: importar → seleccionar RUT → auditar → descargar (sin enviar archivo)", async () => {
  const pagina = construirPagina();
  const get = (id) => pagina.elementos.get(id);
  const csv = "\uFEFFRUT,Nombre,Comentario\n" +
    "12.345.678-5,Ana,Señora\n" +
    "12345678-5,Bea,=2+2\n" +
    "12345678-9,Caro,Mensaje\n";
  const buffer = new TextEncoder().encode(csv);
  get("rut-csv-archivo").files = [{
    size: buffer.byteLength, arrayBuffer: async () => buffer.buffer
  }];
  await get("rut-csv-archivo").trigger("change");
  assert.equal(get("rut-csv-columna").value, "RUT");
  assert.equal(get("rut-csv-auditar").disabled, false);
  await get("rut-csv-auditar").trigger("click");
  assert.equal(get("rut-csv-descargar").disabled, false);
  assert.match(get("rut-csv-resumen").textContent, /Válidos: 2/);
  assert.match(get("rut-csv-resumen").textContent, /Duplicados adicionales: 1/);
  assert.equal(pagina.pythonGlobals.size, 0, "no conservar los valores cargados en Python");
  assert.match(get("rut-csv-estado").textContent, /rutificador 2\.4\.0/);
  await get("rut-csv-descargar").trigger("click");
  assert.equal(pagina.descargas.length, 1);
  const texto = await pagina.blob().text();
  const filas = motorCSV.leerCSV(texto, ",");
  assert.equal(filas.length, 4);
  assert.equal(filas[2][2], "'=2+2");
  assert.equal(filas[3][6], "DV_DISCORDANTE");
  assert.deepEqual(pagina.scriptsExternos, [
    "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js"
  ]);
});

test("validación individual informa la versión del motor realmente verificada", async () => {
  const pagina = construirPagina();
  await pagina.elementos.get("rut-validar").trigger("click");
  assert.match(pagina.elementos.get("rut-salida").textContent, /motor: rutificador 2\.4\.0/);
});

test("cambiar columna invalida la descarga anterior", async () => {
  const pagina = construirPagina();
  const get = (id) => pagina.elementos.get(id);
  const csv = "RUT,Referencia\n1-9,Ana\n";
  const buffer = new TextEncoder().encode(csv);
  get("rut-csv-archivo").files = [{ size: buffer.byteLength, arrayBuffer: async () => buffer.buffer }];
  await get("rut-csv-archivo").trigger("change");
  await get("rut-csv-auditar").trigger("click");
  assert.equal(get("rut-csv-descargar").disabled, false);
  await get("rut-csv-columna").trigger("change");
  assert.equal(get("rut-csv-descargar").disabled, true);
});

test("archivo sobre el límite se rechaza antes de leerlo", async () => {
  const pagina = construirPagina();
  const get = (id) => pagina.elementos.get(id);
  get("rut-csv-archivo").files = [{
    size: 2 * 1024 * 1024 + 1,
    arrayBuffer: async () => { throw new Error("no debe leerse"); }
  }];
  await get("rut-csv-archivo").trigger("change");
  assert.match(get("rut-csv-estado").textContent, /demasiado grande/);
  assert.equal(get("rut-csv-auditar").disabled, true);
});
