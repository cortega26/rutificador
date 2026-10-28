# Playground interactivo

Verifica RUTs individualmente o **audita hasta 15.000 registros de un archivo CSV** (máximo 2 MiB). Detecta formatos inconsistentes, errores y registros duplicados, y descarga el resultado sin alterar tu archivo original.

**Privacidad:** el procesamiento ocurre en tu navegador. Ni los RUT ni el contenido del archivo se envían al servidor. Al iniciar la validación, el navegador sí descarga el motor [Pyodide](https://pyodide.org) y la biblioteca `rutificador` desde proveedores externos.

## Validación individual

<div class="rut-ui rut-individual">
  <div class="rut-field">
    <label for="rut-input">RUT a validar</label>
    <div class="rut-inline">
      <input id="rut-input" type="text" inputmode="text" autocomplete="off" spellcheck="false" value="12.345.678-5" aria-describedby="rut-salida" />
      <button id="rut-validar" class="rut-btn rut-btn--primary" type="button">Validar RUT</button>
    </div>
  </div>
  <p id="rut-salida" class="rut-feedback" role="status" aria-live="polite"></p>
  <p id="rut-version" class="rut-feedback" role="status" aria-live="polite"></p>
</div>

## Auditoría de archivo CSV

Selecciona un archivo **CSV UTF-8** con encabezados y campos separados por comas o puntos y comas. El informe conserva las filas y columnas originales y añade el diagnóstico de cada RUT.

<aside class="rut-sample">
  <strong>¿No tienes un archivo a mano?</strong>
  <a href="../../ejemplos/auditoria-demo.csv" download="rutificador-demo.csv">Descarga un CSV de ejemplo</a> con registros ficticios para probar el flujo.
</aside>

<div class="rut-ui rut-audit">
  <div class="rut-grid">
    <div class="rut-field rut-field--full">
      <label for="rut-csv-archivo">1. Selecciona el archivo CSV</label>
      <input id="rut-csv-archivo" type="file" accept=".csv,text/csv" aria-describedby="rut-csv-limites" />
      <small id="rut-csv-limites">Máximo 2 MiB y 15.000 registros. Solo lectura local.</small>
    </div>
    <div class="rut-field">
      <label for="rut-csv-separador">2. Separador del archivo</label>
      <select id="rut-csv-separador">
        <option value="auto">Detectar automáticamente</option>
        <option value=",">Coma (,)</option>
        <option value=";">Punto y coma (;)</option>
      </select>
    </div>
    <div class="rut-field">
      <label for="rut-csv-columna">3. Columna que contiene el RUT</label>
      <select id="rut-csv-columna" disabled>
        <option value="">Selecciona primero un archivo</option>
      </select>
    </div>
  </div>
  <div class="rut-actions">
    <button id="rut-csv-auditar" class="rut-btn rut-btn--primary" type="button" disabled>Auditar archivo</button>
    <button id="rut-csv-descargar" class="rut-btn rut-btn--secondary" type="button" disabled>Descargar resultados CSV</button>
  </div>
  <p id="rut-csv-estado" class="rut-feedback" role="status" aria-live="polite"></p>
  <div id="rut-csv-resumen" class="rut-stats" role="group" aria-label="Resumen de auditoría" aria-live="polite"></div>
</div>

**Cómo interpretar el resultado:** «válido» solo indica que el formato y el dígito verificador concuerdan; **no prueba que el RUT exista ni identifica a una persona**. «Posible» e «incompleto» se informan por separado. Los duplicados se detectan únicamente entre RUTs válidos normalizados. La auditoría cuenta todas las filas de un grupo duplicado y, por separado, los registros adicionales sobre el primero. Los CSV sin cabecera, con filas irregulares o con comillas malformadas se rechazan sin descartar registros silenciosamente.

<script src="../../javascripts/csv-audit.js"></script>
<script>
(function () {
  "use strict";
  var PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js";
  // La versión publicada en PyPI debe coincidir con la instalada en Pyodide.
  var VERSION_ESPERADA = "2.4.0";
  var PAQUETE = "rutificador==" + VERSION_ESPERADA;
  var pyodide = null;
  var cargando = null;
  var entrada = document.getElementById("rut-input");
  var resultadoIndividual = document.getElementById("rut-salida");
  var versionMotor = document.getElementById("rut-version");
  var archivoInput = document.getElementById("rut-csv-archivo");
  var separadorInput = document.getElementById("rut-csv-separador");
  var columnaInput = document.getElementById("rut-csv-columna");
  var botonAuditar = document.getElementById("rut-csv-auditar");
  var botonDescargar = document.getElementById("rut-csv-descargar");
  var estado = document.getElementById("rut-csv-estado");
  var resumen = document.getElementById("rut-csv-resumen");
  var datos = null;
  var csvExportado = null;
  var revision = 0;
  var procesando = false;

  function mostrar(elemento, texto) { elemento.textContent = texto; }
  function cargarScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("No se pudo cargar Pyodide.")); };
      document.head.appendChild(s);
    });
  }
  function obtenerPyodide() {
    if (pyodide) return Promise.resolve(pyodide);
    if (!cargando) {
      cargando = cargarScript(PYODIDE_URL)
        .then(function () { return loadPyodide(); })
        .then(function (p) {
          return p.loadPackage("micropip").then(function () {
            return p.pyimport("micropip").install(PAQUETE).then(function () {
              var versionInstalada = p.runPython(
                "from importlib.metadata import version as _version_paquete\n" +
                "_version_paquete('rutificador')"
              );
              if (versionInstalada !== VERSION_ESPERADA) {
                throw new Error("Versión inesperada del motor: " + versionInstalada);
              }
              mostrar(versionMotor, "Motor Python: rutificador " + versionInstalada);
              return p;
            });
          });
        });
    }
    return cargando.then(function (p) {
      pyodide = p;
      return p;
    }, function (error) {
      cargando = null;
      throw error;
    });
  }
  function mostrarEstadisticas(cifras) {
    resumen.replaceChildren();
    [
      ["Total", cifras.total],
      ["Válidos", cifras.validos],
      ["Inválidos", cifras.invalidos],
      ["Posibles", cifras.posibles],
      ["Incompletos", cifras.incompletos],
      ["Normalizados", cifras.normalizados],
      ["Filas en grupos duplicados", cifras.filas_en_grupos_duplicados],
      ["Duplicados adicionales", cifras.duplicados_adicionales]
    ].forEach(function (entrada) {
      var tarjeta = document.createElement("div");
      tarjeta.className = "rut-stat";
      var etiqueta = document.createElement("span");
      etiqueta.className = "rut-stat-label";
      etiqueta.textContent = entrada[0] + ": ";
      var valor = document.createElement("strong");
      valor.className = "rut-stat-value";
      valor.textContent = String(entrada[1]);
      tarjeta.appendChild(etiqueta);
      tarjeta.appendChild(valor);
      resumen.appendChild(tarjeta);
    });
  }
  function errorLegible(error) {
    return error && error.message ? error.message : "Se produjo un error al procesar el archivo.";
  }
  function invalidar() {
    revision += 1;
    datos = null;
    csvExportado = null;
    botonDescargar.disabled = true;
    botonAuditar.disabled = true;
    columnaInput.disabled = true;
    columnaInput.replaceChildren();
    mostrar(resumen, "");
  }
  async function inspeccionarArchivo() {
    invalidar();
    var miRevision = revision;
    mostrar(estado, "");
    var archivo = archivoInput.files && archivoInput.files[0];
    if (!archivo) return;
    if (archivo.size > 2 * 1024 * 1024) {
      mostrar(estado, "Archivo demasiado grande: máximo 2 MiB.");
      return;
    }
    try {
      var texto = new TextDecoder("utf-8", { fatal: true })
        .decode(await archivo.arrayBuffer());
      if (miRevision !== revision) return;
      var inspeccion = RutificadorCSV.inspeccionar(texto, separadorInput.value);
      if (miRevision !== revision) return;
      datos = inspeccion;
      inspeccion.cabeceras.forEach(function (cabecera) {
        var opcion = document.createElement("option");
        opcion.value = cabecera;
        opcion.textContent = cabecera;
        columnaInput.appendChild(opcion);
      });
      var sugerida = inspeccion.cabeceras.find(function (c) {
        return /^(rut|run|rut[_ -]?cliente|rut[_ -]?proveedor)$/i.test(c.trim());
      });
      if (sugerida) columnaInput.value = sugerida;
      columnaInput.disabled = false;
      botonAuditar.disabled = false;
      mostrar(estado, "Archivo cargado localmente: " +
        (inspeccion.filas.length - 1) + " registros. Selecciona la columna RUT.");
    } catch (error) {
      mostrar(estado, errorLegible(error));
    }
  }
  archivoInput.addEventListener("change", inspeccionarArchivo);
  separadorInput.addEventListener("change", inspeccionarArchivo);
  columnaInput.addEventListener("change", function () {
    csvExportado = null;
    botonDescargar.disabled = true;
    mostrar(resumen, "");
  });

  document.getElementById("rut-validar").addEventListener("click", async function () {
    var valor = entrada.value.trim();
    if (!valor) {
      mostrar(resultadoIndividual, "Escribe un RUT para validarlo.");
      return;
    }
    mostrar(resultadoIndividual, "Cargando motor de validación…");
    try {
      var p = await obtenerPyodide();
      p.globals.set("rutificador_entrada", valor);
      var respuesta;
      try {
        var resultadoProxy = p.runPython(
          "from rutificador import Rut\n" +
          "def _rutificador_validar_uno():\n" +
          "    resultado = Rut.parse(rutificador_entrada)\n" +
          "    return (resultado.estado, resultado.normalizado or '', resultado.errores[0].codigo if resultado.errores else '')\n" +
          "_rutificador_validar_uno()"
        );
        try {
          respuesta = resultadoProxy.toJs();
        } finally {
          resultadoProxy.destroy();
        }
      } finally {
        p.globals.delete("rutificador_entrada");
        p.runPython("globals().pop('_rutificador_validar_uno', None)");
      }
      mostrar(resultadoIndividual, respuesta[0] + 
        (respuesta[1] ? " — normalizado: " + respuesta[1] : "") +
        (respuesta[2] ? " — código: " + respuesta[2] : ""));
    } catch (_error) {
      mostrar(resultadoIndividual, "No se pudo cargar el validador. Revisa tu conexión.");
    }
  });

  botonAuditar.addEventListener("click", async function () {
    if (!datos || procesando) return;
    var miRevision = revision;
    procesando = true;
    botonAuditar.disabled = true;
    botonDescargar.disabled = true;
    csvExportado = null;
    mostrar(resumen, "");
    mostrar(estado, "Validando localmente…");
    try {
      var columna = columnaInput.value;
      var index = datos.cabeceras.indexOf(columna);
      if (index < 0) throw new Error("Selecciona una columna RUT.");
      var valores = datos.filas.slice(1).map(function (fila) { return fila[index]; });
      var p = await obtenerPyodide();
      if (miRevision !== revision) return;
      p.globals.set("rutificador_csv_json", JSON.stringify(valores));
      var jsonResultados;
      try {
        // Entrada por globals, nunca interpolada en código Python.
        jsonResultados = await p.runPythonAsync(
          "import json\n" +
          "from rutificador import Rut\n" +
          "def _rutificador_auditar_valores():\n" +
          "    valores = json.loads(rutificador_csv_json)\n" +
          "    salida = []\n" +
          "    for valor in valores:\n" +
          "        resultado = Rut.parse(valor)\n" +
          "        salida.append({'estado': resultado.estado, 'normalizado': resultado.normalizado, " +
          "'errores': [e.codigo for e in resultado.errores]})\n" +
          "    return json.dumps(salida, ensure_ascii=False)\n" +
          "_rutificador_auditar_valores()\n"
        );
      } finally {
        p.globals.delete("rutificador_csv_json");
        p.runPython("globals().pop('_rutificador_auditar_valores', None)");
      }
      if (miRevision !== revision) return;
      var informe = RutificadorCSV.auditar(datos, columna, JSON.parse(jsonResultados));
      csvExportado = informe.csv;
      botonDescargar.disabled = false;
      var s = informe.resumen;
      mostrarEstadisticas(s);
      mostrar(estado, "Auditoría terminada. Archivo preparado para descargar.");
    } catch (error) {
      mostrar(estado, errorLegible(error));
    } finally {
      procesando = false;
      botonAuditar.disabled = !datos;
    }
  });

  botonDescargar.addEventListener("click", function () {
    if (!csvExportado) return;
    var url = URL.createObjectURL(new Blob([csvExportado], {
      type: "text/csv;charset=utf-8"
    }));
    var enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "rutificador-auditoria.csv";
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });
})();
</script>
