source /path/to/robodojo-openwam/project-env.sh
$PROJECT/envs/RoboDojo/bin/python -m pip check
nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory,process_name --format=csv
bash -n $PROJECT/scripts/eval_single.sh