set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import collections,datetime,hashlib,json,re,subprocess,time
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';repair=r/'repair-20260929-gpu7-v1';s=p/'scripts/pi05_gpu7_recovery_20260929';cont=r/'continuation-20260929-gpu7-v1'
out={'time':datetime.datetime.now().astimezone().isoformat(),'run_id':r.name,'continuation':cont.name}
for name in ['pipeline-current.json','pipeline-final.json']:
    f=cont/name
    if f.exists():out[name]=json.loads(f.read_text())
def alive(v):
    q=Path('/proc')/str(v['pid'])
    try:
        fs=(q/'stat').read_text().rsplit(')',1)[1].split()
        return q.stat().st_uid==v['uid']==20001 and fs[0] not in ('Z','X') and int(fs[19])==v['start']
    except (FileNotFoundError,ProcessLookupError):return False
out['identities']={}
for f in [repair/'pipeline-launch.json',cont/'dojo-controller-identity.json']:
    if f.exists():
        v=json.loads(f.read_text());out['identities'][f.name]={'pid':v['pid'],'start':v['start'],'alive':alive(v)}
out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()
out['mem_available_gib']=round(int(next(l for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')).split()[1])/1024**2,2)
records=sorted(r.glob('controller-*.json'),key=lambda f:f.stat().st_mtime);cr=json.loads(records[-1].read_text());attempt=cr['attempt'];out['attempt']=attempt
event=r/f'events-{attempt}.jsonl';events=[json.loads(x) for x in event.read_text().splitlines() if x.strip()]
out['controller_errors']=[x for x in events if 'error' in x.get('event','')]
out['workers']=[]
for w in sorted(r.glob('seed*/worker*')):
    fs=list(w.glob(f'tasks/*/stdout-{attempt}.log'))
    if not fs:continue
    f=max(fs,key=lambda q:q.stat().st_mtime)
    with f.open('rb') as stream:stream.seek(max(0,f.stat().st_size-200000));text=stream.read().decode(errors='replace')
    clean=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
    steps={a:{'step':int(b),'max_steps':int(c)} for a,b,c in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)',clean)}
    out['workers'].append({'worker':w.name,'seed':w.parent.name,'task':f.parent.name,'log':str(f.relative_to(r)),'age_seconds':round(time.time()-f.stat().st_mtime,1),'env_steps':steps,'tail':clean.splitlines()[-3:],'fatal_device_errors':sum(k in clean for k in ['ERROR_DEVICE_LOST','CTX SWITCH TIMEOUT','CUDA out of memory','Segmentation fault'])})
out['results']=[]
for f in (p/'RoboDojo/eval_result/RoboDojo').glob('*/*/*/*/'+r.name+'*/_result.json'):
    d=json.loads(f.read_text());out['results'].append({'task':f.parents[4].name,'seed':int(f.parent.parent.name.split('_')[0]),'episodes':d['eval_time'],'successes':sum(x['success'] for x in d['details'].values()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
out['episodes']=sum(x['episodes'] for x in out['results']);out['successes']=sum(x['successes'] for x in out['results'])
verified=0
for f in (repair/'preserved-results').glob('seed*/*/_result.json'):
    d=json.loads(f.read_text());seed=int(f.parent.parent.name[4:]);task=f.parent.name
    current=p/'RoboDojo/eval_result/RoboDojo'/task/'Pi_05/arx_x5'/f'{seed}_ckpt_name=sim,action_type=joint'/f'{r.name}_s{seed}_{task}'/'_result.json'
    now=json.loads(current.read_text());assert all(now['details'].get(k)==v for k,v in d['details'].items()),task
    verified+=len(d['details'])
out['preserved_details_verified']=verified
plan=json.loads((r/'plan.json').read_text());out['source_hashes_unchanged']=all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v for f,v in plan['source_sha256'].items())
out['controller_hashes_unchanged']=all(hashlib.sha256((s/f).read_bytes()).hexdigest()==v for f,v in plan['controller_sha256'].items())
out['task_states']={}
for f in r.glob('seed*/summary.json'):out['task_states'][f.parent.name]=dict(collections.Counter(x['status'] for x in json.loads(f.read_text())['results'].values()))
c=p/'rlt-cycle-sz3-pi05-gpu7-v1';out['rlt_resume_dispatched']=(c/'resumed-dispatched.json').exists()
print(json.dumps(out,ensure_ascii=False))
PY
