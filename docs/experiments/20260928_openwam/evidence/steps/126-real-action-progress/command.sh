p=/path/to/robodojo-openwam
python3 - <<'PY'
from pathlib import Path
s=Path('/path/to/robodojo-openwam/logs/sz2_openwam_stack_bowls_s0_20260928_1944.log').read_text(errors='replace').replace(chr(13),chr(10))
print(chr(10).join(s.splitlines()[-25:]))
PY
test ! -f $p/runs/sz2_openwam_stack_bowls_s0_20260928_1944/exit.txt || cat $p/runs/sz2_openwam_stack_bowls_s0_20260928_1944/exit.txt