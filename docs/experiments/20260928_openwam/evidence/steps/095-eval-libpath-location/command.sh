p=/path/to/robodojo-openwam
sed -n '1,110p' $p/RoboDojo/scripts/eval_policy.sh
cat $p/envs/RoboDojo/conda-meta/libstdcxx*.json | head -c 500
sed -n '1,35p' $p/RoboDojo/third_party/curobo/setup.py