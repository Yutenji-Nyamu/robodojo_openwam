set -euo pipefail
/usr/bin/python3 - <<'PY'
from pathlib import Path
import datetime,json,subprocess
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');c=p/'rlt-cycle-sz3-pi05-gpu7-v1'
reset=json.loads((c/'gpu7-reset.json').read_text());since=datetime.datetime.fromtimestamp(reset['time']).astimezone().strftime('%Y-%m-%d %H:%M:%S')
v=subprocess.run(['journalctl','-k','--since',since,'--no-pager','-g','NVRM: Xid|Out of memory|oom-kill|I/O error|EXT4-fs error|Buffer I/O'],capture_output=True,text=True,timeout=20)
print(json.dumps({'checked_at':datetime.datetime.now().astimezone().isoformat(),'since_reset':since,'kernel_rc':v.returncode,'kernel':v.stdout,'stderr':v.stderr,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu,ecc.errors.uncorrected.volatile.total','--format=csv,noheader,nounits'],text=True).splitlines()}))
PY
