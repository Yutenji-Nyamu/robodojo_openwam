# 可复核的轻量证据

- [runs.csv](evidence/runs.csv)：八次真实容量 probe 的配置、状态、回合和资源摘要；七次 completed，一次 timed_out。
- [groups.json](evidence/groups.json)：已完成组的联合窗口、总动作、整卡资源和四卡 ETA 场景。
- 每个 `evidence/runs/<alias>/summary.json`：固定口径下的单次测量；完整运行另附 `result.json`，数值与官方结果一致。
- 每个 `resources.csv`：单 run 的 elapsed_s、同组共用起点的 group_elapsed_s、该运行相关 GPU 的匿名角色、整卡显存/利用率、该 worker 进程树 RSS 和累计采样动作数。共用起点保留双 worker 实际约五秒的启动差，未保留绝对时间。GPU 整卡计数包含该卡所有并行 worker，不能将两个 worker 的峰值相加。RSS 可包含重复共享页。
- [PROVENANCE.json](PROVENANCE.json)：原始输入 SHA 与公开文件 SHA、变换说明。原始主机路径和账户不包含在索引中。
- [校验脚本](scripts/check_evidence.py)：离线检查完整结果计数、动作总数、组吞吐和 ETA 的一致性，不启动仿真。

采样通常约两秒；动作时窗边界是观测时间，不是每一步精确执行时刻。旧 N1/N4 没有逐动作时间戳，对应指标留空。N25 的观测动作数不等于正式完成回合数。资源表不含其他卡、进程 PID/UID、主机内存清单、凭据或原始训练恢复计划。

所有数值供核查本轮容量与调度判断；正式全套结果尚未完成时，不据此报告基准成功率。
