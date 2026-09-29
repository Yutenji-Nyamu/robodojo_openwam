# SZ2 / SZ3 RoboDojo：运行与修复记录

2026-09-29。本目录补记 SZ2 上午资产恢复之后的权限竞态、OpenWAM 缓存和端口修复，以及晚间 GPU7 故障调查；同时索引 SZ3 已公开的安装、双模型首成功和正式评估记录。

SZ2 于16:11恢复原批次，16:24确认8个 worker × 4个环境均执行动作，原422个已完成回合逐条保留。20:46快照为995 / 6300回合；随后核实 worker6 的7项任务出现 `exit 139 / INCOMPLETE`，这些任务尚缺259回合，不能计作完整评测。两机在 GPU7 同时运行 `make_toast_random` / `fill_pen_holder` 期间，均观察到 `Xid31 → Xid109` 故障链；共同触发条件仍在调查。

**本轮恢复验收通过。** 2026-09-29T21:39:32.138162+08:00核验：8路32环境已执行真实动作，包括GPU7吐司和笔筒；1067条旧回合details逐条一致；已完成1071/6300（本次续跑新增4）。模型/任务/seed/预算、源码和controller hash不变。2026-09-29T21:38:58.075531+08:00回查21:28:20重置以来内核，无所查新增Xid/OOM/I/O错误。完整评估仍在进行，故障根因尚未确定。

| 阅读目的 | 入口 |
|---|---|
| 故障、最小修复与结果保留 | [修复说明](REPAIR_NOTES.md) |
| 时间、步骤、检查和原始证据标签 | [细粒度执行日志](EXECUTION_LOG.md) |
| 两机哪些记录已经上传 | [发布审计](PUBLICATION_AUDIT.md) |
| 官方文档与社区原始讨论 | [GPU恢复资料](COMMUNITY_RESEARCH.md) |

评估协议保持54配置 × seed0/1/2、原生25/50回合，共6300；每 worker 为4环境，官方权重、布局与推理参数沿原固定配置。GPU 重置是基础设施恢复动作，不代表故障根因已消除。

历史入口：[SZ2正式协议及上午修复](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/64e43bcc3036ca68091347530225d657df18feb0/docs/experiments/20260929_parallel_full_eval)、[SZ3双模型首成功](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/d82ad41399e13177c381d937d6a7fa4321577d47/docs/experiments/20260929_sz3_openwam_pi05)、[SZ3正式评估启动与修复](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/4adc41e6c616d32660d597f2d7b5d5ea4eba13da/docs/experiments/20260929_sz3_pi05_full)。这些链接固定到历史 commit，各自带时间戳，不能代替当前运行状态。
