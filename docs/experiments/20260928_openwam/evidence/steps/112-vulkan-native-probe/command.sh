p=/path/to/robodojo-openwam
PYTHONNOUSERSITE=1 $p/envs/RoboDojo/bin/python -B $p/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py --probe > $p/logs/vulkan-native-probe.json
cat $p/logs/vulkan-native-probe.json