# RoboDojo 多模型复现准备 · 2026-09-29

此次整理 π0、π0.5、FastWAM 在 RoboDojo 上的官方适配、权重、成绩与部署顺序；当前 OpenWAM 评测继续运行，三个新增模型尚未部署。

| 阅读目的 | 文档 |
|---|---|
| 先看公开成绩、可部署性与实施顺序 | [总览与规划](MODEL_COMPARISON_PLAN_20260929.md) |
| 3 seed、50回合究竟改变什么 | [seed与布局](SEEDS_AND_EPISODES_20260929.md) |
| π0 / π0.5 权重、安装、动作及命令 | [π系列](PI0_PI05_OFFICIAL_20260929.md) |
| FastWAM 专用Dojo权重、配置及命令 | [FastWAM](FASTWAM_OFFICIAL_20260929.md) |
| 当前官网数值留档 | [榜单快照](leaderboard_snapshot.json) |

## 粗日志

2026-09-29核查官网、固定源码和官方dataset仓库。三个模型均找到Dojo专用发布权重；FastWAM安装示例仍指向RoboTwin，要用Dojo下载器及配套stats。π0/FastWAM默认单环境，π0.5虽接多环境但逐个模型推理，各模型并行需独立实测。建议先π0.5，再π0，再FastWAM，沿现成仿真链路直接做真实推理。

## 细日志与核查边界

1. 内置浏览器读取官方榜单Sim、RealWorld和协议，保存本目录数值快照；逐项来源见专题固定链接。
2. 对照RoboDojo固定源码与官方布局JSON，确认eval_seed选择目录、layout_id选择回合、泛化25+25、unstable单列和_result逐批更新。
3. 对照XPolicyLab固定commit与HF固定revision，读取脚本、部署配置、文件树和小型stats；记录checkpoint体积/哈希、seed对应关系、相机与动作顺序、归一化和batch实现。
4. 11:36:05只读刷新现有OpenWAM：8 worker×4环境运行，27有效完成/3成功，另1 unstable；6增量结果与177视频路径约439MB。原始证据标签h001-model-planning-live-check，exit0；身份和host-key校验通过。
5. 新模型尚未安装、下载大权重或启动。仅将审阅后的六份轻量文档/JSON在独立发布checkout提交；实际评测源码与模型配置保持原版本。

这些文档区分官方公开成绩、元数据检查与本机实测。后续从固定版本和命令模板继续，并追加实际执行回执。
