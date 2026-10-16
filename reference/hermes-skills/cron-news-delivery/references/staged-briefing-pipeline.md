# Staged Briefing Pipeline

## Stage 1: deterministic collection

Use a small rerunnable script rather than inline shell and Python inside the LM prompt. Collect:

- weather values for Andorra;
- `/home/ubuntu/scripts/fetch-news.py 24` for the morning window, or the configured shorter evening window;
- the latest two or three briefing artifacts for prior-topic deduplication.

Write separate artifacts such as `weather.json`, `raw-news.txt`, `prior-topics.txt`, and `status.json`. The status must distinguish `empty`, `ok`, and `error`; an empty feed is not proof that there are no news stories until the collector has completed successfully.

## Stage 2: LM selection

Pass only the normalized news entries and prior topics to the LM. Require at most seven distinct stories, with source names preserved and no invented facts. Keep the output structured enough to validate, for example one JSON object per story with `title`, `source`, and `summary`.

Validate before composition:

- input news count greater than zero cannot produce an empty-news claim;
- output count is one through seven when collection status is `ok` and valid entries exist;
- each item has a non-empty title, source, and summary;
- each title matches or clearly corresponds to a collected title;
- no selected topic appears in the prior-topic set;
- malformed LM output is a stage failure, not a reason to fall back to a fabricated empty section.

If no valid stories remain after a successful, non-empty collection, preserve the raw input and record why each candidate was rejected. This makes an empty result auditable.

## Stage 3: composition and audio

Build the final plain-text briefing from validated structured data. Keep the permanent Markdown and TTS text derived from the same validated content. Write to a temporary path, verify weather, email, and news sections, then replace the dated artifact atomically. Generate audio only after the artifact passes validation, use an explicit path under `~/.hermes/audio_cache/`, and verify non-zero size and matching modification time.

On failure, do not overwrite the last valid dated briefing. Emit a concise diagnostic containing the failed stage and the artifact paths; do not silently convert a processing failure into “no hay noticias nuevas”.

## Minimal stage contract

A reliable run should expose these contracts:

- collection: `status`, `news_count`, `weather`, `raw_news_path`;
- selection: `status`, `selected_count`, `stories`, `rejected_reasons`;
- composition: `status`, `briefing_path`, `audio_path`;
- delivery: final response contains only the verified `MEDIA:` path.
