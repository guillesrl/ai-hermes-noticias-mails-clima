Informe de análisis y refuerzo del cron de noticias
Fecha: 16 de octubre de 2026
Cron: Briefing matutino, ID 42e2741205a0

1. Resumen ejecutivo

El fallo principal no fue el modelo LM ni el sistema TTS. El problema fue de arquitectura: el cron había convertido recopilación, procesamiento RSS, deduplicación, lectura de Gmail, redacción, escritura de archivos y generación de audio en un único flujo controlado por un prompt enorme y frágil.

Cuando una parte fallaba, el modelo no tenía una separación clara entre “no hay noticias” y “no pude procesar las noticias”. El resultado incorrecto fue guardar “Hoy no hay noticias nuevas de tecnología” aunque el script de fuentes sí devolvía noticias.

El sistema nuevo ya separa las fases y fue probado correctamente. En la ejecución de prueba produjo 46 noticias de entrada, seleccionó 7, generó el Markdown y creó un audio válido de 1.226.843 bytes.

2. Qué falló

2.1 Prompt excesivamente grande

El cron anterior tenía aproximadamente 13.398 caracteres. En el mismo prompt se mezclaban:

- consultas meteorológicas;
- extracción de temperatura y viento;
- ejecución de RSS;
- Python embebido dentro de shell;
- filtros y categorías;
- deduplicación;
- Gmail;
- redacción en español;
- escritura del archivo;
- generación TTS;
- respuesta MEDIA.

Esto aumentó la probabilidad de que el modelo omitiera pasos, alterara comandos o confundiera un error técnico con una respuesta válida.

Refuerzo: el prompt nuevo tiene aproximadamente 2.419 caracteres y delega la lógica repetitiva a scripts comprobables.

2.2 Un único comando terminal enorme

El diseño anterior obligaba a ejecutar clima, deduplicación y noticias en un solo comando. Los logs muestran errores de sintaxis de Bash, paréntesis mal cerrados, comillas rotas, pipes bloqueados por seguridad y scripts Python temporales incompletos.

Ejemplos observados:

- `unexpected EOF while looking for matching ')'`;
- `syntax error near unexpected token 'fi'`;
- `SyntaxError: unterminated string literal`;
- `NameError: name 'title' is not defined`;
- bloqueo del escáner por `python3 | python3`;
- bloqueo de comandos con contenido dinámico.

Refuerzo: la recopilación ahora vive en `collect_stage.py` y se ejecuta como un archivo Python normal. No se construye diariamente dentro del prompt.

2.3 Ausencia de contrato entre etapas

Antes no existía un formato firme para decir:

- la recopilación terminó correctamente;
- se encontraron cero noticias;
- la fuente falló;
- el modelo no pudo seleccionar;
- el archivo no se pudo escribir;
- el audio falló.

Por eso una salida vacía podía avanzar como si fuera correcta.

Refuerzo: cada ejecución produce `status.json`, con estado de recopilación, cantidad de noticias, errores del clima y salida del script RSS.

2.4 Error silencioso convertido en “no hay noticias”

El sistema no distinguía entre `empty` y `failed`. Esa es la causa funcional más importante del mensaje incorrecto.

Refuerzo:

- `news_status: ok`: hay noticias válidas;
- `news_status: empty`: la recopilación terminó bien pero no encontró entradas;
- `news_status: failed`: hubo un error técnico.

Solo `empty` permite afirmar que no hay noticias. `failed` detiene el flujo y conserva el último briefing válido.

2.5 Filtros demasiado frágiles

El filtro anterior dependía de muchas expresiones regulares y listas de palabras dentro del prompt. Podía descartar noticias válidas por no contener exactamente una palabra autorizada o aceptar una noticia por coincidir con una palabra demasiado amplia.

Refuerzo: el LM selecciona las noticias, pero la respuesta se valida mecánicamente contra los titulares originales. La validación no decide por sí sola qué es importante, pero evita que el modelo invente titulares o declare vacío un conjunto que no lo está.

2.6 Escrituras de archivos no seguras

Los logs registraron varios rechazos porque el agente intentaba sobrescribir archivos existentes sin haberlos leído completamente. También se detectó el riesgo de reemplazar un briefing válido por un archivo vacío o incompleto.

Refuerzo:

- cada ejecución trabaja en un directorio separado;
- la composición escribe primero un archivo temporal;
- solo después lo promueve atómicamente al nombre final;
- una validación fallida no reemplaza el briefing anterior.

2.7 Cambios de modelo y deriva de configuración

El cron antiguo fue creado con OpenRouter y `nvidia/nemotron-3-super-120b-a12b:free`. Posteriormente la configuración global cambió a OpenAI Codex y `gpt-5.6-luna`. Hermes llegó a omitir una ejecución por detectar deriva de proveedor y modelo.

También hubo errores HTTP 404 de Gemini y errores HTTP 429 de proveedor en meses anteriores.

Refuerzo actual:

- el cron está usando explícitamente `gpt-5.6-luna` con `openai-codex`;
- no se cambia el modelo como parte del pipeline de noticias;
- el flujo de datos está desacoplado del proveedor.

Mejora adicional recomendada: fijar explícitamente el modelo del cron mediante la opción de pin de Hermes y documentar cualquier cambio deliberado.

2.8 Fallos independientes de TTS

Entre el 12 y el 14 de octubre Edge TTS respondió HTTP 403. También se intentó usar Piper, pero el paquete no estaba instalado. Esto produjo ejecuciones donde el Markdown se generaba, pero el audio fallaba.

Refuerzo actual:

- el texto se guarda antes del audio;
- se comprueba que el archivo de audio existe y tiene tamaño mayor que cero;
- el fallo de audio ya no destruye el texto generado.

Mejora adicional recomendada: registrar en un archivo de estado el proveedor y voz utilizados, la ruta exacta, tamaño y hora de modificación del audio.

3. Puntos débiles que permanecen

3.1 El cron todavía depende del LM para coordinar varias herramientas

Aunque el prompt es mucho más pequeño, el LM aún debe ejecutar el script, leer archivos, escribir la selección, validar, componer, consultar Gmail y llamar a TTS.

Riesgo: puede omitir una etapa o no respetar una ruta.

Refuerzo recomendado: convertir el orquestador completo en un script controlado, dejando al LM únicamente la selección y redacción de noticias. El script debería invocar al LM con una interfaz estructurada y ejecutar automáticamente validación, composición y TTS.

3.2 La selección se guarda mediante write_file

La ejecución de prueba mostró que el archivo `selection-response.txt` ya existía y el primer intento de escritura fue rechazado por el verificador de mutaciones. El cron se recuperó leyendo y escribiendo posteriormente, pero sigue siendo un punto débil.

Refuerzo recomendado: crear un nombre único por ejecución o borrar el archivo temporal de selección al inicio mediante un script controlado. Mejor aún, que la respuesta del LM se capture directamente por un mecanismo de salida estructurada.

3.3 La validación de titulares puede ser demasiado estricta o demasiado laxa

La coincidencia textual actual funciona, pero los titulares pueden traducirse o resumirse. Una validación por texto exacto podría rechazar una buena selección; una validación demasiado flexible podría aceptar algo no relacionado.

Refuerzo recomendado:

- conservar un identificador estable por noticia en `fetch-news.py`;
- pedir al LM que devuelva esos identificadores;
- validar por identificador, no por coincidencia de texto;
- mantener el titular original únicamente para presentación.

3.4 Clima aún tiene normalización mejorable

La nueva composición convierte símbolos como grados, porcentaje y flechas, pero la prueba mostró una salida como “viento noreste 4km/h”. No es peligrosa, pero debería convertirse siempre a “viento del noreste a 4 kilómetros por hora”.

Refuerzo recomendado: guardar valores meteorológicos estructurados, no texto libre, y hacer la conversión final en una función única con pruebas.

3.5 Gmail sigue dentro del turno del LM

El acceso a Gmail puede fallar, tardar o devolver una salida inesperada. El cron debe tratar los mails como una sección opcional y no permitir que un fallo de Gmail bloquee las noticias.

Refuerzo recomendado: recopilar Gmail en una etapa independiente con `email_status: ok`, `empty` o `failed`, igual que las noticias.

3.6 No hay pruebas de fallo suficientes

Se probó el caso positivo, pero faltan pruebas automatizadas para:

- RSS vacío;
- RSS con error;
- respuesta del LM que dice falsamente que no hay noticias;
- más de siete noticias;
- titular inventado;
- archivo final inválido;
- TTS de cero bytes;
- fallo de Gmail.

Refuerzo recomendado: añadir una matriz de pruebas de regresión y ejecutarla antes de modificar el cron.

4. Arquitectura recomendada

Etapa A: recopilación determinista

Entrada: fuentes RSS, clima, Gmail y briefings anteriores.

Salida:

- `raw-news.json` con identificadores, fuente, fecha, título y resumen;
- `weather.json` estructurado;
- `emails.json` estructurado;
- `prior-headlines.json`;
- `status.json`.

Etapa B: selección del LM

Entrada: solo los datos estructurados y una instrucción corta.

Salida JSON esperada:

```json
{
  "stories": [
    {
      "id": "news-001",
      "title": "Título original",
      "summary_es": "Resumen en español"
    }
  ]
}
```

Etapa C: validación determinista

Comprueba IDs, cantidad, duplicados, longitud y ausencia de afirmaciones contradictorias.

Etapa D: composición determinista

Genera el Markdown mediante plantilla, incorpora clima y mails, valida secciones y promueve el archivo atómicamente.

Etapa E: TTS

Genera audio desde el texto validado, comprueba existencia, tamaño, fecha de modificación y proveedor.

Etapa F: entrega

Solo entrega `MEDIA:` cuando todas las etapas anteriores están en estado válido.

5. Prioridad de mejoras

Prioridad alta:

1. Separar Gmail de la coordinación del LM.
2. Usar IDs de noticias en lugar de comparar títulos por texto.
3. Evitar que `selection-response.txt` dependa de una escritura manual sobre un archivo existente.
4. Añadir pruebas de fallo y regresión.
5. Fijar explícitamente el modelo y proveedor del cron.

Prioridad media:

1. Convertir `raw-news.txt` a JSON estructurado.
2. Mejorar la normalización meteorológica.
3. Crear un estado global de ejecución con duración y errores por etapa.
4. Añadir limpieza controlada de ejecuciones antiguas.

Prioridad baja:

1. Añadir fuentes RSS alternativas.
2. Medir diversidad de fuentes.
3. Añadir métricas de noticias descartadas por duplicación o categoría.

6. Estado actual

La arquitectura nueva ya resolvió el fallo principal. La prueba real ejecutada el 16 de octubre obtuvo:

- 46 noticias recopiladas;
- clima correcto;
- 32 titulares anteriores;
- 7 noticias seleccionadas;
- 7 noticias conservadas en el Markdown;
- audio de 1.226.843 bytes;
- cron terminado con estado `ok`.

El sistema es ahora mucho más diagnosticable y resistente, pero todavía conviene completar la automatización del orquestador y las pruebas de fallos antes de considerarlo totalmente endurecido.
