#!/usr/bin/env python3
import json, pathlib, sys
r=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
if not r or not r.exists(): print("Request file missing", file=sys.stderr); sys.exit(2)
data=json.loads(r.read_text(encoding="utf-8"))
mode=data.get("mode","dry-run")
assert mode in ("dry-run","apply")
print(f"Validated request {r} in mode {mode}")
