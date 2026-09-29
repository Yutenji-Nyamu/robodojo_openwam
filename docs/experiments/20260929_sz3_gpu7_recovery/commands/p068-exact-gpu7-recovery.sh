set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import datetime,fcntl,json,os,signal,socket,subprocess,time
assert os.getuid()==0 and socket.gethostname()=='h100-gpu01'
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';c=p/'rlt-cycle-sz3-pi05-full-r2'
repair=r/'repair-20260929-gpu7-v1'; repair.mkdir(exist_ok=False);os.chown(repair,20001,20001)
def save(name,value):
    dest=repair/name; dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.chown(dest,20001,20001)
def identity(row):
    q=Path('/proc')/str(row['pid'])
    try:
        fields=(q/'stat').read_text().rsplit(')',1)[1].split()
        return q.stat().st_uid==20001 and int(fields[19])==row['start'] and fields[0] not in ('Z','X'),fields[0],(q/'cmdline').read_bytes()
    except (FileNotFoundError,ProcessLookupError):return False,None,b''
outer=json.loads((r/'pipeline-launch.json').read_text());inner=json.loads((r/'dojo-controller-identity.json').read_text())
assert (outer['pid'],outer['start'])==(3373285,663902919)
assert (inner['pid'],inner['start'])==(3373449,663903345)
assert identity(outer)[0] and b'pi05_formal_20260929_r2/formal_pipeline.py' in identity(outer)[2]
assert identity(inner)[0] and b'pi05_formal_20260929_r2/dojo_sweep.py' in identity(inner)[2]
assert json.loads((r/'pipeline-current.json').read_text())['phase']=='EVALUATING'
assert not (c/'resumed-dispatched.json').exists()
handles={name:os.pidfd_open(row['pid']) for name,row in [('outer',outer),('inner',inner)]}
record={'time':datetime.datetime.now().astimezone().isoformat(),'outer':outer,'inner':inner,'actions':[],'gpu':7,'uuid':'GPU-0423def8-ef84-a808-6582-7dc2130f58fc','reason':'GPU7 Xid31 then Xid109 across make_toast_random and fill_pen_holder','protocol_change':False}
paused=False
try:
    save('intent.json',record)
    assert identity(outer)[0]
    signal.pidfd_send_signal(handles['outer'],signal.SIGSTOP);paused=True
    for _ in range(50):
        if identity(outer)[1]=='T':break
        time.sleep(.02)
    assert identity(outer)[1]=='T' and json.loads((r/'pipeline-current.json').read_text())['phase']=='EVALUATING'
    record['actions'].append('exact outer paused before automatic resource return')
    assert identity(inner)[0]
    signal.pidfd_send_signal(handles['inner'],signal.SIGTERM)
    deadline=time.monotonic()+180
    while identity(inner)[0] and time.monotonic()<deadline:time.sleep(1)
    assert not identity(inner)[0], 'Controller did not finish cleanup within 180 seconds'
    with (r/'controller.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    final=json.loads((r/'final.json').read_text());record['controller_final']=final
    assert final['processes_clear'] and final['gpus_released'], final
    record['actions'].append('controller ended with exact processes and GPUs released')
    archive=repair/'preserved-before-resume';archive.mkdir();os.chown(archive,20001,20001)
    count=0
    for f in (p/'RoboDojo/eval_result/RoboDojo').glob('*/*/*/*/'+r.name+'*/_result.json'):
        dest=archive/(f.parents[4].name+'_'+f.parent.parent.name.split('_')[0]+'.json')
        dest.write_bytes(f.read_bytes());os.chown(dest,20001,20001);count+=len(json.loads(f.read_text())['details'])
    record['preserved_episodes']=count
    uuid=record['uuid'];q=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,pci.bus_id,memory.used','--format=csv,noheader,nounits'],text=True).strip().split(', ')
    assert q==[uuid,'00000000:C1:00.0','0'],q
    deadline=time.monotonic()+25
    while True:
        res=subprocess.run(['fuser','/dev/nvidia7'],capture_output=True,text=True,timeout=10)
        blocked=[]
        for pid in [int(x) for x in res.stdout.split()]:
            q=Path('/proc')/str(pid)
            try:uid=q.stat().st_uid;comm=(q/'comm').read_text().strip()
            except FileNotFoundError:continue
            if not(uid==0 and comm=='nvidia-persiste'):blocked.append({'pid':pid,'uid':uid,'comm':comm})
        if not blocked or time.monotonic()>deadline:break
        time.sleep(1)
    assert not blocked,blocked
    reset=subprocess.run(['nvidia-smi','-i',uuid,'--gpu-reset'],capture_output=True,text=True,timeout=45)
    record['reset']={'exit':reset.returncode,'stdout':reset.stdout,'stderr':reset.stderr,'time':time.time()}
    assert reset.returncode==0,record['reset']
    print(json.dumps({'reset':record['reset'],'preserved_episodes':count}),flush=True)
except BaseException as exc:
    record['error']=repr(exc);raise
finally:
    if paused and identity(outer)[0]:
        signal.pidfd_send_signal(handles['outer'],signal.SIGCONT)
        record['actions'].append('exact outer continued; original RLT return remains active')
    for fd in handles.values():os.close(fd)
    record['finished_at']=time.time();save('reset-gate.json',record)
    print(json.dumps({'gate_finished':True,'error':record.get('error'),'actions':record['actions']}),flush=True)
PY
