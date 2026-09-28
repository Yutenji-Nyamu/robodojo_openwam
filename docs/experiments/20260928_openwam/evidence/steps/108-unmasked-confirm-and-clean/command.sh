p=/path/to/robodojo-openwam
l=$p/logs/sim-unmasked.log
grep -n -E "^SIMULATION_APP|CUDA_VISIBLE|bad state|carbOnPluginStartup|app ready" "$l" | head -n 12
cat $p/logs/sim-unmasked.exit
ps -eo user,pid,pgid,args | awk '$3==1834092'
nvidia-smi --query-gpu=index,memory.used --format=csv