#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=Path('/path/to/robodojo-openwam')
matches=list((p/'RoboDojo/eval_result').rglob('sz2_openwam_stack_bowls_s0_20260928_1944'))
assert len(matches)==1
dest=p/'runs/success-preview'; dest.mkdir(exist_ok=False)
data=[]
for video in sorted(matches[0].glob('*.mp4')):
    camera=video.name.split('_cam_')[1].split('_success')[0]
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    for sec in ([0,6.4,12.7] if camera=='head' else [0,12.7]):
        subprocess.run(['ffmpeg','-v','error','-ss',str(sec),'-i',str(video),'-frames:v','1','-threads','1',str(dest/f'{camera}_{sec}.png')],check=True)
    data.append({'camera':camera,'metadata':meta,'source':str(video)})
(dest/'media-metadata.json').write_text(json.dumps(data,indent=2))
print(json.dumps({'output':str(dest),'files':len(list(dest.iterdir())),'videos':[{'camera':x['camera'],'frames':x['metadata']['streams'][0].get('nb_frames'),'duration':x['metadata']['format']['duration']} for x in data]}))
PY
