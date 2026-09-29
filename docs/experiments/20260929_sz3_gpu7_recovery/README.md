# 深圳3 π0.5 全量评测：GPU7故障与续评

本轮延续用户授权：修复Dojo问题，保持官方任务、权重、种子与回合预算，保存粗细记录并发布同仓库SZ3分支。深圳2由“0927 exp”窗口处理，本窗口仅操作深圳3。以下时间均为2026-09-29 UTC+8。

## 事实与判断

- 原批次 `sz3_pi05_official_6300_n4_dual_20260929_r2`，15:46启动，54配置×3seed、原生25/50，共6300回合；GPU4–7，8worker×4环境。
- p065，21:10：436回合、25成功、5项满预算；worker0–5仍有实时动作或reset，GPU7的worker6（make_toast_random）反复DEVICE_LOST，worker7（fill_pen_holder）停止更新。pipeline EVALUATING和controller无error不能单独证明全部worker健康。
- p067内核：21:03:18，GPU7/PCI C1:00，两仿真PID4054286和4014299同时出现Xid31/graphics MMU FAULT_PDE；21:04以后新吐司重试陆续报Xid109/CTX SWITCH TIMEOUT。ECC不可纠正计数均0；未据此判定硬件损坏。
- 深圳2另一窗口核到同GPU7、相同“做吐司＋收纳笔”组合也出现Xid31→109。两机同组复现是后续定位线索；尚不能归因为特定驱动、资产或并发缺陷。当前先做空闲单卡reset并保持原32并发，恢复后检查真实动作及新增回合。
- worker0的历史Traceback是Isaac GUI `NoneType.scroll_y_max`，该路仍正常动作；与GPU7的DEVICE_LOST分别记录。
- 官方依据已用内置浏览器核对：[NVIDIA Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html) 将H100的109列为Context Switch Timeout，即时恢复建议RESET_GPU。重置是恢复操作，不能据此声称已修复根因。另一窗口也完成了RoboDojo、Isaac及NVIDIA社区检索，尚未找到对本任务组合可直接采用的已确认补丁；这不是对上游所有讨论的穷尽结论。

## 粗日志

| 步骤 | 动作与结果 |
|---|---|
| p065–066 | 固定host-key/账号现场核验，部署HEAD与所有源码/控制器hash未变。公开分支仍4adc41e，仅包含15:55启动记录，后续进展尚未公开。 |
| p067 | root只读核GPU UUID/PCI、全部计算进程和21:03以来内核错误，确认故障卡7及两任务；未向无关进程发信号。 |
| p068 | 按PID/start暂停原外层监督器，TERM其controller，等待正常清理；已知仿真进程退出时environ短暂不可读，controller最终exit5。未满足清空条件，**没有reset**；finally恢复外层监督器。失败门控记录完整保留。 |
| p069 | 外层独立cleanup再次执行成功，四卡均0MiB，processes_clear/gpus_released为true，随后自动派发原四组RLT恢复；未改共享Ray。 |
| p070–071 | 复制固定控制器到独立续评目录。原controller、配置、模型和任务预算hash完全一致；17项进程/原生结果恢复测试通过。440条已落盘回合、5满预算+7部分任务逐条验证、三路录像齐全，7份原生resume manifest一致，无需重建。存档既有_result与manifest。新借卡cycle精确引用刚恢复的四个RLT run。 |
| p072 | 21:22原四组RLT再次精确暂停，各组真实恢复点仍CP25，保留完整N8和累计3000预算。 |
| p073 | 21:22:31核GPU7 UUID/PCI、0MiB及全UID设备FD仅剩persistenced后，单卡reset成功exit0；其他GPU未reset、共享Ray未改。 |
| p074 | 核原生7份resume manifest，restart_count均0、abandoned为空；井字棋unstable2按原记录保留，没有重置统计或丢弃已有失败。 |
| p075 | 21:23:46从同run启动独立continuation，pipeline PID466585/start665925027。续评沿用旧controller与配置，结束/失败仍走精确清理及新cycle自动归还RLT。 |
| p076–079 | 21:24八模型/仿真初始化；21:26从21:22:31 reset结束起的root内核无所查Xid/OOM/I/O，ECC均0。21:28七路恢复动作，包括GPU7收纳笔114步；吐司尚初始化。440条旧details逐条一致、源码/controller hash不变；未将7路动作写成8路验收通过。 |
| p080–084 | 21:29内核仍无新Xid/OOM/I/O；21:33八路全进入真实动作，步骤375/208/195/389/333/401/2/434。新controller PID466737/start665925350，attempt1790688232132720307；当前无controller错误/DEVICE_LOST，原440条details逐条一致。吐司多花约8分钟完成场景初始化，未擅自改场景或模型。 |
| p085–087 | 21:38首批新增4回合落盘，累计444回合、25成功；440条历史details全部一致，8路仍有动作或正常回合重置，controller错误与DEVICE_LOST计数均0。21:38:41 root内核复查：自21:22:31 reset后无所查Xid/OOM/I/O，ECC均0。GPU4–7显存73619/77187/74299/76134MiB，主机可用1733.49GiB；这是恢复后继续产出回合的验收，完整6300仍在运行。 |

## 路由与验收

- 项目：`/data/chenyiteng/projects/robodojo-openwam-sz3`。
- 运行源码保持 `50aab2b28298db42c4b25c59c8967eae8d91e84c`；原controller两文件不变。
- 续评脚本：`scripts/pi05_gpu7_recovery_20260929/`。
- 新借卡cycle：`rlt-cycle-sz3-pi05-gpu7-v1`；精确停止和仅GPU7 reset已完成，续评已产出新增真实回合；结束或失败后精确清理、核GPU释放，再从最新有效checkpoint恢复原四组RLT。
- 续评输出：原run下 `continuation-20260929-gpu7-v1/`；启动后 `active-continuation.json` 指向最新监督器。旧根目录pipeline-final属于上次退出，不能当成续评终态。
- 既有结果存档：原run下 `repair-20260929-gpu7-v1/preserved-results/`；预算不重置，完整任务跳过，部分任务从官方manifest接续。
- 原始细粒度证据：E当前根 `exp2-research/implementation-sz3-20260929/steps/p065-*` 起，每步保存命令、stdout、stderr、退出码、时间及主机校验。

21:38已确认8路真实动作、4个新增回合落盘、440条原始details完整保留，并通过reset后的内核检查。原并发方式继续运行，未声称GPU故障根因已解决。
