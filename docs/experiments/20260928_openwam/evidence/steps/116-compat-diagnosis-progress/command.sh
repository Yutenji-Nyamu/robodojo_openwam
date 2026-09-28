p=/path/to/robodojo-openwam
grep -n -E "^SIMULATION_APP|vulkan_compat|app ready|Error|Fatal" $p/logs/sim-compat.log | tail -n 15
tail -n 8 $p/logs/sim-compat.log
test ! -f $p/logs/sim-compat.exit || cat $p/logs/sim-compat.exit