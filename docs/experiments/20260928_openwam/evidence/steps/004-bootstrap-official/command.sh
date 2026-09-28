set -euo pipefail
PROJECT=/path/to/robodojo-openwam
test ! -e "$PROJECT"
mkdir -p "$PROJECT"/{logs,runs,cache/pip,cache/conda,cache/huggingface,tmp,envs,checkpoints,scripts}
git clone https://github.com/RoboDojo-Benchmark/RoboDojo.git "$PROJECT/RoboDojo"
git -C "$PROJECT/RoboDojo" checkout -b codex/openwam-robodojo 726e9aabfaa642203722eb126f5eaf0f37f3e1ad
cat > "$PROJECT/project-env.sh" <<'EOF'
export PROJECT=/path/to/robodojo-openwam
export PIP_CACHE_DIR="$PROJECT/cache/pip"
export CONDA_PKGS_DIRS="$PROJECT/cache/conda"
export CONDA_ENVS_PATH="$PROJECT/envs"
export HF_HOME="$PROJECT/cache/huggingface"
export TMPDIR="$PROJECT/tmp"
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export OMNI_KIT_ACCEPT_EULA=YES
export ACCEPT_EULA=Y
export PRIVACY_CONSENT=Y
export TERM=xterm-256color
export MAX_JOBS=8
export TORCH_CUDA_ARCH_LIST=9.0
export PATH="$HOME/miniconda3/bin:$PATH"
EOF
cat > "$PROJECT/scripts/install-official.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
cd "$PROJECT/RoboDojo"
date -Is
bash scripts/install.sh -i
rc=$?
printf '%s\n' "$rc" > "$PROJECT/logs/install-official.exit"
git rev-parse HEAD
git submodule status
date -Is
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/install-official.sh" > "$PROJECT/logs/install-official.log" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$PROJECT/logs/install-official.pid"
ps -p "$pid" -o pid,lstart,args
printf 'PROJECT=%s\n' "$PROJECT"
