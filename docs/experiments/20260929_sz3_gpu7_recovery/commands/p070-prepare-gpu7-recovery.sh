set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json,shutil
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');old=p/'scripts/pi05_formal_20260929_r2';new=p/'scripts/pi05_gpu7_recovery_20260929'
new.mkdir(exist_ok=False)
for name in ['dojo_sweep.py','process_guard.py','dojo_sweep.config.json','test_dojo_sweep.py']:
    shutil.copy2(old/name,new/name)
prior=p/'rlt-cycle-sz3-pi05-full-r2'
text=(prior/'rlt_cycle_sz3.py').read_text()
before="PREVIOUS = ROOT / 'projects/robodojo-openwam-sz3/rlt-cycle-sz3-pi05-full-r1'"
after="PREVIOUS = ROOT / 'projects/robodojo-openwam-sz3/rlt-cycle-sz3-pi05-full-r2'"
assert text.count(before)==1
(new/'rlt_cycle_sz3.py').write_text(text.replace(before,after))
print(json.dumps({'directory':str(new),'previous_cycle':str(prior),'resume_dispatched':(prior/'resumed-dispatched.json').exists()}))
PY
