# 最小修复与结果保留

日期：2026-09-29；时间均为 UTC+08:00。本文使用 `PROJECT` 表示项目根目录、`RUN` 表示原6300评估结果目录、`ATTEMPT` 表示独立续跑尝试；原始私有路径不公开。

## 上午：已有公开记录

原批次02:14因6530个资产文件仍为 Git LFS 指针而退出，正式评估尚未开始。显式展开缓存后15365个资产文件全量核验通过。11:00资源交接又发现最新 RLT checkpoint 的回放索引与实际文件不一致，按真实文件选择最近完整恢复点；11:06独立重试进入评估。上述记录已由 `332a7072` 发布，部署源码未随文档发布切换；详见[上午恢复记录](https://github.com/Yutenji-Nyamu/robodojo_openwam/blob/332a70726a27ed30967e774c9059d951c28b64a5/docs/experiments/20260929_parallel_full_eval/RECOVERY_20260929.md)。

## 下午：三项局部修复

| 故障 | 现场依据 | 实际修复与验证 |
|---|---|---|
| 调度 / 清理 `PermissionError` | 同 UID 的 SSH 会话可能无权读取进程环境；退出 / exec 切换期间也有短暂不可读窗口 | 核验真实 SSH 会话和 PID / 启动时刻；短暂异常有界重读；持续未知进程错误仍停止。没有扩大进程清理范围 |
| OpenWAM LRU 淘汰 `KeyError` | `classify_objects_by_language` 的栈指向满容量缓存淘汰；提取原类在实际 Python3.10中复现 | 使用官方已合并 [PR37](https://github.com/OpenWAM-Official/OpenWAM/pull/37)：先取最旧 key，再调用父类删除，避开重排访问逻辑；100次淘汰 / 顺序检查通过 |
| 续跑预检 `EADDRINUSE` | 15:52尝试的端口位于主机临时端口范围32768–60999 | 预检采用 `SO_REUSEADDR`，8个端口移至63090–63097；仍拒绝现有监听。失败尝试已自动归还 RLT，并验证恢复首轮 |

14项调度 / 进程身份 / 权限竞态 / 端口检查和4项结果续跑检查全部通过，共18项；缓存检查另外执行。正式 plan-only 通过，配置变化仅端口及派生 worker 端口，模型、任务、seed、回合预算和并发环境数不变。

固定部署 RoboDojo commit 为 `1d3e375add2557557291cc3050d8068ed0dc3f31`，XPolicyLab 为 `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4`。OpenWAM `engine.py` 补丁后 SHA256 为 `3fe9377115154bf965ff03fcbdab7f7ce42b0b75662be678fae7c21a7eb13b70`；控制器逐任务核验该文件。缓存修复针对 Python 异常，不能作为 GPU Xid 的修复证据。

## 已完成回合如何保留

修复时核实422个完成回合。5个满预算任务各50回合，续跑直接跳过：`build_tower`、`classify_objects`、`imitate_sorting_sequence`、`play_stacking_toy`、`pour_by_language`。另外4个部分任务为 `classify_objects_by_language` 40、`fasten_screws` 44、`play_tic_tac_toe` 44、`store_tools_in_toolbox` 44。

后三个部分任务直接使用原生 resume 记录；语言分类的 resume 文件已在异常退出路径被移除，依据40份真实回合详情与现有三路视频重建同结构 manifest。原始结果文件留备份，没有新增或更改回合结论。16:24核验422份原回合详情逐条一致，8个 worker 的32个环境均执行真实动作。

## 晚间：GPU7 故障与未完成范围

20:46快照已有995 / 6300个回合。随后核实 GPU7 的 worker6 七项任务 `INCOMPLETE`，均出现 `exit 139`；`stack_blocks` 的10次重试在19:13:31耗尽。这里的任务未完成属于评估基础设施异常，不能记为模型任务成功率零。

| worker6任务 | 原预算 | 已落盘 | 待补 |
|---|---:|---:|---:|
| make_toast_random | 25 | 16 | 9 |
| swap_blocks | 50 | 0 | 50 |
| put_bottles_into_dustbin | 50 | 0 | 50 |
| play_Xylophone | 50 | 0 | 50 |
| fold_clothes_random | 25 | 0 | 25 |
| deposit_coin | 50 | 0 | 50 |
| stack_blocks | 25 | 0 | 25 |
| 合计 | 275 | 16 | 259 |

该表是20:50核查时的明确缺口，不是最终成绩。另一同卡 worker7 当时仍在 `fill_pen_holder`，所以不能直接 reset。最新双机比对又发现 SZ2 / SZ3 均在 GPU7 并行执行 `make_toast_random` 与 `fill_pen_holder` 时出现 `Xid31 → Xid109`。这说明应重点保留同一任务组合、GPU 上下文和时序证据；尚不能证明是任务、并发、驱动或硬件中的某一项单独导致，也不能证明缓存补丁有影响。

## 本轮恢复验收

21:15精确停止旧controller并清空Dojo；退出态权限竞态使第一次gate未reset，原外层自动归还RLT。21:25四组RLT恢复首轮均验证；新借卡周期精确停止四组，21:28:20仅空闲GPU7 reset成功，21:29:06同run的独立continuation启动。原生部分manifest直接复用，完整任务跳过。

2026-09-29T21:39:32.138162+08:00核验：8路32环境已执行真实动作，包括GPU7吐司和笔筒；1067条旧回合details逐条一致；已完成1071/6300（本次续跑新增4）。模型/任务/seed/预算、源码和controller hash不变。2026-09-29T21:38:58.075531+08:00回查21:28:20重置以来内核，无所查新增Xid/OOM/I/O错误。完整评估仍在进行，故障根因尚未确定。

官方资料支持在排空后对故障 GPU 做局部重置并验收，但 H100 不在 Isaac Sim 5.1 的官方支持范围；当前 reset 成功也不能保证之后不复发。来源与处理边界见[GPU恢复资料](COMMUNITY_RESEARCH.md)。
