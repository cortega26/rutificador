# Auditoría de RUT para empresas

**¿Importas listas de clientes o proveedores y te encuentras RUT mal escritos, formatos distintos o duplicados?** Rutificador permite localizar esos problemas antes de cargar los registros a otro sistema. Para flujos que se repiten, estamos evaluando una modalidad profesional de automatización y control.

[Probar auditoría CSV gratuita](../../guia/playground.md) · [Conversar sobre un control recurrente](https://tooltician.com/es/?utm_source=rutificador&utm_medium=referral&utm_campaign=auditoria_rut_b2b&utm_content=recurrente#contact)

## Tres problemas concretos

### 1. Proveedores que aparecen más de una vez

Un listado puede contener el mismo RUT como `12.345.678-5` y `12345678-5`. Normalizar antes de comparar ayuda a **identificar registros duplicados**, sin eliminar filas automáticamente. La decisión de fusionar fichas corresponde al dueño de los datos.

### 2. Clientes que fallan al importar al CRM o ERP

Una planilla con dígitos verificadores incorrectos, valores vacíos y formatos inconsistentes puede generar reprocesos. La auditoría marca las filas problemáticas y permite devolver al equipo un **CSV con el diagnóstico por registro** y todas las columnas originales.

### 3. Archivos que llegan todas las semanas o meses

Si debes hacer las mismas verificaciones sobre exportaciones sucesivas, se puede estudiar un flujo con controles de calidad, umbrales de error, ejecución repetible y reporte de excepciones. **Esa automatización recurrente es una propuesta de servicio, no una función ya disponible en el playground gratuito.**

## Lo que puedes hacer hoy sin pagar

El [auditor CSV](../../guia/playground.md) ya está publicado:

- Analiza archivos UTF-8 de hasta **2 MiB y 15.000 registros**, con selección de columna RUT.
- Distingue válidos, inválidos, incompletos, posibles y duplicados normalizados.
- Descarga un CSV con diagnósticos, manteniendo el orden y las demás columnas.
- Procesa el archivo **en tu navegador**: no sube su contenido a un servidor. La carga del motor Python sí utiliza descargas externas de Pyodide y PyPI.

El resultado indica **coherencia de formato y dígito verificador**, no existencia del RUT, identidad, estado tributario, vigencia comercial ni verificación en el SII. Tampoco reemplaza la revisión de duplicados de personas o empresas por otras reglas de negocio.

[Auditar un archivo ahora](../../guia/playground.md)

## Servicio recurrente: propuesta en validación

Para equipos de operaciones, administración o tecnología que realizan este control repetidamente, la oferta a explorar con [Tooltician](https://tooltician.com/es/) es la siguiente:

1. **Diagnóstico de encaje.** Definir las fuentes, el formato de los archivos, la frecuencia, la tasa tolerable de errores y quién recibe las excepciones. Basta un esquema o muestra sintética; no hace falta enviar datos de clientes.
2. **Implementación acotada, si existe encaje.** Configurar la validación usando Rutificador en un entorno acordado, con reglas versionadas, pruebas, manejo explícito de fallas y salida reproducible. Alcance y precio por escrito antes de implementar.
3. **Operación y mantenimiento opcionales.** Revisar cambios en los archivos, errores del proceso y ejecución periódica, con un responsable definido y documentación para traspaso. No se promete una plataforma SaaS ni una operación desatendida sin antes diseñarla.

### Referencia de precios, no plan de suscripción

Según las [tarifas generales de Tooltician](https://tooltician.com/es/), la conversación inicial de encaje es gratuita; el diagnóstico de alcance parte desde **3 UF** y se acredita a una implementación posterior. La automatización se cotiza por proyecto y el mantenimiento opcional parte desde **6 UF/mes**, según alcance.

**No existe todavía una tarifa cerrada ni una suscripción automatizada específica de Rutificador.** Estas cifras sirven para evaluar disposición a pagar por un servicio profesional, no para prometer que toda la implementación esté incluida en la mensualidad.

## Consultar sin enviar archivos ni RUT

Para determinar si el servicio tiene sentido, describe solamente:

- **Origen:** CSV exportado desde CRM, ERP, planilla u otra fuente.
- **Volumen aproximado:** número de filas y archivos por período, sin copiar registros.
- **Frecuencia:** semanal, mensual o antes de una importación.
- **Problema y resultado esperado:** duplicados, fallas de DV, control previo a carga, informe de excepciones.
- **Entorno y responsable:** quién ejecutaría y revisaría los resultados.

[Solicitar diagnóstico de este flujo](https://tooltician.com/es/?utm_source=rutificador&utm_medium=referral&utm_campaign=auditoria_rut_b2b&utm_content=diagnostico#contact)

[Explorar operación recurrente](https://tooltician.com/es/?utm_source=rutificador&utm_medium=referral&utm_campaign=auditoria_rut_b2b&utm_content=recurrente#contact)

También puedes escribir a [carlos@tooltician.com](mailto:carlos@tooltician.com?subject=Rutificador%20-%20Auditoria%20recurrente) con el asunto «Rutificador - Auditoría recurrente». Si utilizas el brief de Tooltician, menciona «Rutificador» para identificar el interés en este servicio. **No adjuntes listas de RUT ni otros datos personales en el primer contacto.**

Las consultas no comprometen una contratación. El formulario y el correo son canales externos al auditor y siguen sus propias condiciones de privacidad.
