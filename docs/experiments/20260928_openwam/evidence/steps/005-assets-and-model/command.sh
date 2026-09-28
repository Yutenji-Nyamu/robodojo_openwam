set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
cat > "$PROJECT/scripts/assets-official.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
cd "$PROJECT/RoboDojo"
date -Is
export HF_REVISION=$(git ls-remote https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo HEAD | cut -f1)
test -n "$HF_REVISION" || exit 2
printf '%s\n' "$HF_REVISION" > "$PROJECT/logs/assets-revision.txt"
bash scripts/init_assets.sh
rc=$?
printf '%s\n' "$rc" > "$PROJECT/logs/assets-official.exit"
date -Is
exit "$rc"
EOF
cat > "$PROJECT/scripts/download-checkpoint.py" <<'PY'
import datetime,hashlib,json,pathlib,subprocess,urllib.request
root=pathlib.Path('/path/to/robodojo-openwam')
repo='OpenWAM/OpenWAM-Alpha-Sim-RoboDojo';rev='2c1302294e3ba8319bbdb2c803b7a27de9292d03'
target=root/'checkpoints/OpenWAM-Alpha-Sim-RoboDojo';target.mkdir(parents=True,exist_ok=True)
meta=json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{repo}/revision/{rev}?blobs=true',timeout=60))
assert meta['sha']==rev
(root/'logs/checkpoint-manifest.json').write_text(json.dumps(meta,indent=2))
for item in meta['siblings']:
    name=item['rfilename'];path=target/name;path.parent.mkdir(parents=True,exist_ok=True)
    print(datetime.datetime.now().isoformat(),name,item.get('size'),flush=True)
    subprocess.run(['curl','-fL','--retry','5','--retry-delay','5','--connect-timeout','30','-C','-','-o',str(path),f'https://huggingface.co/{repo}/resolve/{rev}/{name}?download=true'],check=True)
    if 'size' in item:assert path.stat().st_size==item['size'],name
    if item.get('lfs',{}).get('sha256'):
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(16*1024*1024),b''):h.update(block)
        assert h.hexdigest()==item['lfs']['sha256'],name
        print('SHA256_OK',name,h.hexdigest(),flush=True)
print('CHECKPOINT_COMPLETE',rev,flush=True)
PY
cat > "$PROJECT/scripts/checkpoint-download.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
source /path/to/robodojo-openwam/project-env.sh
python3 -u "$PROJECT/scripts/download-checkpoint.py"
rc=$?
printf '%s\n' "$rc" > "$PROJECT/logs/checkpoint-download.exit"
exit "$rc"
EOF
nohup bash "$PROJECT/scripts/assets-official.sh" > "$PROJECT/logs/assets-official.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/assets-official.pid"
nohup bash "$PROJECT/scripts/checkpoint-download.sh" > "$PROJECT/logs/checkpoint-download.log" 2>&1 < /dev/null &
echo $! > "$PROJECT/logs/checkpoint-download.pid"
cat "$PROJECT/logs/"*.pid
tail -15 "$PROJECT/logs/install-official.log"
