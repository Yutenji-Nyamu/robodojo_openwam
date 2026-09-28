# 本次 H100 / 595 启动问题

本次保持 H100、595.71.05 驱动、Isaac Sim 5.1，通过官方 OpenWAM 推理完成叠碗。没有更换整机驱动，也没有安装 Isaac 6。

1. 第一轮模型已加载，仿真缺 `libGLU.so.1`，MDL 加载失败并退出139。在自己的仿真 Conda 环境安装 `libglu=9.0.3`，并前置该环境的 `lib` 路径。
2. 第二轮缺库错误消失，仍在 `librtx.scenedb.plugin.so!carbOnPluginStartup+0x3b4de` 退出139。取消 CUDA mask、只运行官方 `SimulationApp` 仍能复现，因此继续检查仿真启动兼容性。
3. 原生 Vulkan 查询显示 `maxMemoryAllocationSize=UINT64_MAX`。使用本仓库保留的 [RoboDawn 兼容脚本](../../../third_party/RoboDawn/README.md)，只在仿真进程查询时把此字段改报4292870144（4 GiB−2 MiB）。同一最小程序构造及5次update返回，退出0。
4. 同一任务、布局、模型和GPU设置第三次运行成功。策略进程不启用该层；系统驱动与其他进程不变。

该字段是单次内存分配上限，不是把整卡显存变成4GB；该层不模拟RT Core，也不替换渲染器。本次验证的是指定回合可以运行，未验证跨渲染设备的像素等价、多环境长期运行或完整基准。

原先另一台575驱动H100的已有运行经验帮助检查动态库、单GPU和CUDA/Vulkan编号。它不能直接解释本机595的崩溃；他人的目录、配置、录像不包含在公开归档中。

575/595内核驱动不能像Conda一样按任务切换；普通同一Linux主机运行时共享一套驱动。Python/Conda/Isaac用户环境可并存。

来源：[IsaacSim #677](https://github.com/isaac-sim/IsaacSim/issues/677)、[Discussion #648](https://github.com/isaac-sim/IsaacSim/discussions/648)、[Vulkan 属性定义](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceMaintenance3Properties.html)、[固定兼容源码](https://github.com/Hugo-AGI/RoboDawn/blob/9247f366cd31f278e10f2fbe5fe8469b5f1b5b94/scripts/robodojo/compat/vulkan_driver_compat.py)。这些社区报告不构成 NVIDIA 官方兼容认证。详见[两次失败与修复日志](RUN_LOG.md)。
