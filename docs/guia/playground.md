# Playground interactivo

Valida un RUT directamente en tu navegador: esta página carga
[Pyodide](https://pyodide.org) bajo demanda y usa la rueda oficial de
`rutificador` publicada en PyPI, sin servidor intermedio. El motor es el mismo
código Python puro del paquete, y su comportamiento esperado está fijado por el
[harness de conformidad](../conformidad.md).

<label for="rut-input">RUT a validar</label>
<input id="rut-input" type="text" inputmode="text" autocomplete="off" spellcheck="false" value="12.345.678-5" />
<button id="rut-validar" type="button">Validar</button>
<div id="rut-salida" aria-live="polite"></div>

<script>
(function () {
  // Versiones fijadas: no usar etiquetas móviles en el CDN.
  var PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/pyodide.js";
  var PAQUETE = "rutificador==2.2.1";
  var pyodide = null;
  var cargando = null;
  var salida = document.getElementById("rut-salida");
  var entrada = document.getElementById("rut-input");

  function mostrar(texto) {
    salida.textContent = texto;
  }

  function cargarScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("error de red")); };
      document.head.appendChild(s);
    });
  }

  function obtenerPyodide() {
    if (pyodide) {
      return Promise.resolve(pyodide);
    }
    if (!cargando) {
      cargando = cargarScript(PYODIDE_URL)
        .then(function () { return loadPyodide(); })
        .then(function (p) {
          return p.loadPackage("micropip").then(function () {
            var micropip = p.pyimport("micropip");
            return micropip.install(PAQUETE).then(function () { return p; });
          });
        });
    }
    return cargando.then(
      function (p) {
        pyodide = p;
        return p;
      },
      function (err) {
        cargando = null; // permitir reintento en el próximo clic
        throw err;
      }
    );
  }

  document.getElementById("rut-validar").addEventListener("click", function () {
    var valor = entrada.value.trim();
    if (!valor) {
      mostrar("Escribe un RUT para validarlo, por ejemplo 12.345.678-5.");
      return;
    }
    mostrar("cargando…");
    obtenerPyodide().then(
      function (p) {
        // JSON.stringify genera un literal válido también en Python para
        // entradas de texto simples; evita depender de la API de globals.
        var programa =
          "from rutificador import Rut\n" +
          "rut_entrada = " + JSON.stringify(valor) + "\n" +
          "r = Rut.parse(rut_entrada)\n" +
          "codigo = r.errores[0].codigo if r.errores else ''\n" +
          "str(r.estado) + '|' + str(r.normalizado or '') + '|' + str(codigo)";
        var partes = String(p.runPython(programa)).split("|");
        var estado = partes[0];
        var normalizado = partes[1];
        var codigo = partes[2];
        if (estado === "valido") {
          mostrar("válido — normalizado: " + normalizado);
        } else {
          mostrar(
            "inválido — estado: " + estado +
              (normalizado ? ", normalizado: " + normalizado : "") +
              (codigo ? ", código: " + codigo : "")
          );
        }
      },
      function () {
        mostrar("error de red — no se pudo cargar Pyodide o el paquete; revisa tu conexión e inténtalo de nuevo.");
      }
    );
  });
})();
</script>

> **Privacidad**: el RUT que escribes nunca sale de tu navegador, salvo la
> descarga del paquete `rutificador` desde PyPI al cargar el entorno.
