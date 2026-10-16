#!/usr/bin/env python3
"""Etapa 3: composición segura del briefing y promoción atómica."""
from __future__ import annotations
import argparse, json, os, re, tempfile
from pathlib import Path

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
    def spoken(value: str, fallback: str) -> str:
        value = (value or '').strip()
        if not value:
            return fallback
        value = re.sub(r'^[+−-]', '', value)
        value = value.replace('°C', ' grados').replace('°', ' grados')
        value = value.replace('%', ' por ciento')
        value = re.sub(r'↖', 'noroeste ', value).replace('↗', 'noreste ')
        value = value.replace('↘', 'sureste ').replace('↙', 'suroeste ')
        value = value.replace('→', 'este ').replace('←', 'oeste ')
        value = value.replace('↑', 'norte ').replace('↓', 'sur ')
        value = re.sub(r'(?P<n>\\d+)km/h', r'\\g<n> kilómetros por hora', value)
        return re.sub(r'\\s+', ' ', value).strip()
    condition = spoken(weather.get('condition'), 'Condición no disponible')
    temp = spoken(weather.get('temp'), 'temperatura no disponible')
    max_temp = spoken(weather.get('max_temp'), 'temperatura máxima no disponible')
    humidity = spoken(weather.get('humidity'), 'humedad no disponible')
    wind = spoken(weather.get('wind'), 'viento no disponible')
    lines = ['Buenos días Guille, aquí va tu briefing.', '', f'En Andorra hoy: {condition}, {temp}, máxima {max_temp} grados, humedad {humidity}, viento {wind}.', '', 'Mails pendientes:', args.emails.strip(), '', 'Y en noticias de IA y tecnología:']
    for item in selection['response'].splitlines():
        item = item.strip()
        if re.match(r'^(Uno|Dos|Tres|Cuatro|Cinco|Seis|Siete|Ocho|Nueve|Diez)\.\s+', item):
            item = re.sub(r'\s*\(?ID\s*[:=]\s*[A-Za-z0-9]+\)?\s*', ' ', item, count=1, flags=re.I).strip()
            lines.append(item)
    lines += ['', 'Eso es todo por hoy.']
    text = '\n'.join(lines).strip() + '\n'
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
