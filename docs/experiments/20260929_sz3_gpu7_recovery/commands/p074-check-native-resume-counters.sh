set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';repair=r/'repair-20260929-gpu7-v1'
rows=[]
for f in (repair/'preserved-results/seed0').glob('*/resume-original.json'):
    v=json.loads(f.read_text());rows.append({'task':f.parent.name,'restart_count':v.get('restart_count'),'episodes':len(v['details']),'abandoned':v.get('abandoned_layout_ids'),'unstable':v.get('unstable_nums')})
print(json.dumps({'resume_manifests':rows}))
for name in ['scripts/eval_policy.sh','src/eval_client/main.py','src/eval_client/eval_env.py']:
    lines=(p/'RoboDojo'/name).read_text().splitlines()
    idx=set()
    for i,l in enumerate(lines):
        if 'restart_count' in l or 'MAX_RE' in l or 'retry_count' in l:
            idx.update(range(max(0,i-2),min(len(lines),i+3)))
    print(json.dumps({'source':name,'snippets':[{'line':i+1,'text':lines[i]} for i in sorted(idx)]}))
PY
