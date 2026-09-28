#!/usr/bin/env bash
set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 - <<'PY'
from pathlib import Path
p=Path('/path/to/robodojo-openwam/RoboDojo/scripts/eval_policy.sh')
s=p.read_text()
needle='set -euo pipefail\n'
assert s.count(needle)==1 and 'Local environment libraries' not in s
s=s.replace(needle,needle+'\n# Local environment libraries provide libGLU and C++ runtime for Isaac Sim.\nexport LD_LIBRARY_PATH="${CONDA_PREFIX:?}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n',1)
p.write_text(s)
PY
bash -n "$PROJECT/RoboDojo/scripts/eval_policy.sh"
git -C "$PROJECT/RoboDojo" diff -- scripts/eval_policy.sh env_cfg/sim/sim_config.yml > "$PROJECT/logs/local-sim-libraries.patch"
nohup bash "$PROJECT/scripts/install_glu.sh" > "$PROJECT/logs/install-glu.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/install-glu.pid"
cat "$PROJECT/logs/install-glu.pid"
