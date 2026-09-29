# 细粒度执行记录

时间为UTC+8；每行链接是实际执行的命令，返回状态/时间/命令SHA256见evidence/execution-receipts.json。p061–064补齐上次公开启动之后的核验；p065起为本次故障定位和恢复。完整stdout/stderr留本地受限证据目录，公开GPU/结果证据经过筛选。失败步骤同样保留，禁止直接重放旧PID/cycle。

| 步骤/实际命令 | 开始 | 结束 | 退出码 | 固定主机与身份 |
|---|---|---|---:|---|
| [p061-stage-32-env-launch](commands/p061-stage-32-env-launch.sh) | 15:56:07 | 15:56:08 | 0 | 已核验 |
| [p062-publish-confirmed-launch](commands/p062-publish-confirmed-launch.sh) | 15:56:30 | 15:56:41 | 0 | 已核验 |
| [p063-final-runtime-identity](commands/p063-final-runtime-identity.sh) | 15:57:05 | 15:57:05 | 0 | 已核验 |
| [p064-final-status](commands/p064-final-status.sh) | 16:00:30 | 16:00:31 | 0 | 已核验 |
| [p065-evening-audit](commands/p065-evening-audit.sh) | 21:10:33 | 21:10:42 | 0 | 已核验 |
| [p066-evening-identity](commands/p066-evening-identity.sh) | 21:11:03 | 21:11:04 | 0 | 已核验 |
| [p067-evening-gpu-diagnostic](commands/p067-evening-gpu-diagnostic.sh) | 21:11:55 | 21:11:56 | 0 | 已核验 |
| [p068-exact-gpu7-recovery](commands/p068-exact-gpu7-recovery.sh) | 21:15:26 | 21:15:35 | 1 | 已核验 |
| [p069-cleanup-diagnostic](commands/p069-cleanup-diagnostic.sh) | 21:16:15 | 21:16:15 | 0 | 已核验 |
| [p070-prepare-gpu7-recovery](commands/p070-prepare-gpu7-recovery.sh) | 21:17:54 | 21:17:54 | 0 | 已核验 |
| [p071-validate-preserve-resume](commands/p071-validate-preserve-resume.sh) | 21:18:54 | 21:19:31 | 0 | 已核验 |
| [p072-reborrow-exact-rlt](commands/p072-reborrow-exact-rlt.sh) | 21:21:15 | 21:22:08 | 0 | 已核验 |
| [p073-reset-idle-gpu7](commands/p073-reset-idle-gpu7.sh) | 21:22:23 | 21:22:31 | 0 | 已核验 |
| [p074-check-native-resume-counters](commands/p074-check-native-resume-counters.sh) | 21:23:22 | 21:23:23 | 0 | 已核验 |
| [p075-launch-same-protocol-continuation](commands/p075-launch-same-protocol-continuation.sh) | 21:23:46 | 21:23:46 | 0 | 已核验 |
| [p076-continuation-startup](commands/p076-continuation-startup.sh) | 21:24:54 | 21:24:55 | 0 | 已核验 |
| [p077-post-reset-kernel](commands/p077-post-reset-kernel.sh) | 21:26:06 | 21:26:06 | 0 | 已核验 |
| [p078-continuation-actions](commands/p078-continuation-actions.sh) | 21:27:11 | 21:27:11 | 0 | 已核验 |
| [p079-continuation-actions](commands/p079-continuation-actions.sh) | 21:28:46 | 21:28:46 | 0 | 已核验 |
| [p080-continuation-progress](commands/p080-continuation-progress.sh) | 21:29:56 | 21:29:57 | 0 | 已核验 |
| [p081-post-reset-kernel](commands/p081-post-reset-kernel.sh) | 21:29:58 | 21:29:58 | 0 | 已核验 |
| [p082-continuation-progress](commands/p082-continuation-progress.sh) | 21:31:12 | 21:31:13 | 0 | 已核验 |
| [p083-recovery-artifacts](commands/p083-recovery-artifacts.sh) | 21:32:36 | 21:32:37 | 0 | 已核验 |
| [p084-continuation-progress](commands/p084-continuation-progress.sh) | 21:33:05 | 21:33:06 | 0 | 已核验 |
| [p085-continuation-progress](commands/p085-continuation-progress.sh) | 21:37:32 | 21:37:33 | 0 | 已核验 |
| [p086-continuation-progress](commands/p086-continuation-progress.sh) | 21:38:29 | 21:38:30 | 0 | 已核验 |
| [p087-post-reset-kernel-final](commands/p087-post-reset-kernel-final.sh) | 21:38:41 | 21:38:41 | 0 | 已核验 |
