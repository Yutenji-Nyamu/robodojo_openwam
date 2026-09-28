#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
source "$HOME/miniconda3/etc/profile.d/conda.sh"
cd "$PROJECT/RoboDojo"
export EVAL_ENV_TYPE=sim
export OPENWAM_ALLOW_DUMMY_POLICY=false
export OPENWAM_CKPT_DIR="$PROJECT/checkpoints/OpenWAM-Alpha-Sim-RoboDojo"
export ROBODOJO_MAX_BASH_RETRIES=1
export ROBODOJO_RENDER_GPU=2
export ROBODOJO_VULKAN_COMPAT_SCRIPT="$PROJECT/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py"
export ROBODOJO_RUN_ID="${1:?explicit unique run id required}"
test "$(cat "$PROJECT/logs/install-policy.exit")" = 0 || exit 10
test "$(cat "$PROJECT/logs/install-mirror.exit")" = 0 || exit 11
test "$(cat "$PROJECT/logs/checkpoint-ranges-v2.exit")" = 0 || exit 12
test -f "$PROJECT/logs/task-assets.ready.json" || exit 13
run_dir="$PROJECT/runs/$ROBODOJO_RUN_ID"
mkdir "$run_dir" || exit 14
date -Is > "$run_dir/start.txt"
cp "$PROJECT/project-env.sh" "$run_dir/project-env.sh"
cp "$0" "$run_dir/eval_single.sh"
sha256sum "$ROBODOJO_VULKAN_COMPAT_SCRIPT" > "$run_dir/vulkan-compat.sha256"
cp "$PROJECT/third_party/RoboDawn/.cache/robodojo-vulkan/package_info.json" "$run_dir/vulkan-layer-package.json"
cp env_cfg/sim/sim_config.yml "$run_dir/sim_config.yml"
git rev-parse HEAD > "$run_dir/dojo-head.txt"
git submodule status > "$run_dir/submodules.txt"
git diff -- env_cfg/sim/sim_config.yml scripts/eval_policy.sh > "$run_dir/local-config.patch"
nvidia-smi --query-gpu=index,uuid,pci.bus_id,memory.used --format=csv > "$run_dir/gpu-before.csv"
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory,process_name --format=csv > "$run_dir/gpu-processes-before.csv"
cmd=(bash scripts/robodojo.sh eval
 --policy-dir XPolicyLab/policy/OpenWAM
 --task stack_bowls --ckpt OpenWAM-Alpha-Sim-RoboDojo
 --env-cfg arx_x5 --action-type ee --seed 0 --eval-num 1
 --policy-env "$PROJECT/envs/openwam" --eval-env "$PROJECT/envs/RoboDojo"
 --policy-gpu 3 --env-gpu 2)
printf '%q ' "${cmd[@]}" > "$run_dir/command.sh"
printf '\n' >> "$run_dir/command.sh"
echo "RUN_ID=$ROBODOJO_RUN_ID"
echo "RUN_DIR=$run_dir"
timeout --verbose --signal=TERM --kill-after=30s 1800s "${cmd[@]}" &
runner=$!
echo "$runner" > "$run_dir/timeout.pid"
sleep 0.3
ps -p "$runner" -o pid,ppid,pgid,lstart,args > "$run_dir/timeout-process.txt"
wait "$runner"
rc=$?
echo "$rc" > "$run_dir/exit.txt"
date -Is > "$run_dir/end.txt"
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory,process_name --format=csv > "$run_dir/gpu-processes-after.csv"
echo "RUN_EXIT=$rc"
exit "$rc"
