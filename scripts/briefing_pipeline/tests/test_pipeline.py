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
assert compose.spoken_temperature('-5°C', 'fallback') == 'cinco grados bajo cero'
assert compose.spoken_temperature('+6°C', 'fallback') == 'seis grados'
assert compose.spoken_temperature('12', 'fallback') == 'doce grados'
assert compose.spoken('↖4km/h', 'fallback') == 'noroeste cuatro kilómetros por hora'
assert compose.spoken('↓ 9 km/h', 'fallback') == 'sur nueve kilómetros por hora'
assert compose.spoken_wind('↓9 KM/H', 'fallback') == 'sur nueve kilómetros por hora'
assert compose.spoken_wind('0km/h', 'fallback') == 'calma, sin viento'
assert compose.spoken('45%', 'fallback') == '45 por ciento'
assert compose.spoken('45 percent', 'fallback') == '45 por ciento'
assert compose.spoken('45 PERCENTAGE', 'fallback') == '45 por ciento'
assert compose.weather_sentence({'condition': '', 'temp': '', 'max_temp': '', 'humidity': '', 'wind': ''}) == 'Clima no disponible.'
assert compose.weather_sentence({'condition': 'Soleado', 'temp': '21°C', 'max_temp': '24°C', 'humidity': '45%', 'wind': '0km/h'}) == 'En Andorra hoy: Soleado, veintiuno grados, máxima veinticuatro grados, humedad 45 por ciento, viento calma, sin viento.'
assert compose.spoken_numbers('20.000 y 100.000 y 1.000.000') == 'veinte mil y cien mil y un millón'
assert compose.spoken('La empresa tiene 20.000 usuarios y 1.000.000 de visitas.', 'fallback') == 'La empresa tiene veinte mil usuarios y un millón de visitas.'

collect_spec=importlib.util.spec_from_file_location('collect_stage','/opt/proyectos/noticias-ia/scripts/briefing_pipeline/collect_stage.py')
assert collect_spec is not None and collect_spec.loader is not None
collect=importlib.util.module_from_spec(collect_spec); collect_spec.loader.exec_module(collect)
assert collect.wind_direction(0) == 'norte'
assert collect.wind_direction(96) == 'este'
assert collect.WMO_CONDITIONS[0] == 'Cielo despejado'
print('OK: temperaturas sin cero negativo y unidades pronunciables')
