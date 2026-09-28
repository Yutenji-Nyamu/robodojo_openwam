set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
test -x "$HOME/miniconda3/bin/conda"
cat > "$PROJECT/scripts/install-policy.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
(
set -e
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda create -y -n openwam python=3.10
conda activate openwam
python -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
while ! test -f "$PROJECT/RoboDojo/XPolicyLab/policy/OpenWAM/install.sh"; do sleep 5; done
cd "$PROJECT/RoboDojo/XPolicyLab/policy/OpenWAM"
bash install.sh
python -m pip freeze > "$PROJECT/logs/policy-pip-freeze.txt"
)
rc=$?
printf '%s\n' "$rc" > "$PROJECT/logs/install-policy.exit"
date -Is
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/install-policy.sh" > "$PROJECT/logs/install-policy.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/install-policy.pid"
ps -p "$(cat "$PROJECT/logs/install-policy.pid")" -o pid,lstart,args
command -v aria2c || true
find /data/USER/tools /home/USER/tools -maxdepth 3 -name aria2c 2>/dev/null || true
