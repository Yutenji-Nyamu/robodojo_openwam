p=/path/to/robodojo-openwam
grep -E "SIMULATION_APP|app ready|Error|CUDA_VISIBLE|Active|GPU2|RUN_EXIT" $p/logs/sim-unmasked.log | tail -n 12
tail -n 5 $p/logs/sim-unmasked.log
test ! -f $p/logs/sim-unmasked.exit || cat $p/logs/sim-unmasked.exit