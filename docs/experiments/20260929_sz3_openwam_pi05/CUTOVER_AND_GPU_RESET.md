# SZ3：切换 RLT、单卡重置与首次成功回合

记录时间：2026-09-29 14:54（UTC+8）。本文承接本目录早先的安装与初始化失败记录。

## 切换范围与恢复点

用户授权暂时停止本人 GPU4–7 上的四组 RLT，切换到 RoboDojo；Dojo 结束后恢复原训练，继续使用 GPU4–7。

停训前固定当前源码、配置、进程身份和恢复信息，按具体 driver 与 Ray namespace 清理本人四组训练。停机完成后的检查确认：**四组均已有有效的 Stage2 `global_step_25` checkpoint**，此次冻结的恢复方式全部为完整 checkpoint 续训，包含模型、优化器、回放池与训练状态。此前“尚无 Stage2 checkpoint”的记录属于更早快照，本次以停机后检查为准。

Dojo 结束后，监督器已自动调用四组 checkpoint 25 的恢复流程，14:43:07 恢复 helper 返回 0；14:54进一步确认四组均从第25轮推进至第26轮，driver身份、checkpoint加载日志、累计轮次和回放池均通过验收。

## GPU4：重置前后有直接对照

| 顺序 | 操作与结果 |
|---|---|
| 1 | 停止 RLT 并释放卡后，在 GPU4 运行已有独立 SimulationApp 短测；仍出现 `ERROR_DEVICE_LOST` / Xid109。仅停训未解决问题。 |
| 2 | 按本次 probe 的 PID、UID、启动时间及后代关系清理失败进程，确认目标卡没有计算或图形任务。 |
| 3 | 按已核验的 GPU4 身份执行一次单卡 reset；命令返回 0，驱动明确报告该卡重置成功。未停止 persistence daemon。 |
| 4 | 保持短测代码、仿真环境和兼容配置不变，在同一 GPU4 重跑；约 32 秒显示 `Simulation App Startup Complete`，构造及 update 返回，进程退出 0，显存回到 0 MiB。 |

两次短测沿用已记录的进程内 EGL 登记、缺失库名链接和 NVIDIA 595 Vulkan allocation-limit 兼容层。本次没有通过更换这些配置获得前后差异。

**可以确认 GPU4 在此次单卡重置后恢复了相同仿真短测；尚未证实最初触发 Xid109 的根因。** 不能将结果直接归因于某个训练进程、IOMMU 参数或 H100 硬件能力，也不能保证其他机器遇到相同报错都由 reset 解决。

NVIDIA 将 Xid109 的恢复动作列为 GPU reset，并要求目标设备没有应用占用；Hopper NVSwitch 支持单卡重置。本次只对核验过的目标卡操作。[Xid 目录](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html)、[nvidia-smi 单卡重置说明](https://docs.nvidia.com/deploy/nvidia-smi/index.html#r-gpu-reset)。

GPU6 随后在同样已释放的条件下执行一次单卡 reset，返回 0。GPU6 没有单独做重置前后的 probe 对照；其后进入真实 π0.5 评测，不能把 GPU4 的对照证据等同套用到 GPU6。

## 两个真实评测 worker

本次使用独立运行目录，同时启动两个官方评测入口：

| 模型 | 仿真 GPU | 策略 GPU | checkpoint | 动作类型 |
|---|---:|---:|---|---|
| OpenWAM | 4 | 5 | `OpenWAM-Alpha-Sim-RoboDojo` | `ee` |
| π0.5 | 6 | 7 | 官方 RoboDojo `sim` / seed0 / step59999 | `joint` |

共同配置保持 `stack_bowls / arx_x5 / seed 0 / layout 0 / num_envs 1 / eval_num 1`，不更换任务或筛选布局。两者均保留现有兼容设置，使用官方策略服务与仿真客户端执行真实动作。

监督器为 `$PROJECT/scripts/dojo_pair.py`；本次 pair 为 `sz3_pair_20260929_143536`，输出位于 `$PROJECT/runs/sz3_pair_20260929_143536/`。两模型各有独立 run ID、日志、原生结果目录和进程身份记录。

## 退出与自动恢复

1. 监督器在启动前核验 GPU4–7 的固定身份及空闲状态。
2. 总运行期限为 1800 秒；每个 worker 沿用现有单回合 helper。一个 worker 提前结束时，另一组可继续运行到完成或期限。
3. 正常完成、模型失败、任务未成功或超时均进入收尾。监督器使用 Linux child subreaper 追踪本次子孙进程，包括重新挂接的 Isaac、策略服务和录像进程；仅对记录并重新核验身份的进程执行清理。
4. 确认本次工作进程全部退出且 GPU4–7 已释放后，写出 `release.json`，默认调用冻结的 RLT 恢复 helper，从四组 checkpoint 25 恢复训练。
5. `actual_success` 单独取自原生回合结果；任务未成功不会阻止已释放资源归还 RLT。若清理或 GPU 释放未完成，恢复不会与残留 Dojo 进程并发启动，错误会保留供处理。

本次 release 回执确认 `all_workers_stopped=true`、`gpus_released=[4,5,6,7]`、`errors=[]`，随后恢复 helper 返回 0。14:54四组恢复首轮验收全部通过，见下表及公开回执。`--no-resume` 是人工排障选项；本次正式 pair 使用默认自动恢复。

整个切换未重启共享 Ray、未变更其他用户实验、未安装或切换系统驱动，也未重启服务器。单卡 reset 的范围限于 GPU4 和 GPU6。

## 本次终态

两个模型均完成一个真实叠碗回合并正常退出。各自原生 `_result.json` 均为 `eval_time=1`、`success_rate=1`、`score=100`；`details["0"]` 均记录 `layout_id=0`、`success=true`、`score=1`。

| 模型 | 成功回合 | 三路视频（头部、左右腕） |
|---|---|---|
| π0.5 | seed0 / layout0，1/1 | 每路 279 帧、25 fps、640×480，11.16 秒 |
| OpenWAM | seed0 / layout0，1/1 | 每路 320 帧、25 fps、640×480，12.8 秒 |

这些是**各一个回合的部署成功里程碑，不是完整基准成功率**。原生结果与视频详见 [π0.5 里程碑](MILESTONE_pi05.md)、[OpenWAM 里程碑](MILESTONE_openwam.md)。Dojo 资源已归还，RLT 已自动恢复并确认首轮推进。

依据为本次私有细粒度回执 s144、s148–s156、s164、s168、s170、s179 及原生结果和视频检查；原始进程身份、设备标识和私有路径不随本公开文档发布。

## RLT恢复验收（14:54）

| GPU | checkpoint轮次 | 恢复后真实轮次 | 回放池样本 | 首轮验收 |
|---|---:|---:|---:|---|
| 4 | 25 | 26 | 3957 | 通过 |
| 5 | 25 | 26 | 3983 | 通过 |
| 6 | 25 | 26 | 4097 | 通过 |
| 7 | 25 | 26 | 4088 | 通过 |

四组均保留原累计目标3000轮及算法/预算配置。当前仍处于 teacher warmup，`update_step=0`、`ready_for_online=0`与恢复点一致；回放池与采集轮次已继续推进。[脱敏回执](evidence/cutover-result.json)。
