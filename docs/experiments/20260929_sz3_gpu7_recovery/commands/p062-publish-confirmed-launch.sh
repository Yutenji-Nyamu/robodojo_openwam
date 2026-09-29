set -euo pipefail
P=/data/chenyiteng/projects/robodojo-openwam-sz3
cd "$P/publication-pi05-full/repo"
python3 - <<'PY'
from pathlib import Path
import json,hashlib,subprocess
p=Path('/data/chenyiteng/projects/robodojo-openwam-sz3');repo=p/'publication-pi05-full/repo';r=json.loads((p/'publication-pi05-full/review.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==r['base']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='codex/sz3-dojo-openwam-pi05'
assert set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())==set(r['files'])
assert all(hashlib.sha256((repo/f).read_bytes()).hexdigest()==h for f,h in r['sha256'].items())
current=json.loads((p/'runs/sz3_pi05_official_6300_n4_dual_20260929_r2/pipeline-current.json').read_text());assert current['phase']=='EVALUATING'
subprocess.run(['git','diff','--cached','--check'],check=True)
PY
git -c user.name=Yutenji-Nyamu -c user.email=Yutenji-Nyamu@users.noreply.github.com commit -m "Launch SZ3 full Pi05 evaluation and document startup recovery"
export GIT_SSH_COMMAND='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10'
export GIT_TERMINAL_PROMPT=0
git push origin HEAD:refs/heads/codex/sz3-dojo-openwam-pi05
test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/codex/sz3-dojo-openwam-pi05 | cut -f1)"
git log -1 --format='%H %s'
git show --format= --name-status HEAD
test "$(git -C "$P/RoboDojo" rev-parse HEAD)" = 50aab2b28298db42c4b25c59c8967eae8d91e84c
