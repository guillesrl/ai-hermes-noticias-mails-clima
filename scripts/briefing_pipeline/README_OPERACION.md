# Briefing matutino: arquitectura y operación

Este documento explica la reparación del briefing matutino de Hermes.

## Por qué se cambió

El cron anterior tenía un prompt de más de trece mil caracteres. Obligaba al modelo a ejecutar un único comando que mezclaba clima, RSS, Python embebido, deduplicación, Gmail, redacción, escritura y audio. Cuando una parte fallaba, el modelo podía terminar guardando “Hoy no hay noticias nuevas” aunque sí hubiera noticias.

El nuevo diseño separa el trabajo en etapas y deja registros intermedios.

## Componentes

- `/home/ubuntu/scripts/fetch-news-structured.py`: lector RSS estructurado con IDs estables.
- `/home/ubuntu/scripts/briefing_pipeline/collect_emails.py`: recopilación opcional de Gmail con estado independiente.
- `/home/ubuntu/scripts/briefing_pipeline/validate_selection.py`: validación de la respuesta del LM.
- `/home/ubuntu/scripts/briefing_pipeline/compose_stage.py`: composición y escritura atómica del briefing.
- `/home/ubuntu/scripts/briefing_pipeline/run_collection.py`: lanzador de la primera etapa.
- `/home/ubuntu/.hermes/scripts/briefing-collect.py`: entrada que usa el cron.
- `/home/ubuntu/.hermes/briefing-runs/AAAA-MM-DD/`: artefactos de cada ejecución.
- `/home/ubuntu/hermes-notes/news/`: briefing permanente.
- `/home/ubuntu/.hermes/audio_cache/`: audio entregado a Telegram.

## Flujo normal

1. Recopilación

   El cron ejecuta `/home/ubuntu/.hermes/scripts/briefing-collect.py`. El script usa `fetch-news.py`, recoge el clima y lee titulares anteriores. Guarda `weather.json`, `raw-news.txt`, `prior-headlines.json` y `status.json`.

2. Selección con LM

   El LM lee únicamente los datos recopilados. Selecciona hasta diez noticias distintas y las redacta en español. Su respuesta queda en `selection-response.txt`.

3. Validación

   `validate_selection.py` comprueba que la respuesta no diga que no hay noticias cuando sí existen, que haya entre una y siete entradas y que cada titular proceda de la entrada original. Un error detiene el flujo.

4. Composición

   `compose_stage.py` combina clima, mails y selección validada. Escribe primero un archivo temporal y luego lo promociona atómicamente a `briefing-manana-AAAA-MM-DD.md`.

5. Audio

   Solo después se llama a TTS. El audio se guarda en `~/.hermes/audio_cache/briefing-AAAA-MM-DD.ogg` y se comprueba que no esté vacío.

## Diagnóstico

- `news_status: failed`: falló RSS o el script de recopilación.
- `news_status: empty`: no llegaron titulares; no se debe inventar ni reutilizar el briefing anterior.
- `selection.json` inválido: falló el LM o la selección no pasó las reglas. El límite actual es diez noticias. Para no superar el límite del audio, el cron pide resúmenes de 25 a 35 palabras y un texto final de menos de 3900 caracteres.
- `composition-status.json` inválido: falló la construcción del texto.
- Audio inexistente o de cero bytes: falló TTS.

Nunca se debe convertir una excepción en “Hoy no hay noticias”. Solo se puede afirmar que no hay noticias cuando la recopilación terminó correctamente y devolvió cero entradas.

## Pruebas realizadas

- Compilación Python de los scripts: correcta.
- Prueba positiva de validación: correcta.
- Recopilación real: 46 noticias, clima correcto, 32 titulares previos.
- Selección real de prueba: 7 noticias válidas.
- Composición real: 7 noticias conservadas en el Markdown y 3297 caracteres.

## Mantenimiento

Si cambia una fuente RSS, modificar `fetch-news.py`. Si cambia el formato, modificar `compose_stage.py`. Si cambia el criterio de selección, modificar el prompt corto del cron y mantener las validaciones mecánicas.
