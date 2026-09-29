#!/usr/bin/env bash
set -uo pipefail
source $PROJECT/project-env.sh
source "$HOME/miniconda3/etc/profile.d/conda.sh"
cd "$PROJECT/RoboDojo"
model="${1:?openwam or pi05}"
export ROBODOJO_RUN_ID="${2:?unique run id required}"
compat="${3:-native}"
env_gpu="${4:-4}"
policy_gpu="${5:-5}"
[[ "$env_gpu" =~ ^[4-7]$ && "$policy_gpu" =~ ^[4-7]$ && "$env_gpu" != "$policy_gpu" ]] || exit 21
export EVAL_ENV_TYPE=sim
export ROBODOJO_MAX_BASH_RETRIES=1
export ROBODOJO_RENDER_GPU="$env_gpu"
export ROBODOJO_EGL_VENDOR_FILE="$PROJECT/cache/nvidia-egl/10_nvidia.json"
export ROBODOJO_NVIDIA_LIBRARY_DIR="$PROJECT/cache/nvidia-libs"
export OPENPI_DATA_HOME="$PROJECT/cache/openpi"
export UV_PYTHON_INSTALL_DIR="$PROJECT/tools/uv-python"
unset CUDA_VISIBLE_DEVICES ROBODOJO_VULKAN_COMPAT_SCRIPT
test "$(cat "$PROJECT/logs/install-sim.exit")" = 0 || exit 10
test "$(cat "$PROJECT/logs/prepare-sim.exit")" = 0 || exit 11
test -f "$PROJECT/logs/task-assets.ready.json" || exit 12
test -f "$ROBODOJO_EGL_VENDOR_FILE" || exit 20
if [[ "$model" == openwam ]]; then
  test "$(cat "$PROJECT/logs/install-openwam.exit")" = 0 || exit 13
  test -f "$PROJECT/logs/checkpoint-import.ready.json" || exit 14
  export OPENWAM_ALLOW_DUMMY_POLICY=false
  export OPENWAM_CKPT_DIR="$PROJECT/checkpoints/OpenWAM-Alpha-Sim-RoboDojo"
  policy=OpenWAM; ckpt=OpenWAM-Alpha-Sim-RoboDojo; action=ee; policy_env="$PROJECT/envs/openwam"
elif [[ "$model" == pi05 ]]; then
  test "$(cat "$PROJECT/logs/install-pi05-r2.exit")" = 0 || exit 15
  test -f "$PROJECT/checkpoints/Pi_05/RoboDojo-sim-arx_x5-joint-0/59999/pi05-inference-ready.json" || exit 16
  policy=Pi_05; ckpt=sim; action=joint; policy_env=uv
else
  exit 17
fi
if [[ "$compat" == compat ]]; then
  export ROBODOJO_VULKAN_COMPAT_SCRIPT="$PROJECT/RoboDojo/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py"
elif [[ "$compat" != native ]]; then
  exit 18
fi
run_dir="$PROJECT/runs/$ROBODOJO_RUN_ID"
mkdir "$run_dir" || exit 19
date -Is > "$run_dir/start.txt"
cp "$PROJECT/project-env.sh" "$run_dir/project-env.sh"
cp "$0" "$run_dir/eval_single.sh"
cp "$ROBODOJO_EGL_VENDOR_FILE" "$run_dir/egl-vendor.json"
cp "$ROBODOJO_NVIDIA_LIBRARY_DIR/libcuda-link.json" "$run_dir/libcuda-link.json"
cp env_cfg/sim/sim_config.yml "$run_dir/sim_config.yml"
git rev-parse HEAD > "$run_dir/dojo-head.txt"
git submodule status > "$run_dir/submodules.txt"
git diff -- scripts/install.sh env_cfg/sim/sim_config.yml scripts/eval_policy.sh > "$run_dir/local-config.patch"
if [[ "$compat" == compat ]]; then
  sha256sum "$ROBODOJO_VULKAN_COMPAT_SCRIPT" > "$run_dir/vulkan-compat.sha256"
  cp third_party/RoboDawn/.cache/robodojo-vulkan/package_info.json "$run_dir/vulkan-layer-package.json"
fi
nvidia-smi --query-gpu=index,uuid,pci.bus_id,memory.used --format=csv > "$run_dir/gpu-before.csv"
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory,process_name --format=csv > "$run_dir/gpu-processes-before.csv"
cmd=(bash scripts/robodojo.sh eval
 --policy-dir "XPolicyLab/policy/$policy"
 --task stack_bowls --ckpt "$ckpt"
 --env-cfg arx_x5 --action-type "$action" --seed 0 --eval-num 1
 --policy-env "$policy_env" --eval-env "$PROJECT/envs/RoboDojo"
 --policy-gpu "$policy_gpu" --env-gpu "$env_gpu")
printf '%q ' "${cmd[@]}" > "$run_dir/command.sh"
printf '\n' >> "$run_dir/command.sh"
echo "RUN_ID=$ROBODOJO_RUN_ID MODEL=$model MODE=$compat"
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
