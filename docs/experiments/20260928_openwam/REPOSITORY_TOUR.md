> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# RoboDojo 仓库逐文件导览

固定版本：[官方仓库 `726e9aabfaa642203722eb126f5eaf0f37f3e1ad`](https://github.com/RoboDojo-Benchmark/RoboDojo/tree/726e9aabfaa642203722eb126f5eaf0f37f3e1ad)，核查日期 2026-09-28。本文按完整 Git tree 和每个自有文件的内容/定义整理：**204 个自有文本文件、3 个第三方子模块指针**，没有只列目录而漏掉文件。它是帮助阅读的源码导览，不是逐行安全审计或运行验收；本轮没有安装、部署或训练，SSH只读现场核查另见[硬件专题](H100_COMPATIBILITY.md)。

先把职责分清：**RoboDojo 管仿真与评测，XPolicyLab 管模型和训练/服务接口，OpenWAM 是其中一个策略。** OpenWAM 输出动作；Dojo 执行动作、再取图、检查任务完成并保存结果。下载数据做 SFT 的训练过程属于模型侧，当前 Dojo release 自称 eval-only；目录里有布局生成器、规划器，并不表示完整专家采集流水线已经开源。

## 1. 用 RoboTwin 的经验建立对应关系

| 你熟悉的职责 | RoboDojo 在哪里 | 先理解什么 |
|---|---|---|
| 一个任务的场景与目标 | `task/RoboDojo/tasks/*.py` + `config/*.yml` | Python写成功/阶段分/指令，YAML写摆哪些物体、怎么摆 |
| 共用仿真与机器人底座 | `env/environment/` + 各 manager | Isaac/PhysX负责物理，manager把资源与任务组装起来 |
| 取图和机器人状态 | `env/camera_manager/`、`observation_manager/` | 物理状态与图像必须是同一时刻，不能直接忽略渲染同步 |
| 策略推理闭环 | `src/eval_client/` + `XPolicyLab/` | Dojo client发观测，模型server返回joint或EE动作 |
| 批量评测和统计 | `scripts/robodojo.sh`、`scripts/internal/` | episode成功率与阶段score不同；标准版与random版也分开 |
| RL训练环境适配 | 当前官方树没有完整RLinf adapter | 名为 `IsaacRLEnv` 的底层多个RL hooks仍为空，不能仅凭继承关系认定在线RL已完成 |

## 2. 一次评估从哪里走到哪里

```text
robodojo.sh eval / XPolicyLab policy/<模型>/eval.sh
  ├─ 启动/连接模型 server（如 OpenWAM，模型侧环境）
  └─ scripts/eval_policy.sh
       → src/eval_client/main.py：先启动 Isaac，再加载配置
       → task_registry：按名称选 task class + YAML
       → create_eval_env：在该 task class 上加评测闭环
       → TaskEnv / BaseEnv：机器人 + 场景 + 相机 + 物理
       → reset：布局/种子 → 稳定物理 → 同步渲染
       → 观测 → 模型返回动作 → 控制/IK/插值 → 物理步
       → RewardManager：成功条件与阶段score → 下一次观测
       → 结束/异常：结果JSON + 视频 + 恢复manifest
       → summarize_result.py：按任务/维度/seed汇总
```

重要层次：`task.py` 不是模型；`task.yml` 不是训练超参数；`eval_env.py` 才是公开评测动作循环；`RewardManager` 不是 RL optimizer。`num_envs` 是单进程场景数，脚本把不同任务分到多个进程/GPU又是另一层。详细参数和协议见同目录的官方文档导览。

## 3. 建议的阅读顺序

1. `README.md` → `scripts/README.md`：先看支持边界和入口。
2. `scripts/robodojo.sh` → `scripts/eval_policy.sh` → `src/eval_client/main.py`：看命令如何启动一次评测。
3. `task_registry.py` → `stack_bowls.py` → `stack_bowls.yml` → `_task.yml`：用一个简单任务读懂“任务规则 / 物体布局 / 默认覆盖”三者关系。
4. `TaskEnv` → `RobotManager` / `SceneManager` / `CameraManager`：理解场景如何装配。
5. `eval_env.py` 的 `get_obs_batch/take_action_batch/run_eval` → `ObsManager` → `RewardManager`：理解一次episode。
6. `render_sync.py`、`SeedManager`、`PhysXWarningMonitor`、`summarize_result.py`：最后看复现与故障处理。
7. 到 XPolicyLab 的 OpenWAM adapter，再到 OpenWAM 模型仓库读推理与训练；不要在 Dojo 的 `env/` 中寻找 WAM 网络。

## 4. 自有文件逐个说明

下列链接都固定到同一个 commit。任务逻辑与任务配置在后面的成对表中逐文件列出；此处没有展开第三方子模块内部的文件。
### 根目录与协作/容器文件

| 文件 | 作用 |
|---|---|
| [.dockerignore](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/.dockerignore) | 排除权重、资产、结果和缓存等不应进入 Docker build context 的内容。 |
| [.github/pull_request_template.md](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/.github/pull_request_template.md) | 提交 PR 时说明更改、验证和影响的模板；不参与仿真执行。 |
| [.gitignore](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/.gitignore) | 忽略本地资产、结果和生成文件，区分仓库源码与运行产物。 |
| [.gitmodules](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/.gitmodules) | 声明 XPolicyLab、IsaacLab 和 cuRobo 三个子模块的远端地址。实际复现以 gitlink 的固定 SHA 为准。 |
| [.pre-commit-config.yaml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/.pre-commit-config.yaml) | 提交前的格式和静态检查工具配置。 |
| [CLAUDE.md](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/CLAUDE.md) | 上游面向代码助手的仓库维护说明，可了解约定；它是被阅读的仓库内容，不是本次执行授权。 |
| [Dockerfile](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/Dockerfile) | 构建 RoboDojo 仿真镜像，安装 Isaac/渲染与 Python 依赖并接入入口脚本；不会自动包含外置全部资产和模型权重。 |
| [LICENSE](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/LICENSE) | 该快照文件正文为 MIT；README 则描述非商业研究许可，二者尚有不一致，不能用其中一处替另一处作许可结论。 |
| [README.md](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/README.md) | 项目定位、文档/论文入口、eval-only 边界、仓库分工和发布变更。 |
| [docker/README.md](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/docker/README.md) | Docker 安装、运行、资产挂载、检查和 smoke 流程的说明。 |
| [docker/entrypoint.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/docker/entrypoint.sh) | 容器启动时整理运行环境并执行传入命令。 |
| [docker/install_docker_nvidia.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/docker/install_docker_nvidia.sh) | 安装/配置 Docker 与 NVIDIA container toolkit 的宿主机辅助脚本；属于系统环境准备。 |
| [docker/smoke_docker.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/docker/smoke_docker.sh) | 容器侧 smoke 调度与参数校验；检查镜像、挂载和小规模评估链路。 |
| [pyproject.toml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/pyproject.toml) | 项目元数据（0.2.0、Python>=3.11、eval-only）及 Ruff 格式/检查规则；不是完整模型依赖清单。 |

### 环境、相机、机器人、场景和判据

| 文件 | 作用 |
|---|---|
| [env/camera_manager/camera_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/camera_manager/camera_manager.py) | 创建和重建各环境的相机，设置位姿/语义并返回内外参；reset 时处理相机与随机种子。 |
| [env/camera_manager/capture/camera_view.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/camera_manager/capture/camera_view.py) | 包装 tiled camera 传感器；把拼接的大图缓冲还原成单个相机的图像数据。 |
| [env/camera_manager/capture/render_sync.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/camera_manager/capture/render_sync.py) | 协调物理步与渲染时间，等待最新相机缓冲，避免拿到前一帧图像；包含 zero-delay Kit 设置。 |
| [env/camera_manager/capture/tiled_capture_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/camera_manager/capture/tiled_capture_manager.py) | 统一初始化、推进、reset 和销毁 tiled 相机采集，是相机创建与观测读取之间的连接。 |
| [env/description_manager/desc_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/description_manager/desc_manager.py) | 根据环境标签和模板生成/选择自然语言指令，并用每环境种子保证选择可追踪。 |
| [env/environment/__init__.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/__init__.py) | 空包标记，便于 Python 导入 environment 模块。 |
| [env/environment/base_env.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/base_env.py) | Gym 风格外壳：配置并启动 Isaac、物理与渲染参数、sim_step、reset/close、全局和逐环境种子。 |
| [env/environment/isaac/__init__.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/isaac/__init__.py) | 注册/暴露内部 Isaac 环境入口，让上层按环境 ID 构造它。 |
| [env/environment/isaac/direct_rl_env.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/isaac/direct_rl_env.py) | 对 IsaacLab DirectRLEnv 增加可直接调用的物理步，供外层控制循环推进仿真。 |
| [env/environment/isaac/isaac_rl_env.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/isaac/isaac_rl_env.py) | 配置 Isaac 场景并把 setup/reset 回调交还外层。obs/reward/done/action 等 RL hooks 仍有 pass；文件名含 RL 不代表已提供完整在线 RL 契约。 |
| [env/environment/task_env.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/environment/task_env.py) | 将机器人、场景、相机和 tiled capture manager 装配成共用任务基类；reset 重载场景、复位机器人并等待物理稳定。 |
| [env/global_configs.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/global_configs.py) | 集中保存仓库/资产/配置路径与全局常量，让模块使用一致的资源根目录。 |
| [env/observation_manager/obs_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/observation_manager/obs_manager.py) | 组合机器人关节、末端、视觉、指令等观测；读取前等待最新渲染，输出给策略的观测字典。 |
| [env/planner_manager/.gitignore](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/planner_manager/.gitignore) | 忽略规划器本地生成文件。 |
| [env/planner_manager/curobo_planner.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/planner_manager/curobo_planner.py) | 包装 cuRobo 的关节/末端规划、批处理和 IK；转换世界坐标与机器人基坐标并提取轨迹。 |
| [env/reward_manager/func_parser.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/reward_manager/func_parser.py) | 低层几何/状态判据库：抬起、放入、堆叠、对齐、衣物关键点、液体、关节按钮等。它把场景状态变成布尔条件。 |
| [env/reward_manager/reward_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/reward_manager/reward_manager.py) | 把低层判据组合成有顺序、触发、重复计次的成功检查和阶段 score；管理每个环境的完成/失败状态。score 与最终成功应分开读。 |
| [env/robot_manager/.gitignore](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/.gitignore) | 忽略机器人目录下的本地生成内容。 |
| [env/robot_manager/control_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/control_manager.py) | MetaControl 表示一个动作片段，ControlSeq 排队；ControlManager 补齐未变化的控制量并维护各机器人执行队列。 |
| [env/robot_manager/robot_class/franka.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/robot_class/franka.py) | Franka 的机器人本体包装，配置它的关节、夹爪和末端命名约定。 |
| [env/robot_manager/robot_class/x5.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/robot_class/x5.py) | ARX X5 的机器人本体包装，提供关节、夹爪和末端的命名与基本信息。 |
| [env/robot_manager/robot_config/franka.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/robot_config/franka.py) | 生成 Franka 的 IsaacLab articulation/actuator 配置，连接 USD 机器人资源。 |
| [env/robot_manager/robot_config/x5.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/robot_config/x5.py) | 生成 X5 的 articulation/actuator 配置，连接 USD 与关节默认设置。 |
| [env/robot_manager/robot_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/robot_manager/robot_manager.py) | 实例化机器人、设置初始状态、读取关节/末端、规划/IK、执行控制、挂相机；是策略动作落到物理机器人的中心。 |
| [env/scene_manager/layout_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/layout_manager.py) | 解析任务 YAML，选择物体和布局、读取保存的 layout、维护标签/类别/功能点/包围盒，并检查布局稳定性。 |
| [env/scene_manager/objects/articulation.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/articulation.py) | 带关节物体：关节位置、驱动目标、根固定、材质与物理比例随机化；用于抽屉、按钮等可动机构。 |
| [env/scene_manager/objects/background.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/background.py) | 建立并重置背景/环境光资源。 |
| [env/scene_manager/objects/dynamic.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/dynamic.py) | 动态物体共用操作：读取网格、包围盒、恢复保存位姿和移出场景。 |
| [env/scene_manager/objects/fluid.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/fluid.py) | 粒子液体包装；生成容器内粒子、设置材质、读取/恢复粒子位置。 |
| [env/scene_manager/objects/garment.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/garment.py) | 衣物/布料对象包装；读取网格和关键点状态、变换/恢复形状并设置视觉材质。 |
| [env/scene_manager/objects/geometry.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/geometry.py) | 普通几何资源包装：加载、着色、恢复位姿、隐藏/销毁；可移除不需要的刚体属性。 |
| [env/scene_manager/objects/ground.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/ground.py) | 创建地面几何并应用 MDL/颜色材质及接触属性，支持材质随机化。 |
| [env/scene_manager/objects/light.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/light.py) | 创建、初始化和重置灯光。 |
| [env/scene_manager/objects/physics_material.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/physics_material.py) | 将摩擦、恢复系数等配置转成可赋给物体的物理材质。 |
| [env/scene_manager/objects/primitives.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/primitives.py) | 程序化生成立方体、平面、圆锥、圆盘、柱体、球、圆环和胶囊等基础网格。 |
| [env/scene_manager/objects/rigid.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/rigid.py) | 刚体物体：USD 加载、物理属性、初速度、网格/包围盒、恢复位姿和销毁。 |
| [env/scene_manager/objects/room.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/room.py) | 根据资源与变换配置放置房间外壳。 |
| [env/scene_manager/objects/table.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/objects/table.py) | 创建桌面、父坐标层级、材质和物理属性；恢复位姿时保持桌面与场景一致。 |
| [env/scene_manager/scene_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/scene_manager/scene_manager.py) | 实际创建和刷新场景；按类别分派对象 wrapper，处理每环境的重载、背景/灯光/桌面以及旧物体清理。 |
| [env/seed_manager/seed_manager.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/seed_manager/seed_manager.py) | 管理评估使用的 seed/layout 列表和完成进度，为环境槽分配下一个待评估布局。 |
| [env/seeding.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/seeding.py) | 统一设置 Python、NumPy、Torch 等随机数种子；与上层逐环境 seed 分配配合。 |

### 共用运行配置

| 文件 | 作用 |
|---|---|
| [env_cfg/arx_x5.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/arx_x5.yml) | 顶层组合配置：选择仿真/场景/双 X5/相机子配置，并声明 25Hz 观测与需要输出的状态/视觉字段。 |
| [env_cfg/camera/camera_config.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/camera/camera_config.yml) | 相机分辨率、姿态与传感器参数；读三路图像如何产生时从这里入手。 |
| [env_cfg/camera/template.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/camera/template.py) | 相机配置模板/参数示例，用于理解可配置字段。 |
| [env_cfg/robot/_robot_info.json](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/robot/_robot_info.json) | 机器人资源信息索引，关联具体机器人及其资产路径。 |
| [env_cfg/robot/dual_x5.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/robot/dual_x5.yml) | 两台 X5 的根位姿和抓取方向，是标准双臂 embodiment 布局。 |
| [env_cfg/robot/dual_x5_and_franka_competition.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/robot/dual_x5_and_franka_competition.yml) | 双 X5 加对面的 Franka，用于观察对手、轮流动作或模仿顺序类任务。 |
| [env_cfg/scene/conveyor.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/scene/conveyor.yml) | 传送带任务使用的场景底座/桌面与几何配置。 |
| [env_cfg/scene/default.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/scene/default.yml) | 标准房间、桌面、HDR 背景、地面材质和相机支架等共用场景。 |
| [env_cfg/sim/sim_config.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/sim/sim_config.yml) | 仿真步长和 scene.num_envs/env_spacing 等基本设置。 |

### 命令行与评测调度

| 文件 | 作用 |
|---|---|
| [scripts/README.md](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/README.md) | 公开 CLI、内部脚本与 Docker/policy 分工的导航；部分文档提及的运行时文件不在当前树中，需按实际路径核对。 |
| [scripts/RoboDojo/download_ckpt.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/RoboDojo/download_ckpt.sh) | 按支持的策略/任务条件下载 checkpoint 的交互/命令行辅助脚本。 |
| [scripts/RoboDojo/download_data.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/RoboDojo/download_data.sh) | 选择并下载 RoboDojo 数据子集；数据本体不存于本代码树。 |
| [scripts/eval_policy.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/eval_policy.sh) | 仿真 client shell 入口：解释模型/环境参数，启动 Python eval client，并处理进程重启约定。 |
| [scripts/init_assets.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/init_assets.sh) | 获取并整理机器人、对象和 layout 等仿真资产。 |
| [scripts/install.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/install.sh) | 准备 Conda/Python、Isaac 与依赖/子模块的安装流程；阅读即可，不应当作本轮已运行。 |
| [scripts/internal/prepare_policy_server.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/prepare_policy_server.sh) | 兼容入口，将策略服务准备工作转给对应 policy/server 路径。 |
| [scripts/internal/run_policy_eval.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/run_policy_eval.sh) | 连接一次模型评估：校验 policy 目录和参数，再调用策略自己的 eval 启动逻辑。 |
| [scripts/internal/run_policy_server.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/run_policy_server.sh) | 只启动策略服务器，支持模型与仿真分机部署。 |
| [scripts/internal/smoke_all_tasks.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/smoke_all_tasks.sh) | 批量选择任务、组织 smoke/benchmark、分配 GPU 并记录运行结果；含 dry-run 和失败/恢复处理。 |
| [scripts/internal/stat_score_distribution.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/stat_score_distribution.py) | 离线读取结果 JSON，统计每个任务/策略的 score 分布，便于区分全失败与部分完成。 |
| [scripts/internal/summarize_result.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/summarize_result.py) | 汇总任务、维度、seed 的 score/SR，拆分泛化标准/随机结果，检查结果与视频数量并输出 Markdown 表格。 |
| [scripts/internal/task_inventory.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/task_inventory.py) | 无需导入 Isaac，静态扫描任务类和同名 YAML；注册五类能力并报告可运行条目/缺失配置。42基任务加12随机版的依据。 |
| [scripts/internal/verify_install.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/verify_install.sh) | doctor 检查：核对环境、依赖、GPU/资产与入口是否就绪。 |
| [scripts/requirements.txt](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/requirements.txt) | RoboDojo 客户端额外 Python 依赖列表；Isaac 和策略依赖仍由各自安装路径负责。 |
| [scripts/robodojo.sh](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/robodojo.sh) | 公开总 CLI，分发 doctor/eval/client/server/smoke/benchmark/tasks/dimensions/summarize 等子命令。 |

### 评测客户端

| 文件 | 作用 |
|---|---|
| [src/__init__.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/__init__.py) | 客户端包的初始化说明/标记。 |
| [src/eval_client/eval_env.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/eval_env.py) | 核心闭环：从任务动态派生 EvalEnv，组装观测/seed/reward，连接模型客户端，执行 joint或EE动作与插值，终止判定、写结果/视频、恢复manifest。 |
| [src/eval_client/main.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/main.py) | 进程级入口：先启动 Isaac AppLauncher，再加载任务与配置；外层循环处理模型连接、PhysX异常、恢复和退出。 |
| [src/eval_client/physx_warning_monitor.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/physx_warning_monitor.py) | 监听 PhysX/Carb 原生日志，定位损坏环境和致命错误；按阈值节流，并向 main 抛出重建/重启信号。 |

### 任务注册与任务共用覆盖

| 文件 | 作用 |
|---|---|
| [task/RoboDojo/config/_task.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/_task.yml) | 全任务共用默认值与个别任务覆盖：数据源、场景/机器人配置、render_interval、自碰撞、eval_nums（例如泛化常为25，其他常为50）。 |
| [task/RoboDojo/task_registry.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/task_registry.py) | 按 task_name 动态导入同名模块与同名类，并定位同名 YAML；这里没有把54个类硬编码逐个注册。 |

### 通用工具

| 文件 | 作用 |
|---|---|
| [utils/cluttered_generator.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/cluttered_generator.py) | 生成随机杂物候选布局并检查碰撞/稳定性；保存的是场景布局逻辑，不等于开放了完整专家动作 DataGen。 |
| [utils/ensure_usd_path.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/ensure_usd_path.py) | 确保待访问的 USD prim 路径及其层级可用。 |
| [utils/load_file.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/load_file.py) | 读取 YAML/JSON/pickle、物体元信息和描述资源的共用函数。 |
| [utils/path.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/path.py) | 解析资源根/相对路径，发现 USD/MDL 文件并递归替换配置中的路径。 |
| [utils/pipeline_utils.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/pipeline_utils.py) | 组合 embodiment 与任务覆盖配置，处理随机化和 random任务并行数量上限，生成最终运行配置。 |
| [utils/rotations.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/rotations.py) | 欧拉角与四元数转换的小工具。 |
| [utils/save_file.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/save_file.py) | 持续向 FFmpeg 写视频、完成/中断时整理输出文件，以及保存结果 JSON。 |
| [utils/transformer.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/transformer.py) | 位姿矩阵/四元数变换、轴夹角、坐标与包围盒判断等数学工具；供机器人和奖励几何条件使用。 |
| [utils/update_embodiment_config_path.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/update_embodiment_config_path.py) | 交互式更新机器人资源路径，方便资产安装到不同位置。 |
| [utils/usd_schema.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/usd_schema.py) | 安全设置 USD schema 属性并转换属性名，减少动态创建几何/物理对象时的重复代码。 |

## 5. 54 个任务实现与 54 个场景配置，逐文件对应

每行的 `.py` 和 `.yml` 是两个独立文件，分别解释。Python通常定义 `*Common` 与同名任务类，包含 reset、成功判定、指令及可选阶段分；随机版仍以其自身实现为准，不假定全部只是导入别名。下表step_lim是源码的任务动作步上限，**不能直接换算成物理dt次数或某模型的chunk数**。YAML列出的类别是资产类别，不是模型标签。

### 泛化

| Python：目标与控制步上限 | YAML：场景组成 |
|---|---|
| [stack_bowls.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_bowls.py)：叠碗；目标见[任务图册](TASK_ATLAS.md#stack-bowls)；`step_lim=800`。 | [stack_bowls.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/stack_bowls.yml)：配置 Rigid；资产类别如 bowl。 |
| [stack_bowls_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_bowls_random.py)：随机场景版；叠碗；目标见[任务图册](TASK_ATLAS.md#stack-bowls)；`step_lim=800`。 | [stack_bowls_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/stack_bowls_random.yml)：配置 Rigid、Clutter、ProhibitedArea；资产类别如 bowl。 |
| [push_T.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/push_T.py)：推 T 形块；目标见[任务图册](TASK_ATLAS.md#push-t)；`step_lim=600`。 | [push_T.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/push_T.yml)：配置 Rigid、Geometry；资产类别如 t、t_cushion。 |
| [push_T_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/push_T_random.py)：随机场景版；推 T 形块；目标见[任务图册](TASK_ATLAS.md#push-t)；`step_lim=600`。 | [push_T_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/push_T_random.yml)：配置 Rigid、Geometry、Clutter、ProhibitedArea；资产类别如 t、t_cushion。 |
| [pack_objects_into_box.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pack_objects_into_box.py)：定向装箱；目标见[任务图册](TASK_ATLAS.md#pack-objects-into-box)；`step_lim=1300`。 | [pack_objects_into_box.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pack_objects_into_box.yml)：配置 Rigid；资产类别如 car、electric_toothbrush、hammer、shoe、box。 |
| [pack_objects_into_box_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pack_objects_into_box_random.py)：随机场景版；定向装箱；目标见[任务图册](TASK_ATLAS.md#pack-objects-into-box)；`step_lim=1300`。 | [pack_objects_into_box_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pack_objects_into_box_random.yml)：配置 Rigid；资产类别如 car、electric_toothbrush、hammer、shoe、box。 |
| [fold_clothes.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fold_clothes.py)：折衣服；目标见[任务图册](TASK_ATLAS.md#fold-clothes)；`step_lim=500`。 | [fold_clothes.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/fold_clothes.yml)：配置 Garment；资产类别如 Top_Long。 |
| [fold_clothes_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fold_clothes_random.py)：随机场景版；折衣服；目标见[任务图册](TASK_ATLAS.md#fold-clothes)；`step_lim=500`。 | [fold_clothes_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/fold_clothes_random.yml)：配置 Garment、Clutter、ProhibitedArea；资产类别如 Top_Long。 |
| [hang_mugs.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/hang_mugs.py)：挂杯子；目标见[任务图册](TASK_ATLAS.md#hang-mugs)；`step_lim=800`。 | [hang_mugs.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/hang_mugs.yml)：配置 Rigid、Geometry；资产类别如 mug、cup_holder。 |
| [hang_mugs_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/hang_mugs_random.py)：随机场景版；挂杯子；目标见[任务图册](TASK_ATLAS.md#hang-mugs)；`step_lim=800`。 | [hang_mugs_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/hang_mugs_random.yml)：配置 Rigid、Geometry、Clutter、ProhibitedArea；资产类别如 mug、cup_holder。 |
| [sweep_blocks.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sweep_blocks.py)：扫积木；目标见[任务图册](TASK_ATLAS.md#sweep-blocks)；`step_lim=1000`。 | [sweep_blocks.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/sweep_blocks.yml)：配置 Rigid；资产类别如 broom_shovel、broom、small_cube。 |
| [sweep_blocks_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sweep_blocks_random.py)：随机场景版；扫积木；目标见[任务图册](TASK_ATLAS.md#sweep-blocks)；`step_lim=1000`。 | [sweep_blocks_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/sweep_blocks_random.yml)：配置 Rigid；资产类别如 broom_shovel、broom、brick、earbuds、paper_ball。 |
| [pour_liquid_into_cup.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_liquid_into_cup.py)：倒液体；目标见[任务图册](TASK_ATLAS.md#pour-liquid-into-cup)；`step_lim=400`。 | [pour_liquid_into_cup.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pour_liquid_into_cup.yml)：配置 Rigid、Fluid；资产类别如 wuliangye、mug、goblet。 |
| [pour_liquid_into_cup_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_liquid_into_cup_random.py)：随机场景版；倒液体；目标见[任务图册](TASK_ATLAS.md#pour-liquid-into-cup)；`step_lim=400`。 | [pour_liquid_into_cup_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pour_liquid_into_cup_random.yml)：配置 Rigid、Fluid、Clutter、ProhibitedArea；资产类别如 wuliangye、mug。 |
| [make_toast.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/make_toast.py)：烤吐司；目标见[任务图册](TASK_ATLAS.md#make-toast)；`step_lim=1400`。 | [make_toast.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/make_toast.yml)：配置 Articulation、Geometry、Rigid；资产类别如 toaster、bread_shelf、bread。 |
| [make_toast_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/make_toast_random.py)：随机场景版；烤吐司；目标见[任务图册](TASK_ATLAS.md#make-toast)；`step_lim=1400`。 | [make_toast_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/make_toast_random.yml)：配置 Articulation、Geometry、Rigid、Clutter、ProhibitedArea；资产类别如 toaster、bread_shelf、bread。 |
| [arrange_largest_number.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/arrange_largest_number.py)：排出最大数字；目标见[任务图册](TASK_ATLAS.md#arrange-largest-number)；`step_lim=1050`。 | [arrange_largest_number.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/arrange_largest_number.yml)：配置 Rigid、Geometry、ProhibitedArea；资产类别如 由配置对象项指定。 |
| [arrange_largest_number_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/arrange_largest_number_random.py)：随机场景版；排出最大数字；目标见[任务图册](TASK_ATLAS.md#arrange-largest-number)；`step_lim=1050`。 | [arrange_largest_number_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/arrange_largest_number_random.yml)：配置 Rigid、Geometry、Clutter、ProhibitedArea；资产类别如 由配置对象项指定。 |
| [sort_nesting_dolls_by_size.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sort_nesting_dolls_by_size.py)：按大小排套娃；目标见[任务图册](TASK_ATLAS.md#sort-nesting-dolls-by-size)；`step_lim=1050`。 | [sort_nesting_dolls_by_size.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/sort_nesting_dolls_by_size.yml)：配置 Rigid、ProhibitedArea；资产类别如 由配置对象项指定。 |
| [sort_nesting_dolls_by_size_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sort_nesting_dolls_by_size_random.py)：随机场景版；按大小排套娃；目标见[任务图册](TASK_ATLAS.md#sort-nesting-dolls-by-size)；`step_lim=1050`。 | [sort_nesting_dolls_by_size_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/sort_nesting_dolls_by_size_random.yml)：配置 Rigid、Clutter、ProhibitedArea；资产类别如 由配置对象项指定。 |
| [store_laptop_and_headphones.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/store_laptop_and_headphones.py)：收电脑和耳机；目标见[任务图册](TASK_ATLAS.md#store-laptop-and-headphones)；`step_lim=800`。 | [store_laptop_and_headphones.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/store_laptop_and_headphones.yml)：配置 Articulation、Rigid、Geometry；资产类别如 laptop、headset、laptop_stand、vertical_laptop_storage_rack、headset_stand。 |
| [store_laptop_and_headphones_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/store_laptop_and_headphones_random.py)：随机场景版；收电脑和耳机；目标见[任务图册](TASK_ATLAS.md#store-laptop-and-headphones)；`step_lim=800`。 | [store_laptop_and_headphones_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/store_laptop_and_headphones_random.yml)：配置 Articulation、Rigid、Geometry、Clutter、ProhibitedArea；资产类别如 laptop、headset、laptop_stand、vertical_laptop_storage_rack、headset_stand。 |
| [stack_blocks.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks.py)：叠不同纹理积木；目标见[任务图册](TASK_ATLAS.md#stack-blocks)；`step_lim=550`。 | [stack_blocks.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/stack_blocks.yml)：配置 Rigid、ProhibitedArea；资产类别如 block。 |
| [stack_blocks_random.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks_random.py)：随机场景版；叠不同纹理积木；目标见[任务图册](TASK_ATLAS.md#stack-blocks)；`step_lim=550`。 | [stack_blocks_random.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/stack_blocks_random.yml)：配置 Rigid、Clutter、ProhibitedArea；资产类别如 block。 |

### 记忆

| Python：目标与控制步上限 | YAML：场景组成 |
|---|---|
| [cover_blocks.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/cover_blocks.py)：盖住后按颜色揭开；目标见[任务图册](TASK_ATLAS.md#cover-blocks)；`step_lim=800`。 | [cover_blocks.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/cover_blocks.yml)：配置 Rigid；资产类别如 cube、cup。 |
| [match_and_pick_from_conveyor.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/match_and_pick_from_conveyor.py)：记住并匹配传送带物体；目标见[任务图册](TASK_ATLAS.md#match-and-pick-from-conveyor)；`step_lim=700`。 | [match_and_pick_from_conveyor.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/match_and_pick_from_conveyor.yml)：配置 Dynamic、Rigid；资产类别如 conveyor、bottle、camera、game_machine、headset、ice_cream、phone、garage、puppet、bag、plate。 |
| [swap_blocks.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/swap_blocks.py)：借空位交换积木；目标见[任务图册](TASK_ATLAS.md#swap-blocks)；`step_lim=700`。 | [swap_blocks.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/swap_blocks.yml)：配置 Geometry、Rigid、Articulation；资产类别如 cube_cushion、cube、SpringButton。 |
| [swap_T.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/swap_T.py)：交换两个 T 形块；目标见[任务图册](TASK_ATLAS.md#swap-t)；`step_lim=400`。 | [swap_T.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/swap_T.yml)：配置 Rigid；资产类别如 t。 |
| [press_by_number.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/press_by_number.py)：按数字计次按键；目标见[任务图册](TASK_ATLAS.md#press-by-number)；`step_lim=700`。 | [press_by_number.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/press_by_number.yml)：配置 Geometry、Articulation；资产类别如 number_card、SpringButton。 |
| [imitate_sorting_sequence.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/imitate_sorting_sequence.py)：模仿入篮顺序；目标见[任务图册](TASK_ATLAS.md#imitate-sorting-sequence)；`step_lim=1600`。 | [imitate_sorting_sequence.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/imitate_sorting_sequence.yml)：配置 Geometry、Rigid、Prohibited_Area；资产类别如 basket、toy_car、action_camera、phone、watch、garage。 |

### 精密操作

| Python：目标与控制步上限 | YAML：场景组成 |
|---|---|
| [fasten_screws.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fasten_screws.py)：配色拧螺丝；目标见[任务图册](TASK_ATLAS.md#fasten-screws)；`step_lim=1900`。 | [fasten_screws.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/fasten_screws.yml)：配置 Rigid、Geometry、ProhibitedArea；资产类别如 factory_nut、factory_bolt。 |
| [plug_in_charger.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/plug_in_charger.py)：插充电器；目标见[任务图册](TASK_ATLAS.md#plug-in-charger)；`step_lim=400`。 | [plug_in_charger.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/plug_in_charger.yml)：配置 Rigid；资产类别如 charger、socket。 |
| [insert_tubes.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/insert_tubes.py)：插试管；目标见[任务图册](TASK_ATLAS.md#insert-tubes)；`step_lim=500`。 | [insert_tubes.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/insert_tubes.yml)：配置 Rigid、Geometry；资产类别如 test_tube、test_tube_slot。 |
| [pour_balls_into_vase.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_balls_into_vase.py)：把小球倒进花瓶；目标见[任务图册](TASK_ATLAS.md#pour-balls-into-vase)；`step_lim=600`。 | [pour_balls_into_vase.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pour_balls_into_vase.yml)：配置 Rigid、Geometry；资产类别如 cup、sphere、vase。 |
| [play_Xylophone.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_Xylophone.py)：敲木琴；目标见[任务图册](TASK_ATLAS.md#play-xylophone)；`step_lim=500`。 | [play_Xylophone.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/play_Xylophone.yml)：配置 Rigid、Geometry；资产类别如 mallet_stand、mallet、xylophone。 |
| [deposit_coin.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/deposit_coin.py)：投硬币；目标见[任务图册](TASK_ATLAS.md#deposit-coin)；`step_lim=300`。 | [deposit_coin.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/deposit_coin.yml)：配置 Geometry、Rigid；资产类别如 vertical_coin_stand、piggy_bank、coin。 |
| [insert_key.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/insert_key.py)：插钥匙并转动；目标见[任务图册](TASK_ATLAS.md#insert-key)；`step_lim=300`。 | [insert_key.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/insert_key.yml)：配置 Geometry、Rigid；资产类别如 key_slot、key。 |
| [build_tower.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/build_tower.py)：搭多层塔；目标见[任务图册](TASK_ATLAS.md#build-tower)；`step_lim=1050`。 | [build_tower.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/build_tower.yml)：配置 Rigid；资产类别如 block。 |

### 长程操作

| Python：目标与控制步上限 | YAML：场景组成 |
|---|---|
| [fill_pen_holder.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fill_pen_holder.py)：把笔装入笔筒；目标见[任务图册](TASK_ATLAS.md#fill-pen-holder)；`step_lim=1100`。 | [fill_pen_holder.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/fill_pen_holder.yml)：配置 Rigid；资产类别如 pen、oil_pen、pen_holder。 |
| [classify_objects.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/classify_objects.py)：按类别分篮；目标见[任务图册](TASK_ATLAS.md#classify-objects)；`step_lim=1100`。 | [classify_objects.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/classify_objects.yml)：配置 Geometry、Rigid；资产类别如 basket、toy_car、action_camera、pen、watch、garage。 |
| [put_bottles_into_dustbin.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/put_bottles_into_dustbin.py)：把四个瓶子扔进垃圾桶；目标见[任务图册](TASK_ATLAS.md#put-bottles-into-dustbin)；`step_lim=700`。 | [put_bottles_into_dustbin.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/put_bottles_into_dustbin.yml)：配置 Rigid、Geometry；资产类别如 bottle、dustbin。 |
| [play_tic_tac_toe.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_tic_tac_toe.py)：轮流下满井字棋盘；目标见[任务图册](TASK_ATLAS.md#play-tic-tac-toe)；`step_lim=1100`。 | [play_tic_tac_toe.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/play_tic_tac_toe.yml)：配置 Geometry、Rigid；资产类别如 checkerboard、chessman。 |
| [fill_egg_holder.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fill_egg_holder.py)：装鸡蛋并盖盒；目标见[任务图册](TASK_ATLAS.md#fill-egg-holder)；`step_lim=700`。 | [fill_egg_holder.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/fill_egg_holder.yml)：配置 Geometry、Rigid、Articulation；资产类别如 egg_basket、egg、egg_holder。 |
| [organize_table.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/organize_table.py)：整理桌面；目标见[任务图册](TASK_ATLAS.md#organize-table)；`step_lim=1000`。 | [organize_table.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/organize_table.yml)：配置 Geometry、Rigid、ProhibitedArea；资产类别如 drawer、cube_cushion、monitor、mousemat、frame、mouse、alarm、keyboard、garage。 |
| [make_kong.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/make_kong.py)：观察对手后杠牌；目标见[任务图册](TASK_ATLAS.md#make-kong)；`step_lim=600`。 | [make_kong.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/make_kong.yml)：配置 Rigid；资产类别如 mahjong。 |
| [play_stacking_toy.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_stacking_toy.py)：分类套叠玩具；目标见[任务图册](TASK_ATLAS.md#play-stacking-toy)；`step_lim=1200`。 | [play_stacking_toy.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/play_stacking_toy.yml)：配置 Geometry、Rigid；资产类别如 stack_base、stackingblocks。 |

### 开放泛化

| Python：目标与控制步上限 | YAML：场景组成 |
|---|---|
| [align_blocks.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/align_blocks.py)：用三角尺推齐积木；目标见[任务图册](TASK_ATLAS.md#align-blocks)；`step_lim=200`。 | [align_blocks.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/align_blocks.yml)：配置 Rigid；资产类别如 triangular_prism、cube。 |
| [general_pickup.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/general_pickup.py)：按语言抓起目标；目标见[任务图册](TASK_ATLAS.md#general-pickup)；`step_lim=200`。 | [general_pickup.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/general_pickup.yml)：配置 Rigid、Clutter；资产类别如 bell、pepper、bicycle、binoculars、bottle、bottle_opener、bread、cactus、can、car、cassette、chick。 |
| [solve_equation.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/solve_equation.py)：补全算式；目标见[任务图册](TASK_ATLAS.md#solve-equation)；`step_lim=300`。 | [solve_equation.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/solve_equation.yml)：配置 Rigid、Geometry；资产类别如 equal、number、plus、minus、division、multiplication、cube_cushion。 |
| [stack_blocks_by_language.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks_by_language.py)：按语言顺序叠色块；目标见[任务图册](TASK_ATLAS.md#stack-blocks-by-language)；`step_lim=400`。 | [stack_blocks_by_language.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/stack_blocks_by_language.yml)：配置 Rigid、ProhibitedArea；资产类别如 cube。 |
| [classify_objects_by_language.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/classify_objects_by_language.py)：按语言指定篮子分类；目标见[任务图册](TASK_ATLAS.md#classify-objects-by-language)；`step_lim=1100`。 | [classify_objects_by_language.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/classify_objects_by_language.yml)：配置 Geometry、Rigid；资产类别如 basket、watch、car、wooden_toy、pepper、chocolate_bar。 |
| [pick_from_conveyor_by_image.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pick_from_conveyor_by_image.py)：看图从传送带取物；目标见[任务图册](TASK_ATLAS.md#pick-from-conveyor-by-image)；`step_lim=700`。 | [pick_from_conveyor_by_image.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pick_from_conveyor_by_image.yml)：配置 Dynamic、Geometry、Rigid；资产类别如 conveyor、photo、basket_grasp、car、can、correction_tape、figurine、donut、cup、glue、noodles、remote。 |
| [store_tools_in_toolbox.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/store_tools_in_toolbox.py)：把工具放进匹配槽位；目标见[任务图册](TASK_ATLAS.md#store-tools-in-toolbox)；`step_lim=900`。 | [store_tools_in_toolbox.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/store_tools_in_toolbox.yml)：配置 Geometry、Rigid；资产类别如 toolbox、hammer、pliers、tape_measure、wrench。 |
| [pour_by_language.py](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_by_language.py)：按语言配对倒液体；目标见[任务图册](TASK_ATLAS.md#pour-by-language)；`step_lim=800`。 | [pour_by_language.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/pour_by_language.yml)：配置 Rigid、Fluid；资产类别如 wine_bottle、wine_bowl、wuliangye。 |

## 6. 第三方、下载资产与机器生成内容的明确范围

| 范围 | 固定内容/职责 | 为什么不逐文件展开 |
|---|---|---|
| `XPolicyLab` | [固定SHA `bb9a0b5f5136a74503b679af830bfd0a3a837d5c`](https://github.com/XPolicyLab/XPolicyLab/tree/bb9a0b5f5136a74503b679af830bfd0a3a837d5c)；策略适配、依赖、checkpoint布局、训练/数据转换和WebSocket服务。OpenWAM适配在这里。 | 独立维护的第三方子模块，不计入204个自有文件；本导览讲接口边界。 |
| `third_party/IsaacLab` | [固定SHA `afca7b09d60d8beb9c1cb28b43066499940b969b`](https://github.com/yuechen0614/IsaacLab/tree/afca7b09d60d8beb9c1cb28b43066499940b969b)；底层IsaacLab环境、场景、机器人与传感器基础库。 | 独立维护的第三方子模块，不计入204个自有文件；本导览讲接口边界。 |
| `third_party/curobo` | [固定SHA `d17b54ce32cba095c0b000c4c58777075d11de0e`](https://github.com/yuechen0614/curobo/tree/d17b54ce32cba095c0b000c4c58777075d11de0e)；运动规划和IK求解库。 | 独立维护的第三方子模块，不计入204个自有文件；本导览讲接口边界。 |
| `Assets/` | 下载后的USD机器人/物体、材质、layout与相关元信息 | 不在该Git tree中，不伪列不存在的源码文件。 |
| checkpoint / 数据集 | 外部模型权重与演示数据 | 不属于Dojo源码；模型训练与部署另有各自仓库/资源版本。 |
| `eval_result/`、logs、视频、resume manifest、缓存 | 运行后生成 | 本轮没有运行，因此没有把这些产物假冒为仓库现有文件。 |

当前 tree 没有需单独合并的已提交机器生成源码大目录；204个blob均以文件为单位覆盖。布局生成器只是普通自有源码，已单列，并未归入“机器生成”而略过。

## 7. 阅读时保留的三个版本边界

- 官网模拟任务目录写43个页面：42个正式基任务加DLC页面；该SHA代码只有42基任务+12随机版，DLC无同名实现。详见任务图册。
- `organize_table` 官网叙述还包括开抽屉收杂物，而该SHA的 `gen_instruction` 只列鼠标/键盘/摆件/闹钟；学习任务概念可以看网页，精确复现要回到锁定源码和资产。
- README的eval-only定位、`IsaacRLEnv`中空RL hooks，以及DataGen未完整公开属于不同层面的事实：可以评测/读现有数据，不表示已有完整在线RL与专家数据生成流程。

## 8. 覆盖核验

本地证据包括官方完整Git tree（`truncated=false`）、204个文本源码下载结果（全部HTTP200）、源码定义索引和60项媒体映射。任务类/同名配置通过AST及文件列表静态核对；没有通过import启动Isaac。内部文档中的历史或运行时路径按现存tree解释，未把它们算作漏文件。
