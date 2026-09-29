set -euo pipefail
/usr/bin/python3 - <<'PY'
from pathlib import Path
import json,os,socket,subprocess,time
assert os.getuid()==0 and socket.gethostname()=='h100-gpu01'
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');c=p/'rlt-cycle-sz3-pi05-gpu7-v1'
assert json.loads((c/'rlt-stopped.json').read_text())['gpus_released']==[4,5,6,7]
assert not (c/'resumed-dispatched.json').exists()
uuid='GPU-0423def8-ef84-a808-6582-7dc2130f58fc';receipt=c/'gpu7-reset.json'
with receipt.open('x') as f:json.dump({'state':'preflight','uuid':uuid,'time':time.time()},f)
os.chown(receipt,20001,20001)
q=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,pci.bus_id,memory.used','--format=csv,noheader,nounits'],text=True).strip().split(', ')
assert q==[uuid,'00000000:C1:00.0','0'],q
deadline=time.monotonic()+25
while True:
    res=subprocess.run(['fuser','/dev/nvidia7'],capture_output=True,text=True,timeout=10);blocked=[]
    for pid in [int(x) for x in res.stdout.split()]:
        proc=Path('/proc')/str(pid)
        try:uid=proc.stat().st_uid;comm=(proc/'comm').read_text().strip()
        except FileNotFoundError:continue
        if not(uid==0 and comm=='nvidia-persiste'):blocked.append({'pid':pid,'uid':uid,'comm':comm})
    if not blocked or time.monotonic()>deadline:break
    time.sleep(1)
assert not blocked,blocked
reset=subprocess.run(['nvidia-smi','-i',uuid,'--gpu-reset'],text=True,capture_output=True,timeout=45)
record={'state':'reset_completed' if reset.returncode==0 else 'reset_failed','uuid':uuid,'gpu':7,'pci':'00000000:C1:00.0','time':time.time(),'exit_code':reset.returncode,'stdout':reset.stdout,'stderr':reset.stderr}
receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
raise SystemExit(reset.returncode)
PY
