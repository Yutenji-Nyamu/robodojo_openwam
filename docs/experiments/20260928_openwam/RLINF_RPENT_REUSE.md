> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# RPent / RLinf 接入 RoboDojo 与 XPolicyLab 分工核查

核查日期：2026-09-28；PR 状态刷新于 16:41 CST。本文是公开来源核查，范围包括 GitHub profile、REST API、PR 正文、历史评论与最新 review、提交/文件列表及相关分支源码。下文运行数据均归属作者公开报告，不能当作我们的独立复现结果；本轮服务器现场情况另见 [H100 与已有运行证据](H100_COMPATIBILITY.md)。

## 当前 OpenWAM + RoboDojo 路线怎样复用

**当前直接沿 OpenWAM → XPolicyLab → RoboDojo 的官方推理入口推进。** 这里的 RPent/RLinf 桥接代码用来参考环境接口和故障处理。π0.5 + RLinf + RoboDojo 仅在后续需要单独验证 RLinf 环境、隔离模型与环境问题时作为可选对照，不是 OpenWAM + RoboDojo 的前置任务。具体推理契约见 [官方复现准备流程](OFFICIAL_RUNBOOK.md)。

| 部分 | 可以借鉴什么 | 对本轮 OpenWAM 路线的处理 |
|---|---|---|
| 环境生命周期 | Isaac 先启动后导入；主线程执行仿真/相机；单环境服务与多 slot 进程隔离；reset/close 明确归属 | 借鉴职责与诊断方式。先沿官方 Dojo eval client 验证，不把 RPent runtime 的打包源码替换当成必做步骤。 |
| 观察契约 | 三路 RGB、指令、逐环境状态组织；相机顺序、有限值、归一化和 reset 后状态检查 | OpenWAM 需要绝对末端状态与正确坐标变换，不能直接复制 π0.5 的14维关节 observation/state。三相机“数量相同”也不代表预处理相同。 |
| 动作契约 | action shape 校验、夹爪检查、chunk 执行与终止截断 | π0.5 bridge 是 **14维 joint / 50步**；发布 OpenWAM 路线是 **eef / 32步完整输出块**，双臂20维末端表示映射内部80维，再转换成Dojo原生动作。实际执行长度可受 `replan_steps` 限制；不能照搬维度、delta mask、坐标系或chunk长度。 |
| seed / reset / terminal | 固定/分组seed、部分reset、autoreset、final observation、成功和超时分开记录 | 后续接 RLinf 时逐项对齐；当前官方评测的 layout、seed 和任务协议仍应沿发布配置，不能把“seed可加载”当专家可解性证明。 |
| reward与阶段分 | 复用原生predicate及score，追踪何时结束、是否完成任务 | 现有 wrapper 把 **chunk聚合奖励和终止放在末位**，不是逐动作奖励。接我们的动作级方法时必须保留/重建每一步与mask的对应，不能原样套用这个归并结果。 |
| 退出清理 | readiness、超时、子进程与显存回收记录；区分policy退出与sim退出 | 9/23报告中policy正常退出，但环境close卡住并最终SIGTERM；这段实现是已知问题的排查线索，不能当清理已通过的模板。 |
| RPent高层agent | planner、SAM3、工具primitive、Flash replay的服务拆分可供理解 | 当前OpenWAM固定策略推理不需要引入这些模块；以后做高层agent时再单独考虑。 |

依据：[RLinf环境wrapper](https://github.com/littleZ05/RLinf/blob/91e0c6e361eff9371e2423a4183602481ae95ee5/rlinf/envs/sim/robodojo/robodojo_env.py)、[runtime bridge](https://github.com/RLinf/RoboDojo/blob/6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7/robodojo_runtime/bridge.py)、[OpenWAM动作adapter](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/model.py)、[OpenWAM部署配置](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/deploy.yml)、[作者9/23验证记录](https://github.com/RLinf/RPent/pull/96#issuecomment-5802279871)。这张表是接口审阅后的复用建议，不是已执行的迁移或RL验收。

## 16:41 状态刷新：代码未变，维护者新增评审要求

- **RPent #96**：仍为 open、非Draft、未合并，head仍是 `8b1f96ccf33d660338cd0acefc487e9703329115`；43 commits、51 files、30条普通评论。9/28新增5条代码评审评论，review_comments由158增至163。维护者要求依赖改用 [RLinf组织的RoboDojo/rpent](https://github.com/RLinf/RoboDojo/tree/rpent)，补充Isaac Sim 5.0/5.1选择说明和IsaacLab下载入口。[依赖评审](https://github.com/RLinf/RPent/pull/96#discussion_r4119732534)、[版本说明评审](https://github.com/RLinf/RPent/pull/96#discussion_r4119640833)
- 已核该组织fork存在，`rpent` head为 `6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7`，与此前个人fork的桥接commit相同。**这是维护者提出的新来源调整，#96 head未变，不能写成PR已经落实了依赖修改。**
- **RLinf #1606**：仍为 open、非Draft、未合并，head仍是 `7d3813bb256ca2dba2673e6c77a53f32a7eb27c1`；3 commits、5 files；普通评论与代码评审评论均为0。未出现新增验收结果。[当前PR](https://github.com/RLinf/RLinf/pull/1606)
- **最新运行证据没有升级**：#96最新人工运行报告仍是9/23的700步失败rollout与shutdown卡住；新增review不是新实验。#1606仍只有公开报告的7个无simulator接口测试，不能推导在线RL已跑通。

原始REST响应与最新评论保存在 E: 资料目录，入口为刷新摘要（完整本地证据未随公开版发布）。本节只对上述两个PR及新组织fork作本次刷新，以下其他历史资料仍按本日此前核查理解。

## 核心结论

1. 有人在认真接，而且有维护者参与。RPent 的 [PR #96](https://github.com/RLinf/RPent/pull/96) 已实现环境桥与策略服务；同一作者还向 RLinf 本体提交了 [PR #1606](https://github.com/RLinf/RLinf/pull/1606)。两者当前都是 open、未合并；#96 并非 GitHub Draft 状态，准确称“待合并提案”。
2. 最新证据比 #96 的旧正文前进了一步：9 月 23 日作者报告完成一次真实 π0.5 → RoboDojo 的完整 700 步 rollout，但官方任务判定失败，reward=0、score=0；退出还会卡住，60 秒后需要 SIGTERM。不能称作成功任务基线或在线 RL 跑通。[最新验收报告](https://github.com/RLinf/RPent/pull/96#issuecomment-5802279871)
3. 这份工作可作为接入起点，不能直接据此假定 PPO/GRPO、我们的动作级算法或多环境训练已经验收。现有 RPent 路径使用 RLinf 的环境和模型部件做 agent 交互/推理；没有提交可核验的在线 RL 训练结果。

## 作者是谁、是否官方

- 作者账号：[littleZ05](https://github.com/littleZ05)。[公开 profile API](https://api.github.com/users/littleZ05) 的 name/company/location/bio 均为空、blog 为空；[公开组织列表](https://api.github.com/users/littleZ05/orgs) 为空。不能据此推断实名、单位或是否私下属于某团队。
- #96 的作者关联字段是 `NONE`，分支来自个人 fork `littleZ05:feat/robodojo-integration`。#1606 同样由其个人 fork 提交。能确认的是“个人 fork 发起、维护者参与审查的待合并提案”；公开证据不足以断言“官方成员项目”或“完全无官方关系”。[PR 元数据](https://api.github.com/repos/RLinf/RPent/pulls/96)
- 其在 RLinf 组织内公开提出的相关 PR 包括 RPent #96、RLinf #1606、RPent #219。维护者 qurakchin、wilburx813 等参与了实现边界、依赖安装和特权状态访问的审查。
- 最强官方关联证据是 [issue #143](https://github.com/RLinf/RPent/issues/143) 中，标注 `COLLABORATOR` 的 qurakchin 于 9 月 23 日回复正在集成 robodojo-sim，并指向 #96。[该回复](https://github.com/RLinf/RPent/issues/143#issuecomment-5795532824)
- #143 当前只有这一条回复；没有看到在其中承诺上线日期或正式支持版本。此前搜索摘要将 #176 与 RoboDojo 对应是错配，直接页面 #176 是 dual-Franka，不能作为本结论来源。

## 当前版本与依赖链

| 对象 | 当前状态 / 固定版本 | 含义 |
|---|---|---|
| [RPent #96](https://github.com/RLinf/RPent/pull/96) | open，43 commits，51 files；head `8b1f96ccf33d660338cd0acefc487e9703329115`；updated 2026-09-28（新增review，head未变） | agent backend、环境 RPC、VLA/SAM3 服务、primitive、文档与测试 |
| [RLinf #1606](https://github.com/RLinf/RLinf/pull/1606) | open，3 commits，5 files；head `7d3813bb256ca2dba2673e6c77a53f32a7eb27c1`；updated 2026-09-28 | RLinf 环境枚举/注册、action split、薄 Gym wrapper、接口测试；运行时发行与可运行示例配置仍列为后续事项 |
| [littleZ05/RLinf 的 rpent/robodojo](https://github.com/littleZ05/RLinf/tree/91e0c6e361eff9371e2423a4183602481ae95ee5) | `91e0c6e361eff9371e2423a4183602481ae95ee5` | 同时包含 RoboDojo 环境 wrapper 与 OpenPI 的 RoboDojo policy/data config |
| [littleZ05/RoboDojo 的 rpent](https://github.com/littleZ05/RoboDojo/tree/6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7) | `6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7` | `robodojo_runtime` 包、桥接代码、锁定源与补丁、打包的 RoboDojo 源码 |
| [RLinf/RoboDojo 的 rpent](https://github.com/RLinf/RoboDojo/tree/6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7) | 同一桥接commit `6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7`；9/28新核验 | 维护者在最新review中要求改用的组织fork；不代表#96依赖已修改或已合并 |

注意：PR 正文的环境验证部分会落后于评论。9 月 23 日最新完整 rollout 对应作者报告的 `3eff95b`，之后 head 合并 main 至 `8b1f96c`；不能自动说最新 head 已重复同样实测。

## 怎么接：两个服务边界

```text
RPent planner / tools
  ├─ 环境 RPC client → 单环境 env_server（Isaac 必需的主线程执行）
  │                    → RoboDojoAgentEnv
  │                    → RLinf RoboDojoEnv
  │                    → robodojo_runtime.bridge.VectorEnv / NativeEnv
  │                    → RoboDojo collect_env + Isaac 仿真任务
  ├─ VLA RPC client → 共享 π0.5 policy server → RLinf OpenPI model
  │                    → action chunk → primitive 逐 native action 推给环境
  └─ SAM3 RPC client → 独立感知服务（agent 工具使用）
```

RPent 的环境 RPC 当前是一服务一环境、序列化执行；它不是已经验收的高吞吐 RL 集群。底层 runtime 对多个 slot 设计了独立进程/Pipe 路径，用于隔离 Isaac scene reset/step，不能仅因存在代码便认为规模性能已验证。RPC facade 的 chunk stepping 尚未开放，RPent primitive 当前逐步推进；RLinf 底层 wrapper 自己提供 chunk 接口。这两层不要混淆。

主要文件：

- [RPent 文档（固定 head）](https://github.com/RLinf/RPent/blob/8b1f96ccf33d660338cd0acefc487e9703329115/docs/source-en/rst_source/usage/robodojo.rst)
- [robot_spec.py：服务启动与默认 policy backend](https://github.com/RLinf/RPent/blob/8b1f96ccf33d660338cd0acefc487e9703329115/robots/robodojo/robot_spec.py)
- [env_server.py：环境构造、RPC 服务](https://github.com/RLinf/RPent/blob/8b1f96ccf33d660338cd0acefc487e9703329115/robots/robodojo/env_server.py)
- [rlinf_env.py：agent 层记录/元信息包装](https://github.com/RLinf/RPent/blob/8b1f96ccf33d660338cd0acefc487e9703329115/robots/robodojo/rlinf_env.py)
- [RLinf RoboDojoEnv](https://github.com/littleZ05/RLinf/blob/91e0c6e361eff9371e2423a4183602481ae95ee5/rlinf/envs/sim/robodojo/robodojo_env.py)
- [RoboDojo runtime bridge](https://github.com/littleZ05/RoboDojo/blob/6d76a0c4a49a7a47bf5ee3924de2ccd7ecb8a8b7/robodojo_runtime/bridge.py)

模型与数据契约：默认 `--policy-backend rlinf`，使用 RLinf OpenPI π0.5；另有可选 XPolicyLab server。三路 RGB 为 head/左腕/右腕；实际关节状态与动作顺序是左臂 6、右臂 6、左夹爪 1、右夹爪 1，共 14 维。policy chunk=50，模型内部 padding 与 native 14 维需要正确转换；夹爪 1=open、0=closed。最新修复把 delta mask 改成 `(12,-2)`，避免按旧的左右臂/夹爪交错布局误减关节值。[最新验证](https://github.com/RLinf/RPent/pull/96#issuecomment-5802279871)

底层 bridge 负责 reset/get_obs/step/reward/terminal/seed/close；调用 RoboDojo 原生 reward/成功判据。当前 RLinf wrapper 将 chunk 的聚合奖励与终止落到最后一个 chunk 位置，不能直接当作天然动作级奖励监督；我们若接动作级方法需先对齐这一语义。[wrapper 源码](https://github.com/littleZ05/RLinf/blob/91e0c6e361eff9371e2423a4183602481ae95ee5/rlinf/envs/sim/robodojo/robodojo_env.py)

## 真正测试到了什么

以下是作者报告；本文公开来源中没有取得可独立复核的对应 rollout 原始日志、视频或训练曲线。

| 层级 | 公开结果 | 能支持 / 不能支持 |
|---|---|---|
| #1606 接口单测 | Ubuntu 24.04 / Python 3.11，7 个 stub tests 通过，测试机无 simulator | 支持 wrapper 接口行为；不等于 Isaac 仿真或 RL 验收 |
| #96 新环境安装 | Python 3.11.16；410 packages；489 秒；环境 20.7 GiB；cuRobo 构建成功 | 需将同 revision IsaacLab 改 editable 才解决缺失 `config/extension.toml`；`uv pip check` 仍有四项 metadata mismatch，尚非零干预安装 |
| 真实 RoboDojo π0.5 checkpoint 推理 | 正确转换的 checkpoint + norm stats；18.1 秒就绪；finite actions `(1,50,14)`；policy server exit 0；显存约 20→7657→20 MiB | 证明真实权重推理链；不单独证明动作或任务成功 |
| 最新一次完整任务 rollout | `put_bottles_into_dustbin`，layout 0，settle=1000；700 native steps / 14 次 prediction；3 个视频各 701 帧、640×480、25fps；rollout 72 秒、全流程 205 秒、GPU0 峰值约 16.6 GiB | 原生 predicate **success=false**，reward=0，score=0；仅一 episode，不能外推总体成功率 |
| 环境退出 | parent-watch EOF、显式 shutdown RPC 均会卡住，60 秒后 SIGTERM | 最新仍有生命周期缺陷；旧正文曾称清理通过，不能覆盖这一更新 |
| 在线 RL | 未找到 PPO/GRPO 训练、优化器更新、奖励曲线、稳定多 seed 成功率的公开验收 | 不能称 RL 已跑通 |

资源上下文是单张 NVIDIA RTX PRO 6000 Blackwell；不是已报告的 H100 复现。最新报告把退出栈定位为 `SimulationApp.close/context.close_stage` 触发 timeline STOP callback 后，`SimulationContext._app_control_on_stop_handle_fn` 内的 render 循环阻塞。作者仍将其列为 current gap。[9/23 完整报告](https://github.com/RLinf/RPent/pull/96#issuecomment-5802279871)

早期 P6–P9 agent/planner 实验集中于 dustbin layout 1，出现 provider streaming 断连、目标身份漂移、拿错白瓶、持物失败等，没有完成成功的任务/Flash replay。不能把 `pi0_pick` 的启发式 pick=true 当官方任务成功。PR 声明面向的 dustbin/fill_pen_holder/stack_bowls_random 是目标范围，不是三项成功结果。[PR 正文](https://github.com/RLinf/RPent/pull/96)

复现细节还有一个具体坑：较早转换脚本按路径是否含小写 `pi05` 选择分支，原始 `Pi_05` 路径误走 pi0 分支产生 KeyError；作者用包含 `pi05` 的别名路径转换了真实 checkpoint `59999`，得到约 7.2 GB bf16 safetensors。早期 generic π0.5 权重 smoke 与此后的真实 checkpoint smoke 必须分开。[转换记录](https://github.com/RLinf/RPent/pull/96#issuecomment-5771683415)

补充 [RPent #219](https://github.com/RLinf/RPent/pull/219) 是独立的 scripted control runner，移除 planner/VLA/SAM3 需求，用 cuRobo IK。其提交单测不能代替 GPU 测试。仓库保存了两个历史手工控制计划，声称 general_pickup layout 1 成功（94 actions/200 horizon）、pour_by_language layout 1 成功（690/800）；但当时 controller 的 orientation IK/apply_action 与现在 position IK/step 接口不同，原始视频/日志未公开，计划不是当前 runner 的可执行输入。作者文档明确没有已验收的当前接口可靠成功 recipe，因此不能借它宣称 #96 的 VLA 或 RL 成功。[recipe 限定](https://github.com/RLinf/RPent/blob/8c34dcb84f67d64fe31e809c64751b981992b4a9/robots/robodojo/recipes/README.md)

## 以后明确开展 RLinf 接入时的四步工作（工程判断）

以下是后续RL环境适配路线，**不是本轮OpenWAM官方推理的前置清单**；也不自动授权安装RPent或增加π0.5实验。

1. 锁定 RPent/RLinf/runtime、IsaacLab 和任务资产版本；先复现真实 checkpoint 的三相机/14维/50步契约与环境启动退出。修好 shutdown、确定可重复安装，形成小而明确的基础运行记录。
2. 将 RLinf #1606 的环境注册与 bridge 合到隔离分支，补最小可运行 task config；核对 reset seed、success/reward、termination/truncation、autoreset/final observation、动作顺序与 chunk 语义。此阶段可只用一个现成任务。
3. 在 RLinf EnvWorker / RolloutWorker 的实际闭环中做短评估，记录动作、图像、官方 predicate 与显存/进程退出；随后完成一次真实 optimizer update，才可说 RL 主链路打通。RPent 的 planner/SAM3 不属于 RLinf 在线训练必须引入的部分。
4. 沿我们最近已跑通的 control 配置做最小扩展，保留固定的预算与任务设置；再核验多个 episode、进程长期稳定性和动作级奖励。只有这些结果足够后，才谈与 RoboTwin 横向对比或扩模型/扩任务。

## XPolicyLab 引入前后，RoboTwin 哪部分变了

历史源码可精确定位：在 [迁移前提交 264b426](https://github.com/RoboTwin-Platform/RoboTwin/tree/264b426e778b37ed390ca88f11bfdc4a025824df) 中存在 `policy/ACT`、`policy/DP`、`policy/DP3`、`policy/pi0` 等，各自带 deploy/train/process_data 脚本；[4f00483 提交](https://github.com/RoboTwin-Platform/RoboTwin/commit/4f00483bb6ff42950b53cf18a01a24a9bda5380d) 移除了本地 policy 树并调整 eval；随后 [2a6d9f5 提交](https://github.com/RoboTwin-Platform/RoboTwin/commit/2a6d9f5e5d6b2773e54a8a3e2bd777dee92ad659) 加入 XPolicyLab 子模块。不能只看“Add XPolicyLab”提交的父目录来判定旧职责，因为前一提交已移除旧 policy。

| 职责 | 以前 | 当前 RoboTwin main |
|---|---|---|
| 仿真环境/机器人/物体/任务/原生成功条件/专家采集 | RoboTwin `envs/assets/task_config/...` | 仍由 RoboTwin 提供 |
| 模型部署入口/训练配方/模型专用预处理 | RoboTwin 内各 `policy/<model>` | 共享到 `XPolicyLab/policy/<model>` 与统一数据/服务接口 |
| 标准评估脚本 | 直接调用本仓 policy adapters | `scripts/eval_policy.sh` 分发到 XPolicyLab eval、multitask eval、policy server 路径 |
| 数据协议 | 原本 RoboTwin 各 policy 的转换链 | 当前文档统一 XPolicyLab HDF5 schema、公共图像编码/解码与 LeRobot 转换；任务采集逻辑仍在 RoboTwin |

所以可以通俗理解为“把模型工具箱与评估部署接口集中管理”，并未用 XPolicyLab 替换 RoboTwin 的仿真器或任务本身。[当前 README](https://github.com/RoboTwin-Platform/RoboTwin/blob/ea8b21121ebb3cd201ff5b3fe361944ac94eda3f/README.md)

**现有 RLinf_support 不走这一标准 XPolicyLab eval 入口。** 实查该分支 head `dca9ec682688821c42944eacd7f5dd9bfb15396f` 的完整 tree：没有 XPolicyLab 子模块，仍为 `robotwin/envs/vector_env.py` 和旧 `script/`。RLinf 环境 adapter 直接调用这套 VectorEnv，模型由 RLinf 自己加载并接入训练 worker；不能把 main 分支的新 README 当作 RLinf_support 的依赖要求。[RLinf_support VectorEnv](https://github.com/RoboTwin-Platform/RoboTwin/blob/dca9ec682688821c42944eacd7f5dd9bfb15396f/robotwin/envs/vector_env.py)

## 本文公开来源证据边界

确认：PR/issue 状态、作者公开字段、分支/提交/目录/接口、完整公开评论中的作者运行陈述。未独立确认：作者身份、未公开组织关系、本地日志/视频真实性、成功率、H100 可复现性、多环境吞吐、在线 RL 收敛。未把无公开结果写成“绝对没有人做”，未将 issue 搜索摘要替代直接页面。
