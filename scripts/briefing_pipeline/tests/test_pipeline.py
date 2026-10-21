#!/usr/bin/env python3
"""Pruebas de regresión para validación por IDs y fallos."""
import json, subprocess, tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    source=[{'id':'abc123','source':'Fuente','title':'Titular de IA','summary':'Resumen'}]
    (root/'raw-news.json').write_text(json.dumps(source),encoding='utf-8')
    (root/'raw-news.txt').write_text('[abc123] [2026-10-16 10:00] Fuente: Titular de IA\n    Resumen\n',encoding='utf-8')
    good=root/'good.txt'; good.write_text('Uno. ID: abc123 Titular de IA. Resumen suficiente sobre un desarrollo tecnológico importante.',encoding='utf-8')
    out=root/'valid.json'
    p=subprocess.run(['python3','/home/ubuntu/scripts/briefing_pipeline/validate_selection.py','--input',str(root),'--response',str(good),'--output',str(out)],capture_output=True,text=True)
    assert p.returncode==0, p.stdout+p.stderr
    bad=root/'bad.txt'; bad.write_text('Hoy no hay noticias nuevas de tecnología.',encoding='utf-8')
    bad_out=root/'bad.json'
    p=subprocess.run(['python3','/home/ubuntu/scripts/briefing_pipeline/validate_selection.py','--input',str(root),'--response',str(bad),'--output',str(bad_out)],capture_output=True,text=True)
    assert p.returncode!=0
print('OK: validación por ID y rechazo de vacío falso')

import importlib.util
spec=importlib.util.spec_from_file_location('compose_stage','/opt/proyectos/noticias-ia/scripts/briefing_pipeline/compose_stage.py')
assert spec is not None and spec.loader is not None
compose=importlib.util.module_from_spec(spec); spec.loader.exec_module(compose)
assert compose.spoken_temperature('-0°C', 'fallback') == 'cero grados'
assert compose.spoken_temperature('+6°C', 'fallback') == 'seis grados'
assert compose.spoken_temperature('12', 'fallback') == 'doce grados'
assert compose.spoken('↖4km/h', 'fallback') == 'noroeste 4 kilómetros por hora'
print('OK: temperaturas sin cero negativo y unidades pronunciables')
