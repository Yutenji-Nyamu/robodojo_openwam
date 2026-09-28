p=/path/to/robodojo-openwam
ps -p 3967922 -o pid,etime,time,%cpu,rss,stat,wchan
ps --ppid 3967922 -o pid,etime,%cpu,rss,args
ls -l $p/logs/sz2_openwam_stack_bowls_s0_20260928_1944.log
find $p/envs/RoboDojo -maxdepth 8 -type f -name py-spy 2>/dev/null | head -n 3
tail -n 5 $p/logs/sz2_openwam_stack_bowls_s0_20260928_1944.log