source /path/to/robodojo-openwam/project-env.sh
$PROJECT/envs/RoboDojo/bin/python -m pip freeze > $PROJECT/logs/sim-pip-freeze.txt
conda list -p $PROJECT/envs/RoboDojo --explicit > $PROJECT/logs/sim-conda-explicit.txt
git -C $PROJECT/RoboDojo diff --stat
ps -eo user,pid,args | grep -E "diagnose_sim_unmasked|eval_single.sh|setup_policy_server.py" | grep -v grep