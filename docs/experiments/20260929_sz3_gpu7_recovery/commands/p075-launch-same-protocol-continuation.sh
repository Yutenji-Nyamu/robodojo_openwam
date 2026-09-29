set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,time
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');s=p/'scripts/pi05_gpu7_recovery_20260929';r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';repair=r/'repair-20260929-gpu7-v1';c=p/'rlt-cycle-sz3-pi05-gpu7-v1'
assert os.getuid()==20001 and (c/'rlt-stopped.json').exists() and not (c/'resumed-dispatched.json').exists()
assert json.loads((c/'gpu7-reset.json').read_text())['exit_code']==0
ready=json.loads((repair/'ready.json').read_text());assert ready['continuation_sha256']==hashlib.sha256((s/'continue_pipeline.py').read_bytes()).hexdigest()
assert not (r/'continuation-20260929-gpu7-v1').exists() and not (repair/'pipeline-launch.json').exists()
argv=[str(p/'envs/RoboDojo/bin/python'),'-u','-B',str(s/'continue_pipeline.py'),'--config',str(s/'dojo_sweep.config.json'),'--cycle-dir',str(c)]
with (repair/'pipeline.log').open('xb') as out:
    proc=subprocess.Popen(argv,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
fields=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
v={'pid':proc.pid,'start':int(fields[19]),'uid':os.getuid(),'time':time.time(),'argv':argv,'run_id':r.name}
with (repair/'pipeline-launch.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(v),flush=True)
PY
