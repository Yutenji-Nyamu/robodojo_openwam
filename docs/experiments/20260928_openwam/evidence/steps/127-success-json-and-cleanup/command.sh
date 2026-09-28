p=/path/to/robodojo-openwam
find $p/RoboDojo/eval_result -path '*sz2_openwam_stack_bowls_s0_20260928_1944/*' -name '*.json' -print -exec cat {} \;
ps -p 3657210,3657291,3967922 -o user,pid,pgid,args
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv