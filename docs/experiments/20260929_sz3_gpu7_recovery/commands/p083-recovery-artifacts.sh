set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,time
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';repair=r/'repair-20260929-gpu7-v1';c=p/'rlt-cycle-sz3-pi05-gpu7-v1'
ready=json.loads((repair/'ready.json').read_text());stopped=json.loads((c/'rlt-stopped.json').read_text())
v={'preservation':{'episodes':ready['episodes'],'protocol_unchanged':ready['protocol_unchanged'],'source_hashes_unchanged':ready['source_hashes_unchanged'],'controller_hashes_unchanged':ready['controller_hashes_unchanged'],'config_sha256':ready['config_sha256'],'continuation_sha256':ready['continuation_sha256'],'tasks':[{k:x[k] for k in ['task','seed','expected','action','episodes','successes'] if k in x} for x in ready['rows'] if x['action']!='fresh']},'rlt':{'cycle':c.name,'all_original_drivers_stopped':stopped['all_original_drivers_stopped'],'all_original_namespaces_empty':stopped['all_original_namespaces_empty'],'gpus_released':stopped['gpus_released'],'recovery':{k:{'mode':x['recovery']['mode'],'checkpoint_step':x['recovery']['checkpoint']['step']} for k,x in stopped['runs'].items()},'resume_dispatched':(c/'resumed-dispatched.json').exists()},'current_plan_sha256':hashlib.sha256((r/'plan.json').read_bytes()).hexdigest(),'deployment_head':subprocess.check_output(['git','-C',str(p/'RoboDojo'),'rev-parse','HEAD'],text=True).strip(),'time':time.time()}
print(json.dumps(v,ensure_ascii=False))
PY
