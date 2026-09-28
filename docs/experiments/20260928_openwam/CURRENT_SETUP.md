> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# 深圳 2：OpenWAM + RoboDojo 当前实配入口

记录日期：2026-09-28，19:50:45 运行结束后更新。**深圳 2 的 OpenWAM + RoboDojo 首个真实回合已成功：`stack_bowls / seed 0 / layout 0 / eval_num=1`，`success_rate=1.0`、汇总 `score=100.0`，退出码 0。** 保留驱动 595.71.05 和 Isaac Sim 5.1，仿真进程使用已验证的 Vulkan 兼容 wrapper。这是一个回合的基础设施验收，不是完整基准成绩。

## 位置与版本

- 服务器/账户：深圳 2，`USER`。
- 项目：`/path/to/robodojo-openwam`；实际路径为 `/path/to/robodojo-openwam`。
- 源码：项目下 `RoboDojo/`；分支 `codex/openwam-robodojo`。
- 环境：项目下 `envs/RoboDojo`（仿真）、`envs/openwam`（策略）；日志 `logs/`，每次运行记录 `runs/<run-id>/`。
- 模型目录：`checkpoints/OpenWAM-Alpha-Sim-RoboDojo`。

| 源码 | 已确认 SHA |
|---|---|
| RoboDojo | `726e9aabfaa642203722eb126f5eaf0f37f3e1ad` |
| XPolicyLab | `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4` |
| IsaacLab fork | `afca7b09d60d8beb9c1cb28b43066499940b969b` |
| curobo fork | `895c6517243f8cb091c73c018c8167192d39599a` |
| RoboDawn 兼容脚本来源 | `9247f366cd31f278e10f2fbe5fe8469b5f1b5b94`，仅引入已审计的 Vulkan compatibility / probe 脚本 |

## 已完成与验证范围

| 项目 | 当前证据 |
|---|---|
| 策略安装 | 安装退出码 0；隔离环境 `pip check` 退出码 0，输出 `No broken requirements found.` |
| 策略导入 | PyTorch `2.7.1+cu128`、NumPy `2.2.6`、Transformers `5.17.0`、Diffusers `0.40.0`、Hugging Face Hub `1.33.0`；Hub 从项目环境加载。 |
| 任务资产 | 固定官方 HF revision `43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab`，284 文件、573,739,871 B 全部 hash 通过；保留 `stack_bowls / arx_x5 / seed 0` 全部 55 份布局。已按本机路径生成 `curobo.yml`。 |
| 仿真安装 | 2026-09-28 19:16:57（UTC+8）完成，`logs/install-mirror.exit=0`；19:19:57 的 084 回执确认完成状态及源码版本。 |
| 模型权重 | `checkpoint-ranges-v2.exit=0`，整包文件校验通过；固定HF revision `2c1302294e3ba8319bbdb2c803b7a27de9292d03`，主权重SHA256 `78ca4ef5d2f6c8fa877bcae8b40c36b3d8700547fd5a708b472c4564e5f40abb`。 |
| 本地动态库修复 | 19:25:48 安装 `libglu 9.0.3` 完成，退出码 0；仿真脚本已将 `${CONDA_PREFIX}/lib` 前置到 `LD_LIBRARY_PATH`，`ctypes.CDLL('libGLU.so.1')` 输出 `GLU_LOAD_OK`。第二次运行不再出现首次的 GLU / MDL 加载错误。 |
| 启动兼容修复 | 社区 RoboDawn 进程级 Vulkan compatibility layer 已在本项目准备；两份官方来源 `.deb` 已校验并解包至项目目录。19:42:54 独立启动诊断退出码 0，构造函数与 5 次 update 均返回。 |
| 真实评测 | `eval_single.sh` 已通过 `bash -n`；前两次尝试退出 139；第三次真实评测成功，`eval_time=1`、`success_rate=1.0`、汇总 `score=100.0`，`details["0"]` 为 `layout_id=0 / success=true / score=1.0`。 |
| 输出与退出 | 头部、左腕、右腕 3 个视频均已保存，ffprobe 确认各 320 帧、640×480、25 FPS、12.8 秒；整次命令墙钟 397 秒，退出码 0。进程树已退出，GPU 2 / 3 显存恢复至 6 / 4 MiB。已目视头部首尾帧和双腕末帧，均为真实 RGB，头部末帧可见碗已叠起。 |

这里安装的是该任务资产子集，不是完整基准 Assets。静态依赖核查未发现需追加的其他官方资产目录；原始相机支架仍保留远程 MDL 与作者图片悬空引用。本次 layout 0 已完成真实回合并输出三路视频，这些引用未阻止该回合完成；其他布局和材质的视觉等价尚未验证。资产范围与 CPU 解析记录（完整本地证据未随公开版发布）

## 实际运行与兼容性处理

| 运行 | 已确认结果 |
|---|---|
| `sz2_openwam_stack_bowls_s0_20260928_1921`，19:20:49–19:24:14 | 真实模型加载及策略服务启动成功；仿真日志确认 GPU 2 为 `Active Yes`。出现 `libGLU.so.1` 缺失、MDL SDK 加载失败，随后在 RTX scene database 栈崩溃，退出码 139。 |
| `sz2_openwam_stack_bowls_s0_20260928_1926`，19:26:12–19:29:23 | 已补 GLU 和动态库路径，相关 GLU / MDL 错误消失；仍在 `app ready` 后、任务初始化前出现相同 `librtx.scenedb.plugin.so` 栈并退出 139。 |
| `sim-unmasked`，19:32:46–19:33:20 | 独立调用官方 `SimulationApp`，不加载 RoboDojo 任务、cuRobo 或 OpenWAM；取消 `CUDA_VISIBLE_DEVICES`，设置 `headless=True`、`active_gpu=2`、`physics_gpu=2`、`multi_gpu=False`，追加 `autoEnable=false`、`maxGpuCount=1`。使用默认 `isaacsim.exp.base.python.kit`，未设置 `create_new_stage`。GPU 2 为 `Active Yes`，CVD / bad-state 告警消失，构造函数仍未返回，同一 RTX 栈 `carbOnPluginStartup+0x3b4de`、退出码 139。 |
| `sim-compat`，19:42:54 完成 | 同一独立诊断增加 RoboDawn wrapper，保留驱动、Isaac 版本、GPU 2 和默认 experience。日志出现 `SIMULATION_APP_CONSTRUCTOR_RETURNED`、`SIMULATION_APP_UPDATES_RETURNED`，正常关闭，退出码 0；`app.close()` 结束进程，未打印其后的 `CLOSED` 标记。 |
| `sz2_openwam_stack_bowls_s0_20260928_1944`，19:44:08–19:50:45 | 仅仿真启动命令增加可选兼容 wrapper，策略进程不包裹。真实回合成功，1 次评测、0 失败、0 不稳定布局；汇总 score 100，三路视频均保存，墙钟 397 秒，退出码 0。启动 PID `3657210` 对应进程已退出。时间以 run 目录的 `start.txt / end.txt` 为准。 |

未加兼容层的独立诊断说明，此前崩溃无需加载模型、任务或资产即可复现，取消 CUDA 掩码也未解决。深圳 2 的驱动为 `595.71.05`，现象与 NVIDIA 官方仓库已报告的 Isaac Sim 5.1 / 595.71.05 启动崩溃相符。[官方问题 #677](https://github.com/isaac-sim/IsaacSim/issues/677)

112 回执确认本机 8 张卡均报告 `maxMemoryAllocationSize=18446744073709551615`（`UINT64_MAX`）。社区 wrapper 通过项目内 Khronos Profiles layer，只对被包裹进程查询到的**单次内存分配上限字段**改报 `4292870144` B（4 GiB − 2 MiB），并先验证被探测的 NVIDIA 属性仅这一项改变。它不把整卡显存限制到 4 GiB，不模拟 RT Core，不替换渲染器，也没有切换共享驱动。[固定社区源码](https://github.com/Hugo-AGI/RoboDawn/blob/9247f366cd31f278e10f2fbe5fe8469b5f1b5b94/scripts/robodojo/compat/vulkan_driver_compat.py)

**第三次真实回合已成功，当前复用该实配。** 结果只覆盖 `stack_bowls` 的 seed 0 / layout 0 单回合；没有验证完整标准协议、其他布局、连续 reset 或与其他渲染环境的像素等价。社区方案不能视为 NVIDIA / RoboDojo 的官方认可。现有 5.1 环境继续使用，未安装或切换 Isaac Sim 6。

## 当前两处资源设置差异

1. `env_cfg/sim/sim_config.yml`：`scene.num_envs` 从源码默认 **10 改为 1**。
2. `scripts/eval_policy.sh`：追加 `--/renderer/multiGpu/enabled=false --/renderer/activeGpu=${ROBODOJO_RENDER_GPU:-$device_id}`。本次 helper 设 `ROBODOJO_RENDER_GPU=2`，用于约束 Vulkan 渲染卡。

此外，首次失败后已在同一仿真脚本追加动态库修复：`export LD_LIBRARY_PATH="${CONDA_PREFIX:?}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"`，配合本项目仿真环境内的 `libglu`；这不是系统库或共享驱动修改。

第三次运行前，该脚本再增加可选 `sim_cmd` wrapper：仅在 `ROBODOJO_VULKAN_COMPAT_SCRIPT` 非空时，由它执行 `python -u src/eval_client/main.py`。当前 helper 将该变量设为 `$PROJECT/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py`；只包裹仿真进程，策略启动命令保持原样。每次运行额外保存 wrapper SHA256 和 layer 包校验记录。

环境使用 GPU 2，策略使用 GPU 3。启动前刷新占用，确认仍符合这次资源安排；不要沿用旧快照或占用 GPU 4–7 的现有实验。Kit GPU 编号最终需按日志 GPU UUID/PCI 对照，不能仅凭 CUDA 可见设备变量确认渲染落卡。GPU 源码核对（完整本地证据未随公开版发布）

## 复用入口

下面是已成功的评测入口；helper 已固定本次兼容 wrapper，且只包裹仿真进程。每次先加载项目环境，隔离用户 `.local` 中旧版 Hub 等 Python 包。`project-env.sh` 已设置 `PYTHONNOUSERSITE=1`，并把 conda、pip、HF 缓存定位到本项目。

```bash
source /path/to/robodojo-openwam/project-env.sh
nvidia-smi
# 刷新并确认 GPU 2、3 当前可用，以新的唯一 run-id 调用同一成功配置：
bash "$PROJECT/scripts/eval_single.sh" '<unique-run-id>'
```

脚本实际执行的官方命令如下，参数与 本地 eval_single.sh（完整本地证据未随公开版发布） 一致：

```bash
cd "$PROJECT/RoboDojo"
bash scripts/robodojo.sh eval \
  --policy-dir XPolicyLab/policy/OpenWAM \
  --task stack_bowls --ckpt OpenWAM-Alpha-Sim-RoboDojo \
  --env-cfg arx_x5 --action-type ee --seed 0 --eval-num 1 \
  --policy-env "$PROJECT/envs/openwam" --eval-env "$PROJECT/envs/RoboDojo" \
  --policy-gpu 3 --env-gpu 2
```

复用时调用 helper：它还设置真实模型开关 `OPENWAM_ALLOW_DUMMY_POLICY=false`、checkpoint 路径、一次 bash 尝试、唯一运行 ID，并检查策略/仿真安装、checkpoint 下载退出码及资产 ready 记录。每次保存完整命令、源码/子模块版本、资源 diff、GPU 前后进程、退出码；运行上限 1,800 秒，TERM 后 30 秒仍未退出则结束本次 runner。

## 记录入口

- [本次成功头部录像](media/stack_bowls_head.mp4)；[三路视频元数据](media/metadata.json)。
- 本次实施证据目录（完整本地证据未随公开版发布）：逐步命令、stdout、stderr、回执。
- [策略隔离检查](evidence/steps/055-policy-isolated-check/stdout.log)。
- [284 文件资产校验与本机路径更新](evidence/steps/059-materialize-task-assets/stdout.log)。
- [仿真安装完成回执（084）](evidence/steps/084-curobo-current/stdout.log)。
- [首次真实评测完整日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1921/sz2_openwam_stack_bowls_s0_20260928_1921.log)。
- [GLU 安装回执（097）](evidence/steps/097-glu-install-status/stdout.log)；[动态库路径实际补丁（096）](evidence/steps/096-fix-sim-glu/command.sh)。
- [第二次真实评测完整日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1926/sz2_openwam_stack_bowls_s0_20260928_1926.log)。
- 已执行的独立诊断脚本（完整本地证据未随公开版发布）；[独立诊断完整日志](evidence/sim-unmasked/sim-unmasked.log)；[退出及 GPU 回执（108）](evidence/steps/108-unmasked-confirm-and-clean/stdout.log)。
- [595 驱动原始 Vulkan 属性（112）](evidence/steps/112-vulkan-native-probe/stdout.log)；兼容源码与包校验清单（完整本地证据未随公开版发布）。
- 加入兼容层的实际诊断脚本（完整本地证据未随公开版发布）；[独立启动通过回执（116）](evidence/steps/116-compat-diagnosis-progress/stdout.log)；[第三次真实评测启动及实际补丁（118）](evidence/steps/118-real-run-with-compat/command.sh)。
- [成功回合原始结果 JSON](evidence/sz2_openwam_stack_bowls_s0_20260928_1944/result.json)；日志、视频及配置归档 manifest（完整本地证据未随公开版发布）。
- [回合完成与三路视频记录（126）](evidence/steps/126-real-action-progress/stdout.log)；[结果与进程/GPU 退出确认（127）](evidence/steps/127-success-json-and-cleanup/stdout.log)。
- [完整官方流程讲解](OFFICIAL_RUNBOOK.md)。

复用时以此成功实配为起点；扩大任务、布局或评测预算另行记录，不能把本次 1/1 成功外推为完整基准成功率。
