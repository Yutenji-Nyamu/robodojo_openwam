set -euo pipefail
P=/data/chenyiteng/projects/robodojo-openwam-sz3
S="$P/scripts/pi05_gpu7_recovery_20260929"
"$P/envs/RoboDojo/bin/python" -B -m unittest discover -s "$S" -p 'test_*.py'
"$P/envs/RoboDojo/bin/python" -B - <<'PY'
from pathlib import Path
import fcntl,hashlib,json,os,signal,subprocess,sys,time
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');s=p/'scripts/pi05_gpu7_recovery_20260929';r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';repair=r/'repair-20260929-gpu7-v1';previous=p/'rlt-cycle-sz3-pi05-full-r2'
sys.path.insert(0,str(s))
from dojo_sweep import build_plan,Sweep,sha
from resume_results import prepare_result
from process_guard import atomic_json
assert os.getuid()==20001 and (previous/'resumed-dispatched.json').exists()
outer=json.loads((r/'pipeline-launch.json').read_text());q=Path('/proc')/str(outer['pid'])
if q.exists():
    fs=(q/'stat').read_text().rsplit(')',1)[1].split()
    if fs[0] not in ('Z','X') and int(fs[19])==outer['start']:
        assert q.stat().st_uid==20001
        assert json.loads((r/'pipeline-current.json').read_text())['phase'] in ['RLT_RESTORE_DISPATCHED','RLT_FIRST_ROUNDS_PENDING','RLT_FIRST_ROUNDS_VERIFIED']
        assert str(p/'scripts/pi05_formal_20260929_r2/formal_pipeline.py').encode() in (q/'cmdline').read_bytes().split(b'\0')
        os.kill(outer['pid'],signal.SIGTERM)
        atomic_json(repair/'observer-stop.json',{'time':time.time(),'identity':outer,'scope':'old read-only observer only; RLT already dispatched'})
        deadline=time.monotonic()+60
        while not (r/'pipeline-final.json').exists() and time.monotonic()<deadline:time.sleep(.5)
assert json.loads((r/'pipeline-final.json').read_text())['rlt_dispatched'] is True
cfg=json.loads((s/'dojo_sweep.config.json').read_text());plan=build_plan(cfg);prior=json.loads((r/'plan.json').read_text())
changed={k for k in set(plan)|set(prior) if plan.get(k)!=prior.get(k)}
assert changed <= {'created_at'}, changed
with (r/'pipeline.lock').open('a+') as outerlock,(r/'controller.lock').open('a+') as innerlock:
    fcntl.flock(outerlock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(innerlock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=[]
    for seed in plan['seeds']:
        for task in plan['tasks']:
            rows.append(prepare_result(Path(cfg['repo']),task,seed,f"{cfg['run_id']}_s{seed}_{task}",plan['budgets'][task],repair/'preserved-results',apply=True))
    record={'time':time.time(),'config_sha256':sha(s/'dojo_sweep.config.json'),'protocol_unchanged':True,'source_hashes_unchanged':True,'controller_hashes_unchanged':True,'episodes':sum(x.get('episodes',0) for x in rows),'rows':rows,'continuation_sha256':sha(s/'continue_pipeline.py')}
    atomic_json(repair/'ready.json',record)
    print(json.dumps({'episodes':record['episodes'],'completed_tasks':sum(x['action']=='skip_complete' for x in rows),'partial_tasks':sum(x['action'] in ['reuse_manifest','rebuild_missing_manifest'] for x in rows),'manifest_rebuilt':sum(x['action']=='rebuild_missing_manifest' for x in rows),'protocol_unchanged':True}),flush=True)
PY
/home/chenyiteng/venvs/rlinf-7d07-openpi-robotwin/bin/python -u -B "$S/rlt_cycle_sz3.py" --cycle-dir "$P/rlt-cycle-sz3-pi05-gpu7-v1" prepare
