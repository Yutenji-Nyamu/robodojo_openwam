from pathlib import Path
import concurrent.futures,json,os,subprocess,sys,time,traceback
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3')
sys.path.insert(0,str(p/'scripts'/(sys.argv[1] if len(sys.argv)>1 else 'pi05_formal_20260929')))
from process_guard import ProcessGuard
name='sz3_guard_exec_cpu_'+str(time.time_ns());run=p/'runs'/name
guard=ProcessGuard(name,os.getuid(),run/'cleanup')
errors=[]
def cycle(index):
    env={**os.environ,'DOJO_SWEEP_ID':name,'ROBODOJO_RUN_ID':name+'_w'+str(index)}
    for step in range(50):
        proc=subprocess.Popen(['bash','--noprofile','--norc','-c','for n in 1 2 3 4; do /bin/true; done; exec /bin/sleep 0.03'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            while proc.poll() is None:
                guard.identity(proc.pid)
                time.sleep(0.001)
        except Exception as exc:errors.append({'step':step,'pid':proc.pid,'error':repr(exc),'filename':getattr(exc,'filename',None),'traceback':traceback.format_exc()})
        finally:proc.wait()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    futures=[pool.submit(cycle,i) for i in range(8)]
    for f in futures:f.result()
result={'runs':400,'errors':len(errors),'examples':errors[:4]}
(run/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
