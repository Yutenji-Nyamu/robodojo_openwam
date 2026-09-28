p=/path/to/robodojo-openwam
LD_LIBRARY_PATH=$p/envs/RoboDojo/lib $p/envs/RoboDojo/bin/python -c "import ctypes; ctypes.CDLL('libGLU.so.1'); print('GLU_LOAD_OK')" || exit 1
r=sz2_openwam_stack_bowls_s0_20260928_1926
nohup bash "$p/scripts/eval_single.sh" "$r" > "$p/logs/$r.log" 2>&1 < /dev/null &
echo $! > "$p/logs/$r.pid"
cat "$p/logs/$r.pid"