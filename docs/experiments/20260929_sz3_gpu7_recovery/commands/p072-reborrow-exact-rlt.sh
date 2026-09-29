set -euo pipefail
P=/data/chenyiteng/projects/robodojo-openwam-sz3
python3 - <<'PY'
from pathlib import Path
import hashlib,json,socket
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');s=p/'scripts/pi05_gpu7_recovery_20260929';r=p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2';c=p/'rlt-cycle-sz3-pi05-gpu7-v1'
ready=json.loads((r/'repair-20260929-gpu7-v1/ready.json').read_text())
assert ready['protocol_unchanged'] and ready['source_hashes_unchanged']
assert ready['config_sha256']==hashlib.sha256((s/'dojo_sweep.config.json').read_bytes()).hexdigest()
assert ready['continuation_sha256']==hashlib.sha256((s/'continue_pipeline.py').read_bytes()).hexdigest()
assert not (c/'stop-attempt.json').exists()
cfg=json.loads((s/'dojo_sweep.config.json').read_text())
for port in cfg['ports']:
    with socket.socket() as q:q.bind(('127.0.0.1',port))
print('Same protocol, preserved result archive, exact new RLT cycle and ports verified.',flush=True)
PY
/home/chenyiteng/venvs/rlinf-7d07-openpi-robotwin/bin/python -u -B "$P/rlt-cycle-sz3-pi05-gpu7-v1/rlt_cycle_sz3.py" --cycle-dir "$P/rlt-cycle-sz3-pi05-gpu7-v1" stop
