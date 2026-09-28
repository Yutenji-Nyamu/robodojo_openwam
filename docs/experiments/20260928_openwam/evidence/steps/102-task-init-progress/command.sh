p=/path/to/robodojo-openwam
l=$p/logs/sz2_openwam_stack_bowls_s0_20260928_1926.log
tail -n 50 "$l"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv