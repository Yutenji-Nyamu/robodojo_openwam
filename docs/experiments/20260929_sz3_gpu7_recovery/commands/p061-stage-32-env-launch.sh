set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json,hashlib,subprocess,zipfile,datetime
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');repo=p/'publication-pi05-full/repo';dest=repo/'docs/experiments/20260929_sz3_pi05_full';s=p/'scripts/pi05_formal_20260929_r2';r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';c=p/'rlt-cycle-sz3-pi05-full-r2'
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()=='50aab2b28298db42c4b25c59c8967eae8d91e84c'
assert subprocess.check_output(['git','-C',str(p/'RoboDojo'),'rev-parse','HEAD'],text=True).strip()=='50aab2b28298db42c4b25c59c8967eae8d91e84c'
with zipfile.ZipFile(p/'scripts/publication-formal.zip') as z:
    for name in z.namelist():
        f=(dest/name).resolve();assert f.is_relative_to(dest.resolve());f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))
health=json.loads((r/'health-latest.json').read_text());assert health['pipeline-current.json']['phase']=='EVALUATING' and 'final.json' not in health
assert len(health['workers'])==8 and all('server' in w and 'task' in w for w in health['workers'])
assert all(set(w['task']['env_steps'])=={'0','1','2','3'} and all(v['step']>1 for v in w['task']['env_steps'].values()) for w in health['workers'])
assert not (r/'pipeline-final.json').exists()
for src,name in [(r/'plan.json','plan-preflight.json'),(r/'health-latest.json','launch-health.json'),(p/'runs/full-assets-sz3-20260929-r2/ready.json','assets-ready.json')]:
    v=json.loads(src.read_text());(dest/'evidence'/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
cfg=json.loads((s/'dojo_sweep.config.json').read_text());(dest/'controller/dojo_sweep.config.example.json').write_text(json.dumps(cfg,indent=2)+'\n')
for name in ['dojo_sweep.py','process_guard.py','formal_pipeline.py','test_dojo_sweep.py']:
    assert (dest/'controller'/name).read_bytes()==(s/name).read_bytes(),name
stopped=json.loads((c/'rlt-stopped.json').read_text())
cutover={'cycle':c.name,'all_original_drivers_stopped':stopped['all_original_drivers_stopped'],'all_original_namespaces_empty':stopped['all_original_namespaces_empty'],'gpus_released_before_dojo':stopped['gpus_released'],'recovery':{k:{'mode':v['recovery']['mode'],'checkpoint_step':v['recovery']['checkpoint']['step']} for k,v in stopped['runs'].items()},'automatic_restore':'formal_pipeline.py waits for exact Dojo release receipt, then resumes these four unchanged RLT runs','shared_ray_action':'none'}
(dest/'evidence/rlt-cutover.json').write_text(json.dumps(cutover,indent=2)+'\n')
reset=json.loads((c/'formal-idle-gpu-reset.json').read_text())
reset={'state':reset['state'],'actions':[{k:v for k,v in row.items() if k in ['gpu','state','exit','stdout','stderr','time']} for row in reset['actions']]}
(dest/'evidence/gpu-reset.json').write_text(json.dumps(reset,indent=2)+'\n')
progress=sum(v.get('detail_count',0) for v in health['results']);success=sum(v.get('successes',0) for v in health['results']);videos=sum(v.get('video_count',0) for v in health['results'])
text=f"# 正式启动现场\n\n记录时间：{health['time']}。当前批次 `{health['run_id']}`，状态 **EVALUATING**。8个策略服务、8个仿真worker，每worker4环境；GPU4–7。\n\n"
text+=f"官方预算54配置 × 3个seed，原生25/50回合，总6300。当前落盘 {progress} 回合，成功 {success}，视频 {videos}；这里只是启动现场，完整任务验收和最终官方汇总以跑完后的result-audit为准。\n\n"
text+='全部8个worker的4个环境均已实际推进动作。当前步骤：\n\n| worker | 任务 | env0 | env1 | env2 | env3 |\n|---|---|---:|---:|---:|---:|\n'
for w in health['workers']:
    task=Path(w['task']['log']).parent.name
    text+='| '+w['worker']+' | '+task+' | '+' | '.join(str(w['task']['env_steps'][str(i)]['step']) for i in range(4))+' |\n'
text+='\n'
text+='| GPU | 显存 MiB | 总显存 MiB | 瞬时利用率 % |\n|---:|---:|---:|---:|\n'
for line in health['gpu_snapshot']:
    values=[int(v.strip()) for v in line.split(',')]
    if values[0]>=4:text+='| '+' | '.join(map(str,values))+' |\n'
text+=f"\n整机内存可用 {health['mem_available_gib']} GiB / {health['mem_total_gib']} GiB。各seed权重ready："+', '.join(f"seed{k}={v['ready']}" for k,v in health['seeds'].items())+'。进入每个seed前再次核验固定manifest与实际文件。\n\n'
text+='部署源码锁 `50aab2b28298db42c4b25c59c8967eae8d91e84c`；当前控制器源码及hash见 controller/ 与 evidence/plan-preflight.json。日志发布使用独立checkout，运行时的源码HEAD、配置和controller保持不变。\n\n'
text+='前两次尝试均回合0：第一次临时端口冲突；第二次Linux exec期间进程environ短暂不可读。修复为范围外固定端口，以及每次重新读取身份的有界重试。400次并发exec复现从49错误降至0，13项控制器检查通过；持续权限错误仍报错。两次失败均已清理并自动派发RLT恢复，失败日志保留。\n\n'
text+='当前RLT暂借四卡，已固定有效CP25及原累计3000轮实配。Dojo结束/中断/基础设施错误后，监督器先核全部本批进程与GPU释放，再自动恢复四组RLT；共享Ray和其他用户未操作。\n\n'
text+='产物包括每任务原生_result.json、三路相机MP4、每worker启动/推理日志、GPU/内存采样、逐seed summary及最终官方汇总。当前无法由启动阶段可靠估计整个跨任务耗时，π0.5批接口内部逐环境推理，不套用OpenWAM吞吐。\n'
(dest/'LAUNCH_STATUS.md').write_text(text)
files=[str(f.relative_to(repo)) for f in sorted(dest.rglob('*')) if f.is_file()]
for name in files:
    raw=(repo/name).read_bytes()
    for token in [b'PRIVATE KEY-----',b'hf_',b'ghp_',b'github_pat_',b'zxcv',b'SEETA_SSH_PASSWORD=']:
        assert token not in raw,(name,token)
subprocess.run(['git','-C',str(repo),'add','--',*files],check=True)
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True)
staged=subprocess.check_output(['git','-C',str(repo),'diff','--cached','--name-only'],text=True).splitlines()
assert all(f in files for f in staged)
(p/'publication-pi05-full/review.json').write_text(json.dumps({'base':'50aab2b28298db42c4b25c59c8967eae8d91e84c','files':staged,'sha256':{f:hashlib.sha256((repo/f).read_bytes()).hexdigest() for f in staged}},indent=2)+'\n')
print(json.dumps({'phase':'EVALUATING','run_id':r.name,'snapshot_time':health['time'],'episodes':progress,'successes':success,'videos':videos,'files_staged':len(staged)}))
print(text)
PY
git -C /data/chenyiteng/projects/robodojo-openwam-sz3/publication-pi05-full/repo diff --cached --stat
