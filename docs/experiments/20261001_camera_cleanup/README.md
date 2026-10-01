# 相机关闭修复与原生渲染排查 · 2026-10-01

此分支含最小源码修复，正式评估稳定性尚未验收。

| 问题 | 本轮结果 | 仍未证明的部分 |
|---|---|---|
| 相机关闭字段不一致，解绑未执行，旧引用与回调残留 | 已修；原渲染配置下，同进程两轮 N4 重置、真实 RGB、关闭和再次重建通过 | 不能据此认定历史跨批 CUDA700 已消除 |
| 首次叠碗渲染读取无效 GPU 地址 | 历史转储定位到原生光线追踪；TAA／关闭 DL 去噪的独立候选通过两轮诊断 | 坏地址来源、历史 MMU 的因果和长期修复尚未证明 |

## 最小源码修复

`CameraView` 使用实际创建的 `_render_product` 与 `_annotators`，按“解绑 → 销毁所属渲染产品 → 清空引用 → 父类关闭”收尾；`TiledCaptureManager` 交由相机唯一销毁产品，并清空产品索引和输出缓冲区。

真实 GPU 检查发现 SDK 的 tiled-annotator 解绑会触发 `TypeError: Invalid NodeObj object in Py_Node in getAttributes`。补丁仅对这条完全相同的错误记录警告，继续调用原生产品销毁；其他异常仍抛出。产品的原生图节点与纹理释放已检查。诊断器保留的旧 annotator 中，部分字符串绑定元数据仍存在，不能声称所有旧元数据均已清空。

最终修改 **2 文件，20 行新增／7 行删除**，源码提交 `6dddac88a4fb9a72cbb9d39a90a9850e2ea811a8`，基于 `b96822f333b008ac5bab24ced1fee242865328d2`。没有修改 SDK、全局缓存、图像读取、相机参数、任务、动作预算或正式渲染配置，也没有加入重试、sleep 或 GPU reset。

- [最小补丁](camera-cleanup.diff)
- [脱敏验证摘要与源码 SHA256](VERIFICATION.json)

## 实际验证与限制

服务器 CPU 检查覆盖精确 SDK 异常、其他异常传播和重复关闭。原渲染配置在同一进程完成两轮 `stack_bowls_random / seed1 / N4`，每轮读取 12 张 `640×480` RGB，资源清理与重复关闭通过，进程退出码为 0。独立的 TAA／关闭 DL 去噪候选也通过相同两轮，合计 4 轮、48 张 RGB 快照。

两次诊断使用相同布局索引 0–3；每轮另有 40 次暖机取帧。历史故障的完整布局 ID 未保存，不能称为历史失败样本的精确重放。测试没有加载策略模型、执行动作或生成分数。原渲染配置的短测同样通过，历史 MMU 未复现，因此不能把关闭 DL 去噪认定为根因修复。

H100 不在 Isaac Sim 5.1 的受支持 GPU 范围内。原配置的实际日志提示该构建不支持 H100 的 DLSS-RR；独立候选显式使用 TAA、关闭 DL denoiser 和 DLSSG，其余配置与原测试一致。该候选会改变 RGB 外观，只用于诊断，未并入正式评分。下一步应先用源码补丁验证真实策略、动作和跨批路径，再单独评估渲染候选对图像协议与稳定性的影响。

## 一手来源

- [Isaac Sim 5.1 硬件要求](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [Isaac Sim 5.1 CameraView 源码](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/extensions/isaacsim.sensors.camera/isaacsim/sensors/camera/camera_view.py)
- [NVIDIA 社区：渲染产品销毁](https://forums.developer.nvidia.com/t/how-to-destroy-a-render-product/255637)
- [Stanford OmniGibson 的相邻 tiled-camera 异常处理](https://behavior.stanford.edu/reference/sensors/vision_sensor.html)；相邻实现依据，不是 NVIDIA 对本修复的验收。
- [IsaacLab H100／tiled-camera DEVICE_LOST 报告 #4271](https://github.com/isaac-sim/IsaacLab/issues/4271)；相关线索，不是本现场根因或已验证处方。
- [IsaacLab v2.3.0 渲染配置映射](https://github.com/isaac-sim/IsaacLab/blob/v2.3.0/source/isaaclab/isaaclab/sim/simulation_context.py)
