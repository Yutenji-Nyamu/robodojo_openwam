# RoboDojo：3 个 seed、50 回合究竟是什么意思

核查日期：2026-09-29。本文是协议与源码核查，不部署新模型、不改变当前评测。代码依据固定 RoboDojo `726e9aabfaa642203722eb126f5eaf0f37f3e1ad`，布局依据官方资产 `43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab`。

## 一句话理解

可以把**每个基础任务看成 3 套试卷，每套 50 道场景题**。同一套内的 50 回合会换初始布局、物体实例，部分任务还会换指令条件或演示顺序；不是把完全相同的场景重复 50 次。

泛化类有一个拆分：每个基础任务、每个 seed 的 50 回合 = **标准场景 25 + 随机化场景 25**。另外四类直接各 50。因此是 42 基础任务 × 3 × 50 = **6,300 回合**；执行层面则是 54 个配置 × 3 个 seed，原生预算各 25/50。[官方完整评估](https://robodojo-benchmark.com/doc/usage/quick-evaluation/#complete-evaluation)、[官方汇总规则，行 12–25](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/summarize_result.py#L12-L25)

## 三个容易混淆的数字

| 名字 | 实际作用 | 例子 |
|---|---|---|
| 评估 seed | 选择一套官方布局目录 | `Assets/Eval_Layout/RoboDojo/arx_x5/0/`、`1/`、`2/` |
| layout_id | 该任务在这一套里的具体场景编号 | `stack_bowls_0.json`、`stack_bowls_1.json` |
| num_envs | 同时处理多少回合 | 4 环境同批处理 4 个不同布局；不会把 50 变成 200 |

`SeedManager.init_eval` 按评估 seed 找目录，按文件名数字排序，依次读布局；任务每轮取最多 `num_envs` 个候选。内部一些变量也叫 `seed`，此时实际指 layout_id，不能把两层混成同一个数。[seed_manager.py 行 32–45、62–97](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env/seed_manager/seed_manager.py#L32-L97)

## 50 回合之间具体有什么区别

本轮重新下载了官方固定版本的三个叠碗布局，摘取同一个 `bowl0`：

| 官方文件 | 碗实例编号 category_idx | 初始 x、y，单位米 |
|---|---:|---|
| seed 0 / layout 0 | 10 | 0.043、−0.140 |
| seed 0 / layout 1 | 8 | −0.335、−0.157 |
| seed 1 / layout 0 | 2 | 0.355、−0.168 |

这些是实际 JSON 数据，说明**同 seed 的不同回合、不同 seed 的同编号回合，都可以有不同摆放和物体实例**。布局还记录朝向、尺寸、物理属性等，但不能据此说每个任务每回合都会把所有属性随机一遍。[seed0/layout0](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/blob/43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab/Assets/Eval_Layout/RoboDojo/arx_x5/0/stack_bowls_0.json)、[seed0/layout1](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/blob/43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab/Assets/Eval_Layout/RoboDojo/arx_x5/0/stack_bowls_1.json)、[seed1/layout0](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/blob/43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab/Assets/Eval_Layout/RoboDojo/arx_x5/1/stack_bowls_0.json)

不同任务会改变不同的东西：

- **常规操作**：物体位置、朝向、实例，例如不同碗、不同摆放。
- **语言条件任务**：指令可由场景中的对象属性产生。例如 `stack_blocks_by_language` 根据三个目标块的颜色，生成从底到顶的颜色顺序。[任务代码行 49–56](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks_by_language.py#L49-L56)
- **记忆/模仿任务**：还会读取对应场景的辅助臂演示与目标顺序。`imitate_sorting_sequence` 从 `Traj/.../<eval_seed>/<layout_id>.pkl` 读取轨迹及 `target_label`。[任务代码行 32–58](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/imitate_sorting_sequence.py#L32-L58)
- **泛化 random 配置**：额外考察桌面干扰物、桌面材质、地面材质、光照、HDR 背景变化。[官方随机化说明](https://robodojo-benchmark.com/doc/sim-tasks/domain-randomization/)

标准版与 `_random` 版是两份布局集合，不能默认相同 layout_id 只改背景、其他完全配对。例如本轮读到的 `stack_bowls_random_0.json` 使用实例编号 14，位置也不同于标准 `stack_bowls_0.json`。[官方 random 布局](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/blob/43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab/Assets/Eval_Layout/RoboDojo/arx_x5/0/stack_bowls_random_0.json)

## 评估 seed 和模型训练 seed 有什么关系

官方协议允许两种提交方式：三个训练 seed 的 checkpoint，或者同一个 checkpoint 在三个评估 seed 下评估。本次 OpenWAM 固定一个专用 checkpoint、跑三个评估 seed，属于后者。[官方协议，本轮主任务通过内置浏览器核查](https://robodojo-benchmark.com/leaderboard/protocol#simulation-real-world)

XPolicyLab 的同一个 `seed` 参数也可能参与权重目录查找：默认候选名包含 `<benchmark>-<checkpoint>-<embodiment>-<action>-<seed>`；显式 checkpoint 路径优先。因此部署 π0/π0.5 等模型时要分别记清：**本次评估布局 seed 是多少，实际加载的是哪个 checkpoint**。目录后缀为 0/1/2 的三个权重，与环境的三套布局，是可以同时存在的两层信息。[XPolicyLab 权重解析器行 68–80、99–147](https://github.com/XPolicyLab/XPolicyLab/blob/10ab265/utils/checkpoint_resolver.py#L68-L147)

也不要把“同评估 seed”解释为模型采样噪声逐位相同：OpenWAM 适配器的 `reset()` 清空待处理批次，没有接收环境 layout_id 来重置策略随机数。环境布局可复用，策略采样和物理执行仍可能有波动。[OpenWAM model.py 行 430–432](https://github.com/XPolicyLab/XPolicyLab/blob/10ab265/policy/OpenWAM/model.py#L430-L432)

## 不稳定场景与实时进度怎么读

官方预算的计数是 **success + fail**。正常执行但机器人没完成任务，会计入 fail；布局不稳定或辅助演示失败等无效样本单列 `unstable_nums`，不计入这 25/50 个有效回合。程序继续按顺序拿后面的官方候选，直到预算满或候选耗尽，不是只收成功回合。[eval_env.py 行 786–832](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/eval_env.py#L786-L832)、[main.py 行 434–442](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/main.py#L434-L442)

`abandoned_layout_ids` 是另一项：主要用于被 PhysX 监测器判坏、明确放弃并换候选的布局。普通 unstable 不一定进入 abandoned 集合，所以“已完成 7、unstable 1、abandoned 0”并不矛盾。[main.py 行 376–407](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/main.py#L376-L407)

`_result.json` **每批回合结束都会更新**。例如文件里 `eval_time: 4` 表示目前完成了 4 个有效回合，不代表这个任务已经测完。完成判据要同时看原生预算是否满、进程/调度器终态；候选耗尽或异常退出造成不足 25/50，仍属未完成。[eval_env.py 行 827–839](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/src/eval_client/eval_env.py#L827-L839)

## 后续多模型比较保持什么一致

继续使用相同官方源码与资产版本、机器人、任务/seed、原生回合数、任务步数上限、相机与评分方式；每个模型用对应官方部署参数及明确的 checkpoint。保存每回合 layout_id、无效布局与替换记录，便于确认比较用了哪些场景。不同模型不按成功结果挑布局，也不把同一场景反复尝试后只留最好一次。

原始核查证据标签：`seeds-20260929`。包括本轮从固定 revision 下载的 10 份源码、4 份布局 JSON、两页官方文档文本。未连接服务器，未更改正式评估。
