set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 - <<'PY'
from pathlib import Path
root=Path('/path/to/robodojo-openwam/RoboDojo')
p=root/'env_cfg/sim/sim_config.yml'
s=p.read_text(); assert s.count('  num_envs: 10')==1
p.write_text(s.replace('  num_envs: 10','  num_envs: 1'))
p=root/'scripts/eval_policy.sh'
s=p.read_text(); marker='  KIT_ARGS+=" --enable ${ext}"\ndone\n'
assert s.count(marker)==1
s=s.replace(marker,marker+'# Keep this evaluation on one render GPU in the shared server.\nKIT_ARGS+=" --/renderer/multiGpu/enabled=false --/renderer/activeGpu=${ROBODOJO_RENDER_GPU:-$device_id}"\necho "[INFO] single GPU render: ${ROBODOJO_RENDER_GPU:-$device_id}"\n')
p.write_text(s)
PY
git -C "$PROJECT/RoboDojo" diff -- env_cfg/sim/sim_config.yml scripts/eval_policy.sh > "$PROJECT/logs/local-single-env-render.patch"
cat "$PROJECT/logs/local-single-env-render.patch"
bash -n "$PROJECT/RoboDojo/scripts/eval_policy.sh"
nvidia-smi --query-gpu=index,uuid,pci.bus_id,memory.used --format=csv,noheader
command -v vulkaninfo || true
