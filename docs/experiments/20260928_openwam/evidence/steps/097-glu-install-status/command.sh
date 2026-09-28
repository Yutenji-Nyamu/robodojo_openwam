p=/path/to/robodojo-openwam
tail -n 22 $p/logs/install-glu.log
test ! -f $p/logs/install-glu.exit || cat $p/logs/install-glu.exit
nvidia-smi --query-gpu=index,memory.used --format=csv