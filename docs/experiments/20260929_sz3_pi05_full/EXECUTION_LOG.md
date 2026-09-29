# 细粒度执行记录

逐步命令回执；正式启动现场另存 LAUNCH_STATUS.md。时间为UTC+8。失败步骤保留，未完成的启动不计为健康评测。

| 步骤 | 开始 | 结束 | 退出码 | 身份/固定host-key |
|---|---|---|---:|---|
| p001-sz3-live | 15:00:53 | 15:00:57 | 0 | 已核验 |
| p002-sz2-reference | 15:01:58 | 15:01:59 | 0 | 已核验 |
| p003-sz2-controller-diagnostic | 15:02:35 | 15:02:35 | 0 | 已核验 |
| p004-start-extra-checkpoints | 15:04:40 | 15:04:41 | 0 | 已核验 |
| p005-download-progress | 15:05:17 | 15:05:17 | 0 | 已核验 |
| p006-formal-prepare-directories | 15:07:45 | 15:07:45 | 0 | 已核验 |
| p007-formal-cpu-checks | 15:08:44 | 15:08:48 | 0 | 已核验 |
| p008-formal-config-rlt-prepare | 15:10:49 | 15:10:54 | 1 | 已核验 |
| p009-preparation-progress | 15:11:47 | 15:11:47 | 0 | 已核验 |
| p010-current-rlt-prepare | 15:11:52 | 15:12:22 | 0 | 已核验 |
| p011-asset-import-detail | 15:12:23 | 15:12:24 | 0 | 已核验 |
| p012-stop-asset-transfer-for-resume | 15:13:41 | 15:13:42 | 0 | 已核验 |
| p013-assets-retry-progress | 15:15:12 | 15:15:12 | 0 | 已核验 |
| p014-seed-readiness-regression | 15:15:56 | 15:15:59 | 0 | 已核验 |
| p015-formal-plan-check | 15:16:40 | 15:16:41 | 0 | 已核验 |
| p016-process-identity-checks | 15:17:38 | 15:17:42 | 0 | 已核验 |
| p017-readiness-progress | 15:18:22 | 15:18:22 | 0 | 已核验 |
| p018-preparation-status | 15:21:57 | 15:21:57 | 0 | 已核验 |
| p019-preparation-status | 15:22:56 | 15:22:56 | 0 | 已核验 |
| p020-stage-formal-publication | 15:24:49 | 15:24:53 | 1 | 已核验 |
| p021-stage-formal-publication-retry | 15:26:31 | 15:26:34 | 0 | 已核验 |
| p022-preparation-status | 15:26:38 | 15:26:38 | 0 | 已核验 |
| p023-publish-formal-preparation | 15:27:08 | 15:27:16 | 0 | 已核验 |
| p024-stop-rlt-for-formal | 15:27:29 | 15:28:23 | 0 | 已核验 |
| p025-reset-formal-idle-gpus | 15:28:42 | 15:28:51 | 1 | 已核验 |
| p026-reset-remaining-idle-gpus | 15:29:36 | 15:29:57 | 0 | 已核验 |
| p027-launch-formal-pipeline | 15:30:17 | 15:30:18 | 0 | 已核验 |
| p028-formal-startup-status | 15:30:38 | 15:30:39 | 0 | 已核验 |
| p029-port-conflict-readonly | 15:31:20 | 15:31:21 | 0 | 已核验 |
| p030-prepare-status-checkout | 15:31:54 | 15:31:55 | 0 | 已核验 |
| p031-prepare-formal-retry | 15:32:47 | 15:33:17 | 0 | 已核验 |
| p032-stop-rlt-for-formal-r1 | 15:34:10 | 15:35:01 | 0 | 已核验 |
| p033-reset-formal-r1-idle-gpus | 15:36:02 | 15:36:32 | 0 | 已核验 |
| p034-launch-formal-r1 | 15:37:01 | 15:37:02 | 0 | 已核验 |
| p035-formal-r1-startup-status | 15:37:12 | 15:37:12 | 1 | 已核验 |
| p036-formal-health | 15:37:51 | 15:37:51 | 0 | 已核验 |
| p037-formal-health | 15:38:27 | 15:38:27 | 0 | 已核验 |
| p038-formal-r1-failure-detail | 15:38:59 | 15:38:59 | 0 | 已核验 |
| p039-reproduce-guard-exec-race | 15:39:51 | 15:39:54 | 0 | 已核验 |
| p040-reproduce-guard-transition | 15:40:31 | 15:40:33 | 0 | 已核验 |
| p041-prepare-r2-scripts | 15:41:44 | 15:41:44 | 0 | 已核验 |
| p042-test-r2-guard | 15:42:11 | 15:42:17 | 0 | 已核验 |
| p043-prepare-formal-r2 | 15:43:30 | 15:44:07 | 0 | 已核验 |
| p044-stop-rlt-for-formal-r2 | 15:44:26 | 15:45:19 | 0 | 已核验 |
| p045-reset-formal-r2-idle-gpus | 15:46:09 | 15:46:37 | 0 | 已核验 |
| p046-launch-formal-r2 | 15:46:45 | 15:46:45 | 0 | 已核验 |
| p047-weights-and-assets-status | 15:47:19 | 15:47:19 | 0 | 已核验 |
| p048-formal-r2-health | 15:47:54 | 15:47:55 | 0 | 已核验 |
| p049-formal-r2-health | 15:48:33 | 15:48:34 | 0 | 已核验 |
| p050-formal-r2-health | 15:49:33 | 15:49:34 | 0 | 已核验 |
| p051-official-probe-and-processes | 15:50:06 | 15:50:06 | 0 | 已核验 |
| p052-formal-r2-health | 15:50:23 | 15:50:24 | 0 | 已核验 |
| p053-formal-r2-health | 15:51:33 | 15:51:34 | 0 | 已核验 |
| p054-stage-launch-publication | 15:52:02 | 15:52:02 | 0 | 已核验 |
| p055-formal-r2-health | 15:52:16 | 15:52:16 | 0 | 已核验 |
| p056-formal-r2-health | 15:53:16 | 15:53:16 | 0 | 已核验 |
| p057-formal-progress-confirmed | 15:54:13 | 15:54:14 | 0 | 已核验 |
| p058-stage-confirmed-launch | 15:54:42 | 15:54:42 | 1 | 已核验 |
| p059-all-env-steps | 15:55:06 | 15:55:06 | 0 | 已核验 |
| p060-confirm-32-environments | 15:55:25 | 15:55:26 | 0 | 已核验 |

逐步命令hash及回执见 evidence/execution-receipts.json。完整原始命令、stdout、stderr在本地实验归档中保留，不发布账户凭据或进程环境。

主要操作顺序：现场只读核对 → 固定revision下载seed1/2 → 资产从已验证官方Git/LFS对象分段复制并hash检查 → 官方54配置和三seed布局预检 → 精确RLT借卡准备 → 最终13项Dojo和10项RLT CPU检查 → 发布配置和控制器 → 正式切卡启动。命令模板与停止条件见 README。

已遇到的问题：p008匹配Stage1索引被提前校验拒绝，p010限定四个实际clean/combo恢复run后通过；资产SSH rekey超时后保留partial、用每连接最多256MiB续传并最终核hash。深圳2旧控制器的无关不可读/proc进程问题已在深圳3修正，并覆盖PID复用与已知归属进程不可读两种边界。
