# SZ3：RoboDojo + OpenWAM / π0.5 部署记录

截至2026-09-29 13:58，三套环境与两份官方权重已就绪，π0.5策略服务加载检查通过；Isaac Sim在任务初始化前触发GPU上下文切换超时。**本目录没有成功回合或成功视频，不计入模型成功率。**

目标是先复现SZ2的OpenWAM叠碗成功回合，再切换同一仿真环境到官方π0.5。固定源码，使用独立数据盘目录；模型和仿真环境分离。首回合配置为`stack_bowls / arx_x5 / seed 0 / layout 0 / num_envs 1 / eval_num 1`，OpenWAM使用`ee`，π0.5使用`joint`。

| 项目 | 实际结果 |
|---|---|
| Isaac Sim5.1 / IsaacLab / cuRobo | 官方安装完成，GLU已补齐；真实任务尚未启动成功 |
| OpenWAM | 官方Dojo专用checkpoint加载完成两次；仿真前置失败，无任务结果 |
| π0.5 | 官方Dojo seed0、step59999 checkpoint加载完成；48秒内服务ready，GPU观察值24,880MiB，随后按计划释放 |
| EGL厂商注册 | 项目内补标准JSON后，Vulkan探针由-9变为正常枚举8张H100 |
| CUDA/NVML库名 | 本机缺无版本链接；strace确认加载失败，只在项目内补链接到现有595.71.05库 |
| 真实仿真 | GPU1/2/3独立短测试均出现`ERROR_DEVICE_LOST`，部分本轮PID有Xid109内核记录；均未完成SimulationApp构造 |

当前阻塞属于仿真图形端。NVIDIA的Xid目录建议109错误先重置GPU；本机其他训练进程也持有目标设备句柄，因此本次**没有执行GPU重置、停训或整机重启**。IOMMU启动参数存在两机差异，但尚无证据将其认定为根因。[NVIDIA Xid目录](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html)、[单卡重置条件](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html)。

详见[粗日志](EXPERIMENT_LOG.md)、[执行记录](EXECUTION_LOG.md)和`evidence/`。权重、资产、完整私有原始日志与环境目录不纳入Git。本分支保留上游代码与许可证；根README沿用原仓库。

官方入口：[RoboDojo安装](https://robodojo-benchmark.com/doc/usage/install-and-download/)、[评测流程](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)、[π0.5适配目录](https://github.com/XPolicyLab/XPolicyLab/tree/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05)、[OpenWAM权重](https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo)。
