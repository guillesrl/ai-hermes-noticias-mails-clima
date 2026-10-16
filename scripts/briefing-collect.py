#!/usr/bin/env python3
"""Etapa 1 del cron: recopila datos y devuelve la carpeta de trabajo."""
from __future__ import annotations
import datetime as dt, json, subprocess
from pathlib import Path

DAY=dt.date.today().isoformat()
ROOT=Path('/home/ubuntu/.hermes/briefing-runs')/DAY
ROOT.mkdir(parents=True,exist_ok=True)
p=subprocess.run(['python3','/home/ubuntu/scripts/briefing_pipeline/collect_stage.py','--date',DAY,'--out',str(ROOT)],text=True)
status=json.loads((ROOT/'status.json').read_text())
print(json.dumps({'workdir':str(ROOT),**status},ensure_ascii=False))
raise SystemExit(p.returncode)
