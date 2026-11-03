#!/usr/bin/env python3
"""Recopila Gmail opcionalmente y lo guarda como estado estructurado."""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path


def sender_name(value: str) -> str:
    """Reduce un remitente MIME a un nombre breve, sin exponer direcciones."""
    value = (value or '').strip()
    match = re.match(r'\s*"?([^<"]+?)"?\s*<[^>]+>', value)
    return (match.group(1) if match else value).strip() or 'Remitente desconocido'


def brief(item: dict) -> str:
    """Una línea por correo: nunca insertar el snippet crudo en el briefing."""
    sender = sender_name(str(item.get('from', '')))
    subject = re.sub(r'\s+', ' ', str(item.get('subject', '')).strip())
    return f'- {sender}: {subject or "Sin asunto"}.'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = path.with_name('emails_summary.txt')
    script = Path('/home/ubuntu/.hermes/skills/productivity/google-workspace/scripts/google_api.py')
    query = 'is:unread in:inbox category:primary -category:promotions newer_than:2d'
    if not script.exists():
        result = {'stage': 'emails', 'status': 'failed', 'items': [], 'summary': 'No hay mails pendientes.', 'error': 'google_api.py no existe'}
    else:
        try:
            process = subprocess.run(['python3', str(script), 'gmail', 'search', query, '--max', '10'], capture_output=True, text=True, timeout=45)
            if process.returncode:
                result = {'stage': 'emails', 'status': 'failed', 'items': [], 'summary': 'No hay mails pendientes.', 'error': process.stderr.strip() or process.stdout.strip()}
            else:
                try:
                    data = json.loads(process.stdout or '[]')
                except json.JSONDecodeError:
                    result = {'stage': 'emails', 'status': 'failed', 'items': [], 'summary': 'No hay mails pendientes.', 'error': 'salida no JSON: ' + (process.stdout or process.stderr)[:500]}
                else:
                    items = data if isinstance(data, list) else []
                    result = {
                        'stage': 'emails',
                        'status': 'ok' if items else 'empty',
                        'items': items,
                        'summary': '\n'.join(brief(item) for item in items) if items else 'No hay mails pendientes.',
                        'error': '',
                    }
        except Exception as exc:
            result = {'stage': 'emails', 'status': 'failed', 'items': [], 'summary': 'No hay mails pendientes.', 'error': str(exc)}
    summary_path.write_text(result['summary'] + '\n', encoding='utf-8')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
