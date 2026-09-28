p=/path/to/robodojo-openwam
grep -n -E "active_gpu|physics_gpu|multi_gpu|extra_args|headless" $p/envs/RoboDojo/lib/python3.11/site-packages/isaacsim/exts/isaacsim.simulation_app/isaacsim/simulation_app/simulation_app.py | head -n 40
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv