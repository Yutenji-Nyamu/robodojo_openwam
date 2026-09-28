#!/usr/bin/env bash
set -uo pipefail
p=/path/to/robodojo-openwam
l=$p/logs/sz2_openwam_stack_bowls_s0_20260928_1926.log
sed -n '38,98p' "$l"
grep -n -B 3 -A 4 -E '\[Error\]|Traceback|PythonTracebackStatus|app ready|Simulation App Startup|Fatal' "$l" | head -n 65
find "$p/envs/RoboDojo/lib/python3.11/site-packages/isaacsim/kit/data/Kit/Isaac-Sim/5.1" -maxdepth 1 -name '*.py.txt' -mmin -15 -print -exec head -n 110 {} \;
cat "$p/runs/sz2_openwam_stack_bowls_s0_20260928_1926/timeout-process.txt"
ps -p 1835404,2103329 -o user,pid,pgid,args
