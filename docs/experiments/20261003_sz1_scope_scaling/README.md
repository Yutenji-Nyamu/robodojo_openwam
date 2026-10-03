# RoboDojo 历史记录发布包

本包收录七份本地记录的脱敏副本，整理日期为 2026-10-03。记录中的“当前”“已通过”“尚未完成”等用语均对应各段标明的原始时间；本次整理没有刷新服务器状态，也不增加任何当前 smoke、GPU 稳定性或正式评估完成结论。

| 文档 | 内容与阅读位置 |
| --- | --- |
| [卡位修复与双模型测试](docs/GPU_SCOPE_FIX_20261003.md) | 10 月 3 日晚 EGL 卡位限制、4/6 卡测试与 5/7 卡正式续评的历史验收 |
| [GPU4 扩容与恢复](docs/SCALING_GPU4_20261003.md) | 3 卡迁至 4 卡后的测试方案、监督交接与尚待发生的恢复验收 |
| [GPU3 扩容历史](docs/SCALING_GPU3_20261003.md) | 已被后续授权替代的 N9/16/25/36 方案；中止记录完整保留 |
| [GPU3 N4/N9 对照](docs/PARALLEL_GPU3_20261003.md) | 完整九布局比较、吞吐与显存、ANSI 计数误报及独立验收 |
| [GPU7 故障与修复审计](docs/DOJO_GPU7_AUDIT_20261002.md) | 首个坏状态、已有修复作用、诊断通过范围与未确定的根因 |
| [深圳1续评时间线](docs/SZ1_CONTINUATION_20261001.md) | 准备、取消、迁移、借还、故障、恢复及后续授权的原始时间线 |
| [10月3日阶段评估回顾](docs/REVIEW_20261003.md) | 固定时点资源、完成覆盖、seed0分数与正式协议限制 |

文档间引用使用包内相对路径。包外本地日志、脚本、回执、旧报告及历史个人仓库附件仅作文字来源说明；它们没有复制进本包。官方公开资料链接保留，以支持原记录的来源追溯，不表示本次重新核验这些网页。

个人用户名、组名、UID、个人 GitHub 账号地址与私有绝对路径已替换。`SERVER_PROJECT`、`SERVER_CACHE`、`SERVER_HOME` 与 `LOCAL_EVIDENCE` 是脱敏标识，不是实际可访问路径。源文档未发现服务器 IP 地址；软件版本号保持。任务名、GPU编号、运行ID、PID/start、版本/commit、时间、资源数值、失败记录和结论保持；这些历史标识不授权任何操作。

[manifest.json](manifest.json) 逐项记录来源逻辑路径、原始 SHA256/字节数与发布副本 SHA256/字节数。来源文件只读，未修改；清单用于核验此次复制的内容来源和发布副本。


## Deployed source and evidence snapshot

46 deployed helper/source files are included under `source/`, with original/public SHA256 in `SOURCE_MANIFEST.json`. 630 compact logs and JSON receipts are included under `evidence/`. Eight larger streams remain on the server and are explicitly indexed, not claimed as uploaded. This snapshot includes failures and interruptions; active scaling/formal jobs are not labelled complete. Paths and account identifiers are redacted in public text. The original running checkout was not modified by publication.
