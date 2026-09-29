set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json,os,hashlib,subprocess
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';s=p/'scripts/pi05_formal_20260929_r2'
current=json.loads((r/'pipeline-current.json').read_text());assert current['phase']=='EVALUATING'
alive={}
for name in ['pipeline-launch.json','dojo-controller-identity.json']:
    row=json.loads((r/name).read_text());q=Path('/proc')/str(row['pid'])
    assert q.stat().st_uid==row['uid']==20001
    fields=(q/'stat').read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and int(fields[19])==row['start']
    alive[name]={'pid':row['pid'],'start':row['start'],'verified':True}
plan=json.loads((r/'plan.json').read_text())
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in plan['source_sha256'].items())
assert all(hashlib.sha256((s/f).read_bytes()).hexdigest()==h for f,h in plan['controller_sha256'].items())
assert plan['episode_total']==6300 and len(plan['tasks'])==54 and plan['seeds']==[0,1,2]
assert not (p/'rlt-cycle-sz3-pi05-full-r2/resumed-dispatched.json').exists()
assert not (r/'final.json').exists() and not (r/'pipeline-final.json').exists()
print(json.dumps({'phase':current['phase'],'alive':alive,'runtime_sources_and_controllers_unchanged':True,'episodes_planned':6300,'tasks_per_seed':54,'seeds':[0,1,2],'automatic_return_cycle':'rlt-cycle-sz3-pi05-full-r2'}))
PY
