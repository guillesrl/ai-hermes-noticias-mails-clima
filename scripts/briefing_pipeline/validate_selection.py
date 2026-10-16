#!/usr/bin/env python3
"""Valida la respuesta del LM usando IDs de noticias, no coincidencia textual."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

NUMBERS = ('Uno','Dos','Tres','Cuatro','Cinco','Seis','Siete','Ocho','Nueve','Diez')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--response', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    root = Path(args.input)
    response = Path(args.response).read_text(encoding='utf-8', errors='replace').strip()
    source = json.loads((root / 'raw-news.json').read_text(encoding='utf-8')) if (root / 'raw-news.json').exists() else []
    ids = {str(x['id']) for x in source}
    empty_claim = bool(re.search(r'hoy no hay noticias nuevas', response, re.I))
    entries = []
    current = None
    for line in response.splitlines():
        match = re.match(r'^\s*(Uno|Dos|Tres|Cuatro|Cinco|Seis|Siete|Ocho|Nueve|Diez)\.\s+(.*)', line)
        if match:
            if current:
                entries.append(current)
            text = match.group(2).strip()
            id_match = re.search(r'\bID\s*[:=]\s*([A-Za-z0-9]+)\b', text, re.I)
            current = {'number': match.group(1), 'text': text, 'id': id_match.group(1) if id_match else None}
        elif current and line.strip():
            current['text'] += ' ' + line.strip()
    if current:
        entries.append(current)
    errors = []
    if source and empty_claim:
        errors.append('La entrada contiene noticias pero la respuesta afirma que no hay noticias.')
    if not source:
        errors.append('La fuente no contiene noticias estructuradas.')
    if len(entries) > 10:
        errors.append('Hay más de diez noticias.')
    for item in entries:
        if len(item['text'].split()) < 8:
            errors.append(f"Entrada {item['number']} demasiado corta.")
        if not item['id']:
            errors.append(f"Falta el ID de la noticia en {item['number']}.")
        elif item['id'] not in ids:
            errors.append(f"ID inexistente en {item['number']}: {item['id']}")
    result = {'stage': 'selection', 'valid': not errors and bool(entries), 'source_entries': len(source), 'selected_entries': len(entries), 'errors': errors, 'response': response}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['valid'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
