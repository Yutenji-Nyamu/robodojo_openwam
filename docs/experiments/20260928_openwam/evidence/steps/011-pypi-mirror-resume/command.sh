set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 - <<'PY'
import json,os,pathlib,signal,subprocess,time
root=pathlib.Path('/path/to/robodojo-openwam')
pid=int((root/'logs/install-official.pid').read_text())
proc=pathlib.Path('/proc')/str(pid)
assert proc.stat().st_uid==os.getuid()
assert str(root/'scripts/install-official.sh') in (proc/'cmdline').read_bytes().decode().replace('\0',' ')
mapping={int(a):int(b) for a,b in (l.split() for l in subprocess.check_output(['ps','-eo','pid=,ppid='],text=True).splitlines())}
targets=[pid]
for p in targets:
    targets.extend(c for c,parent in mapping.items() if parent==p and c not in targets)
records=[]
for p in targets:
    q=pathlib.Path('/proc')/str(p)
    if q.exists():
        assert q.stat().st_uid==os.getuid()
        records.append({'pid':p,'cmd':(q/'cmdline').read_bytes().decode(errors='replace').replace('\0',' ')})
assert any('pip install -r '+str(root/'RoboDojo/scripts/requirements.txt') in r['cmd'] for r in records),records
(root/'logs/install-official-network-stop.json').write_text(json.dumps({'reason':'PyPI download 34.6 kB/s; same package constraints via reachable Tsinghua mirror','processes':records},indent=2))
for r in reversed(records):
    try:os.kill(r['pid'],signal.SIGTERM)
    except ProcessLookupError:pass
time.sleep(1)
print('stopped_owned_install', [r['pid'] for r in records])
PY
printf '\nexport PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple\n' >> "$PROJECT/project-env.sh"
cat > "$PROJECT/scripts/install-mirror.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
cd "$PROJECT/RoboDojo"
date -Is
bash scripts/install.sh --from base_deps
rc=$?
echo "$rc" > "$PROJECT/logs/install-mirror.exit"
git rev-parse HEAD
git submodule status
date -Is
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/install-mirror.sh" > "$PROJECT/logs/install-mirror.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/install-mirror.pid"
ps -p "$(cat "$PROJECT/logs/install-mirror.pid")" -o pid,lstart,args
