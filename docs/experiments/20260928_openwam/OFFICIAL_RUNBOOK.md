> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# OpenWAM + RoboDojo 官方实施流程

更新日期：2026-09-28。**用户已于 2026-09-28 授权实施，当前状态：深圳 2 官方 OpenWAM + RoboDojo 推理实施中。** 当前路线为官方安装 → 准备仿真资产与专用 checkpoint → 直接运行真实模型的官方单任务评测，遇到具体问题再诊断。具体执行和结果以 [RUN_LOG.md](RUN_LOG.md)、[EXECUTION_LOG.md](EXECUTION_LOG.md) 为准；本文命令模板不代表已经执行或通过。

本阶段不把独立 RGB、dummy 或连续 reset 检查列为前置关卡，不扩并发、不启动 RL。下方保留的诊断、分离部署、完整 benchmark、SFT/RL 内容供按需参考；π0.5 过桥也不是本轮前置。

## 0. 先确定实际要复现的链路

```text
RoboDojo / Isaac Sim：任务、机器人、三相机、末端控制、成功判据
       ⇅ XPolicyLab 观测/动作与 WebSocket 协议
XPolicyLab/policy/OpenWAM：批量适配、坐标转换、checkpoint 加载
       ⇅ 进程内调用 vendored OpenWAM
OpenWAM-Alpha-Sim-RoboDojo：Wan + ActionDiT + VAE + 文本编码器
```

官方 OpenWAM [RoboDojo 入口](https://github.com/OpenWAM-Official/OpenWAM/blob/main/benchmarks/robodojo/README.md) 把训练留在模型仓、评估交给 XPolicyLab。**XPolicyLab 的 policy server 自己加载 OpenWAM 模型**，不需要另外启动一个 OpenWAM 官方 JSON/WebSocket server 再层层转发。保留其 vendored 实现；它补了 `generate_batch`，不能随意用任意旧版 upstream 路径替换。[适配 README](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/README.md)、[model.py](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/model.py)

结果按服务通信、真实 checkpoint 的完整任务闭环、标准协议成功率分别记录。当前直接运行真实模型评测，从它的日志、图像、动作和结果定位问题；dummy仅作为遇到协议问题时的诊断手段。一次失败但完整结束的 episode 可以证明工程闭环执行到了终点，不能称任务成功。

## 1. 已核实的模型文件与空间

专用仓库：[OpenWAM/OpenWAM-Alpha-Sim-RoboDojo](https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo)。本轮 API 核实为 public、ungated，revision：

`2c1302294e3ba8319bbdb2c803b7a27de9292d03`

| 文件/组 | 实际文件大小或内容 | 用途 |
|---|---:|---|
| `checkpoint_step_60000.safetensors` | 24,813,767,464 bytes | 完整模型权重 |
| `config.yaml` | 3,395 bytes | Dual joint-self-attn、Wan5B、80D、Dojo arx_x5 eef、components 构造信息 |
| `normalization_stats.npy` | 2,190 bytes | 与此模型配套的状态/动作统计，不能借用别的模型统计 |
| `tokenizer/google/umt5-xxl/` | 4 个文件，约 21.45 MB | tokenizer.json、spiece.model、special tokens、tokenizer config |
| 全仓文件合计 | **24,835,230,031 bytes，约 24.835 GB / 23.13 GiB** | 不含 Python 环境、仿真资产、缓存和输出 |

权重 LFS SHA256：`78ca4ef5d2f6c8fa877bcae8b40c36b3d8700547fd5a708b472c4564e5f40abb`。stats SHA256：`48bc266e0390f341c86dc3712501788c2bfdb75e44f005e41cc3e5820ace36a3`。[实际文件元数据 API](https://huggingface.co/api/models/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo?blobs=true)

**已检查实际权重头部，不只看 README。** HTTP Range 读取的 safetensors header 为 259,272 bytes，共 2,089 个 tensors；包含 `video_backbone.dit` 825 个、`video_backbone.text_encoder` 242 个、`video_backbone.vae` 196 个，以及 ActionDiT 和 proprio encoder。发布 config 带 `components` 与相对 tokenizer 路径；当前 checkpoint-first loader 会据此构造空模型再加载完整权重。config 中 `/path/to/Wan2.2-TI2V-5B` 是训练来源占位，**不表示发布推理还要另下一个 Wan 基础包**。[loader](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/OpenWAM/openwam/deploy/model_loader.py)、[pipeline builder](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/OpenWAM/openwam/model/video_backbone/wan/pipeline_builder.py)

存储准备按三部分计数：模型 24.835 GB；本轮官方 Assets 清单为 15,365 文件、41,269,513,111 bytes（38.435 GiB）；Python/Isaac 环境、HF/LFS cache、shader cache、日志和录像另计。首次 `stack_bowls` seed0 因网络慢，按固定官方清单只准备该任务284文件（573,739,871 bytes），含全部55布局；同源缓存复用后用官方Git LFS补差，逐文件核hash。完整基准资产尚未安装。不要把模型文件大小当成峰值显存。

纯推理不需要下载训练集。若以后做 SFT，官网给出的数据估计为仿真 HDF5 523 GB、LeRobot v3 120 GB、v2 64 GB；depth 约 4.5 TB；真实数据 273 GB。OpenWAM 本入口直接消费原生 HDF5，LeRobot 两个版本无需同时下载。这些是文档估计，不是本轮全量文件实测。[安装下载文档](https://robodojo-benchmark.com/doc/usage/install-and-download/)

## 2. 深圳 2 的起点：按官方入口直接运行真实评测

本轮其他并行核查已在深圳 1 `COLLABORATOR` 的已有运行中找到 H100 本机 RoboDojo 闭环证据：Dojo `ee67a146`、XPolicyLab `7e0fd28`、IsaacLab `afca7b09`、Isaac Sim 5.1、Python 3.11、PyTorch 2.7/cu128、driver 575.57.08；Vulkan 日志标出 H100 Active Yes。`build_tower` 三种真实 StarVLA 的单 episode 结果分别为 OFT success 0、score 30；GR00T success 0、score 10；QwenPI_v3 success 1/1、score 100。**QwenPI_v3 不是 π0.5。** 三路视频为 640×480、25fps，抽查 head 帧可见桌面、机器人、积木。它证明现场有可借鉴的路径，不能据此保证深圳 2 当前环境或渲染画质相同。[详细现场证据](./H100_COMPATIBILITY.md)

执行顺序是：刷新深圳 2 环境/磁盘/GPU占用 → 在独立项目环境中按官方流程安装、准备资产和权重 → 运行官方真实模型单任务评测 → 根据实际错误或输出诊断。深圳 1 的版本和启动 helper 是遇到相同问题时的参考，不先把它们整套移植，也不预设必须换 RTX。

真实评测产生结果后，一并检查三路图像、动作、环境步数、原生评分和退出日志。若出现黑帧、画面不更新或控制异常，再针对相关层做RGB/控制诊断；不另设“先通过相机预检才能加载真实模型”的步骤。

现场 helper 使用独立 sim 环境中的 libglu 9.0.3，并把该环境 `lib` 加入进程 `LD_LIBRARY_PATH`；单 sim GPU，关闭 multiGpu enabled/autoEnable、限制 maxGpuCount=1，`num_envs=1`。核查未发现 IsaacLab/XPolicyLab 的 tracked renderer patch；Dojo tracked 变化是 XPolicyLab gitlink。深圳 2 driver 为 595.71.05，与历史现场版本不同。只有遇到对应错误时，才对照这些依赖与参数做必要处理。动态库或GPU选择处理不等于给H100补上RT Core，也没有证据说明其RTX/GI功能与其他显卡等价。若真实评测被相机问题阻断，再考虑官方 split server/client 路线定位渲染与推理。

还有两个旧版启动细节要检查：`run_hf_robodojo_env_client.sh` 在仿真子进程取消 `CUDA_VISIBLE_DEVICES`，并同时传 `--device cuda:<物理ID>` 与 `--device_id <物理ID>`，避免 CUDA/Vulkan 编号空间混淆；Kit 使用 `--enable_cameras --headless`。`run_robodojo_main.py` 只给 argparse 设置 `allow_abbrev=False`，防止 `--device` 被预解析成 `--device_id`，未修改渲染器。**这些是 StarVLA 旧版已跑通参考：先核当前 OpenWAM/Dojo 官方入口是否已处理，再决定最小必要改动，不能把整套 StarVLA helper 原样套上 OpenWAM。**

## 3. 安装与资产：两个独立环境，锁定源码

阶段目的：建立 simulator 环境与 policy 环境，并记录 Dojo/XPolicyLab/vendored OpenWAM 的真实版本。先确认现成环境是否可复用，不更新共享系统、驱动或无关 conda 环境。

以下是实施命令模板，`<...>` 按本次实际路径和资源填写，执行回执另记。官网推荐 Ubuntu 22.04、Isaac Sim 5.1；先使用官方安装流程，遇到具体兼容问题再参考既有现场依赖组合，并记录最终 revision。当前官网与深圳 1 旧 checkout 不应混成“同一个版本”。

```bash
# 模板：在独立项目目录准备官方源码，记录 git HEAD/submodule 状态
git clone https://github.com/RoboDojo-Benchmark/RoboDojo.git <DOJO_ROOT>
cd <DOJO_ROOT>
bash scripts/install.sh -i
conda activate RoboDojo

# 模板：当前固定版本从 Hugging Face 下载仿真 Assets，并修正本机资产绝对路径
bash scripts/init_assets.sh
python utils/update_embodiment_config_path.py
```

安装脚本分 system、conda、basedeps、submodules、isaacsim、isaaclab、curobo 阶段；失败要从对应日志定位，再按官方 `--from` 指定步骤继续，避免盲目全重装。IsaacLab editable/扩展路径与 URDF 内绝对路径是不同问题。[官方安装指南](https://robodojo-benchmark.com/doc/usage/install-and-download/)

```bash
# 模板：仅在独立 policy 环境中使用；环境名称按本次项目清单填写
conda create -n <POLICY_ENV> python=3.10
conda activate <POLICY_ENV>
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 \
  --index-url https://download.pytorch.org/whl/cu128
cd <DOJO_ROOT>/XPolicyLab/policy/OpenWAM
bash install.sh
```

OpenWAM 官方要求 Python ≥3.10；上面 3.10 是 adapter README 模板，现场若复用已验证 Python 3.11，需固定并记录，不要混装二者。`install.sh` editable 安装 XPolicyLab 和 vendored OpenWAM；RoboDojo Wan checkpoint 不需要 Cosmos 额外依赖。[模型安装步骤](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/README.md)

Docker 是可选替代安装路线，不与 native 同时必做。官方镜像不含 Assets、各 policy 的依赖或 checkpoint；文档建议镜像构建与缓存至少留 300 GB 空间。选择 Docker 时还要处理资产绝对路径挂载；不能把“镜像可运行”理解为“模型和任务齐备”。

## 4. 下载并核对唯一 checkpoint

阶段目的：把已经发布、明确属于 RoboDojo simulation 的 60k checkpoint 固定下来，不混用 RoboTwin 或预训练 foundation 包。

官方交互下载入口：

```bash
# 模板：在交互选项中选 RoboDojo simulation 的发布 checkpoint
cd <DOJO_ROOT>/XPolicyLab/policy/OpenWAM/OpenWAM
python scripts/download_assets/download_openwam_checkpoints.py
```

若要严格锁定本轮 revision，可用同一 HF 包的固定版本下载模板：

```python
# 模板：需要 policy 环境已有 huggingface_hub
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="OpenWAM/OpenWAM-Alpha-Sim-RoboDojo",
    revision="2c1302294e3ba8319bbdb2c803b7a27de9292d03",
    local_dir="<CHECKPOINT_DIR>",
)
```

验收：上述全部文件存在；文件大小、SHA256、revision 与记录一致；tokenizer 相对目录正确；没有把 Git LFS pointer 当权重。确认 loader 走 `components` 自包含路径、没有外部 Wan 下载；检查模型参数加载报告和 stats 使用路径。下载日志与模型加载日志分开保存，网络完成不代表模型能运行。

用 `OPENWAM_CKPT_DIR=<CHECKPOINT_DIR>` 或 `--ckpt <绝对目录>` 明确指定路径；不必为了目录名再复制一份 24.8GB。可用 symlink 但应先检查目标，避免覆盖已有别名。[checkpoint 解析脚本](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/setup_eval_policy_server.sh)

## 5. 直接运行官方真实模型单任务评测

### 5.1 当前执行入口

```bash
# 模板：按本次实际路径、任务、seed与卡号填写，直接运行真实checkpoint
cd <DOJO_ROOT>
bash scripts/robodojo.sh eval \
  --policy-dir XPolicyLab/policy/OpenWAM \
  --task <TASK> --ckpt <CHECKPOINT_DIR> --policy-env <POLICY_ENV> \
  --env-cfg arx_x5 --action-type ee --seed <SEED> --eval-num 1 \
  --policy-gpu <POLICY_GPU> --env-gpu <ENV_GPU>
```

按本次启动记录确定任务和seed；模型使用 `allow_dummy_policy:false`，日志应显示实际 checkpoint 路径和动作生成。官网的 `stack_bowls` 是例子，不自动改变已有实验任务。[quick evaluation](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)

### 5.2 按需诊断参考：doctor、dry-run与无simulator接口

这些工具用于出现安装、参数或服务问题后缩小范围，不构成当前真实评测的必经关卡。`doctor` 的轻量用法为 `bash scripts/robodojo.sh doctor --skip-isaac --skip-conda --skip-policy`；需核对命令展开时，可给5.1的评测命令临时加 `--dry-run`。两者都不能证明真实模型/Isaac闭环已经通过。

```bash
# 按需诊断模板：只测 RPC 和动作格式；dummy跳过权重，不能计为模型结果
cd <DOJO_ROOT>/XPolicyLab/policy/OpenWAM
EVAL_ENV_TYPE=debug OPENWAM_ALLOW_DUMMY_POLICY=true \
  bash eval.sh RoboDojo <TASK> dummy arx_x5 ee <SEED> \
  <POLICY_GPU> <ENV_GPU> <POLICY_ENV> <SIM_ENV>
```

如果具体错误需要区分RPC与模型加载，可按上例使用dummy；保留 `EVAL_ENV_TYPE=debug`、取消dummy并指定真实checkpoint，可单独定位模型加载/推理问题。这些诊断结果均不能替代真实相机和环境控制结果。

### 5.3 真实episode的契约与结果记录

从5.1的实际评测记录核对以下契约和产物，遇到具体异常再定位相应层；无需先单跑RGB、dummy或连续reset。

这里的动作契约是 **绝对末端 `ee`**，不是 π0.5 bridge 的 14 维关节。模型需要 head/left-wrist/right-wrist 三路 RGB、语言和当前末端状态，adapter 负责基座坐标转换、旋转格式、归一化和夹爪。输出内部 80 维有效位置经反转换成为 RoboDojo 原生动作。维度对上不足以证明坐标、夹爪方向或动作语义正确。[数据/动作适配](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/model.py)

当前 `deploy.yml` 有 `eval_batch:true`；`deploy.py` 的 `eval_one_episode_batch` 获取 active env，调用 `get_action_batch`，模型用一次 `engine.generate_batch`，已完成环境从 active list 删除。仿真 `num_envs` 由 Dojo 配置决定；不要把 OpenWAM YAML 注释的 10 当成实际值，也不要为首轮闭环扩大批量。[批处理循环](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/deploy.py)

验收最小集合：真实权重加载成功；三路图像有效；动作数值有限且坐标/夹爪合理；环境累计步数推进；原生 success/score、episode 终止、录像和 `_result.json` 一致；policy 与 simulator 正常退出；GPU/PID 占用返回基线。失败时保存其完整结果，不用重跑到一次成功来替换首次失败。

## 6. 同机不满足时，再用官方分离部署

这条路用于拆分模型 GPU 与模拟器，不意味着深圳 2 先验无法渲染。policy 和 env 两端固定同一 task、env config、seed、action type；远端 client 填 policy 的真实可达地址，`localhost` 仅适合同机。

```bash
# 未执行：policy 主机
bash scripts/robodojo.sh server \
  --policy-dir XPolicyLab/policy/OpenWAM --task <TASK> \
  --ckpt <CHECKPOINT_DIR> --policy-env <POLICY_ENV> \
  --env-cfg arx_x5 --action-type ee --seed <SEED> \
  --policy-gpu <POLICY_GPU> --policy-port <PORT> --bind-host 0.0.0.0

# 未执行：simulator 主机
bash scripts/robodojo.sh client \
  --policy-name OpenWAM --task <TASK> --ckpt <CHECKPOINT_LABEL> \
  --policy-host <POLICY_IP> --policy-port <PORT> \
  --env-cfg arx_x5 --action-type ee --seed <SEED> \
  --env-gpu <ENV_GPU> --eval-num 1
```

client 的 checkpoint label 用于结果标识，真实权重加载在 server；两端都需满足各自运行依赖。端口选择与访问范围在启动清单里写明；不用修改共享防火墙或停止不相关服务来试错。服务连通后先分清网络耗时、预处理、GPU 推理、模拟器推进，不用总 episode 时间直接冒充模型延迟。[分离部署文档](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)

## 7. 结果、日志与失败定位

每次正式动作前形成一页启动清单：源码 commit/submodule、补丁、Python/PyTorch/CUDA/Isaac/驱动、checkpoint revision/hash、资产版本、完整命令、最终解析 YAML、task/seed/layout、动作模式/chunk/replan、env 数、卡号与端口、输出目录、停止条件。共享服务器占用以启动前刷新为准。

| 记录层 | 保存内容 | 建议位置 |
|---|---|---|
| 粗粒度 | 目的、实际做了什么、关键结果、问题与处理、下一步 | `docs/robodojo-openwam/RUN_LOG.md`（已记录准备阶段，执行时继续追加） |
| 细粒度 | UTC/北京时间、命令、cwd、退出码、开始/结束、配置快照、stdout/stderr、PID/卡号/端口、产物哈希 | 每次独立的 `runs/<run_id>/`，大文件放数据盘 |
| 模型加载 | checkpoint 路径和 revision、组件加载、stats、tokenizer、真实/dummy、显存峰值 | `policy.log` + `resolved_policy.yaml` |
| 环境与行为 | reset、相机、实际 action、step、reward/success、termination/truncation、录像 | `env.log` + 原生结果/录像 |

不要在日志保存账号密码或令牌。RoboDojo 原生结果通常位于 `eval_result/RoboDojo/<task>/<policy>/<env_cfg>/<seed>_<additional_info>/<run_id>/`；保留 run_id、`_result.json`、episode 视频和 `_stream/`。`smoke_results/` 是批 smoke 汇总；`_summary.md` 可能混入历史结果，核验时先绑定本次 run_id。[评估输出与汇总](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)

| 故障表现 | 先检查哪一层 | 不应据此下的结论 |
|---|---|---|
| 找不到 Wan 占位目录 | checkout 是否有 checkpoint-first loader；config components/tokenizer 是否完整 | 不能立即认定需要再下基础 Wan |
| tokenizer/stats/参数缺失 | HF revision、下载完整性、路径解析、软件版本 | 不等同于 GPU 不够 |
| 服务在线但动作不动 | dummy 标志、真实 checkpoint、夹爪/坐标/输入状态、eval loop | 不等同于模型本身任务能力为零 |
| 颜色异常 | HDF5 编码、decoder、在线 RGB 契约 | 不应盲目对全部 RGB 做通道反转 |
| 相机黑帧/缺资产 | 已验证启动 helper、Isaac 扩展、资产路径和相机输出 | 不等同于模型 checkpoint 坏了 |
| OOM | 完整模型显存、active batch、图像和视频长度、同时占用 | 24.8GB 权重不等于 24.8GB 峰值显存 |
| 结果有分数但 success=false | 官方 predicate、任务进度计分、终止条件 | score 不能改称任务成功 |
| 退出卡住 | server PID、client close、Isaac stage/context close 日志 | 接口 unit tests 通过不能排除真实生命周期缺陷 |

**RGB 编码 issue #116 已关闭，当前 vendored 代码也已修复。** 原问题是旧 HDF5 的 OpenCV JPEG 编码与 PIL 解码路径造成通道语义不一致；当前 `_decode_jpeg` 调用统一 `XPolicyLab.utils.process_data.decode_image_bit`，再转成 PIL。不能继续列成“现存未修复 blocker”，也没有证据要求把发布模型重训一遍。以后训练或重用旧数据时记录 decoder revision、样例 HDF5 的解码结果；在线 observation 已声明 RGB，不额外交换通道。[issue #116](https://github.com/XPolicyLab/XPolicyLab/issues/116)、[当前 decoder](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/OpenWAM/openwam/dataloader/robodojo.py)

## 8. 更大范围评估、SFT 和 RL 是三个后续决策

标准 RoboDojo 仿真评估包含 42 个基础任务、加上 generalization 的随机化配置，共 54 runnable configs；标准 seeds 为 0/1/2，`--eval-num native` 使用各任务原生次数。首轮单 episode 并非整套性能复现，完整 benchmark 的任务数、GPU 并发、输出录像和预算以后单列，不默认启动。[标准评估协议](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)

若以后 SFT：采用原生 HDF5 `<dataset_root>/<task>/<embodiment>/data/episode_*.hdf5`，`OPENWAM_DATASET_DIR` 指向它，用 `OPENWAM_FINETUNE_CKPT_PATH` warm-start；`train.sh` 包装官方 `dataloader=robodojo`。不为了现成推理先做数据采集、LeRobot 转换、重新微调。全参训练的 optimizer/梯度/激活开销与推理不同，不能按权重大小承诺 H100 卡数。[训练说明](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/README.md)

若以后接 RLinf，需要两个独立接口都成立：

1. **环境侧**：reset/seed、三相机与状态、绝对末端动作、逐步 reward/success、terminated/truncated、final observation、batch reset、close，接到 RLinf EnvWorker。Dojo eval wrapper 能循环动作不等于所有在线 RL hook 完整。
2. **模型侧**：真实可训练 forward 与状态加载，rollout 所需去噪轨迹/概率定义、算法所需 value 等量、动作块与动作级奖励对齐、梯度和 actor 参数同步。推理 WebSocket 本身不提供这些。采用何种 flow-policy RL 形式是方法选择，不能偷偷把当前控制算法换掉。

RLinf [#1597](https://github.com/RLinf/RLinf/pull/1597) 当前 open，只提供 OpenWAM SFT/评估，并明确拒绝 RL 配置；它的 LIBERO/RoboTwin 配方也不能直接叫 OpenWAM+RoboDojo RL。RoboDojo 环境 [#1606](https://github.com/RLinf/RLinf/pull/1606) 与 RPent [#96](https://github.com/RLinf/RPent/pull/96) 是可借鉴的未合并桥；最新公开 π0.5 单次完整 rollout 仍 success=false、reward=0，退出还需处理，不能称在线 RL 已验收。详见 [接入证据与边界](./RLINF_RPENT_REUSE.md)。

**是否先 π0.5 过桥：按目标选。** 如果先回答“OpenWAM 在 Dojo 能否按官方权重正常推理”，直接走本文链路最短；如果先回答“RLinf 的 Dojo 环境控制和奖励有没有接对”，π0.5 可以隔离 WAM 模型侧开发。它不自动解决 OpenWAM 的末端/关节转换、flow 概率或训练显存，因此只是条件性工程选项，不是当前新增必做路线。

## 资料核查阶段保存的证据

资料原始快照位于 `<LOCAL_ARCHIVE>`：`paper.pdf`/`paper.txt`、`source-manifest.json`、`openwam-hf-metadata.json`、`robodojo-release-config.yaml`、`robodojo-safetensors-header.json`、`issue-116.html`、官方与 XPolicyLab 源码。该资料核查阶段只读取文档、源码、元数据和权重头部；后续实际下载、安装和评测的进度与结果另记执行日志，不以模板内容代替执行回执。
