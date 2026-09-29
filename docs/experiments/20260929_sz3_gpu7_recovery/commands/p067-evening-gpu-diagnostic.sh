set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,re
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3'); r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2'
def cmd(a):
    v=subprocess.run(a,capture_output=True,text=True,timeout=25);return {'rc':v.returncode,'stdout':v.stdout[-16000:],'stderr':v.stderr[-500:]}
out={'gpu':cmd(['nvidia-smi','--query-gpu=index,uuid,pci.bus_id,memory.used,utilization.gpu,ecc.errors.uncorrected.volatile.total','--format=csv,noheader,nounits']), 'kernel':cmd(['journalctl','-k','--since','2026-09-29 20:45:00','--no-pager','-g','NVRM: Xid|Out of memory|oom-kill|I/O error|EXT4-fs error|Buffer I/O']), 'apps':cmd(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory','--format=csv,noheader,nounits'])}
out['logs']={}
for worker in [0,6,7]:
    f=max((r/f'seed0/worker{worker}/tasks').glob('*/stdout-*.log'),key=lambda q:q.stat().st_mtime)
    text=f.read_text(errors='replace');lines=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text).splitlines()
    patterns=['Traceback (most recent call last):','ERROR_DEVICE_LOST','Fatal Python','Segmentation fault','[crash]','retry','Retry','Finished','Unstable','RuntimeError','FileNotFoundError']
    hits=[i for i,l in enumerate(lines) if any(k in l for k in patterns)]
    idx=set(range(max(0,len(lines)-30),len(lines)))
    for i in hits[-14:]:idx.update(range(max(0,i-1),min(len(lines),i+8)))
    out['logs'][f'seed0/worker{worker}/{f.parent.name}']={'age':round(time.time()-f.stat().st_mtime,1),'lines':len(lines),'excerpts':[{'line':i+1,'text':lines[i]} for i in sorted(idx)]}
out['processes']=[]
for q in Path('/proc').iterdir():
    if not q.name.isdigit():continue
    try:
        if q.stat().st_uid!=20001:continue
        c=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if not any(x in c for x in ['robodojo_openwam_sz3','robodojo-openwam-sz3','src.eval','serve_policy.py']):continue
        if 'python3 -'==c.strip():continue
        out['processes'].append({'pid':int(q.name),'start':(q/'stat').read_text().rsplit(')',1)[1].split()[19],'cmd':c})
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
print(json.dumps(out,ensure_ascii=False))
PY
