# 官方全量口径与依据

固定 RoboDojo 源码提供 42 个基任务、54 个可执行配置。三个评测 seed 为 0、1、2；每 seed 合计 2100 回合，三 seed 为 **6300 回合**。

| 能力 | 可执行配置数 | 每配置每 seed 回合 | 每 seed 合计 |
|---|---:|---:|---:|
| 泛化：12 标准 + 12 random | 24 | 25 | 600 |
| 记忆 | 6 | 50 | 300 |
| 精度 | 8 | 50 | 400 |
| 长时程 | 8 | 50 | 400 |
| 开放环境 | 8 | 50 | 400 |

使用 `--eval-num native`。`eval-num` 是一个任务/seed 的总回合，所有并行环境共同完成；不是每个环境各跑这么多。设置 100 仍受任务原生上限 25/50 限制。[任务预算](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/config/_task.yml) · [计数与限制](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/main.py#L328)

布局来自 `Assets/Eval_Layout/RoboDojo/arx_x5/<seed>/`，按编号消费；不稳定布局可能跳过，后续候选补齐。seed 改变官方布局组，而不是在本次实验中自行改变模型采样噪声。[布局管理](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/seed_manager/seed_manager.py#L29)

固定 OpenWAM 实现中，CLI seed 进入模型配置/回退权重路径；本次显式固定 checkpoint。OpenWAM 调用未传入新的 generation seed，engine 默认 42，动作初始化按其实现设随机生成器。因此每 seed 重启服务是批次管理选择，同 seed 跨任务复用服务，不额外修改模型噪声。[模型接口](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/OpenWAM/model.py#L315) · [生成入口](https://github.com/XPolicyLab/XPolicyLab/blob/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/OpenWAM/OpenWAM/openwam/deploy/engine.py#L494)

完整汇总需要 42 基任务 ×3 seed =126 个完整任务/seed 格，泛化的标准/random 配对；最终按五种能力汇总，不能简单平均 54 配置的分数。原生控制动作总上界 4,920,000，平均 780.95 步/回合，不含初始化或布局重试。[官方汇总器](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/summarize_result.py) · [评测协议](https://robodojo-benchmark.com/leaderboard/protocol)

官方调度 `PASS` 仅检查退出成功且至少有一回合；正式完成必须另核 25/50 的完整预算。每 seed 使用独立 run-id/summary；续跑从精确批次结果构造剩余任务表，不能把部分 JSON 当成任务完成。汇总器按目录名字典序选择，正式结果应放在独立选择根目录，避免混入旧探测。[PASS 条件](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/smoke_all_tasks.sh#L822) · [结果选择](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/summarize_result.py#L105)

官方参考：[快速评测](https://robodojo-benchmark.com/doc/usage/quick-evaluation/) · [并行环境](https://robodojo-benchmark.com/doc/sim-tasks/parallel-environments/) · [安装与资产](https://robodojo-benchmark.com/doc/usage/install-and-download/)。本地完整复现与申请官方 verified 排名是不同的交付；本记录先覆盖本地评测。
