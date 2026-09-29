# 细粒度执行记录

截至发布前准备阶段；后续启动现场另存 LAUNCH_STATUS.md。时间为UTC+8。失败步骤保留，未执行的启动不计成功。

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

逐步命令hash及回执见 evidence/execution-receipts.json。完整原始命令、stdout、stderr在本地实验归档中保留，不发布账户凭据或进程环境。

主要操作顺序：现场只读核对 → 固定revision下载seed1/2 → 资产从已验证官方Git/LFS对象分段复制并hash检查 → 官方54配置和三seed布局预检 → 精确RLT借卡准备 → 最终13项Dojo和10项RLT CPU检查 → 发布配置和控制器 → 正式切卡启动。命令模板与停止条件见 README。

已遇到的问题：p008匹配Stage1索引被提前校验拒绝，p010限定四个实际clean/combo恢复run后通过；资产SSH rekey超时后保留partial、用每连接最多256MiB续传并最终核hash。深圳2旧控制器的无关不可读/proc进程问题已在深圳3修正，并覆盖PID复用与已知归属进程不可读两种边界。
