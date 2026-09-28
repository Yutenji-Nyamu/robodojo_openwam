p=/path/to/robodojo-openwam
r=sz2_openwam_stack_bowls_s0_20260928_1921
nohup bash "$p/scripts/eval_single.sh" "$r" > "$p/logs/$r.log" 2>&1 < /dev/null &
echo $! > "$p/logs/$r.pid"
cat "$p/logs/$r.pid"
sleep 2
tail -n 20 "$p/logs/$r.log"