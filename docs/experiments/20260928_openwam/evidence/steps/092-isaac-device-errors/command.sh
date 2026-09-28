p=/path/to/robodojo-openwam
l=$p/logs/sz2_openwam_stack_bowls_s0_20260928_1921.log
grep -n -E "OpenWAM|loaded|Error|ERROR|Traceback|GPU |Active|Driver Version|DEVICE|Success|Fail" "$l" | tail -n 45
tail -n 16 "$l"