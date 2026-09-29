# FastWAM × RoboDojo：官方材料、权重与部署准备

核对日期：2026-09-29。范围为官方仓库、论文、RoboDojo 文档和官方 Hugging Face 文件元数据；本轮未下载大权重、未安装环境、未修改或占用服务器。

## 结论

**FastWAM 在 RoboDojo 上有官方适配、有专用训练后权重、有公开仿真成绩，可以准备部署。** 适配由 RoboDojo Team 维护在 XPolicyLab；FastWAM 作者原仓库主要介绍 LIBERO/RoboTwin。两条发布链需要合起来看。

关键发现是：Dojo 专用权重放在 **Hugging Face 的 dataset 仓库** `RoboDojo-Benchmark/RoboDojo/ckpt/RoboDojo/FastWAM/`，不在作者的 `yuanty/fastwam` model 仓库。XPolicyLab 的 FastWAM `INSTALLATION.md` 仍举 RoboTwin 权重下载例子，不能把那个例子直接用作 Dojo 基准权重，也不能因此断言 Dojo 未发布权重。[官方 checkpoint 下载说明](https://robodojo-benchmark.com/doc/usage/install-and-download/#7-download-ckpt)、[Dojo 专用文件目录](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/tree/35efbc7dedfdbeeb6e95fb749bd885d73d483e41/ckpt/RoboDojo/FastWAM)、[XPolicyLab 适配说明](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/README.md)。

## 固定版本与文件

| 对象 | 本轮核实版本 / 内容 |
|---|---|
| XPolicyLab 当前 main | `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4`，与当前 OpenWAM 部署锁定版本一致 |
| 作者 FastWAM 当前 main | `7faa71108368fbb3b6885649f112af607427a2d4`；并非本次 XPolicyLab 内嵌代码的版本保证 |
| 官方 Dojo dataset | `35efbc7dedfdbeeb6e95fb749bd885d73d483e41` |
| 专用权重目录 | `ckpt/RoboDojo/FastWAM/RoboDojo-sim-arx_x5-joint-0/` |
| 权重 | `checkpoints/weights/step_020000.pt`，12,041,813,433 B（约 12.04 GB / 11.21 GiB） |
| 权重 LFS SHA256 | `38d38afac480e151c4df079dbf4e869d3b45f3a023f862215a7baaa689af4db0` |
| 配套统计 | `dataset_stats.json`，10,942 B，SHA256 `af119307e4fdd0cc0c052e2017d1aa2afc270a07e7d0dedf1f325b86f3c8c4ef` |
| 发布的 seed 目录 | **只有 `joint-0` 这一套**；未见 FastWAM 的 `joint-1/2` 或真机权重 |

统计文件已读取：action/state 都是 14 维，含左右臂关节与夹爪统计，`global_count=1,859,602` 与 Dojo 官方仿真训练数据帧数一致。这是元数据对齐证据，不等于已在本机验证模型推理。12.04 GB 是任务权重体积，运行还涉及 Wan/T5/VAE/tokenizer 等基础组件，不能当总下载或显存预算。[固定版官方目录/API](https://huggingface.co/api/datasets/RoboDojo-Benchmark/RoboDojo/tree/35efbc7dedfdbeeb6e95fb749bd885d73d483e41/ckpt/RoboDojo/FastWAM/RoboDojo-sim-arx_x5-joint-0?recursive=true)、[基础模型配置](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/FastWAM/configs/model/fastwam.yaml)。

作者 `yuanty/fastwam` 当前 revision `8eaceeb24c3cc92ff2a9c9a9d266a4941b836705` 仅列 LIBERO、LIBERO Optional-IDM、RoboTwin 三套权重及对应统计；**这些不是这里的 Dojo checkpoint**。[作者模型卡与文件](https://huggingface.co/yuanty/fastwam/tree/8eaceeb24c3cc92ff2a9c9a9d266a4941b836705)。

## 官方目前公开成绩

2026-09-29 官网 Simulation 榜单，Fast-WAM 行如下；Score 是阶段得分，SR 是完整成功率，二者不能互换。

| 指标 | 泛化 | 精细 | 长任务 | 记忆 | 开放 | 五维平均 |
|---|---:|---:|---:|---:|---:|---:|
| Score | 2.33 | 1.96 | 9.14 | 3.55 | 0.42 | **3.48** |
| SR | 1.11% | 0.00% | 5.17% | 3.44% | 0.42% | **2.03%** |

来源：[官方当前榜单](https://robodojo-benchmark.com/leaderboard)。主线程同日通过内置浏览器核实此行；当前真机榜的 11 条记录中未列 Fast-WAM，不能据此填一个真机零分。

RoboDojo 论文 v1 的表 1 于 **2026-07-03 冻结**，总分同样为 **3.48 / 2.03%**，但泛化 Score 写 **2.34**，与现网页差 0.01，保留来源差异。论文附录 K 记录该基线从 Wan2.2-TI2V-5B 初始化，batch 256、20K 训练步；与专用 `step_020000.pt` 文件名对应。作者最初 Fast-WAM 论文没有 RoboDojo 结果，Dojo 数字来自 Dojo 团队的基准复现，不是作者原始 LIBERO/RoboTwin 成绩。[RoboDojo 论文表 1 与附录 K](https://arxiv.org/html/2607.04434v1)、[Fast-WAM 原论文](https://arxiv.org/html/2603.16666v1)。

目前公开包只含一套 FastWAM 权重。计划可固定这套 checkpoint 测官方环境 seed 0/1/2，并明确记录这是“同权重、三评测布局集”；不能虚构三套训练 seed 权重，也不把现有包理解为已证实完全重建论文所有训练随机性。

## 代码如何连接

```text
RoboDojo 三路 RGB、机器人状态、任务指令
    → XPolicyLab/policy/FastWAM/model.py
    → 内嵌 FastWAM 的真实 get_model / _infer_action_chunk
    → 关节动作块
    → deploy.py / RoboDojo 客户端执行与评分
```

| 文件 / 环节 | 对部署的实际作用 |
|---|---|
| `install.sh` | 独立 Python 3.10 环境；Torch 2.7.1+cu128、torchvision 0.22.1、FFmpeg 6、OpenCV，再安装内嵌 FastWAM 和 XPolicyLab |
| `setup_eval_policy_server.sh` | 根据 checkpoint 名/路径解析权重和 stats，启动 WebSocket 策略服务；支持显式权重及统计路径覆盖 |
| `model.py` | 接收 head/left-wrist/right-wrist RGB，将各相机规范到 320×240，打包机器人状态；调用真实模型预测后解包动作 |
| 内嵌 `deploy_policy.py` | 按官方方式拼三路图为 384×320 输入、加载模型和归一化、进行动作推理 |
| `deploy.yml` | 默认 bf16、动作预测 horizon 32、执行 24 步后重规划、10 次去噪、`eval_batch:false`、`allow_dummy_policy:false` |
| `deploy.py` | 环境读取观测、请求动作、逐步执行；批量接口存在，但默认关闭 |

此 Dojo 权重用 **`arx_x5 + joint`**。OpenWAM 当前用 `ee`，不能把 OpenWAM 的动作参数及统计搬过来。FastWAM 当前包装直接使用共享 pack/unpack，没有额外的 EE 坐标变换。[适配源码](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/model.py)、[部署参数](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/deploy.yml)、[真实图像和推理实现](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/FastWAM/experiments/robotwin/fastwam_policy/deploy_policy.py)。

`sim_robotwin.yaml` 等名字是此适配复用的内部配置模板；只要权重、stats、14 维关节契约都使用 Dojo 对应项，这个文件名本身不表示正在跑 RoboTwin。固定版 action scheduler 的默认 infer shift 是 5.0；保留 XPolicyLab 内嵌版，避免直接换作者新 main 导致默认值变化。[固定模型配置](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/FastWAM/configs/model/fastwam.yaml)。

## 准备按官方流程部署

本节是待执行方案，不是已经完成。复用我们已有的 RoboDojo 仿真环境、资产和深圳 2 兼容启动层，新建 FastWAM 策略环境、独立模型目录、端口和结果 run-id；不修改正在运行的 OpenWAM 批次源码或配置。

1. 在独立模型准备目录固定上述 XPolicyLab 版本，按 `policy/FastWAM/install.sh` 安装策略环境。官方 `INSTALLATION.md` 还介绍 ActionDiT 预处理；现有推理 `sim_robotwin.yaml` 已设 `skip_dit_load_from_pretrain:true` 与 `action_dit_pretrained_path:null`，具体加载按这套固定配置检查，训练初始化需求另计。
2. 用 **RoboDojo 官方下载器**取 FastWAM，而非复制其模型安装文档中的 RoboTwin 下载例子：

   ```bash
   # 在准备使用的 RoboDojo checkout 根目录；仅示意，尚未执行。
   bash scripts/RoboDojo/download_ckpt.sh huggingface FastWAM
   ```

   下载器会把专用目录链接至 `XPolicyLab/policy/FastWAM/checkpoints/`。保存实际 repository revision，核对上述两个文件的大小/SHA256，避免把 LFS 指针当权重。若走 ModelScope，官方同一脚本支持 `modelscope FastWAM`，仍需核实该源对应文件。
3. 首次推理显式选完整 checkpoint 目录名，使用同一已知仿真任务：

   ```bash
   bash scripts/robodojo.sh eval \
     --policy-dir XPolicyLab/policy/FastWAM \
     --task stack_bowls \
     --ckpt RoboDojo-sim-arx_x5-joint-0 \
     --env-cfg arx_x5 --action-type joint --seed 0 --eval-num 1 \
     --policy-env <独立FastWAM环境> --eval-env <现有Dojo环境> \
     --policy-gpu <当时可用卡> --env-gpu <当时可用卡>
   ```

   调用我们已验证的项目兼容 wrapper，GPU/端口按启动时实际资源填写。成功加载、真实动作、正常写结果，与“机器人该回合做成功”分别记录；一个失败回合本身不是环境故障。
4. 之后评测环境 seed 1/2 时，**`--ckpt` 仍固定 `RoboDojo-sim-arx_x5-joint-0`**。不要用短名 `sim` 导致脚本自动寻找尚不存在的 `joint-1/2`。仿真预算沿用 54 配置 × 3 seed、native 25/50；不要假定“每 seed 一套权重”是必需条件。
5. 并行单独测 FastWAM 的实际吞吐。当前 `get_action_batch` 对环境列表逐个调用 `_infer_actions`，不是 OpenWAM 的一次真正张量批推理；因此“每卡两 worker × 每 worker 四环境”只能作待测候选，不能直接引用 OpenWAM 的吞吐/显存。可沿用环境进程并发框架，模型侧参数保持 FastWAM 默认。

官方依据：[安装脚本](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/install.sh)、[额外安装说明](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/INSTALLATION.md)、[Dojo checkpoint 下载器](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/RoboDojo/download_ckpt.sh)、[策略服务 checkpoint 解析](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/setup_eval_policy_server.sh)。

## 如果以后要训练

现有接口支持 Dojo 数据的离线监督训练：官方 LeRobot v2.1 导出 → 对应 dataset stats → T5 文本缓存 → ActionDiT 初始化 → `train.sh` 多卡训练。没有顶层 `process_data.sh`，这些准备由官方转换器和内嵌 FastWAM 工具承担。与本轮“直接部署已发布权重推理”分开安排。

当前 wrapper 默认每进程 batch 8、梯度累积 1、16 epochs；**这不自动等于论文的全局 batch 256 / 20K steps**。将来要重训复现时必须按论文和实际 GPU 数明确总 batch、步数及保存点，不能仅运行 README 示例就声称同配方复现。[训练脚本](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/FastWAM/train.sh)。

## 本轮完成与证据

- 完成官方适配、基础配置、安装/训练/服务脚本、专用权重元数据与小型统计文件核对；没有加载或反序列化 12 GB checkpoint。
- 确认可直接准备已有模型的推理，暂不需要先训练 Dojo FastWAM。
- 尚待本机验证：依赖安装、基础组件下载/缓存、模型真实加载、首回合、FastWAM 专属并行吞吐、全量指标复现。
- 本轮轻量源码与 metadata 已独立归档；公开复核可直接使用本文固定 revision 的官方文件和 API 链接。
