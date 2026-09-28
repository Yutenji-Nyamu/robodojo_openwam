# 复用这次成功配置

本仓库是 **RoboDojo 源码仓库**；OpenWAM 的策略适配在 `XPolicyLab/policy/OpenWAM/`。原先部署目录如下，环境、权重和资产不属于 Git 源码：

```text
robodojo-openwam/                  # PROJECT，外层部署目录
├── RoboDojo/                      # 本公开仓库
│   ├── XPolicyLab/policy/OpenWAM/ # 官方策略适配、训练与服务入口
│   ├── third_party/RoboDawn/      # 本次兼容脚本及原许可证
│   └── docs/experiments/20260928_openwam/
├── envs/RoboDojo/                 # Python 3.11，Isaac Sim 5.1，仿真
├── envs/openwam/                  # Python 3.10，OpenWAM 策略
├── checkpoints/OpenWAM-Alpha-Sim-RoboDojo/
├── cache/                        # 下载资产和各类缓存
├── logs/                         # 安装与运行完整日志
├── runs/                         # 每次运行的配置和回执
└── project-env.sh                # 项目路径与隔离变量
```

## 已有成功环境上继续使用

设置 `PROJECT` 为自己的外层部署路径，载入已有环境。确认仿真GPU2、模型GPU3当前可用，以新的唯一run-id运行先前成功的 `scripts/eval_single.sh`。该脚本在本目录 [成功回合证据](evidence/sz2_openwam_stack_bowls_s0_20260928_1944/eval_single.sh) 中保留脱敏副本；占位路径需要还原成实际路径。原成功运行的完整版本、配置、退出和数值保存在同一证据目录。

```bash
export PROJECT=/your/data/path/robodojo-openwam
source "$PROJECT/project-env.sh"
nvidia-smi
bash "$PROJECT/scripts/eval_single.sh" "openwam_stack_bowls_$(date +%Y%m%d_%H%M%S)"
```

这条是复用已有部署，不会重新安装。成功机器的历史兼容脚本在外层 `third_party/RoboDawn`；本公开仓库将相同原始脚本放在仓库内 `RoboDojo/third_party/RoboDawn`，全新部署时按下节指定路径。

## 从源码准备新部署

按照[官方安装与下载](https://robodojo-benchmark.com/doc/usage/install-and-download/)及[官方快速评测](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)完成仿真与策略两个环境。可查[本次安装步骤命令与回执](evidence/STEPS.md)；带历史PID、目录和停止操作的命令不要整批重放。

```bash
export PROJECT=/your/data/path/robodojo-openwam
git clone --recurse-submodules https://github.com/Yutenji-Nyamu/robodojo_openwam.git "$PROJECT/RoboDojo"
cd "$PROJECT/RoboDojo"
git submodule status
```

源码的子模块指针记录的是成功运行时版本。上游安装器使用 `git submodule update --remote`，可能移动子模块；安装后与 [versions.json](versions.json) 核对，不能把较新依赖称为本次原配置。

- 仿真：Python3.11、Torch2.7.0+cu128、Isaac Sim5.1；运行官方 `bash scripts/install.sh -i`。本次因网络使用清华默认PyPI镜像继续官方 `--from base_deps`，Torch仍取官方cu128源。
- 策略：单独Python3.10、Torch2.7.1+cu128，按 `XPolicyLab/policy/OpenWAM/install.sh` 安装；设置 `PYTHONNOUSERSITE=1`，避免用户旧Hub包进入环境。
- 权重：[OpenWAM-Alpha-Sim-RoboDojo](https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo)，固定revision见版本清单。24.835GB发布包包括本次所需模型组件；不是只下载配置或权重头。
- 资产：[官方数据仓库](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo)，固定revision见版本清单。本次只准备叠碗任务的284文件，包含55布局，共573,739,871字节；原官方下载入口也可准备全Assets。模型推理不需要训练集。
- 下载后运行官方路径更新逻辑，使x5的cuRobo配置指向当前Assets位置。资产、checkpoint和环境不随本仓库分发。

## 本机确实用到的兼容处理

仿真环境补齐 `libglu=9.0.3`，源码 `scripts/eval_policy.sh` 已包含该环境库路径、单GPU渲染及可选wrapper。GLU安装还引入libglvnd/libopengl并更新OpenSSL，具体事务见细日志。

```bash
conda install -y --freeze-installed -p "$PROJECT/envs/RoboDojo" -c conda-forge libglu=9.0.3
export COMPAT="$PROJECT/RoboDojo/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py"
"$PROJECT/envs/RoboDojo/bin/python" "$COMPAT" --probe
"$PROJECT/envs/RoboDojo/bin/python" "$COMPAT" --prepare
```

此wrapper是本次595驱动问题的社区兼容方案，适用条件会由脚本检查；不必把它当作所有驱动的默认要求。在线下载遇403时，按固定官方URL取得脚本指定的两个deb并核对SHA，再用 `--package <vulkan-profiles.deb> --jsoncpp-package <libjsoncpp.deb>` 离线准备。包仅解到本项目 `.cache`，不是系统驱动安装。机制与证据见[H100_COMPATIBILITY](H100_COMPATIBILITY.md)。

## 真实评测命令

完成环境与资产准备，载入项目环境与Conda初始化后：

```bash
cd "$PROJECT/RoboDojo"
export PYTHONNOUSERSITE=1
export EVAL_ENV_TYPE=sim
export OPENWAM_ALLOW_DUMMY_POLICY=false
export OPENWAM_CKPT_DIR="$PROJECT/checkpoints/OpenWAM-Alpha-Sim-RoboDojo"
export ROBODOJO_MAX_BASH_RETRIES=1
export ROBODOJO_RENDER_GPU=2
export ROBODOJO_RUN_ID="openwam_stack_bowls_$(date +%Y%m%d_%H%M%S)"
export ROBODOJO_VULKAN_COMPAT_SCRIPT="$PROJECT/RoboDojo/third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py"
timeout --signal=TERM --kill-after=30s 1800s bash scripts/robodojo.sh eval \
  --policy-dir XPolicyLab/policy/OpenWAM \
  --task stack_bowls --ckpt OpenWAM-Alpha-Sim-RoboDojo \
  --env-cfg arx_x5 --action-type ee --seed 0 --eval-num 1 \
  --policy-env "$PROJECT/envs/openwam" --eval-env "$PROJECT/envs/RoboDojo" \
  --policy-gpu 3 --env-gpu 2
```

该仓库 `env_cfg/sim/sim_config.yml` 已固定单环境。设备编号最终以Kit活动GPU记录为准；并行环境、任务、动作频率、种子和checkpoint都没有为本次成功临时修改。示例与原成功运行的差异仅是部署路径和新run-id；公开整理后没有额外重跑。

本次结果 `_result.json` 在 `eval_result/RoboDojo/stack_bowls/OpenWAM/arx_x5/0_ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee/<run-id>/`。三路视频由评测入口写出；成功运行详情可直接看[结果JSON](evidence/sz2_openwam_stack_bowls_s0_20260928_1944/result.json)与[原日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1944/sz2_openwam_stack_bowls_s0_20260928_1944.log)。
