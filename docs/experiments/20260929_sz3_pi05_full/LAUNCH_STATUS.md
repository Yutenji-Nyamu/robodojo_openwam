# 正式启动现场

记录时间：2026-09-29T15:55:25.954938+08:00。当前批次 `sz3_pi05_official_6300_n4_dual_20260929_r2`，状态 **EVALUATING**。8个策略服务、8个仿真worker，每worker4环境；GPU4–7。

官方预算54配置 × 3个seed，原生25/50回合，总6300。当前落盘 0 回合，成功 0，视频 0；这里只是启动现场，完整任务验收和最终官方汇总以跑完后的result-audit为准。

全部8个worker的4个环境均已实际推进动作。当前步骤：

| worker | 任务 | env0 | env1 | env2 | env3 |
|---|---|---:|---:|---:|---:|
| worker0 | imitate_sorting_sequence | 172 | 172 | 172 | 172 |
| worker1 | play_tic_tac_toe | 148 | 148 | 148 | 148 |
| worker2 | pour_by_language | 97 | 97 | 97 | 97 |
| worker3 | fasten_screws | 252 | 252 | 252 | 252 |
| worker4 | play_stacking_toy | 306 | 306 | 306 | 306 |
| worker5 | classify_objects_by_language | 195 | 195 | 195 | 195 |
| worker6 | classify_objects | 197 | 197 | 197 | 197 |
| worker7 | build_tower | 254 | 254 | 254 | 254 |

| GPU | 显存 MiB | 总显存 MiB | 瞬时利用率 % |
|---:|---:|---:|---:|
| 4 | 71713 | 81559 | 0 |
| 5 | 74234 | 81559 | 87 |
| 6 | 71890 | 81559 | 31 |
| 7 | 72429 | 81559 | 10 |

整机内存可用 1690.52 GiB / 2014.92 GiB。各seed权重ready：seed0=True, seed1=True, seed2=True。进入每个seed前再次核验固定manifest与实际文件。

部署源码锁 `50aab2b28298db42c4b25c59c8967eae8d91e84c`；当前控制器源码及hash见 controller/ 与 evidence/plan-preflight.json。日志发布使用独立checkout，运行时的源码HEAD、配置和controller保持不变。

前两次尝试均回合0：第一次临时端口冲突；第二次Linux exec期间进程environ短暂不可读。修复为范围外固定端口，以及每次重新读取身份的有界重试。400次并发exec复现从49错误降至0，13项控制器检查通过；持续权限错误仍报错。两次失败均已清理并自动派发RLT恢复，失败日志保留。

当前RLT暂借四卡，已固定有效CP25及原累计3000轮实配。Dojo结束/中断/基础设施错误后，监督器先核全部本批进程与GPU释放，再自动恢复四组RLT；共享Ray和其他用户未操作。

产物包括每任务原生_result.json、三路相机MP4、每worker启动/推理日志、GPU/内存采样、逐seed summary及最终官方汇总。当前无法由启动阶段可靠估计整个跨任务耗时，π0.5批接口内部逐环境推理，不套用OpenWAM吞吐。
