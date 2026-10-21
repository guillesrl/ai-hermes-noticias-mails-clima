# Pipeline del briefing matutino

## Objetivo

El briefing se divide en etapas pequeñas. La recopilación y las validaciones son deterministas; el modelo LM solo selecciona y redacta noticias. TTS solo se ejecuta después de que el texto ha sido validado y guardado.

## Flujo

1. Recopilación

   Script: `/home/ubuntu/scripts/briefing_pipeline/collect_stage.py`

   Ejecuta `fetch-news.py`, recoge el clima y lee titulares de briefings anteriores. Guarda:

   - `raw-news.json` con IDs estables, fuente, fecha, título y resumen.
- `raw-news.txt` como vista legible.
- `emails.json` con estado independiente.

   La salida queda en `/home/ubuntu/.hermes/briefing-runs/AAAA-MM-DD/`.

2. Selección con LM

   El cron debe leer únicamente `raw-news.txt` y `prior-headlines.json`, y pedir al LM que seleccione hasta diez noticias distintas y las redacte en español.

   La respuesta se guarda en `selection-response.txt`.

   No se permite responder “Hoy no hay noticias nuevas” si `status.json` indica que hay titulares.

3. Validación

   Script: `/home/ubuntu/scripts/briefing_pipeline/validate_selection.py`

   Comprueba que:

   - haya noticias de entrada;
   - no se declare falsamente que no hay noticias;
   - haya entre una y siete entradas;
   - cada entrada tenga contenido suficiente;
   - cada selección se pueda relacionar con un titular original.

   Si falla, se conserva el último briefing válido y se informa de que falló la etapa de selección.

4. Composición

   Script: `/home/ubuntu/scripts/briefing_pipeline/compose_stage.py`

   Combina clima, mails y selección validada. Escribe primero un archivo temporal y después lo promociona atómicamente a:

   `/home/ubuntu/hermes-notes/news/briefing-manana-AAAA-MM-DD.md`

   Antes de componer, las temperaturas se normalizan: `-0` y `+0` se convierten
   en `cero grados`, los valores negativos como `-5` en `cinco grados bajo cero`,
   y los valores habituales se escriben en palabras para evitar lecturas ambiguas
   del TTS (`seis grados`, `doce grados`). El viento también se escribe completo:
   `4km/h` se convierte en `cuatro kilómetros por hora`.

5. Audio

   Solo después de validar y guardar el Markdown se ejecuta `text_to_speech` con el modelo TTS actualmente configurado. El audio debe guardarse en:

   `/home/ubuntu/.hermes/audio_cache/briefing-AAAA-MM-DD.ogg`

   Hay que verificar que existe y que su tamaño es mayor que cero antes de entregar `MEDIA:`.

## Diagnóstico rápido

- `status.json` con `news_status: failed`: falló la recopilación RSS.
- `status.json` con `news_status: empty`: no llegaron titulares; no se debe inventar ni reutilizar el briefing anterior.
- `selection-validation.json` inválido: falló el LM o sus selecciones no pudieron validarse.
- `composition-status.json` inválido: falló la construcción del texto.
- Audio inexistente o de cero bytes: falló TTS.

## Prueba manual

```bash
D=$(date +%F)
W=/home/ubuntu/.hermes/briefing-runs/$D
python3 /home/ubuntu/scripts/briefing_pipeline/collect_stage.py --date "$D" --out "$W"
cat "$W/status.json"
cat "$W/raw-news.txt"
```

Después de generar `selection-response.txt` con el LM:

```bash
python3 /home/ubuntu/scripts/briefing_pipeline/validate_selection.py \
  --input "$W" \
  --response "$W/selection-response.txt" \
  --output "$W/selection-validation.json"
```

Si la validación es correcta:

```bash
python3 /home/ubuntu/scripts/briefing_pipeline/compose_stage.py \
  --date "$D" \
  --workdir "$W"
```

## Reglas de seguridad

- No sobrescribir un briefing válido con una respuesta vacía o inválida.
- No meter Python embebido dentro de un prompt shell enorme.
- No ejecutar recopilación, selección, composición y audio dentro de un único comando.
- No cambiar el modelo LM ni TTS como parte de esta reparación.
- Mantener los archivos de cada ejecución para localizar exactamente la etapa que falló.

## Estado de la migración

Los scripts de las tres etapas ya están creados y comprobados sintácticamente. El cron existente todavía debe migrarse a este flujo y probarse de extremo a extremo antes de considerarlo terminado.
