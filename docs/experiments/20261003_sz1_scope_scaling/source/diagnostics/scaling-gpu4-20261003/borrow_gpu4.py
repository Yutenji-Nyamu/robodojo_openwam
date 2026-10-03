"""Adopt the existing supervisor; borrow only GPU4 and restore its original lane."""
import ast, fcntl, hashlib, json, os, shutil, signal, socket, subprocess, sys, time
from pathlib import Path

P=Path('/srv/dojo')
O=P/'runs/sz1-dojo-continuation-20261002-v1'
D=O/'gpu4-scaling-20261003-v1'
PROBE=P/'diagnostics/scaling-gpu4-20261003/scale_probe_gpu4.py'
RUN=P/'runs/sz1-gpu4-scaling-20261003-v1'
sys.path[:0]=[str(P/'scripts/rlt'),str(P/'scripts/lanes/openwam')]
import owner_sz1 as M
from process_guard import ProcessGuard
from eval_recovery import FATAL
M.GPUS=(4,5)

def exact_signal(identity, sig):
    current=M.identity(identity['pid'])
    assert current and all(current[k]==identity[k] for k in ('pid','uid','start_ticks','cmdline_sha256'))
    if hasattr(os,'pidfd_open'):
        fd=os.pidfd_open(current['pid'])
        try:
            assert M.same(current)
            signal.pidfd_send_signal(fd,sig)
        finally: os.close(fd)
    else:
        assert M.same(current)
        os.kill(current['pid'],sig)

class Adopted:
    def __init__(self, identity, final, started):
        self.identity,self.pid,self.final,self.started=identity,identity['pid'],final,started
    def poll(self):
        if M.same(self.identity): return None
        if self.final.exists():
            data=M.read(self.final)
            if data.get('finished_at',0)>self.started:
                return 0 if data.get('state')=='COMPLETE' else 1
        return 1

def snapshots(cfg):
    control=Path(cfg['control_dir']); plan=M.read(control/'plan.json')
    tasks={t['task'] for g in plan['groups'] if g['gpu']==4 for t in g['tasks']}
    records=[]
    for seed in (0,1,2):
        for task in sorted(tasks):
            root=P/'RoboDojo/eval_result/RoboDojo'/task/'OpenWAM/arx_x5'/(
                f'{seed}_ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee')/(f"{cfg['run_id']}_s{seed}_{task}")
            for f in root.glob('*.json'):
                destination=D/'saved-results'/str(seed)/task/f.name
                destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,destination)
                records.append(dict(path=str(f),sha256=M.sha(f),snapshot=str(destination)))
    if (control/'final.json').exists():shutil.copy2(control/'final.json',D/'gpu4-pause-final.json')
    return records

def preflight():
    assert os.getuid()==1003 and socket.gethostname()=='admin'
    ast.parse(PROBE.read_text());assert not RUN.exists()
    state=M.read(O/'status.json');old=state['identity']
    assert old['pid']==3881745 and old['start_ticks']==379867940 and M.same(old)
    assert all(state['lanes'][str(g)]['state']=='DOJO_RUNNING' for g in (4,5))
    cfgs={g:M.read(P/f'scripts/lanes/configs/gpu{g}.json') for g in (4,5)}
    guards={g:ProcessGuard(state['lanes'][str(g)]['sweep_id'],1003,Path(cfgs[g]['control_dir'])/'cleanup') for g in (4,5)}
    controllers={}
    for g in (4,5):
        previous=state['lanes'][str(g)]['managed_processes'][0]
        actual=guards[g].identity(previous['pid'])
        assert actual and actual['start_ticks']==previous['start_ticks'] and actual['role']=='controller'
        controllers[g]=M.identity(previous['pid'])
        cfg=cfgs[g];assert cfg['lane_gpu']==g and cfg['workers_per_gpu']==1
        saved=M.read(Path(cfg['control_dir'])/'plan.json')
        assert saved['config']==cfg
        for name,sha in saved['source_sha256'].items(): assert M.sha(Path(name))==sha
        assert (P/f'rlt-cycle-{O.name}-gpu{g}'/'rlt-stopped.json').exists()
    return state,old,cfgs,guards,controllers

def main():
    state,old,cfgs,guards,controllers=preflight()
    if '--check' in sys.argv:
        print(json.dumps(dict(check='PASS',gpus=[4,5],gpu_to_pause=4,old_owner=old,controllers=controllers)));return
    D.mkdir(exist_ok=False)
    stopped=False;retired=False
    try:
        exact_signal(old,signal.SIGSTOP);stopped=True
        for _ in range(30):
            if Path(f"/proc/{old['pid']}/stat").read_text().rsplit(')',1)[1].split()[0]=='T':break
            time.sleep(.1)
        else:raise RuntimeError('Old owner did not stop')
        state,old,cfgs,guards,controllers=preflight()
        children={int(x) for x in Path(f"/proc/{old['pid']}/task/{old['pid']}/children").read_text().split()}
        assert children=={v['pid'] for v in controllers.values()}, 'Unexpected active owner child/helper'
        M.atomic(D/'previous-owner-status.json',state)
        M.atomic(D/'handoff-ready.json',dict(identity=M.identity(os.getpid()),old=old,controllers=controllers,time=time.time()))
        exact_signal(old,signal.SIGKILL);retired=True
        for _ in range(50):
            if not M.same(old):break
            time.sleep(.1)
        assert not M.same(old)
        lock=(O/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except Exception:
        if stopped and not retired and M.same(old):exact_signal(old,signal.SIGCONT)
        raise
    owner=M.Owner(P,O);owner.state=state;owner.configs=cfgs;owner.guards=guards
    owner.state['identity']=M.identity(os.getpid());owner.state['handoff']=str(D)
    owner.state['stage']='RUNNING';owner.save()
    owner.processes={g:Adopted(controllers[g],Path(cfgs[g]['control_dir'])/'final.json',state['lanes'][str(g)]['started_at']) for g in (4,5)}
    M.atomic(O/'active-gpu4-scaling.json',dict(identity=owner.state['identity'],directory=str(D),probe=str(RUN),resume_original=True))
    owner.state['lanes']['4'].update(state='PAUSING_FOR_SCALING',pause_requested_at=time.time());owner.save()
    exact_signal(controllers[4],signal.SIGTERM)
    phase='PAUSING';probe=None;pause_start=time.time();cancel=False
    def request_cancel(*_):
        nonlocal cancel
        cancel=True
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,request_cancel)
    def resume_formal():
        nonlocal phase
        M.gpu_health(4)
        proof=D/'gpu4-pause-proof.json'
        if proof.exists():
            for record in M.read(proof)['results']:assert M.sha(Path(record['path']))==record['sha256']
        log=O/'gpu4-dojo.log'
        if log.exists() and not (D/'gpu4-dojo-before-scaling.log').exists():shutil.copy2(log,D/'gpu4-dojo-before-scaling.log')
        phase='FORMAL_RESUMING';owner.start_lane(4);phase='FORMAL_RESUMED'
        M.atomic(D/'formal-resumed.json',dict(time=time.time(),lane=owner.state['lanes']['4'],original_config=cfgs[4]))
    def test_fatal(summary):
        if any(row.get('client_exit') in (99,134,139,-6,-11) or
               any(s in row.get('error','') for s in ('GPU/physics failure','Fatal in final log'))
               for row in summary.get('cases',[])):return True
        return any(FATAL.search(f.read_text(errors='replace')) or 'Invalid PhysX transform' in f.read_text(errors='replace')
                   for f in RUN.glob('n*/*.log'))
    def recover4(error):
        nonlocal phase
        M.atomic(D/('recovery-'+str(time.time_ns())+'.json'),dict(error=repr(error),phase=phase,time=time.time()))
        if phase in ('FORMAL_RESUMING','FORMAL_RESUMED') and 4 in owner.processes and owner.processes[4].poll() is None:
            phase='FORMAL_RESUMED';return
        if probe is not None and probe.poll() is None:
            exact_signal(M.read(D/'probe-process.json'),signal.SIGTERM)
            probe.wait(timeout=120)
        if (RUN/'cleanup/ownership-anchor.json').exists():
            test_guard=ProcessGuard(RUN.name,1003,RUN/'cleanup')
            test_guard.cleanup(None,'scaling_error_cleanup',grace=20)
            assert not test_guard.scan()
        guards[4].cleanup(None,'scaling_pause_error_cleanup',grace=20)
        assert not guards[4].scan();owner.processes.pop(4,None);M.gpu_health(4)
        summary=M.read(RUN/'summary.json') if (RUN/'summary.json').exists() else {}
        if test_fatal(summary):owner.return_lane(4,'failed');phase='RLT_RETURNING'
        else:resume_formal()
    def tick():
        nonlocal phase,probe,cancel
        if cancel and phase=='TESTING' and probe.poll() is None:
            exact_signal(M.read(D/'probe-process.json'),signal.SIGTERM);cancel=False
        if phase=='PAUSING' and owner.processes[4].poll() is None and time.time()-pause_start>180:
            guards[4].cleanup(None,'operator_pause_for_scaling',grace=20)
        for g,proc in list(owner.processes.items()):
            code=proc.poll()
            if code is None:continue
            del owner.processes[g]
            try:
                if g==4 and phase=='PAUSING':
                    guards[4].cleanup(None,'operator_pause_for_scaling',grace=20)
                    assert not guards[4].scan()
                    health=M.gpu_health(4)
                    records=snapshots(cfgs[4])
                    M.atomic(D/'gpu4-pause-proof.json',dict(time=time.time(),gpu=health,results=records,reason='User-requested concurrency test'))
                    if cancel:
                        resume_formal();continue
                    with (D/'probe-owner.log').open('xb') as out:
                        probe=subprocess.Popen([str(P/'envs/openwam/bin/python'),'-u',str(PROBE)],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
                    M.atomic(D/'probe-process.json',M.identity(probe.pid))
                    phase='TESTING';owner.state['lanes']['4'].update(state='SCALING_TEST',probe_run=str(RUN));owner.save()
                else:
                    owner.return_lane(g,'completed' if code==0 else 'failed')
            except Exception as exc:
                if g==4 and phase=='PAUSING':recover4(exc)
                else:
                    owner.state['lanes'][str(g)].update(state='NEEDS_ATTENTION',error=repr(exc));owner.save()
                    if g==4:phase='NEEDS_ATTENTION'
        if phase=='TESTING' and probe.poll() is not None:
            try:
                release=M.read(RUN/'released.json');summary=M.read(RUN/'summary.json')
                assert release['source_unchanged'] and not release['owned_processes']
                M.gpu_health(4)
                fatal=test_fatal(summary)
                M.atomic(D/'scaling-finished.json',dict(time=time.time(),exit_code=probe.returncode,summary=summary,release=release,fatal=fatal))
                if fatal:
                    owner.return_lane(4,'failed');phase='RLT_RETURNING'
                else:
                    resume_formal()
            except Exception as exc:
                recover4(exc)
        owner.verify_returns()
        if not owner.processes and phase not in ('PAUSING','TESTING') and not any(x['state']=='RLT_VERIFYING' for x in owner.state['lanes'].values()):
            owner.state['stage']='NEEDS_ATTENTION' if any(x['state']=='NEEDS_ATTENTION' for x in owner.state['lanes'].values()) else 'FINISHED'
            owner.save();return True
    while True:
        try:
            if tick():return
        except Exception as exc:
            owner.event('adopted_owner_attention',error=repr(exc),phase=phase)
            if phase in ('PAUSING','TESTING','FORMAL_RESUMING'):
                try:recover4(exc)
                except Exception as recovery_error:
                    phase='NEEDS_ATTENTION';owner.state['lanes']['4'].update(state=phase,error=repr(recovery_error));owner.save()
        time.sleep(3)

if __name__=='__main__':main()
