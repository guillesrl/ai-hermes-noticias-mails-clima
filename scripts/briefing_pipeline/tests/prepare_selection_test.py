#!/usr/bin/env python3
"""Ejecuta recopilación y prepara una selección con IDs para una prueba del LM."""
from __future__ import annotations
import datetime as dt, json, subprocess
from pathlib import Path

DAY=dt.date.today().isoformat(); root=Path('/home/ubuntu/.hermes/briefing-runs')/DAY; root.mkdir(parents=True,exist_ok=True)
subprocess.run(['python3','/home/ubuntu/scripts/briefing_pipeline/collect_stage.py','--date',DAY,'--out',str(root)],check=False)
data=json.loads((root/'raw-news.json').read_text())
lines=[]
for i,item in enumerate(data[:10]):
    words=('Uno','Dos','Tres','Cuatro','Cinco','Seis','Siete','Ocho','Nueve','Diez')
    lines.append(f"{words[i]}. ID: {item['id']} {item['title']}. {item['summary'] or 'Noticia relevante de tecnología.'}")
(root/'selection-response.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'date':DAY,'entries':len(data),'selection_file':str(root/'selection-response.txt')},ensure_ascii=False))
