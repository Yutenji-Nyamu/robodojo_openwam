# RoboDojo：π0、π0.5、FastWAM 部署准备与公开成绩

核查日期：2026-09-29。此次为官方材料、源码、权重目录与现有运行状态的核查；尚未部署或启动三个新增模型。复用已跑通的仿真侧，模型侧按各自官方适配安装。

## 1. 先理解三 seed 与 50 回合

从 **42 个基础任务** 看，每任务每 seed 共 50 个有效评测回合，三 seed 合计 150；其中 12 个泛化任务每 seed 分成标准 25＋随机化 25。执行时因此是 **54 个配置 × 3 seed，总计 6,300 回合**，不是 54×3×50。

每回合读取一个官方布局 JSON。布局之间可以改变物体型号、位置、朝向，以及任务所需的颜色、数字、目标关系或操作顺序；具体变化取决于任务。`eval_seed` 选择布局集合，`layout_id` 选择集合内的场景。重复测试的是同一种能力，不是同一画面机械重跑 50 次。精确源码、真实布局例子及不稳定回合处理见 [seed 与回合说明](SEEDS_AND_EPISODES_20260929.md)。

官方榜单协议同时允许“三份训练 seed checkpoint”或“同一 checkpoint 在三个 evaluation seed 上测试”，报告三次结果的均值与标准差。当前 OpenWAM 是后者；π 系列官方短名加载路径可按 seed 选择三份权重。两种实验都须记录清楚，不能把训练 seed 与布局 seed 混写。[官方协议](https://robodojo-benchmark.com/leaderboard/protocol#simulation-real-world) · [完整评测](https://robodojo-benchmark.com/doc/usage/quick-evaluation/#complete-evaluation)

## 2. 当前公开成绩

以下在内置浏览器直接读取 RoboDojo 官方榜单，页面更新标记为 2026-09-28。是官方公开结果，不是我们的本地结果。Score 是阶段完成得分（0–100），SR 是整任务成功率；完成部分步骤可得分，但未完成整任务不会算成功。总体按五类能力汇总，不能把 6,300 个 episode 的成功数直接混成同一个官方总分。

### RoboDojo-Sim

表格各格均为 **Score / SR**：

| 模型 | 综合 | 泛化 | 精细操作 | 长任务 | 记忆 | 开放任务 |
|---|---|---|---|---|---|---|
| OpenWAM-α | **17.18 / 11.92%** | 20.71 / 14.83% | 18.45 / 9.25% | 34.93 / 25.33% | 10.41 / 9.11% | 1.41 / 1.08% |
| π0.5（Pi-05） | **11.44 / 6.93%** | 13.38 / 8.17% | 12.40 / 5.50% | 23.54 / 14.67% | 5.89 / 4.67% | 1.98 / 1.67% |
| FastWAM（Fast-WAM） | **3.48 / 2.03%** | 2.33 / 1.11% | 1.96 / 0.00% | 9.14 / 5.17% | 3.55 / 3.44% | 0.42 / 0.42% |
| π0（Pi-0） | **3.48 / 1.53%** | 3.94 / 2.55% | 3.56 / 0.75% | 6.19 / 2.00% | 3.47 / 2.11% | 0.25 / 0.25% |

这四个公开模型中 OpenWAM 综合最高，π0.5 次之；开放任务四者都很低，π0.5 略高于 OpenWAM。FastWAM 与 π0 的综合 Score 四舍五入后相同，但 SR 不同。FastWAM 原论文表中泛化 Score 为 2.34，当前网页为 2.33，记录时注明版本，不混改原表。

### RoboDojo-RealWorld

| 模型 | 综合 Score / SR | 本次可见条目 |
|---|---|---|
| OpenWAM-α | 37.60 / 24.40% | ARX X5、Piper、Piper X |
| π0.5 | 22.90 / 12.80% | 三种机器人 |
| π0 | 5.80 / 1.70% | 三种机器人 |
| FastWAM | 未见条目 | 不记为 0 |

真机任务和仿真任务不同，两个榜单的数值不宜直接比较难度。页面底部还嵌有 RoboTwin 榜单，其 FastWAM 39.9% 等数字不属于 RoboDojo。[官方榜单](https://robodojo-benchmark.com/leaderboard)

## 3. 官方材料与可部署性

共同入口是 RoboDojo 仿真客户端 → XPolicyLab 策略接口 → 各模型环境。仿真资产、机器人与任务实现可以复用；权重、归一化统计、动作类型与模型依赖分别对齐。

| 模型 | 官方 Dojo 适配与权重 | 首次部署依据 | 需要注意 |
|---|---|---|---|
| π0.5 | XPolicyLab `Pi_05`；官方 dataset 仓库有 sim seed 0/1/2 | [π 系列准备](PI0_PI05_OFFICIAL_20260929.md) | joint 动作；batch 接口内部逐环境推理，吞吐不能照搬 OpenWAM |
| π0 | XPolicyLab `Pi_0`；官方 dataset 仓库有 sim seed 0/1/2 | 同上 | 默认 `eval_batch: false`，官方评测会强制单环境 |
| FastWAM | XPolicyLab `FastWAM`；官方 dataset 仓库有 sim seed 0 checkpoint 与 stats | [FastWAM 准备](FASTWAM_OFFICIAL_20260929.md) | 安装示例下载的是 RoboTwin 权重；Dojo 要换官方 joint 权重及配套 14 维 stats |
| OpenWAM-α | 已使用官方 RoboDojo 专用模型包及 XPolicyLab `OpenWAM` | 已有成功回合与正式批次 | 当前为末端动作；其批量生成能力与上面三者不同 |

本次检查的 XPolicyLab commit 为 `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4`；官方权重 dataset revision 为 `35efbc7dedfdbeeb6e95fb749bd885d73d483e41`。权重位于 **dataset 仓库的 `ckpt/RoboDojo/`**，仅在 Hugging Face 的 models 标签搜索会漏掉。[XPolicyLab](https://github.com/XPolicyLab/XPolicyLab) · [官方权重目录](https://huggingface.co/datasets/RoboDojo-Benchmark/Robodojo/tree/35efbc7dedfdbeeb6e95fb749bd885d73d483e41/ckpt/RoboDojo)

权重存在、配置可读和官方有成绩，足以进入部署；尚不等于本机已复现对应分数。保留官方 robot、相机顺序、动作与归一化，不把已用于 RoboTwin 的同名模型包直接移来充当 Dojo 模型。

## 4. 建议实施顺序

1. **π0.5 先行**：官方 Dojo 路径齐全、与我们的既有经验接近，也是这四个模型中仅次于 OpenWAM 的公开基线。沿用已成功仿真环境，新建模型环境，按官方 `Pi_05` 配置直接跑真实推理。
2. **π0 接续**：复用相近的 OpenPI 安装经验，使用 `Pi_0` 自己的配置、权重和 stats；首次保留官方单环境设定。
3. **FastWAM**：先将官方示例中的 RoboTwin 权重项替换为已经找到的 Dojo checkpoint 与 stats，再用 Dojo joint 配置运行；保留模型官方重规划和去噪参数。
4. **各模型测一次实际吞吐后再定并行**：先用官方支持的配置获得真实回合，依据显存、推理耗时与环境步速选择 worker 数。`eval_batch=true` 不保证模型真正同时计算多个环境；不能直接承诺每模型四卡 32 环境都有 OpenWAM 的速度。
5. **正式比较沿用同一官方评测口径**：54 配置、三 seed、原生 25/50、有相同资产 revision 的布局与评分代码；记录训练 checkpoint seed、eval seed、layout ID、动作类型、chunk/replan/denoising、并发与失败重试。按各模型官方控制配置评测，不为统一表面参数而强改动作长度。

这次已把版本、具体路径、命令模板、下载体积和待对齐项放入两个模型专题。开始部署时从这些固定版本继续，不重新发散到 RL 或训练。本轮未自动预约或占用空闲卡，也未改变当前 OpenWAM 任务和 RLT 归还流程。

## 5. 当前 OpenWAM 评测快照

2026-09-29 11:36:05 只读核验：当前正式批次仍在 EVALUATING，8 worker×4 环境；seed0 有 8 个任务运行、46 个等待。原生 resume 记录已有 **27 个有效完成回合，3 次成功**；其中 build_tower 为 3/4，其他已写结果任务仍处于很早期，不能据此估计完整成绩。另有 1 次 unstable 记录；它不是额外的有效失败回合。

已有 6 个增量 `_result.json`、177 个视频路径，当前产物约 439 MB。`_result.json` 每批会刷新，文件存在不代表该任务 50 回合已完成；仍在写入的视频路径也不等于完整视频。GPU4–7 显存约 71.1–74.3 GiB，系统可用内存约 1,750 GiB。此前 1–2 天仅是吞吐估算，需更多不同长度任务完成后再收窄。

原始只读证据标签 `h001-model-planning-live-check`，包含身份及 host-key 校验、时间、命令哈希、输出与退出码。此处不将早期结果与官方榜单作有效比较。

## 6. 资料覆盖与下一次入口

- 官方网页：榜单 Sim/Real 两标签、榜单协议、完整评测与并行文档。
- 固定源码：RoboDojo 布局加载/计数/输出、XPolicyLab 三模型安装、配置、加载、动作与 batch 实现。
- 官方资产与模型：布局 JSON、Hugging Face dataset 固定 revision 的 checkpoint 树与文件元数据；π 系列和 FastWAM 各自 stats。
- 模型/基准论文与官方仓库：见两个模型专题的逐条链接和核查范围。

下次读本页 → 对应模型专题 → 已成功仿真实配；部署前刷新现场资源。当前目标仍是 RoboDojo 官方模型推理复现，后续 RL 接入另开阶段。
