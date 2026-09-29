# 细粒度执行记录

2026-09-29，UTC+08:00。以下保留事件、证据标签、检查结果和失败尝试；`PROJECT` / `RUN` / `ATTEMPT` 是脱敏标签。标签对应保留的原始回执，不代表本目录包含完整系统日志。未完成事项明确标为 pending。

| 时间 / 阶段 | 操作与结果 | 证据索引 |
|---|---|---|
| 02:14 | 原6300批次资产校验失败；6530个工作树文件仍为 LFS 指针，正式回合0，未借用训练资源 | 上午公开 `RECOVERY_20260929.md` |
| 上午 g003 | 显式展开现有缓存，15365资产全量校验通过，机器人路径更新正常退出 | `g003` |
| 11:00–11:06 | 资源交接发现 checkpoint 回放索引越界；按真实文件选择最近完整点，补全唯一停止回执，独立重试进入评估 | `g007`、`g014`、`g016` |
| 11:14 | 上午恢复和评估说明发布 `332a7072`，新增2 / 修改3 / 删除0；两远端引用回读一致，部署 HEAD 保持原值 | `g031` |
| 11:46 | 模型资料发布 `64e43bcc`，新增6 / 修改0 / 删除0；未修改运行配置 | `h003` |
| 13:59 | 调度退出5，清理未完成，RLT 未自动恢复；部分子进程仍运行，不能把残留进程算作健康调度 | 下午原故障回执 |
| 15:24起 | 精确核验本批进程身份、失败清理与已有结果；此时较早快照392回合，后续核准实际422回合 | `openwam-repair-probe-0929-v1`、`openwam-repair-details-0929-v2` |
| 下午缓存检查 | 原 Python 缓存类复现 KeyError；采用上游 PR37，100次淘汰 / 访问顺序检查通过 | `openwam-repair-cacheaudit-0929-v1`、`openwam-repair-cachecheck-0929-v1` |
| 下午恢复准备 | 处理精确清理竞态，保留422回合，重建有真实详情 / 视频依据的40回合 resume manifest | `openwam-repair-execute-recovery-0929-v1`、`openwam-repair-cleanup-race-0929-v1` |
| 15:52 | 第一次续跑因端口预检失败而退出；按冻结计划自动恢复4组 RLT，并验证首轮 | `openwam-repair-started-0929-v1`、`openwam-repair-port-return-0929-v1` |
| 16:11前 | 14项调度检查、4项结果续跑检查通过；将8端口移出临时端口范围；plan-only 通过，原评估预算不变 | `openwam-repair-retry3-prepared-0929-v1`、`openwam-repair-fixedports-0929-v1` |
| 16:11:02 | 新 ATTEMPT 恢复原 RUN；4组 RLT 借卡停止回执完整，恢复点分别1075 / 1075 / 1025 / 1025，原训练累计3000目标不变 | `openwam-repair-retry3-execute-0929-v1`、`openwam-repair-retry3-started-0929-v1` |
| 16:18–16:24 | 从6路到8路实际动作；最终32环境均执行动作；422份旧回合详情一致，源码 / 控制器 hash 一致，8端口监听 | `openwam-repair-retry3-verified-0929-v3` 至 `v6` |
| 16:20:59 | 随机场景仍有材质编译与 UI 回调日志，但随后动作继续；没有据此误判任务失败 | `openwam-repair-retry3-health-0929-v2` |
| 20:46 | SZ2 快照995 / 6300回合、20个任务-seed满预算；该数字仅为部分结果 | `refresh-current-0929-2045`、`refresh-health-0929-2045` |
| 20:48–20:50 | GPU7 worker6的7项任务INCOMPLETE，合计275预算、16已完成、259待补；worker7当时仍运行。内核Xid109与退出139构成同一故障链，未直接reset | `refresh-worker6-0929-2048`、`refresh-worker6-detail-0929-2050` |
| 本轮双机比对 | SZ2 / SZ3均在GPU7并行执行make_toast_random / fill_pen_holder期间出现Xid31→109；共同触发条件未定 | SZ2 `gpu7-repair-root-inspect-0929`，18:18:16/17首Xid31；SZ3 `p067`，21:03:18首Xid31 |
| 本轮gate预检 | Conda Python没有pidfd API，首次gate创建intent后提前失败，未发信号。改用系统Python后才进入精确停止流程 | `gpu7-recovery-gate-0929` |
| 21:15–21:29 | 旧controller清理、C3自动归还与四路首轮验证、新C4停机、21:28单卡reset、21:29原批次续跑 | `gpu7-recovery-gate-systempy-0929`、`gpu7-c3-progress-0929-2126`、`gpu7-c4-prepare/stop/reset/launch-0929` |
| 2026-09-29T21:39:32.138162+08:00 | 2026-09-29T21:39:32.138162+08:00核验：8路32环境已执行真实动作，包括GPU7吐司和笔筒；1067条旧回合details逐条一致；已完成1071/6300（本次续跑新增4）。模型/任务/seed/预算、源码和controller hash不变。2026-09-29T21:38:58.075531+08:00回查21:28:20重置以来内核，无所查新增Xid/OOM/I/O错误。完整评估仍在进行，故障根因尚未确定。 | `gpu7-c4-verified-0929-v5`、`gpu7-c4-health-0929-v2` |

早期一份 `openwam-repair-details-0929-v1` 文件为空，未当作成功检查；随后非空 `v2` 保留实际结果。失败回执不覆盖，后续尝试有独立标签。

## SZ3 已公开的同类记录

SZ3 s001–s182保留安装、EGL / CUDA登记、仿真崩溃、GPU4 / 6精确reset、双模型单回合成功及RLT恢复首轮验收。正式评估 p001–p064保留完整资产 / 三份权重校验、临时端口失败、exec期间短暂权限错误、400次压力复现和13项检查、独立重试与8 worker实际动作证据。它们已发布在SZ3分支：[双模型粗细记录](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/d82ad41399e13177c381d937d6a7fa4321577d47/docs/experiments/20260929_sz3_openwam_pi05)、[正式评估执行日志](https://github.com/Yutenji-Nyamu/robodojo_openwam/blob/4adc41e6c616d32660d597f2d7b5d5ea4eba13da/docs/experiments/20260929_sz3_pi05_full/EXECUTION_LOG.md)。

## 本次发布清单与核验

本目录包含粗细文档、当前STATUS、检查与尝试摘要、源码manifest及6份可复用最小源码。只在独立publication checkout按清单提交；源码hash见evidence/source-manifest.json，当前进展和预算见STATUS.json。实际提交SHA以本目录Git历史及独立发布回执为准；发布不会改变运行checkout。完整6300尚未完成。
