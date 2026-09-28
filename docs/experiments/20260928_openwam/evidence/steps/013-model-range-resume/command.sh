set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 - <<'PY'
import json,os,pathlib,signal,subprocess,time
root=pathlib.Path('/path/to/robodojo-openwam')
pid=int((root/'logs/checkpoint-download.pid').read_text())
p=pathlib.Path('/proc')/str(pid)
assert p.stat().st_uid==os.getuid()
assert str(root/'scripts/checkpoint-download.sh') in (p/'cmdline').read_bytes().decode().replace('\0',' ')
mapping={int(a):int(b) for a,b in (l.split() for l in subprocess.check_output(['ps','-eo','pid=,ppid='],text=True).splitlines())}
targets=[pid]
for p in targets:targets.extend(c for c,parent in mapping.items() if parent==p and c not in targets)
records=[]
for pid in targets:
    p=pathlib.Path('/proc')/str(pid)
    if p.exists():
        assert p.stat().st_uid==os.getuid()
        records.append({'pid':pid,'cmd':(p/'cmdline').read_bytes().decode().replace('\0',' ')})
for r in reversed(records):
    try:os.kill(r['pid'],signal.SIGTERM)
    except ProcessLookupError:pass
time.sleep(1)
for r in records:
    p=pathlib.Path('/proc')/str(r['pid'])
    if p.exists():assert p.joinpath('stat').read_text().split()[2]=='Z'
size=(root/'checkpoints/OpenWAM-Alpha-Sim-RoboDojo/checkpoint_step_60000.safetensors').stat().st_size
(root/'logs/checkpoint-download-superseded.json').write_text(json.dumps({'reason':'slow single connection; continue same verified official file with six ranges','prefix_bytes':size,'stopped_processes':records},indent=2))
print('preserved_prefix_bytes',size)
PY
cat > "$PROJECT/scripts/checkpoint-ranges.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 -u "$PROJECT/scripts/download_ranges.py"
rc=$?
echo "$rc" > "$PROJECT/logs/checkpoint-ranges.exit"
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/checkpoint-ranges.sh" > "$PROJECT/logs/checkpoint-ranges.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/checkpoint-ranges.pid"
ps -p "$(cat "$PROJECT/logs/checkpoint-ranges.pid")" -o pid,lstart,args
