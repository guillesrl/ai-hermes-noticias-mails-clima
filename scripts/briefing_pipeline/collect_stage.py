#!/usr/bin/env python3
"""Etapa 1: recopilación determinista del briefing matutino.

Guarda clima, noticias RSS, titulares previos y status.json en un directorio
por ejecución. No llama al LM ni genera audio.
"""
from __future__ import annotations
import argparse, datetime as dt, json, re, subprocess
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = Path('/home/ubuntu/hermes-notes/news')
NEWS_SCRIPT = Path('/home/ubuntu/scripts/fetch-news-structured.py')

def run(cmd: list[str], timeout: int = 40) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, '', str(e)

WMO_CONDITIONS = {
    0: 'Cielo despejado', 1: 'Mayormente despejado', 2: 'Parcialmente nublado',
    3: 'Nublado', 45: 'Niebla', 48: 'Niebla con escarcha', 51: 'Llovizna ligera',
    53: 'Llovizna moderada', 55: 'Llovizna intensa', 56: 'Llovizna helada ligera',
    57: 'Llovizna helada intensa', 61: 'Lluvia ligera', 63: 'Lluvia moderada',
    65: 'Lluvia intensa', 66: 'Lluvia helada ligera', 67: 'Lluvia helada intensa',
    71: 'Nevada ligera', 73: 'Nevada moderada', 75: 'Nevada intensa', 77: 'Granizo',
    80: 'Chubascos ligeros', 81: 'Chubascos moderados', 82: 'Chubascos intensos',
    85: 'Chubascos de nieve ligeros', 86: 'Chubascos de nieve intensos',
    95: 'Tormenta', 96: 'Tormenta con granizo ligero', 99: 'Tormenta con granizo intenso',
}


def wind_direction(degrees: float) -> str:
    directions = ('norte', 'noreste', 'este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste')
    return directions[int((degrees % 360 + 22.5) // 45) % 8]


def weather() -> dict:
    """Consulta gratuita sin clave de Open-Meteo para las coordenadas de Andorra."""
    params = {
        'latitude': '42.5063', 'longitude': '1.5218', 'timezone': 'Europe/Andorra',
        'forecast_days': '1',
        'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m',
        'daily': 'temperature_2m_max',
    }
    url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)
    try:
        request = Request(url, headers={'User-Agent': 'Hermes-briefing/1.0 (personal local briefing)'})
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
        current = data['current']
        daily = data['daily']
        wind_speed = round(float(current['wind_speed_10m']))
        direction = wind_direction(float(current['wind_direction_10m']))
        out = {
            'condition': WMO_CONDITIONS.get(int(current['weather_code']), 'Condición no disponible'),
            'temp': f"{round(float(current['temperature_2m']))}°C",
            'max_temp': f"{round(float(daily['temperature_2m_max'][0]))}°C",
            'humidity': f"{round(float(current['relative_humidity_2m']))}%",
            'wind': f'{direction} {wind_speed} km/h',
        }
        return {'data': out, 'errors': [], 'source': 'Open-Meteo'}
    except Exception as exc:
        return {'data': {'condition': '', 'temp': '', 'max_temp': '', 'humidity': '', 'wind': ''}, 'errors': [str(exc)], 'source': 'Open-Meteo'}

def previous_headlines(today: str) -> list[str]:
    values = []
    for p in sorted(BASE.glob('briefing-manana-*.md'), reverse=True):
        if p.name == f'briefing-manana-{today}.md':
            continue
        if len(values) >= 30:
            break
        text = p.read_text(encoding='utf-8', errors='replace')
        section = text.split('Y en noticias', 1)[-1].split('Eso es todo', 1)[0]
        for line in section.splitlines():
            line = re.sub(r'^\s*(?:Uno|Dos|Tres|Cuatro|Cinco|Seis|Siete|Ocho|Nueve|Diez)\.\s*', '', line).strip()
            if line and not line.startswith('Hoy no hay') and len(line) > 10:
                values.append(line)
    return values

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=dt.datetime.now().date().isoformat())
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    w = weather()
    (out / 'weather.json').write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding='utf-8')
    news_json = out / 'raw-news.json'
    news_text = out / 'raw-news.txt'
    rc, stdout, err = run(['python3', str(NEWS_SCRIPT), '--hours', '24', '--json-out', str(news_json), '--text-out', str(news_text)], timeout=120)
    news = news_text.read_text(encoding='utf-8', errors='replace') if news_text.exists() else ''
    (out / 'raw-news.txt').write_text(news, encoding='utf-8')
    subprocess.run(['python3', '/home/ubuntu/scripts/briefing_pipeline/collect_emails.py', '--out', str(out / 'emails.json')], text=True, capture_output=True, timeout=60)
    prior = previous_headlines(args.date)
    (out / 'prior-headlines.json').write_text(json.dumps(prior, ensure_ascii=False, indent=2), encoding='utf-8')
    count = len(re.findall(r'^\[[^]]+\]\s+\[\d{4}-\d\d-\d\d ', news, re.M))
    email_status = 'unknown'
    try:
        email_status = json.loads((out / 'emails.json').read_text(encoding='utf-8')).get('status', 'unknown')
    except Exception:
        email_status = 'failed'
    status = {
        'stage': 'collection', 'date': args.date, 'news_returncode': rc,
        'news_entries': count, 'news_status': 'ok' if rc == 0 and count else ('empty' if rc == 0 else 'failed'),
        'email_status': email_status, 'weather_status': 'ok' if not w['errors'] else 'partial', 'weather_errors': w['errors'],
        'previous_headlines': len(prior), 'news_error': err.strip(),
    }
    (out / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(status, ensure_ascii=False))
    return 0 if rc == 0 and count else 2

if __name__ == '__main__':
    raise SystemExit(main())
