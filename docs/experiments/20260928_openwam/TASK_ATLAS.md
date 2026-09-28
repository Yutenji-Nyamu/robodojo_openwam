> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# RoboDojo 全任务图册

核查日期：2026-09-28。正式模拟任务按[官方能力清单](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/scripts/internal/task_inventory.py)与[官网任务页](https://robodojo-benchmark.com/doc/sim-tasks/)交叉核对；源码固定 `726e9aabfaa642203722eb126f5eaf0f37f3e1ad`。图片来自官网主页实际使用的官方媒体CDN，视频来自各任务文档页；本轮仅HEAD检查链接，没有下载媒体、截帧或生成示意图。

## 数量先说清楚

| 口径 | 数量 | 如何理解 |
|---|---:|---|
| 正式仿真基任务 | 42 | 泛化12、记忆6、精密8、长程8、开放8 |
| 可运行task name | 54 | 上述42，加12个泛化任务各自的 `_random` 版；每项都有同名Python类与YAML |
| 仿真任务文档页面 | 43 | 42正式任务页面，加1个训练用途DLC页面；random演示放在基任务页面内 |
| 真机任务 | 18 | Piper X、Piper、ARX X5各6；不是给每个模拟任务复制三种机器人 |

泛化标准版用于Train & Eval，random用于Eval；记忆/精密/长程页标Train & Eval；Open八项标Eval。这里的“Train”是数据/协议用途，不表示Dojo本仓库提供训练器。官网真机页均标Teleop、Train & Eval，每任务100条示范。DLC单列，不混入42项正式成绩口径。

**读图方法：**每幅图是官方演示的静态预览，不是OpenWAM或我们实跑结果。正文简述任务目标，成功条件/阶段分以链接中的任务卡和固定源码为准。真机任务与仿真同名，也可能动作流程或本体不同。
## 仿真：泛化（12个）

<a id="stack-bowls"></a>

### 叠碗 · `stack_bowls`

![叠碗：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/stack_bowls.jpg)

把三个碗叠在一起。它看似接近熟悉的 RoboTwin 堆叠任务，但这里要分别看标准条件和随机场景中的表现。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/stack-bowls/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_bowls.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/stack-bowls.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/stack-bowls-random.mp4)。对应随机入口：`stack_bowls_random`。

<a id="push-t"></a>

### 推 T 形块 · `push_T`

![推 T 形块：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/push_T.jpg)

把 T 形块推到灰色 T 形垫上，让位置与朝向准确重合；核心是连续推移后的姿态对齐。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/push-t/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/push_T.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/push-t.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/push-t-random.mp4)。对应随机入口：`push_T_random`。

<a id="pack-objects-into-box"></a>

### 定向装箱 · `pack_objects_into_box`

![定向装箱：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/pack_objects_into_box.jpg)

把桌上物体逐个装入箱子，并使每个物体的正面朝左；既要装进去，也要保持指定朝向。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/pack-objects-into-box/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pack_objects_into_box.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/pack-objects-into-box.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/pack-objects-into-box-random.mp4)。对应随机入口：`pack_objects_into_box_random`。

<a id="fold-clothes"></a>

### 折衣服 · `fold_clothes`

![折衣服：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/fold_clothes.jpg)

将衣物折整齐。这里操作的是可变形物体，成功条件关注衣物关键点之间的几何关系。

用途：`Train & Eval / Random Eval`；数据源：`DateGen / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/fold-clothes/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fold_clothes.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/fold-clothes.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/fold-clothes-random.mp4)。对应随机入口：`fold_clothes_random`。

<a id="hang-mugs"></a>

### 挂杯子 · `hang_mugs`

![挂杯子：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/hang_mugs.jpg)

把三个带把手的杯子全部挂到杯架上；需要抓取、姿态调整和杯把与挂钩的配合。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/hang-mugs/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/hang_mugs.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/hang-mugs.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/hang-mugs-random.mp4)。对应随机入口：`hang_mugs_random`。

<a id="sweep-blocks"></a>

### 扫积木 · `sweep_blocks`

![扫积木：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/sweep_blocks.jpg)

先拿扫帚并交接到右手，左手拿簸箕，再把右侧积木扫入簸箕；同时涉及工具使用与双手配合。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/sweep-blocks/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sweep_blocks.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/sweep-blocks.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/sweep-blocks-random.mp4)。对应随机入口：`sweep_blocks_random`。

<a id="pour-liquid-into-cup"></a>

### 倒液体 · `pour_liquid_into_cup`

![倒液体：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/pour_liquid_into_cup.jpg)

把瓶内液体倒进杯中；任务关注容器姿态与液体转移，不能仅以瓶子移动成功代替倒液体成功。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/pour-liquid-into-cup/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_liquid_into_cup.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/pour-liquid-into-cup.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/pour-liquid-into-cup-random.mp4)。对应随机入口：`pour_liquid_into_cup_random`。

<a id="make-toast"></a>

### 烤吐司 · `make_toast`

![烤吐司：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/make_toast.jpg)

从篮中取两片面包放入烤面包机，然后压下操作杆；包含取放和关节物体操作。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/make-toast/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/make_toast.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/make-toast.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/make-toast-random.mp4)。对应随机入口：`make_toast_random`。

<a id="arrange-largest-number"></a>

### 排出最大数字 · `arrange_largest_number`

![排出最大数字：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/arrange_largest_number.jpg)

将四个数字牌按能组成最大数的顺序，从左到右放到垫子上；需要视觉识别、排序与有序摆放。

用途：`Train & Eval / Random Eval`；数据源：`DateGen / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/arrange-largest-number/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/arrange_largest_number.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/arrange-largest-number.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/arrange-largest-number-random.mp4)。对应随机入口：`arrange_largest_number_random`。

<a id="sort-nesting-dolls-by-size"></a>

### 按大小排套娃 · `sort_nesting_dolls_by_size`

![按大小排套娃：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/sort_nesting_dolls_by_size.jpg)

把五个不同大小的套娃按从小到大的顺序，从左到右排成一行。

用途：`Train & Eval / Random Eval`；数据源：`DateGen / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/sort-nesting-dolls-by-size/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/sort_nesting_dolls_by_size.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/sort-nesting-dolls-by-size.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/sort-nesting-dolls-by-size-random.mp4)。对应随机入口：`sort_nesting_dolls_by_size_random`。

<a id="store-laptop-and-headphones"></a>

### 收电脑和耳机 · `store_laptop_and_headphones`

![收电脑和耳机：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/store_laptop_and_headphones.jpg)

先把耳机挂到支架上，再合上原本张开的电脑，将它取起并插入竖直电脑架。

用途：`Train & Eval / Random Eval`；数据源：`Teleop / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/store-laptop-and-headphones/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/store_laptop_and_headphones.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/store-laptop-and-headphones.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/store-laptop-and-headphones-random.mp4)。对应随机入口：`store_laptop_and_headphones_random`。

<a id="stack-blocks"></a>

### 叠不同纹理积木 · `stack_blocks`

![叠不同纹理积木：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/stack_blocks.jpg)

把三个纹理不同的方块堆成稳定的一叠；随机版沿用同一目标，改变测试场景。

用途：`Train & Eval / Random Eval`；数据源：`DateGen / Random eval-only`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/stack-blocks/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/stack-blocks.mp4) · [随机版演示](https://robodojo-benchmark.com/doc/videos/tasks/stack-blocks-random.mp4)。对应随机入口：`stack_blocks_random`。

## 仿真：记忆（6个）

<a id="cover-blocks"></a>

### 盖住后按颜色揭开 · `cover_blocks`

![盖住后按颜色揭开：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/cover_blocks.jpg)

先从左到右盖住三个色块，再按红、绿、蓝顺序揭盖；遮挡后必须记住颜色与位置的对应。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/cover-blocks/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/cover_blocks.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/cover-blocks.mp4)

<a id="match-and-pick-from-conveyor"></a>

### 记住并匹配传送带物体 · `match_and_pick_from_conveyor`

![记住并匹配传送带物体：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/match_and_pick_from_conveyor.jpg)

先观察一个随传送带离开的物体，再从后续出现的物体中抓取与它相同的目标；测试延迟视觉记忆。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/match-and-pick-from-conveyor/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/match_and_pick_from_conveyor.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/match-and-pick-from-conveyor.mp4)

<a id="swap-blocks"></a>

### 借空位交换积木 · `swap_blocks`

![借空位交换积木：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/swap_blocks.jpg)

两块积木占据三个垫位中的两个；利用空垫作为中转交换位置，每次移动后按按钮确认。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/swap-blocks/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/swap_blocks.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/swap-blocks.mp4)

<a id="swap-t"></a>

### 交换两个 T 形块 · `swap_T`

![交换两个 T 形块：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/swap_T.jpg)

双手拿起两个 T 形块并交换它们的位置，放回时还要匹配对方原来的朝向；需保存初始姿态信息。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/swap-t/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/swap_T.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/swap-t.mp4)

<a id="press-by-number"></a>

### 按数字计次按键 · `press_by_number`

![按数字计次按键：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/press_by_number.jpg)

读取两张数字牌，让两个红按钮各被按相应次数，再按蓝按钮确认；需要计数与动作顺序控制。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/press-by-number/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/press_by_number.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/press-by-number.mp4)

<a id="imitate-sorting-sequence"></a>

### 模仿入篮顺序 · `imitate_sorting_sequence`

![模仿入篮顺序：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/imitate_sorting_sequence.jpg)

观察对面的机器人把五类物体放进篮子的顺序，再用自己一侧对应物体复现这个顺序；是记忆式示范模仿。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/imitate-sorting-sequence/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/imitate_sorting_sequence.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/imitate-sorting-sequence.mp4)

## 仿真：精密操作（8个）

<a id="fasten-screws"></a>

### 配色拧螺丝 · `fasten_screws`

![配色拧螺丝：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/fasten_screws.jpg)

将三颗螺丝与同色螺母配对、插入并拧紧；颜色组合与位置会变化，必要时可中转交接。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/fasten-screws/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fasten_screws.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/fasten-screws.mp4)

<a id="plug-in-charger"></a>

### 插充电器 · `plug_in_charger`

![插充电器：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/plug_in_charger.jpg)

抓起充电器插头并插入排插；难点是插脚与插孔的精确对齐。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/plug-in-charger/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/plug_in_charger.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/plug-in-charger.mp4)

<a id="insert-tubes"></a>

### 插试管 · `insert_tubes`

![插试管：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/insert_tubes.jpg)

逐个抓起三支试管并插入试管架；要求细长物体与孔位对齐。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/insert-tubes/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/insert_tubes.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/insert-tubes.mp4)

<a id="pour-balls-into-vase"></a>

### 把小球倒进花瓶 · `pour_balls_into_vase`

![把小球倒进花瓶：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/pour_balls_into_vase.jpg)

拿起装有小球的杯子，将全部小球倒入花瓶；需要控制倾倒方向与狭窄入口。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/pour-balls-into-vase/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_balls_into_vase.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/pour-balls-into-vase.mp4)

<a id="play-xylophone"></a>

### 敲木琴 · `play_Xylophone`

![敲木琴：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/play_Xylophone.jpg)

拿起敲击棒，从左到右敲完所有琴键；工具末端必须准确接触每个目标。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/play-xylophone/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_Xylophone.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/play-xylophone.mp4)

<a id="deposit-coin"></a>

### 投硬币 · `deposit_coin`

![投硬币：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/deposit_coin.jpg)

从支架上夹起硬币，并准确插进储钱罐的细槽。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/deposit-coin/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/deposit_coin.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/deposit-coin.mp4)

<a id="insert-key"></a>

### 插钥匙并转动 · `insert_key`

![插钥匙并转动：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/insert_key.jpg)

拿起钥匙并交接给另一只手调整姿态，插进钥匙孔，然后旋转。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/insert-key/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/insert_key.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/insert-key.mp4)

<a id="build-tower"></a>

### 搭多层塔 · `build_tower`

![搭多层塔：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/build_tower.jpg)

用木块和木板逐层搭塔；各层需要对中、获得下层支撑，并保持直立稳定。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/build-tower/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/build_tower.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/build-tower.mp4)

## 仿真：长程操作（8个）

<a id="fill-pen-holder"></a>

### 把笔装入笔筒 · `fill_pen_holder`

![把笔装入笔筒：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/fill_pen_holder.jpg)

一只手举住笔筒，另一只手逐支放入笔，最后把装满的笔筒放回桌面。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/fill-pen-holder/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fill_pen_holder.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/fill-pen-holder.mp4)

<a id="classify-objects"></a>

### 按类别分篮 · `classify_objects`

![按类别分篮：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/classify_objects.jpg)

把三类物体分别装入三个篮子；哪个篮子对应哪类可自由选择，但同类物体必须归在一起。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/classify-objects/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/classify_objects.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/classify-objects.mp4)

<a id="put-bottles-into-dustbin"></a>

### 把四个瓶子扔进垃圾桶 · `put_bottles_into_dustbin`

![把四个瓶子扔进垃圾桶：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/put_bottles_into_dustbin.jpg)

收集桌上站立或倒放的四个瓶子，扔进桌旁垃圾桶；布局使部分右侧瓶子需要双手交接。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/put-bottles-into-dustbin/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/put_bottles_into_dustbin.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/put-bottles-into-dustbin.mp4)

<a id="play-tic-tac-toe"></a>

### 轮流下满井字棋盘 · `play_tic_tac_toe`

![轮流下满井字棋盘：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/play_tic_tac_toe.jpg)

机器人先手，与随机策略的对手轮流落子，直到 3×3 棋盘填满；页面目标不是必须赢棋。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/play-tic-tac-toe/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_tic_tac_toe.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/play-tic-tac-toe.mp4)

<a id="fill-egg-holder"></a>

### 装鸡蛋并盖盒 · `fill_egg_holder`

![装鸡蛋并盖盒：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/fill_egg_holder.jpg)

从篮中取出四个鸡蛋，逐个放进蛋盒，再关上盒盖。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/fill-egg-holder/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/fill_egg_holder.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/fill-egg-holder.mp4)

<a id="organize-table"></a>

### 整理桌面 · `organize_table`

![整理桌面：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/organize_table.jpg)

把鼠标、键盘、摆件和闹钟各归位。官网还描述了开抽屉并收纳杂物；当前固定源码的指令只列前四项，阅读任务时需保留这一版本差异。

用途：`Train & Eval`；数据源：`Teleop`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/organize-table/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/organize_table.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/organize-table.mp4)

<a id="make-kong"></a>

### 观察对手后杠牌 · `make_kong`

![观察对手后杠牌：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/make_kong.jpg)

等待麻将对手打出一张牌，识别自己一侧的匹配牌并完成杠牌；场景保证存在可杠的组合。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/make-kong/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/make_kong.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/make-kong.mp4)

<a id="play-stacking-toy"></a>

### 分类套叠玩具 · `play_stacking_toy`

![分类套叠玩具：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/play_stacking_toy.jpg)

将四类、数量分别为 4/3/2/1 的套叠零件放到各自匹配的柱子上，直到全部归位。

用途：`Train & Eval`；数据源：`DateGen`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/play-stacking-toy/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/play_stacking_toy.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/play-stacking-toy.mp4)

## 仿真：开放泛化（8个）

<a id="align-blocks"></a>

### 用三角尺推齐积木 · `align_blocks`

![用三角尺推齐积木：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/align_blocks.jpg)

使用三角尺把三个方块推成平行、笔直的一排，随后机械臂归位；考察开放工具使用。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/align-blocks/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/align_blocks.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/align-blocks.mp4)

<a id="general-pickup"></a>

### 按语言抓起目标 · `general_pickup`

![按语言抓起目标：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/general_pickup.jpg)

理解指令，从多个物体中找到指定目标并抬高 10 厘米；目标识别与抓取必须同时正确。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/general-pickup/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/general_pickup.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/general-pickup.mp4)

<a id="solve-equation"></a>

### 补全算式 · `solve_equation`

![补全算式：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/solve_equation.jpg)

理解桌上的算式，从打乱的数字或运算符中选出缺失项并放到答案垫上，再让机械臂归位。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/solve-equation/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/solve_equation.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/solve-equation.mp4)

<a id="stack-blocks-by-language"></a>

### 按语言顺序叠色块 · `stack_blocks_by_language`

![按语言顺序叠色块：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/stack_blocks_by_language.jpg)

理解指令指定的颜色顺序，依次叠好三个方块，再机械臂归位；不能沿用固定颜色顺序。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/stack-blocks-by-language/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/stack_blocks_by_language.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/stack-blocks-by-language.mp4)

<a id="classify-objects-by-language"></a>

### 按语言指定篮子分类 · `classify_objects_by_language`

![按语言指定篮子分类：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/classify_objects_by_language.jpg)

面对三类未见物体，根据语言把各类放进指定的左、中、右篮子；与普通分类任务的自由篮位规则不同。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/classify-objects-by-language/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/classify_objects_by_language.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/classify-objects-by-language.mp4)

<a id="pick-from-conveyor-by-image"></a>

### 看图从传送带取物 · `pick_from_conveyor_by_image`

![看图从传送带取物：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/pick_from_conveyor_by_image.jpg)

先将篮子抬高超过 8 厘米，再根据板上的目标图片，从传送带抓取匹配物体放入篮中。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/pick-from-conveyor-by-image/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pick_from_conveyor_by_image.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/pick-from-conveyor-by-image.mp4)

<a id="store-tools-in-toolbox"></a>

### 把工具放进匹配槽位 · `store_tools_in_toolbox`

![把工具放进匹配槽位：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/store_tools_in_toolbox.jpg)

逐个识别工具，并放进工具箱中对应形状的位置，随后机械臂归位。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/store-tools-in-toolbox/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/store_tools_in_toolbox.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/store-tools-in-toolbox.mp4)

<a id="pour-by-language"></a>

### 按语言配对倒液体 · `pour_by_language`

![按语言配对倒液体：官方仿真预览](https://media.luminis-sim.com/media/home/sim/posters/pour_by_language.jpg)

理解语言指定的瓶子与碗的颜色对应，将三瓶液体分别倒进各自目标碗，然后机械臂归位。

用途：`Eval`；数据源：`null (eval-only)`（保留官网写法）。[任务说明与评分](https://robodojo-benchmark.com/doc/sim-tasks/pour-by-language/) · [固定版本逻辑](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/task/RoboDojo/tasks/pour_by_language.py) · [标准演示](https://robodojo-benchmark.com/doc/videos/tasks/pour-by-language.mp4)

## 额外文档条目：DLC（不计入42项）

### 拼出 RoboDojo 字母

在复杂背景与杂乱桌面中找出正确字母，按顺序排成一行“RoboDojo”。官网标记 `Other / DataGen / Train`；该固定源码没有DLC对应任务类/YAML，因此它是额外任务展示/训练用途页面，不能直接当作当前第43个可运行正式任务。未找到该条目的官方静态poster，不造图。

[官方任务页](https://robodojo-benchmark.com/doc/sim-tasks/dlc/) · [官方视频演示](https://robodojo-benchmark.com/doc/videos/tasks/dlc.mp4)

## 真机任务：18项

下列任务不属于本仓库54个仿真task name；在官方真实机器人评测/数据体系中按本体分组。每项均有官方静态预览和视频链接。

### Piper X（6项）

#### 拆乐高 · `disassemble_LEGO`

![Piper X 拆乐高：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/disassemble_LEGO.jpg)

拆开桌上的乐高结构，并把所有分离出来的零件放进碗中。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/disassemble-lego/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/disassemble-lego.mp4)

#### 给笔盖帽 · `cap_pen`

![Piper X 给笔盖帽：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/cap_pen.jpg)

拿起笔与笔帽，调整两者的相对姿态并把笔帽套回笔上。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/cap-pen/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/cap-pen.mp4)

#### 分两类物体 · `classify_objects`

![Piper X 分两类物体：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/classify_objects.jpg)

识别桌上两类物体，将它们分别放入两个篮子。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/classify-objects/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/classify-objects.mp4)

#### 挂杯子 · `hang_mugs`

![Piper X 挂杯子：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/hang_mugs.jpg)

逐个抓起杯子并挂到杯架上。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/hang-mugs/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/hang-mugs.mp4)

#### 扫积木 · `sweep_blocks`

![Piper X 扫积木：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/sweep_blocks.jpg)

将扫帚交接到右手，左手持簸箕，把积木扫进去。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/sweep-blocks/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/sweep-blocks.mp4)

#### 装背包 · `pack_objects_into_backpack`

![Piper X 装背包：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/pack_objects_into_backpack.jpg)

把桌上所有物体逐个放入背包。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/pack-objects-into-backpack/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/pack-objects-into-backpack.mp4)

### Piper（6项）

#### 装笔筒 · `fill_pen_holder`

![Piper 装笔筒：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/fill_pen_holder.jpg)

拿起笔筒，将桌上所有笔逐支放入其中。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/fill-pen-holder/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/fill-pen-holder.mp4)

#### 收物入篮 · `put_objects_into_basket`

![Piper 收物入篮：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/put_objects_into_basket.jpg)

把桌上全部物体逐个放进篮子。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/put-objects-into-basket/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/put-objects-into-basket.mp4)

#### 叠积木后盖杯 · `stack_and_cover_blocks`

![Piper 叠积木后盖杯：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/stack_and_cover_blocks.jpg)

先把方块叠起来，再用杯子罩住堆好的方块。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/stack-and-cover-blocks/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/stack-and-cover-blocks.mp4)

#### 叠碗 · `stack_bowls`

![Piper 叠碗：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/stack_bowls.jpg)

逐个拿起桌上的碗并整齐叠放。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/stack-bowls/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/stack-bowls.mp4)

#### 扶正瓶子 · `stand_up_bottles`

![Piper 扶正瓶子：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/stand_up_bottles.jpg)

把桌上横放的瓶子拿起并竖直放稳。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/stand-up-bottles/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/stand-up-bottles.mp4)

#### 插充电器并接线 · `insert_charger`

![Piper 插充电器并接线：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/insert_charger.jpg)

先把充电器插头插进排插，再把充电线接到插头上。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/insert-charger/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/insert-charger.mp4)

### ARX X5（6项）

#### 插试管 · `insert_tubes`

![ARX X5 插试管：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/insert_tubes.jpg)

逐支拿起桌上的试管，插入试管架槽位。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/insert-tubes/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/insert-tubes.mp4)

#### 放面包与小碗 · `make_bread`

![ARX X5 放面包与小碗：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/make_bread.jpg)

将碗里的两片面包放进烤面包机，再把两个小碗摆到盘子上。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/make-bread/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/make-bread.mp4)

#### 多步备餐 · `make_food`

![ARX X5 多步备餐：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/make_food.jpg)

取出砧板，摆好牛排与刀，将蔬菜和虾放进锅里，把锅放上炉灶，最后盖上盖子。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/make-food/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/make-food.mp4)

#### 收水果后倒碗 · `pack_and_pour_fruit`

![ARX X5 收水果后倒碗：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/pack_and_pour_fruit.jpg)

先把全部水果装进蓝碗，再将蓝碗中的水果倒进大白碗。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/pack-and-pour-fruit/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/pack-and-pour-fruit.mp4)

#### 按记忆揭色块 · `cover_blocks`

![ARX X5 按记忆揭色块：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/cover_blocks.jpg)

从左到右盖住色块，再按红、绿、蓝顺序揭开；遮挡期间要记住颜色位置。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/cover-blocks/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/cover-blocks.mp4)

#### 收进保险箱并关门 · `store_in_safe`

![ARX X5 收进保险箱并关门：官方真机预览](https://media.luminis-sim.com/media/home/real/posters/store_in_safe.jpg)

把桌上全部物体放进保险箱，最后关闭保险箱。

[官方说明与评分](https://robodojo-benchmark.com/doc/real-tasks/store-in-safe/) · [真机演示](https://robodojo-benchmark.com/doc/videos/real-tasks/store-in-safe.mp4)

## 链接和覆盖核验

60幅静态预览（42仿真+18真机）、73条任务视频URL（42标准+12随机+18真机+DLC）和2条并行/随机化说明视频全部通过HTTP HEAD，静态图为`image/jpeg`，视频为`video/mp4`。61个任务说明页（42仿真+18真机+DLC）在完整文档抓取中均HTTP200。媒体只以远程URL引用，未复制到本地。

本文图片对应“这个任务长什么样”，不是某模型完成该任务的成功证据。若远程CDN将来换地址，本地仍保留每项官方任务页面链接供回溯。
