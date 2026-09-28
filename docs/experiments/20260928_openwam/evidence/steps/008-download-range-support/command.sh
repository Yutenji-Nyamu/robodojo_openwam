set -eu
python3 - <<'PY'
import time,urllib.request
url='https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo/resolve/2c1302294e3ba8319bbdb2c803b7a27de9292d03/checkpoint_step_60000.safetensors?download=true'
t=time.time()
req=urllib.request.Request(url,headers={'Range':'bytes=1000000000-1001048575'})
with urllib.request.urlopen(req,timeout=30) as r:
    print('range',r.status,r.headers.get('Content-Range'),r.headers.get('Content-Length'))
    data=r.read(1048576);print('read',len(data),'seconds',time.time()-t)
PY
