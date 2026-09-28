#!/usr/bin/env bash
set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 - <<'PY'
from pathlib import Path
p=Path('/path/to/robodojo-openwam/RoboDojo/scripts/eval_policy.sh')
s=p.read_text()
needle='MAX_BASH_RETRIES="${ROBODOJO_MAX_BASH_RETRIES:-10}"\n'
assert s.count(needle)==1 and 'sim_cmd=(' not in s
prefix='''# Optional process-local Vulkan allocation-limit compatibility for Isaac 5.1.
sim_cmd=(python -u src/eval_client/main.py)
if [[ -n "${ROBODOJO_VULKAN_COMPAT_SCRIPT:-}" ]]; then
  sim_cmd=(python "$ROBODOJO_VULKAN_COMPAT_SCRIPT" --isaac51 --gpu-index "$device_id" -- "${sim_cmd[@]}")
fi

'''
s=s.replace(needle,prefix+needle,1)
assert s.count('  python -u src/eval_client/main.py \\')==1
s=s.replace('  python -u src/eval_client/main.py \\', '  "${sim_cmd[@]}" \\',1)
p.write_text(s)
PY
bash -n "$PROJECT/RoboDojo/scripts/eval_policy.sh"
bash -n "$PROJECT/scripts/eval_single.sh"
git -C "$PROJECT/RoboDojo" diff -- scripts/eval_policy.sh env_cfg/sim/sim_config.yml > "$PROJECT/logs/local-vulkan-compat.patch"
r=sz2_openwam_stack_bowls_s0_20260928_1944
nohup bash "$PROJECT/scripts/eval_single.sh" "$r" > "$PROJECT/logs/$r.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/$r.pid"
cat "$PROJECT/logs/$r.pid"
