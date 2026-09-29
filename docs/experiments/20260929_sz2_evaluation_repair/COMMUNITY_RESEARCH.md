# Dojo GPU 故障：官方与社区依据

2026-09-29。本文记录检索到的原始来源、适用边界和处理依据；实际停止、reset、续跑及回合验收见[执行日志](EXECUTION_LOG.md)。

## 本次能确认什么

SZ2 GPU7出现`Xid109 / CTX SWITCH TIMEOUT`，随后一个worker的7项任务连续`exit139`，另一worker当时仍运行。最新双机比对进一步发现：SZ2 / SZ3在GPU7并行执行`make_toast_random`与`fill_pen_holder`期间，均出现`Xid31 → Xid109`链。任务组合与故障有共同出现的证据，原因尚未定位；没有据此确认硬件损坏、特定驱动回归、模型问题或任务内容单一因果。`exit139`也不能单独证明权限或内存不足。

NVIDIA对H100的Xid109给出的即时恢复动作是reset，后续调查是联系支持。需要先排空目标GPU，再精确重置并验收；不能在同卡另一worker仍活跃时直接执行。来源：[Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html)、[GPU node triage](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html)。

## 官方与社区原始资料

| 来源 | 核查内容 | 本次适用边界 |
|---|---|---|
| [NVIDIA Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html) | 109为Context Switch Timeout；H100即时动作RESET_GPU，调查动作CONTACT_SUPPORT | 支持排空后的局部恢复；错误码不能单独判定坏卡 |
| [GPU node triage](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html) | Hopper + NVSwitch支持单卡重置，不再依赖Fabric Manager | 仍需核验拓扑、目标身份和占用，不能自动扩大到整机 |
| [nvidia-smi官方文档](https://docs.nvidia.com/deploy/nvidia-smi/index.html) | reset需要root；目标设备不能有CUDA、图形、监控进程；重置后需要健康验收，且不保证总能成功 | compute-processes为空或命令返回零都不足以证明安全恢复 |
| [Isaac Sim 5.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html) | H100 / A100无RT Cores，不在支持范围；该版本测试Linux驱动580.65.06 | 本机兼容层跑通不等于官方支持；本轮没有据此擅换系统驱动或渲染协议 |
| [NVIDIA H100 / headless讨论](https://forums.developer.nvidia.com/t/will-isaac-sim-run-on-cloud-h100/261619) | 2026-07-29回复明确headless不改变H100不受支持的边界 | headless不是长跑稳定性的保证 |
| [Omniverse technical requirements](https://docs.omniverse.nvidia.com/dev-guide/latest/common/technical-requirements.html) | 非RTX支持边界；R595需对应产品 / 架构核对；页面列出的shader-compilation修复针对Linux570.144及更早版本 | 未找到直接证明本次595 / H100 / 任务组合的同一已知回归公告，不能照搬别的平台驱动方案 |
| [Xid109社区长讨论](https://forums.developer.nvidia.com/t/xid109-ctx-switch-timeout-driver-crashes-in-many-applications/283722) | 多种Vulkan / CUDA工作负载出现同码；NVIDIA回复记录内部bug5052028并索要复现场景 | 支持保留最小复现与日志；游戏变量和降级建议不能直接用于本批Dojo |
| [IsaacLab issue2309](https://github.com/isaac-sim/IsaacLab/issues/2309) | 集群启动segfault，维护者要求核对推荐驱动并补日志 | 并未证明所有segfault有同一原因 |
| [IsaacSim issue687](https://github.com/isaac-sim/IsaacSim/issues/687) | 社区报告5.1、595.71.05、RTX5090在librtx.scenedb.plugin.so崩溃，checker通过也会发生 | GPU与触发条件不同，仅作旁证；未采用其平台特定改法 |
| [RoboDojo issues](https://github.com/RoboDojo-Benchmark/RoboDojo/issues)、[OpenWAM issues](https://github.com/OpenWAM-Official/OpenWAM/issues) | 查看公开页面并检索H100、Xid109、segmentation、GPU，本轮未定位到可直接套用的已确认修复 | 未定位到不等于上游不存在；部分带查询页面抓取失败也不能作为不存在的证明 |

此前OpenWAM PR37解决的是LRU缓存淘汰的Python KeyError，和当前GPU超时分开记录。补丁依据及验证见[修复说明](REPAIR_NOTES.md)；本轮没有重新验证PR37网页，不把该补丁当成Xid109修复。

## 最小恢复流程与验收

1. 保存supervisor / worker身份、GPU UUID / PCI、Xid时序、结果和恢复点清单；先核清supervisor停止后是否会自动恢复训练，避免任务提前回到故障卡。
2. 停止继续向故障卡派发新任务；只处理身份明确的本批进程，给可正常保存的回合合理退出机会。
3. 目标GPU全部使用者退出后精确reset；若要求连带其他GPU、仍有未知使用者或平台不支持，则停止该分支，不自动扩大范围。
4. 核查GPU健康、新增Xid、真实CUDA / 仿真动作；沿原任务、seed、权重、推理参数和回合预算续跑缺失部分，已有有效回合不重复计数。
5. 验收包含新完成回合、持续动作和旧结果完整性。同卡再现Xid时有界停止并保存证据，不将无限重试或一次reset称为根因修复。

换到已确认空闲且获准使用的GPU可以作为资源映射恢复方案，但必须记录映射变化并保持评估协议。此项为操作建议，不是NVIDIA验证过的本次故障特定修复。需要改变并发、任务配对或驱动的后续对照，应另记实验条件，不混入原批次。

2026-09-29T21:39:32.138162+08:00核验：8路32环境已执行真实动作，包括GPU7吐司和笔筒；1067条旧回合details逐条一致；已完成1071/6300（本次续跑新增4）。模型/任务/seed/预算、源码和controller hash不变。2026-09-29T21:38:58.075531+08:00回查21:28:20重置以来内核，无所查新增Xid/OOM/I/O错误。完整评估仍在进行，故障根因尚未确定。 这些核验支持“已恢复运行”，不支持“根因已消除”。
