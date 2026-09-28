set -euo pipefail
source /path/to/robodojo-openwam/project-env.sh
"$PROJECT/envs/openwam/bin/python" -m pip check
"$PROJECT/envs/openwam/bin/python" - <<'PY'
import torch,numpy,transformers,diffusers,huggingface_hub
print(dict(torch=torch.__version__,numpy=numpy.__version__,transformers=transformers.__version__,diffusers=diffusers.__version__,huggingface_hub=huggingface_hub.__version__,hub_path=huggingface_hub.__file__))
PY
