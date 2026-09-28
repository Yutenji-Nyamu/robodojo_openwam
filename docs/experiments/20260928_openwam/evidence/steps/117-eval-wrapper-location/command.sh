p=/path/to/robodojo-openwam
sed -n '135,205p' $p/RoboDojo/scripts/eval_policy.sh
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv