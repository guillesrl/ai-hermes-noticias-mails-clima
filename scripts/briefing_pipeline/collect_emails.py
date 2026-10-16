#!/usr/bin/env python3
"""Recopila Gmail opcionalmente y lo guarda como estado estructurado."""
from __future__ import annotations
import argparse, datetime as dt, json, os, subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); a=ap.parse_args()
    path=Path(a.out); path.parent.mkdir(parents=True,exist_ok=True)
    script=Path('/home/ubuntu/.hermes/skills/productivity/google-workspace/scripts/google_api.py')
    query='is:unread in:inbox category:primary -category:promotions newer_than:2d'
    if not script.exists():
        result={'stage':'emails','status':'failed','items':[],'error':'google_api.py no existe'}
    else:
        try:
            p=subprocess.run(['python3',str(script),'gmail','search',query,'--max','10'],capture_output=True,text=True,timeout=45)
            if p.returncode:
                result={'stage':'emails','status':'failed','items':[],'error':p.stderr.strip() or p.stdout.strip()}
            else:
                try:
                    data=json.loads(p.stdout or '[]')
                except json.JSONDecodeError:
                    result={'stage':'emails','status':'failed','items':[],'error':'salida no JSON: '+(p.stdout or p.stderr)[:500]}
                    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False)); return 0
                result={'stage':'emails','status':'ok' if data else 'empty','items':data,'error':''}
        except Exception as e:
            result={'stage':'emails','status':'failed','items':[],'error':str(e)}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
