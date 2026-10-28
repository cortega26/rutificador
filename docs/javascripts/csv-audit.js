/* Auditoría CSV de Rutificador: datos siempre locales, sin red ni almacenamiento. */
(function (raiz) {
  "use strict";

  var COLUMNAS = [
    "rutificador_fila",
    "rutificador_estado",
    "rutificador_normalizado",
    "rutificador_errores",
    "rutificador_duplicado"
  ];

  function leerCSV(texto, separador) {
    if (typeof texto !== "string" || (separador !== "," && separador !== ";")) {
      throw new Error("CSV o separador no válido.");
    }
    var fuente = texto.charCodeAt(0) === 0xfeff ? texto.slice(1) : texto;
    if (!fuente || fuente.indexOf("\0") !== -1) {
      throw new Error("El archivo está vacío o contiene caracteres NUL.");
    }
    var filas = [], fila = [], campo = "", estado = "inicio";
    function terminarCampo() {
      fila.push(campo);
      campo = "";
      estado = "inicio";
    }
    function terminarFila() {
      terminarCampo();
      filas.push(fila);
      fila = [];
    }
    for (var i = 0; i < fuente.length; i += 1) {
      var ch = fuente[i];
      if (estado === "entrecomillado") {
        if (ch === '"') {
          if (fuente[i + 1] === '"') {
            campo += '"';
            i += 1;
          } else {
            estado = "cierre";
          }
        } else {
          campo += ch;
        }
        continue;
      }
      var salto = ch === "\n" || ch === "\r";
      if (estado === "cierre" && ch !== separador && !salto) {
        throw new Error("CSV malformado: contenido después de comillas de cierre.");
      }
      if (ch === separador) {
        terminarCampo();
      } else if (salto) {
        terminarFila();
        if (ch === "\r" && fuente[i + 1] === "\n") i += 1;
      } else if (ch === '"' && estado === "inicio") {
        estado = "entrecomillado";
      } else if (ch === '"') {
        throw new Error("CSV malformado: comillas dentro de un campo sin escapar.");
      } else {
        campo += ch;
        estado = "sincomillas";
      }
    }
    if (estado === "entrecomillado") {
      throw new Error("CSV malformado: campo entrecomillado sin cerrar.");
    }
    // Un salto de línea terminal no genera una fila fantasma.
    if (fila.length || campo.length || estado !== "inicio" ||
        (fuente[fuente.length - 1] !== "\n" && fuente[fuente.length - 1] !== "\r")) {
      terminarFila();
    }
    return filas;
  }

  function inspeccionar(texto, preferencia) {
    var delimitador = preferencia || "auto";
    var filas;
    if (delimitador === "auto") {
      var candidatos = [",", ";"].map(function (d) {
        try {
          var r = leerCSV(texto, d);
          return { delimitador: d, filas: r, ancho: r[0] ? r[0].length : 0 };
        } catch (_error) {
          return { delimitador: d, filas: null, ancho: 0 };
        }
      });
      var anchosMultiples = candidatos.filter(function (c) { return c.ancho > 1; });
      if (anchosMultiples.length > 1) {
        throw new Error("Delimitador ambiguo: selecciona coma o punto y coma.");
      }
      var elegido = anchosMultiples[0] || candidatos.find(function (c) { return c.filas; });
      if (!elegido) throw new Error("No se pudo interpretar el CSV.");
      delimitador = elegido.delimitador;
      filas = elegido.filas;
    } else {
      filas = leerCSV(texto, delimitador);
    }
    if (!filas.length) throw new Error("El CSV no contiene cabecera.");
    var cabeceras = filas[0];
    if (cabeceras.some(function (c) { return !c.trim(); })) {
      throw new Error("La cabecera contiene columnas sin nombre.");
    }
    var nombres = cabeceras.map(function (c) { return c.toLowerCase(); });
    if (new Set(nombres).size !== nombres.length) {
      throw new Error("La cabecera contiene columnas duplicadas.");
    }
    if (cabeceras.some(function (c) { return /^\s*\d[\d.]*-[\dkK]\s*$/.test(c); })) {
      throw new Error("Parece faltar la cabecera: la primera fila contiene un RUT.");
    }
    if (nombres.some(function (c) { return COLUMNAS.indexOf(c) !== -1; })) {
      throw new Error("Ya existen columnas rutificador_* reservadas. Renómbralas antes de auditar.");
    }
    if (filas.length > 15001) {
      throw new Error("Límite inicial: 15.000 registros por archivo.");
    }
    filas.slice(1).forEach(function (fila, i) {
      if (fila.length !== cabeceras.length) {
        throw new Error("Fila " + (i + 2) + ": " + fila.length +
          " columnas; se esperaban " + cabeceras.length + ". No se omitieron registros.");
      }
    });
    return { filas: filas, cabeceras: cabeceras, delimitador: delimitador };
  }

  function neutralizarFormula(valor) {
    var texto = String(valor == null ? "" : valor);
    if (/^[\s\uFEFF]*[=+\-@]/.test(texto) || /^[\t\r\n]/.test(texto)) return "'" + texto;
    return texto;
  }

  function escribirCSV(filas, delimitador) {
    return "\uFEFF" + filas.map(function (fila) {
      return fila.map(function (celda) {
        var s = neutralizarFormula(celda);
        if (s.includes(delimitador) || s.includes('"') ||
            s.includes("\r") || s.includes("\n")) {
          return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
      }).join(delimitador);
    }).join("\r\n") + "\r\n";
  }

  function auditar(datos, columna, validaciones) {
    if (!datos || !Array.isArray(datos.filas) || !datos.cabeceras) {
      throw new Error("Primero debes importar un CSV válido.");
    }
    var indice = datos.cabeceras.indexOf(columna);
    if (indice < 0) throw new Error("Selecciona una columna RUT existente.");
    var registros = datos.filas.slice(1);
    if (!Array.isArray(validaciones) || validaciones.length !== registros.length) {
      throw new Error("La cantidad de resultados de validación no coincide con el CSV.");
    }
    var conteos = new Map();
    var resumen = {
      total: registros.length, validos: 0, invalidos: 0,
      incompletos: 0, posibles: 0, normalizados: 0,
      filas_en_grupos_duplicados: 0, duplicados_adicionales: 0
    };
    validaciones.forEach(function (resultado, i) {
      if (!resultado || ["valido", "invalido", "incompleto", "posible"].indexOf(resultado.estado) === -1 ||
          !Array.isArray(resultado.errores)) {
        throw new Error("Resultado de validación inválido en fila " + (i + 2) + ".");
      }
      if (resultado.estado === "valido") {
        resumen.validos += 1;
        var rut = resultado.normalizado;
        if (!rut) throw new Error("Resultado válido sin RUT normalizado.");
        conteos.set(rut, (conteos.get(rut) || 0) + 1);
      } else if (resultado.estado === "invalido") {
        resumen.invalidos += 1;
      } else if (resultado.estado === "incompleto") {
        resumen.incompletos += 1;
      } else {
        resumen.posibles += 1;
      }
      if (resultado.normalizado && resultado.estado === "valido" &&
          registros[i][indice] !== resultado.normalizado) {
        resumen.normalizados += 1;
      }
    });
    conteos.forEach(function (numero) {
      if (numero > 1) {
        resumen.filas_en_grupos_duplicados += numero;
        resumen.duplicados_adicionales += numero - 1;
      }
    });
    var salida = [datos.cabeceras.concat(COLUMNAS)];
    registros.forEach(function (fila, i) {
      var res = validaciones[i];
      var duplicado = res.estado === "valido" &&
        (conteos.get(res.normalizado) || 0) > 1;
      salida.push(fila.concat([
        String(i + 2), res.estado, res.normalizado || "",
        res.errores.join("|"), duplicado ? "si" : "no"
      ]));
    });
    return { resumen: resumen, csv: escribirCSV(salida, datos.delimitador) };
  }

  var api = {
    inspeccionar: inspeccionar,
    auditar: auditar,
    leerCSV: leerCSV,
    neutralizarFormula: neutralizarFormula
  };
  raiz.RutificadorCSV = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
