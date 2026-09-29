set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import collections,datetime,hashlib,json,subprocess,time
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3'); r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2'
h=json.loads(subprocess.check_output(['python3',str(p/'scripts/formal_health_snapshot.py')],text=True))
out={k:h[k] for k in ['time','run_id','deployment_commit','pipeline-current.json','gpu_snapshot','mem_available_gib','mem_total_gib','seeds','task_states','results']}
out['workers']=[]
for w in h['workers']:
    t=w.get('task',{}); f=r/t['log']
    out['workers'].append({'seed':w['seed'],'worker':w['worker'],'task_log':t['log'],'log_age_seconds':round(time.time()-f.stat().st_mtime,1),'env_steps':t.get('env_steps',{}),'tail':t['tail'][-3:],'fatal_signatures':t.get('fatal_signatures',[])})
out['summary']={'episodes':sum(x.get('detail_count',0) for x in h['results']),'successes':sum(x.get('successes',0) for x in h['results']),'videos':sum(x.get('video_count',0) for x in h['results']),'video_bytes':sum(x.get('video_bytes',0) for x in h['results'])}
out['task_records']={}
for f in sorted(r.glob('seed*/summary.json')):
    v=json.loads(f.read_text());out['task_records'][f.parent.name]=v['results']
controllers=sorted(r.glob('controller-*.json'),key=lambda f:f.stat().st_mtime)
if controllers:
    c=json.loads(controllers[-1].read_text());out['controller_record']=c
    e=r/('events-'+str(c['attempt'])+'.jsonl')
    rows=[json.loads(x) for x in e.read_text().splitlines() if x.strip()]
    out['controller_errors']=[x for x in rows if any(s in str(x.get('event',x.get('kind',''))) for s in ['error','fail'])]
out['storage']=subprocess.check_output(['df','-B1','/','/data'],text=True).strip()
out['publication']={}
pub=p/'publication-pi05-full/repo'
for k,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain']),('latest',['log','-4','--format=%H %s']),('files',['ls-tree','-r','--name-only','HEAD','docs/experiments/20260929_sz3_pi05_full'])]:
    out['publication'][k]=subprocess.check_output(['git','-C',str(pub),*args],text=True).strip()
out['publication']['remote_head']=subprocess.check_output(['git','-C',str(pub),'ls-remote','origin','refs/heads/codex/sz3-dojo-openwam-pi05'],text=True,timeout=30).strip().split()[0]
out['cycle']={'name':'rlt-cycle-sz3-pi05-full-r2','stopped':(p/'rlt-cycle-sz3-pi05-full-r2/rlt-stopped.json').is_file(),'resume_dispatched':(p/'rlt-cycle-sz3-pi05-full-r2/resumed-dispatched.json').exists()}
print(json.dumps(out,ensure_ascii=False))
PY
