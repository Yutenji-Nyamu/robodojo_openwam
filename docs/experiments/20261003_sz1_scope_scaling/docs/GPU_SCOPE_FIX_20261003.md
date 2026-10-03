# 深圳1图形卡位修复与双模型并发测试

> 发布副本：以下保留来源文件各时间点的历史记录；未刷新服务器状态，未新增运行或 smoke 验收结论。个人路径以通用标识替代；本地证据与历史公开仓库附件未随包提供。
> [返回索引](../README.md)

**20:14:55最终启动验收：** 0/1/2/3全C/G进程表均空；4卡OpenWAM N16全部16环境各20步（320动作），之后自动25→36，采样显存峰42.85GiB；6卡π0.5 N4已5209动作并跨批运行，之后自动9→16→25→36，采样峰36.14GiB。5正式插充电器四环境306/400步；7已完成新的general_pickup批次并进入随机吐司初始化，旧/新场景进程都只在7卡。见s047–s048。4/5当前共同路由身份已同步，旧维护错误与旧owner均为历史。

2026-10-03，用户授权先恢复4–7卡Dojo测试与评估，0–3留空；RLT低优先级，原终态接替链保留，不额外做RLT训练试验。

## 已验证的修复

原先主计算和Vulkan渲染已经选4–7，但每个仿真进程仍在0卡创建7MiB EGL辅助上下文。CUDA_VISIBLE_DEVICES和renderer/activeGpu并不能约束这条EGL设备选择路径。

使用当前575.57.08驱动正式支持的`EGLVisibleDGPUDevices`：本人账户`SERVER_HOME/.nv/nvidia-application-profiles-rc.d/95-dojo-scope-20261003.json`按独有进程名`dojo-scope-g4`至`g7`分别限制到物理4/5/6/7。私有`sitecustomize.py`仅在显式DOJO_GPU_SCOPE与PYTHONPATH下设置该名字；原Dojo任务、模型、物理、相机、布局和评估源码没有改变。

末尾账户默认规则将新EGL上下文限定到4–7，防止未带标记的我方程序使用0–3；不影响其他用户，不修改驱动、共享Ray、CUDA或Vulkan选卡。它可能把默认辅助上下文放到4，因此正式Dojo仍应逐卡带单卡规则，避免干扰空卡归还检查。以后若明确获准使用0–3，应同步调整此账户规则，不能仅修改CUDA_VISIBLE_DEVICES。

验证结果：

- Vulkan小探针仍枚举8张NVIDIA卡，明确选择4时只在4创建设备；保持原物理renderer索引，未改为逻辑0。
- EGL小探针只见目标NVIDIA设备，真实OpenGL上下文仅在4卡7MiB；模拟改名的账户默认探针只见4台设备，仍只在4创建上下文。
- 4卡真实OpenWAM、瓶子放垃圾桶、seed0、N4诊断完成4回合和1669动作，退出0，4结果和三路视频保存。头相机第100帧640×480，像素标准差59.17，人工查看为真实场景。该独立诊断不计入正式6300。
- 20:05完整C/G进程表显示0–3均无进程；当时5卡旧正式进程自然换场景后在4卡留下7MiB，正在逐卡调整其启动标记。6卡已启动π0.5并发测试，7卡已按原结果续评。

这次解决的是附带图形上下文越出指定卡的问题，不构成CUDA700或H100长期稳定性的根治证明。

## 测试协议与恢复

**20:10最新执行：** 4/5唯一owner已交接为3580494/start391608903，使用原O/status.json与owner.lock；4卡输出`runs/sz1-gpu4-scoped-scaling-20261003-v1`，维护目录`runs/gpu4-scope-maintenance-20261003-v2`。5卡新正式controller3578093已按原config/run_id恢复。6卡owner3544747/start391527513，维护目录`runs/gpu6-scope-maintenance-20261003-v1`，测试输出`runs/sz1-gpu6-pi05-scaling-20261003-v1`。7卡owner3550893/start391545546，维护目录`runs/gpu7-scope-maintenance-20261003-v1`，原gpu7-physics-v1结果续评；旧单次诊断没有重放。以上均有固定host-key现场回执，旧owner均已精确退役，不重放、不SIGCONT。

4短诊断结束后，5的新场景默认辅助上下文落4，原维护程序遵从全进程空卡检查而停在PROBE_RECOVERY。已严格核4诊断完成/释放、原结果未变、两个guard空，再交接5单卡维护；5加单卡标记重启后，4健康空闲检查通过，直接启动长测，没有额外重跑4正式模型。

4卡OpenWAM已完成的原N9/50回合保留；原N16由用户授权的卡位维护中断，不当作完整性能结果。下一序列为N16→25→36，每档同瓶子任务、seed0、原生50回合。

6卡π0.5新增N4→9→16→25→36，同瓶子任务、seed0、每档原生50回合；继承sim/checkpoint59999、joint、chunk50、denoise10，未覆盖原缓存或模型参数。两模型的测试结果各自独立；5卡OpenWAM、7卡π0.5继续正式W1/N4续评。

每档5400秒上限；显存70GiB、节点可用内存128GiB为停止线；记录真实活跃环境、动作、耗时、GPU利用率、显存、进程树PSS与完整结果。GPU致命错误停止扩容；健康释放后恢复同卡原正式配置与结果断点。测试中断不增加正式评估预算。

维护监督接管原owner锁、精确PID/start/UID和既有RLT周期，暂停前保全小型结果JSON，恢复前核对；不重新执行prepare/stop，不计算大资产或视频哈希。RLT helper、plan、checkpoint及nextsix队列保持原样，尚未发生本轮实际RLT归还。应用定时任务继续取消。

## 依据与证据

- [NVIDIA 575.57.08应用配置](https://download.nvidia.com/XFree86/Linux-x86_64/575.57.08/README/profiles.html)：commname、规则顺序、空pattern及EGLVisibleDGPUDevices按minor位限制。
- [Isaac Sim选卡配置](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_faq.html)：主渲染设备与multiGpu配置；已有正确配置不能代替EGL限制。
- [NVIDIA容器工具同类实现](https://github.com/NVIDIA/nvidia-container-toolkit/pull/1939/files)：应用配置用于图形可见设备约束；本次未迁移容器。

轻量证据在`LOCAL_EVIDENCE/dojo-sz1/steps/`：s008 Vulkan、s012 EGL真实上下文、s019/s027测试预检、s026首次真实动作、s032默认规则、s033四回合完成、s039真实视频与全卡进程表、s040–s044精确交接/5恢复/4长测派发。临时维护过程中s034/s035因4卡仍被精确归属5卡的辅助图形上下文占用而拒绝启动，未越过空卡检查；相应旧PROBE_RECOVERY已由新owner接管，不代表当前任务失败。
