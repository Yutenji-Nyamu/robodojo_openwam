p=/path/to/robodojo-openwam
nohup bash $p/scripts/diagnose_sim_unmasked.sh > $p/logs/sim-unmasked.log 2>&1 < /dev/null &
echo $! > $p/logs/sim-unmasked.pid
cat $p/logs/sim-unmasked.pid