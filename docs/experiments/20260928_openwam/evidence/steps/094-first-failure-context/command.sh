p=/path/to/robodojo-openwam
l=$p/logs/sz2_openwam_stack_bowls_s0_20260928_1921.log
grep -n -A 24 -B 5 -E "Traceback|Exception|ModuleNotFound|ImportError|^RUN_EXIT" "$l" | tail -n 100
ps -eo user,pid,pgid,args | awk '$3==1274116'
find $p/envs/RoboDojo/lib -maxdepth 1 -name '*GLU*'