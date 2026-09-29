# 两机 Dojo 记录的发布范围

2026-09-29本轮审计直接读取公开 GitHub 分支与完整 tree。审计时 `main` 和 `codex/openwam-robodojo` 均为 `64e43bcc3036ca68091347530225d657df18feb0`；`codex/sz3-dojo-openwam-pi05` 为 `4adc41e6c616d32660d597f2d7b5d5ea4eba13da`，两棵 tree 均未截断。以下明确区分历史已发布与本次待补录。

| 节点 / 阶段 | 粗细记录及证据 | 历史公开 commit |
|---|---|---|
| SZ2 09-28安装、595兼容、叠碗首成功 | RUN_LOG、EXECUTION_LOG、环境 / 结果 / 媒体摘要 | `ae9114f8` |
| SZ2夜间并发测量、6300计划 | 协议、EXPERIMENT_LOG、controller、资源 / 结果记录 | `1d3e375a` |
| SZ2上午资产展开与恢复点修复 | RECOVERY、评估说明、STATUS、粗日志更新 | `332a7072` |
| 模型 / seed / 官方资源准备 | 四个专题、来源与榜单JSON、粗细核查说明 | `64e43bcc` |
| SZ2下午权限、缓存、端口修复 | 本次补充[修复说明](REPAIR_NOTES.md)和[细日志](EXECUTION_LOG.md)，原始回执保留 | 审计时尚未公开 |
| SZ2晚间GPU7故障与恢复 | 本次补充[修复说明](REPAIR_NOTES.md)、[细日志](EXECUTION_LOG.md)、[社区资料](COMMUNITY_RESEARCH.md) | 本目录补录，恢复结果见STATUS与执行日志 |
| SZ3安装、EGL / CUDA、首成功与训练恢复 | EXPERIMENT_LOG、EXECUTION_LOG、原生结果、录像、reset / 归还证据 | `b60d81b4`失败记录，`d82ad413`成功归档 |
| SZ3正式6300准备和两次启动修复 | README、EXECUTION_LOG、LAUNCH_STATUS、controller、压力复现和启动证据 | `50aab2b2`准备，`4adc41e6`启动 |

SZ3两个实验目录已在同一仓库的SZ3分支发布，但不在审计时的main。这次通过固定commit链接串联，不将“默认分支没有”误写成“没有上传”。

- [SZ2历史目录](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/64e43bcc3036ca68091347530225d657df18feb0/docs/experiments)
- [SZ3双模型首成功与粗细记录](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/d82ad41399e13177c381d937d6a7fa4321577d47/docs/experiments/20260929_sz3_openwam_pi05)
- [SZ3正式π0.5评估启动与修复](https://github.com/Yutenji-Nyamu/robodojo_openwam/tree/4adc41e6c616d32660d597f2d7b5d5ea4eba13da/docs/experiments/20260929_sz3_pi05_full)

本次轻量发布只取审过的文档、脱敏状态 / 检查摘要和可复用最小源码。私有绝对路径使用PROJECT / RUN标签；原始进程环境、系统报告、一次性执行入口、模型 / 资产 / 全量视频不纳入。若公开源码作脱敏转换，需分别记录部署文件与公开副本的hash。

发布在独立checkout执行，固定运行源码与已有实验结果不因文档提交改变。发布前重核base、严格清单、文本脱敏、相对链接、diff检查和远端SHA；旧发布脚本绑定旧base与唯一回执，不能重复执行。

本目录补齐下午与晚间缺口；实际提交SHA可由本目录Git历史查看，发布后另核main和codex/openwam-robodojo远端引用一致。此次仅新增本目录文件，没有改运行checkout或删除实验结果。
