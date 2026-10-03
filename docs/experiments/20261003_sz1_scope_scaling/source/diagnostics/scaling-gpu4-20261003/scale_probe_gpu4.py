"""Bounded GPU4 single-worker scaling; formal source and owners untouched."""
import csv, hashlib, io, json, os, re, shlex, signal, socket, subprocess, sys, time
from pathlib import Path

P = Path('/srv/dojo')
R = P / 'RoboDojo'
RUN = P / 'runs/sz1-gpu4-scaling-20261003-v1'
TASK, EPISODES, ORDER, DEADLINE = 'put_bottles_into_dustbin', 50, (9, 16, 25, 36), 5400
sys.path.insert(0, str(P / 'scripts/lanes/openwam'))
from process_guard import ProcessGuard, atomic_json
from dojo_sweep import result_check
from eval_recovery import FATAL

def gpu():
    row = next(csv.reader(io.StringIO(subprocess.check_output([
        'nvidia-smi', '-i', '4', '--query-gpu=uuid,memory.used,utilization.gpu,gpu_recovery_action',
        '--format=csv,noheader,nounits'], text=True, timeout=15))))
    return dict(uuid=row[0].strip(), memory_mib=int(row[1]), utilization=int(row[2]), recovery=row[3].strip())

def require_idle():
    g = gpu()
    apps = subprocess.check_output(['nvidia-smi','-i','4','--query-compute-apps=pid',
                                   '--format=csv,noheader'], text=True, timeout=15).strip()
    if g['uuid'] != 'GPU-9200fbe8-fdd0-93ae-c221-5f0e9d318bf5' or g['memory_mib'] > 512 or g['recovery'] != 'None' or apps:
        raise RuntimeError('GPU4 not empty/healthy: ' + json.dumps(g))
    return g

def listen(port):
    return any(int(line.split()[1].rsplit(':',1)[1],16)==port and line.split()[3]=='0A'
               for name in ('tcp','tcp6') for line in Path('/proc/net/'+name).read_text().splitlines()[1:])

def ram():
    rss = pss = cpu_ticks = 0
    missing = []
    rows = guard.scan()
    for row in rows:
        proc = Path('/proc')/str(row['pid'])
        try:
            fields = (proc/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[19]) != row['start_ticks']: continue
            cpu_ticks += int(fields[11])+int(fields[12])
            for line in (proc/'smaps_rollup').read_text().splitlines():
                if line.startswith('Rss:'): rss += int(line.split()[1])
                if line.startswith('Pss:'): pss += int(line.split()[1])
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            missing.append(dict(pid=row['pid'],error=type(exc).__name__))
    node = {k:int(v.split()[0]) for line in Path('/proc/meminfo').read_text().splitlines()
            for k,v in [line.split(':',1)] if k in ('MemTotal','MemAvailable')}
    return dict(rss_kib=rss,pss_kib=pss,cpu_ticks=cpu_ticks,pids=len(rows),node_kib=node,missing=missing)

def launch(argv, rid, role, work):
    exports = dict(DOJO_SWEEP_ID=RUN.name, ROBODOJO_RUN_ID=rid, DOJO_ROLE=role,
        EVAL_ENV_TYPE='sim', OPENWAM_ALLOW_DUMMY_POLICY='false', EVAL_NUM=str(EPISODES),
        OPENWAM_CKPT_DIR=str(P/'checkpoints/OpenWAM-Alpha-Sim-RoboDojo'),
        ROBODOJO_RENDER_GPU='4', ROBODOJO_MAX_BASH_RETRIES='1', ROBODOJO_FATAL_RESTART_COUNT='3',
        ROBODOJO_VULKAN_COMPAT_SCRIPT=str(P/'third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py'))
    script = ('set -eo pipefail\nsource '+shlex.quote(str(P/'project-env.sh'))+
        '\nsource /home/researcher/miniforge3/etc/profile.d/conda.sh\nconda activate '+shlex.quote(str(P/'envs/RoboDojo'))+
        '\nunset CUDA_VISIBLE_DEVICES\n'+'\n'.join('export '+k+'='+shlex.quote(v) for k,v in exports.items())+
        '\ncd '+shlex.quote(str(R))+'\nexec '+shlex.join(argv)+'\n')
    command, log = work/(role+'.sh'), work/(role+'.log')
    command.write_text(script)
    with log.open('wb') as out:
        proc = subprocess.Popen(['bash',str(command)],env={**os.environ,**exports},cwd=R,
                                stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
    atomic_json(work/(role+'-process.json'), guard.identity(proc.pid))
    return proc, log

def case(n):
    work = RUN/f'n{n}'; work.mkdir()
    rid = RUN.name+f'-n{n}'
    result = R/f'eval_result/RoboDojo/{TASK}/OpenWAM/arx_x5/0_ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee'/rid/'_result.json'
    if result.parent.exists(): raise RuntimeError('Result identity already exists')
    source = (R/'scripts/eval_policy.sh').read_text()
    root_anchor = 'PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"'
    assert source.count(root_anchor)==1
    source = source.replace(root_anchor,'PROJECT_ROOT='+shlex.quote(str(R)))
    source, replacements = re.subn(r'^num_envs=.*$',f'num_envs={n}',source,flags=re.M)
    assert replacements==1
    copied = work/'eval_policy.sh';copied.write_text(source)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    report = dict(num_envs=n,episodes=EPISODES,task=TASK,seed=0,run_id=rid,result=str(result),gpu_before=require_idle(),start=time.time())
    server = client = None; offsets={}; carry={}; previous={}; total_actions=0; first=None; last=None
    peak=0; utils=[]; completed=False; seen=set(); ram_due=0; rss_peak=pss_peak=0; available_min=None
    try:
        server,slog = launch(['bash','scripts/robodojo.sh','server','--policy-dir','XPolicyLab/policy/OpenWAM',
            '--task',TASK,'--ckpt','OpenWAM-Alpha-Sim-RoboDojo','--env-cfg','arx_x5','--action-type','ee',
            '--seed','0','--policy-env',str(P/'envs/openwam'),'--policy-gpu','4','--policy-port',str(port),
            '--bind-host','127.0.0.1'],rid+'-server','server',work)
        while not listen(port):
            if server.poll() is not None or time.time()-report['start']>600: raise RuntimeError('Policy startup failed/timed out')
            peak=max(peak,gpu()['memory_mib'])
            if time.time() >= ram_due:
                memory=ram();ram_due=time.time()+20
                rss_peak=max(rss_peak,memory['rss_kib']);pss_peak=max(pss_peak,memory['pss_kib'])
                available=memory['node_kib']['MemAvailable']
                available_min=available if available_min is None else min(available_min,available)
                with (work/'startup-resources.jsonl').open('a') as metrics:
                    metrics.write(json.dumps(dict(time=time.time(),ram=memory))+'\n')
                if available < 128*1024*1024: raise RuntimeError('Node memory headroom stop')
            time.sleep(1)
        report['server_ready']=time.time()
        client,clog = launch(['bash',str(copied),'--root_dir',str(R),'--task_name',TASK,
            '--env_cfg_type','arx_x5','--device_id','4','--policy_name','OpenWAM','--port',str(port),
            '--host','127.0.0.1','--protocol','ws','--additional_info',
            'ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee','--seed','0'],rid,'client',work)
        with (work/'resources.jsonl').open('w') as metrics:
            while True:
                now=time.time(); g=gpu();peak=max(peak,g['memory_mib'])
                if first is not None:utils.append(g['utilization'])
                steps=[]
                for log in (clog,slog):
                    with log.open('rb') as f:
                        f.seek(offsets.get(log,0));raw=f.read();offsets[log]=f.tell()
                    text=carry.get(log,'')+raw.decode(errors='replace')
                    split=max(text.rfind('\n'),text.rfind('\r'));carry[log]=text[split+1:];text=text[:split+1]
                    text=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',text)
                    if FATAL.search(text) or 'Invalid PhysX transform' in text: raise RuntimeError('GPU/physics failure; no retry')
                    for e,s,b in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)',text):
                        e,s,b=int(e),int(s),int(b);old=previous.get(e,0);seen.add(e)
                        total_actions+=s-old if s>=old else s;previous[e]=s
                        steps.append([e,s,b]);first=first or now;last=now
                memory = None
                if now >= ram_due:
                    memory = ram(); ram_due = now+20
                    rss_peak=max(rss_peak,memory['rss_kib']);pss_peak=max(pss_peak,memory['pss_kib'])
                    available=memory['node_kib']['MemAvailable']
                    available_min=available if available_min is None else min(available_min,available)
                    if available < 128*1024*1024: raise RuntimeError('Node memory headroom stop')
                metrics.write(json.dumps(dict(time=now,gpu=g,ram=memory,steps=steps,actions=total_actions))+'\n');metrics.flush()
                atomic_json(work/'status.json',{**report,'state':'RUNNING','time':now,'steps':previous,'actions':total_actions,'peak_mib':peak,'pss_peak_kib':pss_peak})
                if client.poll() is not None:break
                if server.poll() is not None:raise RuntimeError('Policy exited before client')
                if g['recovery']!='None' or g['memory_mib']>70*1024:raise RuntimeError('GPU health/capacity stop')
                if now-report['start']>DEADLINE:raise RuntimeError('Case deadline reached')
                time.sleep(2)
        for log in (clog,slog):
            with log.open('rb') as f:
                f.seek(offsets.get(log,0));tail=carry.get(log,'')+f.read().decode(errors='replace')
            if FATAL.search(tail) or 'Invalid PhysX transform' in tail:raise RuntimeError('Fatal in final log bytes')
            tail=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',tail)
            for e,s,b in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)',tail):
                e,s=int(e),int(s);old=previous.get(e,0);seen.add(e)
                total_actions+=s-old if s>=old else s;previous[e]=s
                first=first or time.time();last=time.time()
        report['client_exit']=client.returncode
        report['check']=result_check(result,EPISODES)
        report['expected_layouts']=sorted(report['check'].get('layout_ids',[]))==list(range(EPISODES))
        report['observed_envs']=sorted(seen)
        completed=client.returncode==0 and report['check'].get('complete') is True and seen==set(range(n))
        if not completed: raise RuntimeError('Complete results and active environments not verified')
    except Exception as exc:
        report['error']=repr(exc);completed=False
    finally:
        report.update(end=time.time(),peak_mib=peak,actions=total_actions,first_action=first,last_action=last,
                      rss_peak_kib=rss_peak,pss_peak_kib=pss_peak,node_available_min_kib=available_min,
                      action_gpu_util_mean=sum(utils)/len(utils) if utils else None)
        report['cleanup']=[]
        for identity, proc in ((rid,client),(rid+'-server',server)):
            try:
                report['cleanup'].append(guard.cleanup(identity,'bounded_probe_finished'))
                if proc is not None:proc.wait(timeout=10)
            except Exception as exc:
                report.setdefault('cleanup_errors',[]).append(repr(exc));completed=False
        try:
            if guard.scan():raise RuntimeError('Probe processes remain')
            time.sleep(2);report['gpu_after']=require_idle()
        except Exception as exc:
            report.setdefault('cleanup_errors',[]).append(repr(exc));completed=False
        report['state']='COMPLETE' if completed else 'FAILED'
        atomic_json(work/'status.json',report)
    return report

if __name__=='__main__':
    assert os.getuid()==1003
    RUN.mkdir(exist_ok=False)
    guard=ProcessGuard(RUN.name,1003,RUN/'cleanup')
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(RuntimeError('Operator stop')))
    signal.signal(signal.SIGINT,lambda *_: (_ for _ in ()).throw(RuntimeError('Operator stop')))
    pause=P/'runs/sz1-dojo-continuation-20261002-v1/gpu4-scaling-20261003-v1/gpu4-pause-proof.json'
    assert json.loads(pause.read_text())['gpu']['gpu']==4
    require_idle()
    hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [R/'env_cfg/arx_x5.yml',R/'env_cfg/sim/sim_config.yml',R/'scripts/eval_policy.sh',R/'src/eval_client/main.py']}
    atomic_json(RUN/'plan.json',dict(order=ORDER,gpu=4,task=TASK,episodes_per_case=EPISODES,deadline_per_case_s=DEADLINE,capacity_stop_mib=70*1024,ram_sample_s=20,source_sha256=hashes,formal_untouched=True))
    atomic_json(RUN/'owner.json',dict(pid=os.getpid(),proc_stat=Path('/proc/self/stat').read_text(),uid=os.getuid()))
    reports=[]
    for n in ORDER:
        report=case(n);reports.append(report)
        atomic_json(RUN/'summary.json',dict(cases=reports,finished=len(reports)==len(ORDER) or report['state']!='COMPLETE'))
        if report['state']!='COMPLETE':break
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    atomic_json(RUN/'released.json',dict(time=time.time(),gpu=require_idle(),owned_processes=guard.scan(),source_unchanged=True))
