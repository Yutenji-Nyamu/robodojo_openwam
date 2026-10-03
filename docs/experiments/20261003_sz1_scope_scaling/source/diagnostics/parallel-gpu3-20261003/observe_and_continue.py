"""Correct ANSI-only observation failure without rerunning N9; then run N4."""
import importlib.util,json,os,re,sys,time
from pathlib import Path
source=Path(__file__).with_name('probe.py')
spec=importlib.util.spec_from_file_location('gpu3_probe',source)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
run=p.RUN
owner=json.loads((run/'owner.json').read_text())
old_start=int(owner['proc_stat'].rsplit(')',1)[1].split()[19])
def active():
    try:
        f=Path(f"/proc/{owner['pid']}/stat").read_text().rsplit(')',1)[1].split()
        return int(f[19])==old_start and f[0]!='Z'
    except FileNotFoundError:return False
def clean(s):return re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',s)
deadline=time.time()+1900
with (run/'n9/observed-resources.jsonl').open('x') as out:
    while active():
        log=run/'n9/client.log'
        text=clean(log.read_text(errors='replace')) if log.exists() else ''
        steps={}
        for e,s,b in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)',text):steps[int(e)]=int(s)
        out.write(json.dumps(dict(time=time.time(),gpu=p.gpu(),steps=steps))+'\n');out.flush()
        if time.time()>deadline:raise RuntimeError('Original controller did not terminate; no N4 launch')
        time.sleep(2)
status=json.loads((run/'n9/status.json').read_text())
assert status['error']=="RuntimeError('Nine complete results not verified')",status
assert status['client_exit']==0 and not status.get('cleanup_errors')
assert json.loads((run/'released.json').read_text())['source_unchanged'] is True
assert status['check']['complete'] is True
text=clean((run/'n9/client.log').read_text(errors='replace'))
assert not p.FATAL.search(text) and 'Invalid PhysX transform' not in text
seen=set();last={};count=0
for e,s,b in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)',text):
    e,s=int(e),int(s);seen.add(e);old=last.get(e,0);count+=s-old if s>=old else s;last[e]=s
assert seen==set(range(9))
status.update(state='COMPLETE',observation_correction='ANSI color codes omitted in original step parser',
    original_status_preserved=str(run/'n9/status.json'),observed_envs=sorted(seen),actions=count)
status.pop('error')
p.atomic_json(run/'n9/observed-complete.json',status)
p.require_idle()
p.guard=p.ProcessGuard(run.name,1003,run/'cleanup')
assert not p.guard.scan()
p.atomic_json(run/'n4-owner.json',dict(pid=os.getpid(),proc_stat=Path('/proc/self/stat').read_text(),uid=os.getuid()))
report=p.case(4)
p.atomic_json(run/'comparison.json',dict(cases=[status,report],finished=True))
p.atomic_json(run/'final-released.json',dict(time=time.time(),gpu=p.require_idle(),owned_processes=p.guard.scan()))
