set -euo pipefail
P=/data/chenyiteng/projects/robodojo-openwam-sz3
python3 - <<'PY'
from pathlib import Path
import subprocess,json
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2'
response=subprocess.run(['python3',str(p/'scripts/formal_health_snapshot.py'),str(r/'health-latest.json')],capture_output=True,text=True,check=True)
v=json.loads(response.stdout)
out={k:v[k] for k in ['time','pipeline-current.json','gpu_snapshot','mem_available_gib','seeds','task_states','results']}
if 'final.json' in v:out['final']=v['final.json']
out['workers']=[{'worker':w['worker'],'task':w.get('task',{}).get('log'),'server_tail':w.get('server',{}).get('tail',[])[-1:],'task_tail':w.get('task',{}).get('tail',[])[-2:],'progress':w.get('task',{}).get('progress_lines',[])[-2:],'fatal':w.get('task',{}).get('fatal_signatures',[])} for w in v['workers']]
print(json.dumps(out,ensure_ascii=False))
PY
