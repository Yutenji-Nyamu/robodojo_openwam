p=/path/to/robodojo-openwam
nohup bash $p/scripts/diagnose_sim_compat.sh > $p/logs/sim-compat.log 2>&1 < /dev/null &
echo $! > $p/logs/sim-compat.pid
cat $p/logs/sim-compat.pid