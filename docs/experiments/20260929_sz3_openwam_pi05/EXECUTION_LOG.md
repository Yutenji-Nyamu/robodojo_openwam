# 执行记录

`$PROJECT`代表SZ3独立数据盘项目，`$PROJECT/RoboDojo`为源码。本页给出可审查命令形状、实际输出与原始步骤编号；不是可直接重放的批量脚本。完整命令/stdout/stderr/退出回执保存于私有实施目录，公开证据为脱敏摘要。

## 安装、固定版本

公开基线`64e43bcc3036ca68091347530225d657df18feb0`；子模块见`evidence/source-refs.json`。安装脚本仅去掉`git submodule update`的`--remote`，按已固定gitlink安装，不追随上游分支。

| 步骤 | 命令/配置 | 实际结果 |
|---|---|---|
| sim | `bash scripts/install.sh -i` | 13:11:21退出0；Python3.11.16 / Torch2.7.0+cu128 / IsaacSim5.1.0 |
| OpenWAM | `XPolicyLab/policy/OpenWAM/install.sh`官方入口，独立conda环境 | 12:52:52退出0；Python3.10 / Torch2.7.1+cu128 |
| Pi_05 | 在`XPolicyLab/policy/Pi_05`执行`bash install.sh` | 第一次目标选择错误后终止；r2固定自身`.venv`，12:58:02退出0；Python3.11.16 / JAX0.5.3 / Torch2.10.0 |
| 系统依赖 | 独立sim环境安装`libglu=9.0.3`，`python utils/update_embodiment_config_path.py` | 13:12:09退出0；不改系统驱动 |
| 资产/模型 | 固定revision、实际文件大小与SHA校验，Pi05保留完整params、stats、metadata | 两模型与284项叠碗资产通过；未下载Pi05训练状态 |

Pi05锁定依赖的`rerun-sdk`/NumPy约束，以及sim的starlette/idna约束告警均记录保留，未为消除告警改变官方模型依赖。Pi05 tokenizer使用官方Google对象缓存。

## 两次完整OpenWAM入口

```bash
bash scripts/robodojo.sh eval \
  --policy-dir XPolicyLab/policy/OpenWAM \
  --task stack_bowls --ckpt OpenWAM-Alpha-Sim-RoboDojo \
  --env-cfg arx_x5 --action-type ee --seed 0 --eval-num 1 \
  --policy-env "$PROJECT/envs/openwam" --eval-env "$PROJECT/envs/RoboDojo" \
  --policy-gpu 3 --env-gpu 2
```

`scene.num_envs=1`；`ROBODOJO_MAX_BASH_RETRIES=1`；单GPU渲染；沿用SZ2已验证的595进程级内存上限wrapper。每run最多1800秒，日志、run目录及身份分开保存。两轮退出2/139均发生于任务前，不写成功率。

## 驱动加载定位与局部处理

| 私有步骤 | 检查/操作 | 输出与范围 |
|---|---|---|
| s068–080 | Vulkan探针、loader debug、dpkg校验、GLX函数指针、两机库hash及strace | 同版本库一致；SZ3缺NVIDIA EGL登记；项目JSON恢复探针，8H100正常枚举 |
| s086–090 | 回读完整失败上下文、内核Xid、库清单 | Kit首次图形工作提交失败；目标为GPU2，595wrapper确实生效 |
| s091–098 | GPU2独立SimulationApp+文件打开trace | CUDA无版本库名ENOENT；没有完成构造；退出124 |
| s095/099–103 | 项目内创建`libcuda.so`链接，用`LD_LIBRARY_PATH`重试GPU2 | trace确认成功打开该库；仍DEVICE_LOST，退出124 |
| s104–118 | GPU1/GPU3短测、两机driver参数、IOMMU、nvidia-smi、设备句柄 | 两张卡同错；RLT也持目标GPU句柄；未执行reset |
| s119–125 | 对照SZ2原厂GBM JSON；项目内补GBM描述和NVML链接，再试GPU2 | 库注册缺项补齐，仿真仍失败，退出124 |
| s129 | 仿真入口新增可选`ROBODOJO_NVIDIA_LIBRARY_DIR`；此前已有可选EGL描述入口 | bash语法通过；只作用于仿真进程；未改变策略/任务/成功判据 |

项目EGL文件内容：

```json
{"file_format_version":"1.0.0","ICD":{"library_path":"libEGL_nvidia.so.0"}}
```

项目链接指向**本机**`libcuda.so.595.71.05`与`libnvidia-ml.so.595.71.05`，没有替换系统库。GBM注册仅在独立诊断中使用，不混写成正式回合成功配置。截至13:58的上述阶段，没有执行GPU reset、驱动安装、整机重启、共享Ray重启或RLT停训。

## π0.5官方加载检查

```bash
bash XPolicyLab/policy/Pi_05/setup_eval_policy_server.sh \
  RoboDojo stack_bowls sim arx_x5 joint 0 3 uv 57145 localhost
```

使用`Pi_05/checkpoints/RoboDojo-sim-arx_x5-joint-0/59999`、官方deploy配置、独立uv环境、`OPENPI_DATA_HOME`内官方tokenizer。s127–128记录48秒内服务ready，显存24,880MiB；监督器核PID/start/PGID后终止本检查，回收成功。端口号为当次分配值，复跑应由官方工具重新分配。

后续真实Pi05命令与OpenWAM同构，模型相关参数改为`--policy-dir XPolicyLab/policy/Pi_05 --ckpt sim --action-type joint --policy-env uv`，最终配卡见下节。截至13:58尚未完成实际执行回合；以下续记实际成功结果。

## 借卡、重置与真实成功回合

| 步骤 | 命令/配置与范围 | 实际结果 |
|---|---|---|
| s143–144 | 冻结四组 RLT 实配、有效恢复点；按精确 driver/namespace 停止本人四组 | 四组完整checkpoint均为25；原driver退出、卡空闲 |
| s145–151 | GPU4 同配置 SimulationApp probe；按 probe 身份和后代清理 | 仍Xid109；清理后仅 persistence daemon持目标设备，无任务占用 |
| s152–154 | `nvidia-smi --gpu-reset -i <已核验GPU4 UUID>`；重跑相同 probe | reset退出0；约32秒Startup Complete，构造/update返回并退出0 |
| s155 | 精确核验空闲GPU6后执行单卡reset | 退出0；GPU6未做独立前后probe对照 |
| s156–168 | `$PROJECT/scripts/dojo_pair.py`，本次pair为`sz3_pair_20260929_143536` | OpenWAM 4/5、Pi05 6/7；各1环境1回合，两个原生任务成功、score100、正常退出0 |
| s167–170 | ffprobe与抽帧检查；监督器release/resume回执 | Pi05每路640×480、25fps、279帧；全部Dojo进程退出，4–7释放，自动RLT恢复helper退出0 |
| s171–179 | 冻结恢复 helper `status` 与 driver/actor/GPU 只读检查 | 四组新driver、48 actor存活；14:54全部CP25→第26轮，加载日志、回放池与累计轮次通过验收 |

完整官方评测命令、环境变量、原生结果与视频元数据分别见 `evidence/pi05/`、`evidence/openwam/`。本次 pair 总期限1800秒，正常完成后实际约7分钟；未改任务、seed、布局、动作类型或成功判据。`release.json`确认`all_workers_stopped=true`、四卡释放、`errors=[]`；RLT恢复helper已自动执行，s179最终训练推进核验全部通过，详见 `evidence/cutover-result.json`。系统驱动、共享Ray与其他用户任务未改。
