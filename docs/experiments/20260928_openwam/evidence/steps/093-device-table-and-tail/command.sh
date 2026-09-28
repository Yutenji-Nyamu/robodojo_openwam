p=/path/to/robodojo-openwam
l=$p/logs/sz2_openwam_stack_bowls_s0_20260928_1921.log
sed -n '60,135p' "$l"
tail -n 18 "$l"
cat $p/runs/sz2_openwam_stack_bowls_s0_20260928_1921/timeout-process.txt