set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
test "$(cat "$PROJECT/logs/checkpoint-ranges.exit")" = 1
test ! -e "/proc/$(cat "$PROJECT/logs/checkpoint-ranges.pid")"
sha256sum "$PROJECT/scripts/download_ranges.py"
cat > "$PROJECT/scripts/checkpoint-ranges-v2.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 -u "$PROJECT/scripts/download_ranges.py"
rc=$?
echo "$rc" > "$PROJECT/logs/checkpoint-ranges-v2.exit"
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/checkpoint-ranges-v2.sh" > "$PROJECT/logs/checkpoint-ranges-v2.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/checkpoint-ranges-v2.pid"
ps -p "$(cat "$PROJECT/logs/checkpoint-ranges-v2.pid")" -o pid,lstart,args
