set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2'
out={}
for name in ['pipeline-current.json','pipeline-final.json','final.json']:
    f=r/name
    if f.exists():out[name]=json.loads(f.read_text())
rows=[json.loads(x) for x in (r/'events-1790668012022772162.jsonl').read_text().splitlines()]
out['errors']=[x for x in rows if x.get('event') in ['worker_error','sweep_error','telemetry_error']][-3:]
out['outer_log_tail']=(r/'dojo-cleanup.log').read_text(errors='replace')[-6000:]
print(json.dumps(out))
PY
