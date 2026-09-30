"""Freeze exactly the four live restored RLT runs for this new Dojo cycle."""
import argparse,copy,importlib.util,json,os,shutil,socket
from pathlib import Path

HOST={'h100-gpu02':'sz2','h100-gpu01':'sz3'}[socket.gethostname()]
P=Path('/data/chenyiteng/projects')/('robodojo-openwam' if HOST=='sz2' else 'robodojo-openwam-sz3')
R=P/'runs'/('sz2_openwam_official_6300_n4_dual_20260929_r2' if HOST=='sz2' else 'sz3_pi05_official_6300_n4_dual_20260929_r2')
STAGE=P/('runs/rlt-cycle-20260930-single-v2' if HOST=='sz2' else 'rlt-cycle-sz3-20260930-single-v2')
HELPER='rlt_cycle.py' if HOST=='sz2' else 'rlt_cycle_sz3.py'
D=Path(__file__).parent
read=lambda p:json.loads(Path(p).read_text())
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module(D/HELPER,'new_cycle')

def checkpoint(run,cfg,repo,fallback):
    if HOST=='sz3':
        r=m.select_recovery(run,cfg,repo);assert r['mode']=='resume_checkpoint';return r['checkpoint'],r
    candidates=list(Path(run).glob('checkpoints/global_step_*'))+list(Path(run).glob(Path(run).name+'/checkpoints/global_step_*'))
    candidates=sorted(set(candidates),key=lambda p:int(p.name.rsplit('_',1)[1]),reverse=True)
    errors=[]
    for p in candidates+[Path(fallback)]:
        if not (p/'actor/sac_components/rlt_trainer_state/complete.json').is_file():continue
        try:return m.inspect_checkpoint(p,cfg,repo),{'rejected':errors}
        except (AssertionError,FileNotFoundError,RuntimeError) as e:errors.append({'path':str(p),'error':str(e)[:400]})
    raise RuntimeError('No validated checkpoint for '+str(run))

def prepare():
    from omegaconf import OmegaConf
    a=read(R/'active-continuation.json');previous=Path(a.get('cycle_dir',a.get('cycle')))
    om=module(previous/HELPER,'old_cycle');old=om.load_plan(previous)
    assert (previous/'resumed-dispatched.json').is_file()
    stopped=read(previous/'rlt-stopped.json')
    m.checked_dir(STAGE);assert not STAGE.exists()
    out=copy.deepcopy(old);out.update(cycle_id=STAGE.name,time=m.now(),script_sha256=m.sha(D/HELPER),
        management_namespace='dojo-rlt-ops-'+STAGE.name[-40:],predecessor_cycle=str(previous),runs={})
    live=m.actors(old);prepared=[]
    for key,row in old['runs'].items():
        run=Path(row['new_run']);rt=run/'runtime';identity=read(rt/'driver-identity.json')
        launch=read(previous/(key+'-launched.json'))['identity']
        assert m.same(identity) and identity['uid']==20001
        assert (identity['pid'],identity['start'])==(launch['pid'],launch['start'])
        argv=(Path('/proc')/str(identity['pid'])/'cmdline').read_bytes().split(b'\0')
        assert str(previous/HELPER).encode() in argv and b'driver' in argv and key.encode() in argv
        identity.update(match_cmdline=True,cmdline_sha256=m.proc(identity['pid'])['cmdline_sha256'])
        actors=m.active(live,row['namespace']);jobs={x['job_id'] for x in actors}
        assert len(jobs)==1 and actors;m.validate_actor_rows(actors,row['namespace'],jobs)
        cfg=m.config(rt/'resolved.yaml')
        fallback=stopped['runs'][key]['checkpoint']['path'] if HOST=='sz2' else None
        cp,recovery=checkpoint(run,cfg,old['repo'],fallback)
        target=m.ROOT/'results/rlinf-rlt'/m.resumed_name(run,STAGE.name)
        namespace='dr-'+STAGE.name[-40:]+'-g'+key[3:]
        assert not target.exists() and not m.active(live,namespace)
        new_cfg,changes=m.resumed_config(cfg,run,target,cp['path'])
        env=read(rt/'environment.json');assert not any(k in env for k in m.MASKS)
        env={k:v.replace(str(run),str(target)).replace(row['namespace'],namespace) for k,v in env.items()}
        item={'task':row['task'],'kind':row['kind'],'gpus':row['gpus'],'entry':row['entry'],
            'original_run':str(run),'original_namespace':row['namespace'],'original_identity':identity,
            'original_jobs':sorted(jobs),'original_config_sha256':m.sha(rt/'resolved.yaml'),
            'new_run':str(target),'namespace':namespace,'config_changes':changes,
            'dependencies':m.dependency_snapshot(cfg),'latest_metrics_before':m.latest_metrics(run)}
        if HOST=='sz2':item['checkpoint']=cp
        else:item['recovery']=recovery
        prepared.append((key,cfg,new_cfg,env,item))
    assert {r[0] for r in prepared}=={'gpu4','gpu5','gpu6','gpu7'}
    STAGE.mkdir(mode=0o700);shutil.copyfile(D/HELPER,STAGE/HELPER);(STAGE/HELPER).chmod(0o500)
    for key,cfg,new_cfg,env,item in prepared:
        pre=STAGE/'prepared'/key;pre.mkdir(parents=True,mode=0o700)
        OmegaConf.save(OmegaConf.create(cfg),pre/'original.yaml',resolve=True)
        OmegaConf.save(OmegaConf.create(new_cfg),pre/'resolved.yaml',resolve=True)
        m.save(pre/'environment.json',env)
        for file in pre.iterdir():file.chmod(0o600)
        item['prepared_sha256']={n:m.sha(pre/n) for n in ('original.yaml','resolved.yaml','environment.json')}
        out['runs'][key]=item
    m.save(STAGE/'plan.json',out)
    receipt={'time':m.now(),'cycle':str(STAGE),'runs':{k:{'new_run':v['new_run'],
        'checkpoint_step':(v.get('checkpoint') or v['recovery']['checkpoint'])['step']} for k,v in out['runs'].items()}}
    m.save(STAGE/'prepared.json',receipt);return receipt

def stop():
    plan=m.load_plan(STAGE)
    if HOST=='sz2':
        fallbacks={row['original_run']:row for row in plan['runs'].values()}
        def selected(run):
            row=fallbacks[str(run)];cfg=m.config(STAGE/'prepared'/('gpu'+str(row['gpus'][0]))/'original.yaml')
            cp,_=checkpoint(run,cfg,plan['repo'],row['checkpoint']['path']);return Path(cp['path'])
        m.latest_complete=selected
    return m.stop(STAGE)

if __name__=='__main__':
    assert os.getuid()==20001
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','stop']);args=p.parse_args()
    print(json.dumps(prepare() if args.action=='prepare' else stop()))
