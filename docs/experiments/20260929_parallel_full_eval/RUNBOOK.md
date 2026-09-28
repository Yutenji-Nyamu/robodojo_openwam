# 选用配置与复用入口

先按[首次推理的环境说明](../20260928_openwam/RUNBOOK.md)准备仿真/策略环境、固定权重与完整官方资产；本轮版本列于 [versions.json](versions.json)。只下载叠碗子集不足以执行全套。沿用已验证的本进程 GLU/Vulkan 兼容层，不切换整机驱动。

正式配置：四卡，每卡两个独立 worker，每 worker 四环境；模型与仿真同卡。canonical `arx_x5` 保持原机器人/相机，只把其仿真 `num_envs` 设为 4；`ee`、25Hz、32 步 chunk、10 denoise、native 回合和 seed0/1/2 保持。探测用配置文件别名只适合单任务 client；传给 server 会破坏机器人信息键，正式 sweep 不使用别名。

每 worker 一个 OpenWAM server、独立端口、同时只接一个 client，按分配的任务列表顺序评估。同 seed 跨任务常驻可以省模型冷加载；每 seed 重启服务并使用独立结果/summary。`reset` 清除本 worker 的观测缓存；不能让多个独立 client 共享一个 server 的全局 batch 状态。[批量模型](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/OpenWAM/model.py#L373) · [官方 worker 分配](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/smoke_all_tasks.sh#L626)

固定官方多 GPU 参数接受重复 GPU ID，例如 `4,4,5,5,6,6,7,7` 表示八个 worker；不是把显存合并。任务按官方权重静态分组。每 worker 的 physical GPU 必须同时用于 CUDA 与 Vulkan 渲染。已存在的本地 wrapper 读取 `ROBODOJO_RENDER_GPU`，不能让所有 worker 继承同一个全局固定值。直接使用官方调度时 unset 它以回退到各 worker 的 `device_id`；本次正式 launcher 则在每个 worker 子进程中显式设为该 worker 的 GPU。

以下是官方调度的最小表达模板：重复 GPU ID 使用当前可用四卡；路径与 run-id 由使用者设置。`benchmark` 的一体模式会每任务重载模型，常驻服务版本则使用下一段的 client 模式。

```bash
cd "$PROJECT/RoboDojo"
export OPENWAM_CKPT_DIR="$PROJECT/checkpoints/OpenWAM-Alpha-Sim-RoboDojo"
unset ROBODOJO_RENDER_GPU
bash scripts/robodojo.sh benchmark \
  --policy-dir XPolicyLab/policy/OpenWAM \
  --policy-env "$PROJECT/envs/openwam" --eval-env "$PROJECT/envs/RoboDojo" \
  --ckpt OpenWAM-Alpha-Sim-RoboDojo --env-cfg arx_x5 --action-type ee \
  --gpu-ids 4,4,5,5,6,6,7,7 --seed 0 --eval-num native \
  --run-id "$RUN_ID" --summary "$SUMMARY_JSON"
```

本次选择的常驻模式：先以官方 `server` 单实例入口启动八个独立服务，再用 `scripts/internal/smoke_all_tasks.sh --mode client`，指定等长的 `--env-gpu-ids` 和 `--policy-port` 列表，及 `--policy-host 127.0.0.1`。内部 client 入口支持稳定 `--run-id/--summary`；公共 client 包装未暴露这些恢复参数。[参数表](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/smoke_all_tasks.sh#L39)

本次容量 probe 的 1800 秒超时不用于正式评测。批次完成依赖完整结果和真实子进程退出，不能只看外层退出码。中断后保留 manifest 与结果，对未满原生预算的任务续跑；剩余任务少于 worker 数时相应减少 worker。[manifest 保存](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/eval_env.py#L671)

正式 launcher 文件由发布构建显式纳入，清单见 [脚本索引](SCRIPTS.md)；[STATUS.json](STATUS.json) 记录是否已启动。没有启动回执的脚本不称为已经完成全量验证。
