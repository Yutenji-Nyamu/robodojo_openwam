# 深圳1 GPU4扩容测试与原正式评估归还

> 发布副本：以下保留来源文件各时间点的历史记录；未刷新服务器状态，未新增运行或 smoke 验收结论。个人路径以通用标识替代；本地证据与历史公开仓库附件未随包提供。
> [返回索引](../README.md)

用户17:30新指示：只占4–7，0–3空闲；将4卡正式Dojo暂时换为扩容测试，测完原路恢复。此授权替代先前借3卡范围。

## 已完成与执行配置

- 17:31:51，3卡探针owner3232543已按UID/PID/start精确停止并清理，3MiB/recovery None、所属进程0；0–3均无评估计算负载。未完成的N9是人为换卡中止，不记GPU故障或完整比较结果；其证据保留。
- 4卡原正式controller504939/start382019032；5卡507028/start382023251。5/6/7正式评估继续。
- 4卡复用同扩容方案：OpenWAM / put_bottles_into_dustbin / seed0，W1/N9→16→25→36，每档原生50回合，5400秒上限；原相机、chunk32、denoise10、物理与录像保持。显存70GiB、节点可用RAM128GiB为停止线，GPU/PhysX故障不重试。
- 探针脚本`diagnostics/scaling-gpu4-20261003/scale_probe_gpu4.py`，输出`runs/sz1-gpu4-scaling-20261003-v1`，每组单独结果ID，不混正式6300。
- 正式已保存回合/manifest保留，未提交的当前批次由官方续评逻辑补跑。暂停后将小型结果JSON精确备份，并在恢复前复核未变；视频和大权重不逐份哈希。

## 唯一控制交接

旧外层owner没有单卡暂停开关；4 controller退出会立即调用RLT归还。直接停止外层owner又会连同5退出，不能采用。新脚本仅交接监督进程，复用原Owner类及原RLT cycles/configs/ProcessGuard；不重跑prepare/stop，不停5任务。

交接目录：`runs/sz1-dojo-continuation-20261002-v1/gpu4-scaling-20261003-v1`。脚本`diagnostics/scaling-gpu4-20261003/borrow_gpu4.py`由原RLT Python执行。先核原owner3881745/start379867940，短暂停监督并确认仅4/5子controller、无RLT helper；预检成功后精确退役旧监督PID、取得原owner.lock、写新身份。旧owner禁止重放或SIGCONT。

新监督仅暂停4：精确TERM原sweep，保存已完成结果，GPU释放后异步运行测试；同时持续监督原5任务及其RLT归还。测试结束且健康空闲，按原config、原run_id、W1/N4与原6300预算恢复4正式续评。原日志先归档；4正式终态后仍调用原RLT归还。测试若发生致命GPU故障，则停止扩容，不在同卡盲目重启Dojo，仅沿原健康检查路径归还RLT或报告需处理。

17:38与17:42服务器CPU检查及只读交接预检通过：存活/缺失/过期/新鲜终态、错误身份拒绝发信号、源码AST、原正式源码/配置固定摘要、原RLT停止回执。补齐操作取消/异常时精确收尾和健康归还、原生崩溃退出码分类；无法证明健康释放时仍停在NEEDS_ATTENTION，不盲目续评。

17:43:25交接已执行：新唯一监督PID3283651/start390732435，持原owner.lock，旧3881745已退役。4正式controller收到精确停止请求，17:43:43仍在关闭；5原507028身份保持，6/7独立owner不变。0–3无计算进程。证据o007–o009。当前4/5管理仍在原O/status.json，新路由O/active-gpu4-scaling.json；检查`dojo-sz1/gpu4-borrow-status.sh`，不要重放新旧启动入口。

17:44:00，4正式已暂停并释放至8MiB/recovery None，无所属GPU进程；59份结果/manifest JSON已精确备份（不复制视频，不扫描大权重）。随后启动GPU4顺序测试owner3284935/start390735942，N9先执行。17:45:35模型已占24.4GB级显存，仍在初始化，尚未据此认定真实动作；0–3无计算进程，5/6/7原模型与仿真PID保持。暂停与启动回执o010。

**17:48:32换卡验收完成：** GPU4 N9 env0–8各50/700步、累计450真实动作；显存采样峰38.68GiB、PSS峰32.33GiB、recovery None，无错误。N16/25/36仍待顺序执行，尚无完整比较结果。17:46:27正式5/6/7分别307/700、896/1300、588/800步，均为DOJO_RUNNING；原正式累计OW4557/Pi3453（各6300），4暂停在play_tic_tac_toe/seed2，已保存12回合，当前未提交批从断点补跑。证据o011–o013。测试结束健康释放后自动恢复原正式配置已配置，恢复动作尚未发生；最终须检查formal-resumed.json与新4真实动作，不能把配置成功当作归还已验收。

只读快速入口：`dojo-sz1/scaling-gpu4-compact.sh`看测试，`gpu4-borrow-status.sh`看监督/借还回执；原`evaluation-progress-summary.sh`区分4 SCALING_TEST和5/6/7正式。SSH仍session93792，固定host-key，凭据仅进程内。发布状态：本次新借测文档与辅助脚本在本地/服务器留存，尚未发布Git；先前7f887c4仅N4/N9叠碗对照。

## 18:06–18:13 状态与恢复链核查

- N9仍在运行：已保存9/50回合，其中8成功；第二批9环境均到237/700步，累计6131动作。采样显存峰39.22GiB，进程树PSS峰32.33GiB。N16/25/36尚未开始；测试结果独立于正式评估。
- 18:07正式累计OpenWAM 4569/6300、π0.5 3469/6300。4正式暂停；5正在切换下一批，6/7分别345/1300、333–334/800真实步，仍为DOJO_RUNNING。0–3无计算进程，4–7 recovery均None。
- 4/5监督3283651、6监督556492、7监督1088548均存活、UID/PID/start/cmdline身份相符且持有各自owner.lock；旧owner中的6/7历史状态不代表当前6/7。
- 原4已保存的59份JSON/manifest全部未变。`scaling-finished.json`与`formal-resumed.json`尚未产生，因此当前仅确认恢复路径有效配置，尚未发生正式恢复。
- 四卡当前RLT cycle的准备、停止回执、恢复计划与helper均存在；已核选定CP525/525/575/625及每份6个必要元数据/分片文件存在。此次仅检查文件存在，不重读大权重、不重复跑恢复。初次只读检查漏拼`actor/`子目录，p005核实实际结构后，p006更正并四卡全部通过，无服务器修改。
- 测试完成且健康释放后，4按原config/run_id与W1/N4恢复正式6300续评；测试若GPU致命错误则停止扩容，沿健康检查归还RLT。4–7正式Dojo结束或失败后仍精确清理、检查卡健康空闲，再恢复原RLT累计3000并核验首轮。这轮RLT尚未触发归还，不能据配置宣称已恢复。

证据：本地`dojo-sz1/steps/p001-gpu4-test-status`、`p002-return-routes`、`p003-all-dojo-progress`、`p005-cp-layout`、`p006-rlt-checkpoint-presence-fixed`。本轮只读核查与专题记录，未重启或停止任务。

相关：[原3卡计划](SCALING_GPU3_20261003.md)、[前一轮N4/N9结果](PARALLEL_GPU3_20261003.md)。应用定时任务保持已取消，由这次有限顺序程序完成测试和归还。
