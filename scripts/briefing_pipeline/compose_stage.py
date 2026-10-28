#!/usr/bin/env python3
"""Etapa 3: composición segura del briefing y promoción atómica."""
from __future__ import annotations
import argparse, json, os, re, tempfile
from pathlib import Path

SMALL_NUMBERS = {
    0: 'cero', 1: 'uno', 2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco',
    6: 'seis', 7: 'siete', 8: 'ocho', 9: 'nueve', 10: 'diez', 11: 'once',
    12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince', 16: 'dieciséis',
    17: 'diecisiete', 18: 'dieciocho', 19: 'diecinueve',
}
TENS = {20: 'veinte', 30: 'treinta', 40: 'cuarenta', 50: 'cincuenta'}
HUNDREDS = {100: 'cien', 200: 'doscientos', 300: 'trescientos', 400: 'cuatrocientos', 500: 'quinientos', 600: 'seiscientos', 700: 'setecientos', 800: 'ochocientos', 900: 'novecientos'}
WIND_SPEED_RE = re.compile(r'(?P<n>\d+)\s*km\s*/\s*h', re.IGNORECASE)

def number_words(value: int) -> str:
    if value in SMALL_NUMBERS:
        return SMALL_NUMBERS[value]
    if value in TENS:
        return TENS[value]
    if 20 < value < 30:
        return f'veinti{SMALL_NUMBERS[value - 20]}'
    if 30 < value < 60:
        return f'{TENS[value // 10 * 10]} y {SMALL_NUMBERS[value % 10]}'
    if 60 <= value < 100:
        tens, units = divmod(value, 10)
        return f'{number_words(tens * 10)} y {SMALL_NUMBERS[units]}' if units else number_words(tens * 10)
    if value == 100:
        return 'cien'
    if 100 < value < 200:
        return f'ciento {number_words(value - 100)}'
    if 200 <= value < 1000:
        hundreds, remainder = divmod(value, 100)
        prefix = HUNDREDS[hundreds * 100]
        return f'{prefix} {number_words(remainder)}' if remainder else prefix
    if 1000 <= value < 1000000:
        thousands, remainder = divmod(value, 1000)
        prefix = 'mil' if thousands == 1 else f'{number_words(thousands)} mil'
        return f'{prefix} {number_words(remainder)}' if remainder else prefix
    if 1000000 <= value < 1000000000:
        millions, remainder = divmod(value, 1000000)
        prefix = 'un millón' if millions == 1 else f'{number_words(millions)} millones'
        return f'{prefix} {number_words(remainder)}' if remainder else prefix
    return str(value)

def spoken_numbers(value: str) -> str:
    """Convierte separadores de miles y números grandes a palabras para TTS."""
    def replace(match):
        try:
            return number_words(int(match.group(0).replace('.', '').replace(',', '')))
        except ValueError:
            return match.group(0)
    return re.sub(r'(?<![\w])\d{1,3}(?:[.,]\d{3})+(?![\w])', replace, value)

def spoken_temperature(value: str, fallback: str) -> str:
    raw = (value or '').strip().replace('−', '-')
    match = re.search(r'([+-]?\d+)', raw)
    if not match:
        return fallback
    number = int(match.group(1))
    # Nunca permitir que la salida hablada contenga "menos cero" o "-0".
    if number < 0:
        return f'{number_words(abs(number))} grados bajo cero'
    return f'{number_words(number)} grados'

def spoken(value: str, fallback: str) -> str:
    value = (value or '').strip()
    if not value:
        return fallback
    value = re.sub(r'^[+−-]', '', value)
    value = value.replace('°C', ' grados').replace('°', ' grados')
    value = value.replace('%', ' por ciento')
    # El TTS puede interpretar "percent" en inglés aunque el resto del texto
    # esté en español. Normalizar también la palabra evita que se cuele en
    # clima, titulares o resúmenes de noticias.
    value = re.sub(r'\bpercent(?:age)?\b', 'por ciento', value, flags=re.I)
    value = spoken_numbers(value)
    value = re.sub(r'↖', 'noroeste ', value).replace('↗', 'noreste ')
    value = value.replace('↘', 'sureste ').replace('↙', 'suroeste ')
    value = value.replace('→', 'este ').replace('←', 'oeste ')
    value = value.replace('↑', 'norte ').replace('↓', 'sur ')
    value = WIND_SPEED_RE.sub(
        lambda match: f'{number_words(int(match.group("n")))} kilómetros por hora',
        value,
    )
    return re.sub(r'\s+', ' ', value).strip()

def spoken_wind(value: str, fallback: str) -> str:
    raw = (value or '').strip()
    match = WIND_SPEED_RE.search(raw)
    if match and int(match.group('n')) == 0:
        return 'calma, sin viento'
    return spoken(raw, fallback)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--workdir', required=True)
    ap.add_argument('--emails', default='No hay mails pendientes.')
    ap.add_argument('--output-dir', default='/home/ubuntu/hermes-notes/news')
    args = ap.parse_args()
    root = Path(args.workdir)
    weather = json.loads((root/'weather.json').read_text(encoding='utf-8'))['data']
    selection = json.loads((root/'selection.json').read_text(encoding='utf-8'))
    if not selection.get('valid'):
        print(json.dumps({'stage':'composition','valid':False,'error':'selection inválida','details':selection.get('errors',[])},ensure_ascii=False))
        return 2

    condition = spoken(weather.get('condition'), 'Condición no disponible')
    temp = spoken_temperature(weather.get('temp'), 'temperatura no disponible')
    max_temp = spoken_temperature(weather.get('max_temp'), 'temperatura máxima no disponible')
    humidity = spoken(weather.get('humidity'), 'humedad no disponible')
    wind = spoken_wind(weather.get('wind'), 'viento no disponible')
    lines = ['Buenos días Guille, aquí va tu briefing.', '', f'En Andorra hoy: {condition}, {temp}, máxima {max_temp}, humedad {humidity}, viento {wind}.', '', 'Mails pendientes:', args.emails.strip(), '', 'Y en noticias de IA y tecnología:']
    for item in selection['response'].splitlines():
        item = item.strip()
        if re.match(r'^(Uno|Dos|Tres|Cuatro|Cinco|Seis|Siete|Ocho|Nueve|Diez)\.\s+', item):
            item = re.sub(r'\s*\(?ID\s*[:=]\s*[A-Za-z0-9]+\)?\s*', ' ', item, count=1, flags=re.I).strip()
            lines.append(item)
    lines += ['', 'Eso es todo por hoy.']
    text = '\n'.join(lines).strip() + '\n'
    # Última barrera: los textos de noticias vienen del modelo y pueden traer
    # símbolos o la palabra inglesa aunque el clima ya esté normalizado.
    text = text.replace('%', ' por ciento')
    text = re.sub(r'\bpercent(?:age)?\b', 'por ciento', text, flags=re.I)
    text = spoken_numbers(text)
    selected_numbers = re.findall(r'^(Uno|Dos|Tres|Cuatro|Cinco|Seis|Siete|Ocho|Nueve|Diez)\.\s+', text, re.M)
    if len(selected_numbers) != int(selection.get('selected_entries', 0)):
        print(json.dumps({'stage':'composition','valid':False,'error':'No se conservaron todas las noticias seleccionadas'},ensure_ascii=False))
        return 2

    if 'Hoy no hay noticias nuevas' in text:
        print(json.dumps({'stage':'composition','valid':False,'error':'se intentó generar un briefing vacío'},ensure_ascii=False)); return 2
    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    final=outdir/f'briefing-manana-{args.date}.md'
    fd,tmp=tempfile.mkstemp(prefix=final.name+'.', dir=outdir); os.close(fd)
    Path(tmp).write_text(text,encoding='utf-8')
    os.replace(tmp, final)
    result={'stage':'composition','valid':True,'path':str(final),'news_count':selection['selected_entries'],'chars':len(text)}
    (root/'composition-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False)); return 0

if __name__ == '__main__': raise SystemExit(main())
