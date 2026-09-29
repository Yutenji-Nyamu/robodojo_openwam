# SZ3：RoboDojo + OpenWAM / π0.5 首次成功

2026-09-29，深圳3已使用官方 RoboDojo 专用权重，分别完成 **π0.5 和 OpenWAM 的一个成功叠碗回合**，两个程序均正常退出并产出头部、左腕、右腕三路成功视频。

| 模型 | 原生任务结果 | 三路视频规格 | 详情 |
|---|---|---|---|
| π0.5 | 1 回合，成功，阶段分 100 | 各 279 帧，25 fps，640×480，11.16 秒 | [π0.5 里程碑与视频](MILESTONE_pi05.md) |
| OpenWAM | 1 回合，成功，阶段分 100 | 各 320 帧，25 fps，640×480，12.8 秒 | [OpenWAM 里程碑与视频](MILESTONE_openwam.md) |

共同设置为 `stack_bowls / arx_x5 / seed 0 / layout 0 / num_envs 1 / eval_num 1`。π0.5 使用官方 `sim`、seed0、step59999 权重和 `joint` 动作；OpenWAM 使用 `OpenWAM-Alpha-Sim-RoboDojo` 权重和 `ee` 动作。两份原生结果均为 `eval_time=1`、`success_rate=1`、`score=100`，对应回合的 `success=true`。

**这是各一个回合的部署成功里程碑，不是 RoboDojo 完整基准成功率，也不用于比较两模型总体能力。**

本机沿官方安装和评测入口执行，在独立目录中固定源码、子模块、环境与权重。初期遇到缺失的 EGL 登记与驱动库名链接，按已有日志在项目内补齐；NVIDIA 595 的 Vulkan allocation-limit 兼容处理仅作用于仿真进程。随后仍出现 Xid109，GPU4 精确单卡重置后，同配置短测恢复；GPU6 在空闲状态下也做了单卡重置，两个模型随后完成真实回合。最初触发 Xid109 的根因尚未证实。

用户授权临时将 GPU4–7 从本人 RLT 切给 Dojo：OpenWAM 使用 GPU4 仿真、GPU5 策略，π0.5 使用 GPU6 仿真、GPU7 策略。Dojo 结束后，监督器已确认全部本次进程退出、四卡释放，并自动派发四组 RLT 从有效 checkpoint 25 恢复。14:43:07 恢复 helper 返回 0；14:54 四组均验收通过，真实采集已从 checkpoint 25 推进至第26轮，回放池继续增长。当前仍处于原有 teacher warmup 阶段，累计3000轮目标和实配保持不变。共享 Ray、其他用户实验、系统驱动和服务器启动配置保持原状。

阅读入口：

- [切换 RLT、单卡 reset、资源归还与自动恢复](CUTOVER_AND_GPU_RESET.md)：本次恢复仿真与完成回合的直接证据。
- [粗日志](EXPERIMENT_LOG.md)：安装与早期排障的经过、判断和结果。
- [细粒度执行记录](EXECUTION_LOG.md)：分步操作与回执索引，包含失败尝试。
- `evidence/`：经过筛选的版本与轻量证据；权重、资产、环境、私有原始日志不纳入 Git。

官方依据：[RoboDojo 安装](https://robodojo-benchmark.com/doc/usage/install-and-download/)、[官方评测流程](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)、[π0.5 适配目录](https://github.com/XPolicyLab/XPolicyLab/tree/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05)、[OpenWAM 官方权重](https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo)。

本分支保留上游代码、署名和许可证；本目录集中维护 SZ3 的部署与复现记录。
