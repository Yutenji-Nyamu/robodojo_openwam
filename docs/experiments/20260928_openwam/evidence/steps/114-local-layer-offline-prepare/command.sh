p=/path/to/robodojo-openwam
c=$p/third_party/RoboDawn
PYTHONNOUSERSITE=1 $p/envs/RoboDojo/bin/python -B $c/scripts/robodojo/compat/vulkan_driver_compat.py --prepare --package $c/vulkan-profiles_1.4.313.0~rc1-1lunarg22.04-1_amd64.deb --jsoncpp-package $c/libjsoncpp25_1.9.5-3_amd64.deb