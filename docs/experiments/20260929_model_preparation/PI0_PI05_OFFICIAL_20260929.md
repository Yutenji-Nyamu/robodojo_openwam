# π0 / π0.5 × RoboDojo 官方部署准备 · 2026-09-29

本轮只读官方网页、源码与 Hugging Face 文件元数据，并读取六份约 3.4 KB 的归一化 JSON；未下载大权重、未安装环境、未改服务器。以下是待执行方案，不是两模型已在深圳跑通的记录。当前 OpenWAM 正式评测与部署版本保持原状。

## 结论与来源版本

**两者都有 RoboDojo 团队维护的适配、仿真专用权重、数据转换和训练脚本，可沿已有 RoboDojo 仿真接入。** 不需要先自行训练，也不需要先接 RLinf。模型本体来自 Physical Intelligence OpenPI，Dojo 集成由 XPolicyLab 提供。

- XPolicyLab 当前 `main` 经 GitHub API 核验为 `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4`，恰与我们已安装子模块版本相同；无需为寻找适配更新运行中的仓库。
- 官方权重是 **dataset 仓库** `RoboDojo-Benchmark/RoboDojo`，本轮 revision 为 `35efbc7dedfdbeeb6e95fb749bd885d73d483e41`。
- [π0 官方适配 README](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_0/README.md)、[π0.5 README](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/README.md)、[OpenPI 上游](https://github.com/Physical-Intelligence/openpi)、[官方权重下载器](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/main/scripts/RoboDojo/download_ckpt.sh)。

## 两个适配提供了什么

| 项目 | π0 | π0.5 |
|---|---|---|
| 目录 | `XPolicyLab/policy/Pi_0/` | `XPolicyLab/policy/Pi_05/` |
| 模型实现 | 目录内 `openpi/`，JAX / Orbax checkpoint | 同样为自己的 vendored `openpi/` |
| 安装 | `bash install.sh`，创建 uv `.venv` | 同左 |
| 数据处理 | `process_data.sh`，HDF5 → LeRobot | 同左 |
| 训练 | `train.sh`，Dojo 全参训练配置 | 同左 |
| 推理 | `eval.sh`，或 server/client 分离入口 | 同左 |
| 默认控制 | `joint` | `joint` |
| 默认模型动作块 | 50 步，flow 10 步采样 | 50 步，flow 10 步采样 |
| 默认仿真并行开关 | `eval_batch: false`，Dojo 强制单环境 | `eval_batch: true`，可并行仿真 |
| 当前模型批处理实现 | 批接口存在，但默认不启用 | 批接口内部逐环境调用 `policy.infer` |

最后一行很关键：**π0.5 的多环境仿真已经接好，但当前模型端不是一次 JAX 批量前向。** `model.py::get_action_batch` 有 Python 循环逐环境推理；OpenWAM 使用 `generate_batch`。因此我们的 OpenWAM「每卡双 worker × 每 worker 四环境」不能直接当成 π 系列已验证的最优配置。π0 如保持官方默认，则每个 worker 是一个环境；需要更多独立 worker 才增加并发。

依据：[π0 配置](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_0/deploy.yml)、[π0.5 配置](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/deploy.yml)、[π0.5 推理适配](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/model.py)、[π0.5 仿真循环](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/deploy.py)、[官方并行开关说明](https://robodojo-benchmark.com/doc/usage/quick-evaluation/#split-eval)。

## 权重确实公开了哪些文件

统一前缀为 `ckpt/RoboDojo/<POLICY>/`。以下大小来自该固定 revision 的树 API，不是已下载后的实测大小；GiB 按 2³⁰ 字节计算。

| 模型 / 训练 seed | 发布子目录 | params 大小 | 额外 train_state |
|---|---|---:|---:|
| π0 / 0 | `RoboDojo-sim-arx_x5-joint-0/60000/` | 11.189 GiB | 28.940 GiB |
| π0 / 1 | `RoboDojo-sim-arx_x5-joint-1/59999/` | 11.190 GiB | 本目录未提供 |
| π0 / 2 | `RoboDojo-sim-arx_x5-joint-2/59999/` | 11.190 GiB | 本目录未提供 |
| π0.5 / 0 | `RoboDojo-sim-arx_x5-joint-0/59999/` | 11.587 GiB | 30.048 GiB |
| π0.5 / 1 | `RoboDojo-sim-arx_x5-joint-1/59999/` | 11.586 GiB | 本目录未提供 |
| π0.5 / 2 | `RoboDojo-sim-arx_x5-joint-2/59999/` | 11.587 GiB | 本目录未提供 |

各目录都有 `_CHECKPOINT_METADATA`、完整 `params/` 的 Orbax/OCDBT 分片及 `assets/arx_x5_sim/norm_stats.json`。现成推理读取 `params` 和 normalization assets；不是任意拿一个 `ocdbt` 文件就能推理。下载器默认取模型目录全部内容，所以 π0 合计约 **62.51 GiB**、π0.5 约 **64.81 GiB**；两者三份推理参数本身合计约 **68.33 GiB**，其余主要是 seed 0 训练状态。

六份 norm JSON 本轮均实际读出，SHA256 都为 `ad7dea3e3d2bcdb348945fe03422ab1adccd03baf67318b1a1d153dfe8694db5`，包含 state/actions 各14维的 mean/std/q01/q99。这确认附带归一化文件存在且一致，不等于已经验证权重加载或模型表现。

官方证据：[π0 文件树](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/tree/35efbc7dedfdbeeb6e95fb749bd885d73d483e41/ckpt/RoboDojo/Pi_0)、[π0.5 文件树](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/tree/35efbc7dedfdbeeb6e95fb749bd885d73d483e41/ckpt/RoboDojo/Pi_05)。公开的个人 `cjgogo/RoboDojo-pi05-checkpoints` 是另一套实验发布，不替代这里的官方完整基准权重。

## 输入、动作和归一化与 OpenWAM 有何不同

- 相机仍然是头部、左腕、右腕三路 RGB；π 系列映射为 `cam_high / cam_left_wrist / cam_right_wrist`，并附当前状态和语言指令。
- 官方 XPolicyLab 当前将双臂关节打包为 **左臂6维、左夹爪1维、右臂6维、右夹爪1维**。这与此前 RLinf 社区 bridge 的「两臂关节12维后接两夹爪」不是同一排列，不能照搬 bridge 的 delta mask。
- π 系列外部输出绝对关节动作；OpenPI 内部将臂关节变为相对当前状态的 delta，夹爪仍为绝对值，输出时再还原。此处 mask 为 `(6,-1,6,-1)`，`adapt_to_pi=False`。
- 模型内部 pad 到32维、输出取前14维，再解包给 Dojo。OpenWAM 是末端 `ee` 路径，不能仅换目录名而保留 `--action-type ee`。
- π0 使用 mean/std；π0.5 使用分位数归一化。均由绑定的训练 config 和 checkpoint assets 自动处理，不手工套我们 RoboTwin 的 norm 文件。

依据：[pack/unpack](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/utils/process_data.py)、[训练数据变换](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/src/openpi/training/config.py)、[Aloha 输入输出](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/src/openpi/policies/aloha_policy.py)、[模型默认块长](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/src/openpi/models/pi0_config.py)。

## 环境与尚未实测的地方

保持已有 Isaac Sim / RoboDojo 仿真环境及本机图形兼容设置，模型各用官方独立 uv 环境。当前两适配要求 Python `>=3.11,<3.14`、JAX CUDA12 `0.5.3`、Orbax `0.11.13`；vendored 环境还包含 Torch `2.10.0`、LeRobot `0.4.4`。`install.sh` 通过 `uv sync --group lerobot` 及 editable 安装完成，不往 OpenWAM 或共享训练环境混装。

两模型 server 脚本均设置 `XLA_PYTHON_CLIENT_MEM_FRACTION=0.3`。这是 JAX 内存预分配设置，不代表实际只需要卡的30%，也不是并发 worker 数建议。现有服务器卡上同时放几个 π worker，仍需用短评测看实际吞吐与峰值。初次运行还可能访问 `gs://big_vision/paligemma_tokenizer.model`；本轮未验证深圳到该地址的下载。官方 checkpoint 已有参数，不需要为了推理另下载训练用 `pi0_base` / `pi05_base`。

尚未完成：新策略 uv 安装、全部 LFS 字节校验、JAX 编译/加载、一个真实回合、并行性能测量、对榜单成绩的数值复现。上述是执行时的自然步骤，不需要先额外重训。

依据：[安装脚本](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/install.sh)、[依赖](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/pyproject.toml)、[server](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/setup_eval_policy_server.sh)、[checkpoint loader](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/src/openpi/policies/policy_config.py)、[tokenizer](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05/openpi/src/openpi/models/tokenizer.py)。

## Seed 口径与建议顺序

[官方榜单协议](https://robodojo-benchmark.com/leaderboard/protocol#simulation-real-world) 明确允许两条路线：**三份训练 seed 权重**，或者**同一权重在三组 evaluation seed 上评测**；均报告均值与标准差。二者都合规，但测量的波动来源不同，记录中必须分开写 `checkpoint_seed` 与 `eval_seed`。

π0 / π0.5 既然已公开三个训练 seed，建议主复现使用其原始三个权重，显式记下与环境 seed 0/1/2 的对应关系。XPolicyLab 传 `--ckpt sim` 会按当前 seed 解析 `RoboDojo-sim-arx_x5-joint-<seed>`；传绝对 step 路径则可固定同一权重跑不同 eval seed。不存在「评估 seed 1 自动把 seed 0 模型再训练一遍」的过程。

实施建议：先 π0.5，复用已就绪仿真资产与兼容环境，按官方 joint 路径接入；随后 π0，保持它的官方单环境默认，比较增加独立 worker 的吞吐。两者完整评估都沿用54配置×3评估组×原生25/50预算；不因换模型把每项改成100回合。当前 OpenWAM 在跑，不修改其代码/config/端口/资源。

## 官方命令模板（本轮未执行）

以下在后续独立部署 checkout 中执行；`<...>` 需要替换成当时已分配资源与目录。下载脚本使用 branch/tag 参数，并不保证支持直接把 commit SHA 当 `--branch`；执行时记录并检查实际下载到的 revision，不盲填 SHA。

```bash
cd <DOJO_ROOT>
bash scripts/RoboDojo/download_ckpt.sh huggingface Pi_05
bash scripts/RoboDojo/download_ckpt.sh huggingface Pi_0

cd <DOJO_ROOT>/XPolicyLab/policy/Pi_05
bash install.sh
# π0 后续在自己的 Pi_0/ 目录执行同一安装入口。
```

先按官方入口完成一个真实回合；已有仿真端项目库路径和进程级 Vulkan 设置继续由原环境包装提供：

```bash
cd <DOJO_ROOT>
bash scripts/robodojo.sh eval \
  --policy-dir XPolicyLab/policy/Pi_05 \
  --task stack_bowls --ckpt sim --env-cfg arx_x5 \
  --action-type joint --seed 0 --eval-num 1 \
  --policy-env uv --eval-env <SIM_ENV> \
  --policy-gpu <POLICY_GPU> --env-gpu <SIM_GPU>
```

完整评测模板；实际 worker 数及 GPU 绑定在短测后填入，每个 seed 的输出分开保存。`--ckpt sim` 在此按编号加载不同发布权重：

```bash
for eval_seed in 0 1 2; do
  bash scripts/robodojo.sh benchmark \
    --policy-dir XPolicyLab/policy/Pi_05 \
    --ckpt sim --env-cfg arx_x5 --action-type joint \
    --policy-env uv --eval-env <SIM_ENV> \
    --seed "$eval_seed" --eval-num native \
    --gpu-ids <GPU_IDS>
done
bash scripts/robodojo.sh summarize
```

π0 改成 `Pi_0`，其 seed 0 checkpoint 真实 step 是60000，不是 deploy.yml 默认的59999；当前 resolver 会在目标step不存在时取该目录可用最大step。正式回执仍须记录最后解析到的绝对路径，避免只记录 `sim`。

如以后需要 SFT，官方入口是 `process_data.sh RoboDojo <RUN> arx_x5 joint` → `train.sh RoboDojo <RUN> arx_x5 joint <SEED> <GPU_IDS>`；训练默认60000步、batch256，不是本次推理的前置条件。

## 本轮公开成绩的引用边界

主线程于2026-09-29通过内置浏览器核验当前官网：仿真 π0.5 **Score 11.44 / SR 6.93%**，π0 **3.48 / 1.53%**；真机 π0.5 **22.90 / 12.80%**，π0 **5.80 / 1.70%**。搜索引擎抓取与 XPolicyLab 镜像存在旧的 π0.5 `11.41 / 6.91%`，本轮报告采用当前官网页面。真机与仿真任务/机器人体系统计不同，不混排为一个实验。

来源：[当前榜单](https://robodojo-benchmark.com/leaderboard)、[评测协议](https://robodojo-benchmark.com/leaderboard/protocol)。公开权重目录与成绩行均可查，但本轮未取得榜单后端逐次运行到 checkpoint hash 的完整绑定清单；因此后续本地复现需自行保存权重 revision、解析路径、模型配置和运行结果。
