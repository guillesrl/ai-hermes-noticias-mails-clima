#!/usr/bin/env python3
"""Ejecuta la etapa 1 y deja sus artefactos listos para el cron."""
from __future__ import annotations
import argparse, datetime as dt, json, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default=dt.date.today().isoformat()); ap.add_argument('--root',default='/home/ubuntu/.hermes/briefing-runs'); a=ap.parse_args()
    work=Path(a.root)/a.date; work.mkdir(parents=True,exist_ok=True)
    p=subprocess.run(['python3','/home/ubuntu/scripts/briefing_pipeline/collect_stage.py','--date',a.date,'--out',str(work)],text=True)
    status=json.loads((work/'status.json').read_text())
    print(json.dumps({'workdir':str(work),**status},ensure_ascii=False))
    return p.returncode
if __name__=='__main__': raise SystemExit(main())
