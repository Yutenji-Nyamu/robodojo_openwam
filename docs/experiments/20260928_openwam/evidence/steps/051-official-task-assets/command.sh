set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
test ! -e /proc/1214361
cat > "$PROJECT/scripts/task-assets.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 -u "$PROJECT/scripts/prepare_task_assets.py"
rc=$?
echo "$rc" > "$PROJECT/logs/task-assets.exit"
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/task-assets.sh" > "$PROJECT/logs/task-assets.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/task-assets.pid"
ps -p "$(cat "$PROJECT/logs/task-assets.pid")" -o pid,lstart,args
