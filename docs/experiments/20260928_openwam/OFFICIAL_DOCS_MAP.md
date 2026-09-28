> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# RoboDojo 官方文档逐页导览

核查日期：2026-09-28。这里把初期目的理解为：弄清 OpenWAM 与 RoboDojo/XPolicyLab 的接口，准备离线数据和模型，再完成一个任务的闭环评测。只是阅读路线，不代表已安装或启动实验。

## 阅读与覆盖结果

已从官方文档首页、完整侧栏及所有正文中的 `/doc/` 链接递归枚举并读取 **75 个有效页面**，正文合计 170,304 字符：14 个入口/操作/故障/机制页，42 个仿真基准任务页，1 个 DLC 训练页，18 个真机任务页。下面每个有效页面都占一行，附官方 URL、内容、对当前目的的用途和阅读时机。

另读了站外层级的 [Leaderboard Protocol](https://robodojo-benchmark.com/leaderboard/protocol)：动态页面正文从当前官方前端脚本中的协议数据对象核读，详见 [协议与并行解释](PROTOCOL_AND_PARALLEL.md)。协议不计入 `/doc/` 的 75 页。

正文和 HTML 已读取；没有下载或逐帧观看全部演示视频，媒体 URL 已登记。因此“读完所有页面”指页面文字与链接，不是已验证每段视频、每个安装命令或每个场景。

## 初期先读哪几页

建议先按 Usage → XPolicyLab → Install & Download 的数据格式段 → Configurations → 选定任务页 → Quick Evaluation → Evaluation Issues 的顺序理解。安装部分等硬件路线确定再按需执行。Parallel Environments 在单环境工作后再读；Submission 和正式榜单协议在准备发表/提交时细读。

XPolicyLab 把模型和环境分开：OpenWAM 是策略，RoboDojo 是仿真任务与裁判，XPolicyLab 是两端的数据与调用接口。`debug` 能验证离线接口，却不产生仿真成功率。数据页的绝对 next-state action、RGB 解码、joint/ee 区分，比先调并发更接近当前接通目标。

## 入口、安装与运行：14 页

| 官方页面 | 这一页讲什么 | 对 OpenWAM + RoboDojo 初期有什么用 | 何时读 |
|---|---|---|---|
| [RoboDojo](https://robodojo-benchmark.com/doc/) | 基准定位、42 仿真/18 真机、五维能力、论文和生态入口。 | 建立模型/基准/接口的关系；首页论文摘要中的政策数量不是实时适配清单。 | 现在概览 |
| [Usage](https://robodojo-benchmark.com/doc/usage/) | 环境侧与策略侧分工，以及安装、适配、评测和配置的阅读顺序。 | 最短入门路线；避免把两个仓库的依赖混成一个环境。 | 现在先读 |
| [Install & Download](https://robodojo-benchmark.com/doc/usage/install-and-download/) | 原生安装、assets/权重/数据下载，HDF5 时序与坐标，Docker挂载。 | 确定需要哪种数据；核对 25 Hz、绝对下一帧动作、三相机和资产路径。 | 准备数据与部署前 |
| [XPolicyLab](https://robodojo-benchmark.com/doc/usage/xpolicylab/) | 模型适配、隔离环境、远程服务、debug、观测动作格式、RGB编解码、数据转换。 | OpenWAM 对接最重要的一页；具体模型训练参数仍以其 README 为准。 | 现在重点读 |
| [Configurations](https://robodojo-benchmark.com/doc/usage/configurations/) | 顶层 env_cfg 如何组合物理、场景、机器人、相机、观测；layout和输出命名空间。 | 核对 arx_x5、joint维度、相机输入和最终生效配置。 | 首次闭环前 |
| [Quick Evaluation](https://robodojo-benchmark.com/doc/usage/quick-evaluation/) | doctor/dry-run/smoke/eval/benchmark、分维度、多GPU分组、远程client/server和产物。 | 知道怎么从单任务逐步验证；默认动作是 ee，不能替模型猜动作空间。 | 首次运行时 |
| [RoboDojo Submission](https://robodojo-benchmark.com/doc/usage/robodojo-submission/) | 先 XPolicyLab PR，再向官方申请，固定commit/checkpoint与复现信息。 | 区分本地复现与正式上榜；准备投稿/公开时再落实提交材料。 | 提交前 |
| [Common Issues](https://robodojo-benchmark.com/doc/common-issue/) | 按安装故障与运行故障分流。 | 遇到报错时迅速找对诊断入口。 | 出现问题时 |
| [Installation Issues](https://robodojo-benchmark.com/doc/common-issue/installation/) | GPU/RT Core、驱动、Python/GLIBC、Isaac安装、assets、Docker与cache问题。 | 先核硬件支持，尤其 H100 与 RTX 渲染限制；减少重复装包。 | 部署前及启动失败时 |
| [Evaluation Issues](https://robodojo-benchmark.com/doc/common-issue/evaluation/) | CPU/GPU OOM、PhysX恢复、异常样本、视频、batch强制1、网络超时和分数波动。 | 分清模型失败、环境异常和接口错误；记录异常样本与有效分母。 | 首次闭环及故障时 |
| [Simulation Tasks](https://robodojo-benchmark.com/doc/sim-tasks/) | 42 基准任务和 DLC 的导航、五类能力、世界坐标说明。 | 选定一个任务时先明确类别与训练示范可用性。 | 选任务时 |
| [Domain Randomization](https://robodojo-benchmark.com/doc/sim-tasks/domain-randomization/) | 杂物、桌面/地面材质、光照和背景五类随机化。 | 理解 Generalization 的随机版本改变什么；不是另一份默认训练集。 | 比较标准/随机时 |
| [Parallel Environments](https://robodojo-benchmark.com/doc/sim-tasks/parallel-environments/) | 单进程多环境、num_envs/spacing；网页写默认1，但本次固定源码实际10。 | 知道并发边界并核最终配置；本页没有每环境GB或吞吐实测表。 | 单环境可用后 |
| [Real Robot Tasks](https://robodojo-benchmark.com/doc/real-tasks/) | 18 个真机任务，Piper X/Piper/ARX X5各6；每任务100条遥操作示范。 | 了解将来的真机范围，区分与仿真同名但不同的任务定义。 | 规划真机扩展时 |

## 仿真任务页：42 页

这些页面均含指令、描述、类别、数据来源、用途、视频链接与评分表。Generalization 的12页把 standard/random 放在同页；运行配置却有12个额外 `_random`，所以 **42 基础任务、54 可运行配置、43 仿真任务页面（含DLC）** 是三种计数。

标注 DataGen/DateGen 只说明数据来源，不代表专家生成代码开放；标注 eval-only 的8个Open任务没有该页对应的官方训练示范。

### Generalization：12 页，标准与 random 演示在同页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Stack Bowls](https://robodojo-benchmark.com/doc/sim-tasks/stack-bowls/) | 三个碗叠放；过程分与完整成功还看姿态、回位。 | 看懂最常用入门示例与 score/success 区别。 | 若选此任务，闭环前读 |
| [Push T](https://robodojo-benchmark.com/doc/sim-tasks/push-t/) | 将 T 形块推到目标位姿，禁止抬起，并要求回位。 | 防止把视觉上“差不多对齐”当成成功。 | 若选此任务，闭环前读 |
| [Pack Objects Into Box](https://robodojo-benchmark.com/doc/sim-tasks/pack-objects-into-box/) | 物品入箱且朝向正确，逐件计分。 | 理解物体数量、朝向和目标容器共同约束。 | 若选此任务，闭环前读 |
| [Fold Clothes](https://robodojo-benchmark.com/doc/sim-tasks/fold-clothes/) | 袖子与衣摆依次折叠，按几何关键点判定。 | 认识可变形物体任务，区别刚体抓放。 | 若选此任务，闭环前读 |
| [Hang Mugs](https://robodojo-benchmark.com/doc/sim-tasks/hang-mugs/) | 将三个杯子挂上架，按数量计分。 | 核对挂放几何与阶段进度。 | 若选此任务，闭环前读 |
| [Sweep Blocks](https://robodojo-benchmark.com/doc/sim-tasks/sweep-blocks/) | 双手交接扫帚，持簸箕扫入全部积木。 | 理解工具使用与双臂分工。 | 若选此任务，闭环前读 |
| [Pour Liquid Into Cup](https://robodojo-benchmark.com/doc/sim-tasks/pour-liquid-into-cup/) | 瓶中液体倒入杯子，最终还要求瓶直立。 | 理解液体任务的完整结束条件。 | 若选此任务，闭环前读 |
| [Make Toast](https://robodojo-benchmark.com/doc/sim-tasks/make-toast/) | 插入两片面包并压下烤面包机开关。 | 理解多阶段和关节物体交互。 | 若选此任务，闭环前读 |
| [Arrange Largest Number](https://robodojo-benchmark.com/doc/sim-tasks/arrange-largest-number/) | 数字降序摆位形成最大数；四/五数字布局计分不同。 | 核对指令、排列关系与版式差异。 | 若选此任务，闭环前读 |
| [Sort Nesting Dolls By Size](https://robodojo-benchmark.com/doc/sim-tasks/sort-nesting-dolls-by-size/) | 五个套娃按大小沿直线排序。 | 理解尺寸识别与相对位置泛化。 | 若选此任务，闭环前读 |
| [Store Laptop And Headphones](https://robodojo-benchmark.com/doc/sim-tasks/store-laptop-and-headphones/) | 挂耳机、合笔记本、竖直入架并回位。 | 理解复合子目标与转动关节物体。 | 若选此任务，闭环前读 |
| [Stack Blocks](https://robodojo-benchmark.com/doc/sim-tasks/stack-blocks/) | 把三种纹理的积木叠起来。 | 理解材质变化下的同一叠放目标。 | 若选此任务，闭环前读 |

### Memory：6 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Cover Blocks](https://robodojo-benchmark.com/doc/sim-tasks/cover-blocks/) | 先依次盖住彩色块，再按红绿蓝顺序揭开。 | 观察被遮挡后必须保留历史信息。 | 若选此任务，闭环前读 |
| [Match And Pick From Conveyor](https://robodojo-benchmark.com/doc/sim-tasks/match-and-pick-from-conveyor/) | 记住传送带首个物体，等它再次出现时抓起。 | 理解视觉记忆与动态场景。 | 若选此任务，闭环前读 |
| [Swap Blocks](https://robodojo-benchmark.com/doc/sim-tasks/swap-blocks/) | 利用空垫交换积木，每次移动后按按钮。 | 理解动作顺序约束，不只看最终摆放。 | 若选此任务，闭环前读 |
| [Swap T](https://robodojo-benchmark.com/doc/sim-tasks/swap-t/) | 记住两个T形块原位姿，交换位置和朝向。 | 理解连续位姿记忆。 | 若选此任务，闭环前读 |
| [Press By Number](https://robodojo-benchmark.com/doc/sim-tasks/press-by-number/) | 按数字卡精确计数并确认；评分表给出确认顺序。 | 核对计数与确认按钮逻辑，不能只凭标题执行。 | 若选此任务，闭环前读 |
| [Imitate Sorting Sequence](https://robodojo-benchmark.com/doc/sim-tasks/imitate-sorting-sequence/) | 先看对手放物顺序，再按同一顺序复现。 | 理解历史缓存与支持机械臂等待条件。 | 若选此任务，闭环前读 |

### Precision：8 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Fasten Screws](https://robodojo-benchmark.com/doc/sim-tasks/fasten-screws/) | 同色螺母螺栓匹配并旋入规定深度。 | 理解颜色匹配与接触精度。 | 若选此任务，闭环前读 |
| [Plug In Charger](https://robodojo-benchmark.com/doc/sim-tasks/plug-in-charger/) | 将充电插头完全插入插座。 | 核对深度、姿态和回位条件。 | 若选此任务，闭环前读 |
| [Insert Tubes](https://robodojo-benchmark.com/doc/sim-tasks/insert-tubes/) | 三支管子依次插入管架。 | 按插入深度与直立姿态判断。 | 若选此任务，闭环前读 |
| [Pour Balls Into Vase](https://robodojo-benchmark.com/doc/sim-tasks/pour-balls-into-vase/) | 把杯中七个小球全部倒入花瓶。 | 目标全部完成才成功，不能只看部分入瓶。 | 若选此任务，闭环前读 |
| [Play Xylophone](https://robodojo-benchmark.com/doc/sim-tasks/play-xylophone/) | 按从左到右顺序敲琴键，敲后抬起槌。 | 理解顺序和接触后离开条件。 | 若选此任务，闭环前读 |
| [Deposit Coin](https://robodojo-benchmark.com/doc/sim-tasks/deposit-coin/) | 从支架抓硬币并投入窄槽。 | 区分拿起进度与真正插槽成功。 | 若选此任务，闭环前读 |
| [Insert Key](https://robodojo-benchmark.com/doc/sim-tasks/insert-key/) | 抓钥匙、交接调整、插入并转动。 | 理解双臂交接与精细插入。 | 若选此任务，闭环前读 |
| [Build Tower](https://robodojo-benchmark.com/doc/sim-tasks/build-tower/) | 用木块和板搭多层稳定塔。 | 理解层级居中、稳定与直立条件。 | 若选此任务，闭环前读 |

### Long-Horizon：8 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Fill Pen Holder](https://robodojo-benchmark.com/doc/sim-tasks/fill-pen-holder/) | 一手持笔筒，另一手逐支放笔，最后放回。 | 理解双臂依赖和完整收尾。 | 若选此任务，闭环前读 |
| [Classify Objects](https://robodojo-benchmark.com/doc/sim-tasks/classify-objects/) | 将三个物体类别分入三个篮子，篮子分配可自选。 | 与语言指定篮子的Open版本区分。 | 若选此任务，闭环前读 |
| [Put Bottles Into Dustbin](https://robodojo-benchmark.com/doc/sim-tasks/put-bottles-into-dustbin/) | 将四个瓶子入垃圾桶，部分位置需双手交接。 | 理解重复抓放和空间可达性。 | 若选此任务，闭环前读 |
| [Play Tic-Tac-Toe](https://robodojo-benchmark.com/doc/sim-tasks/play-tic-tac-toe/) | 与支持机械臂轮流落子，目标是完成摆放。 | 不要误读成棋局获胜；对手动作时有等待要求。 | 若选此任务，闭环前读 |
| [Fill Egg Holder](https://robodojo-benchmark.com/doc/sim-tasks/fill-egg-holder/) | 把四枚蛋入盒并合上盒盖。 | 理解收纳完成与关盖阶段的区别。 | 若选此任务，闭环前读 |
| [Organize Table](https://robodojo-benchmark.com/doc/sim-tasks/organize-table/) | 整理鼠标、键盘、摆件、闹钟；描述还有抽屉步骤。 | 注意当前评分表重点是四个目标物，细节再核源码。 | 若选此任务，闭环前读 |
| [Make Kong](https://robodojo-benchmark.com/doc/sim-tasks/make-kong/) | 等对手打出麻将，再识别匹配牌完成杠。 | 理解支持机械臂、等待和规则条件。 | 若选此任务，闭环前读 |
| [Play Stacking Toy](https://robodojo-benchmark.com/doc/sim-tasks/play-stacking-toy/) | 把4/3/2/1件四组积木放到对应柱上。 | 理解重复子任务与分组进度。 | 若选此任务，闭环前读 |

### Open：8 页，均标 eval-only

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Align Blocks](https://robodojo-benchmark.com/doc/sim-tasks/align-blocks/) | 用三角尺推齐三个积木，不能抬起。 | 理解工具指令和未提供官方训练示范的边界。 | 若选此任务，闭环前读 |
| [General Pickup](https://robodojo-benchmark.com/doc/sim-tasks/general-pickup/) | 按语言找目标并抬高10cm。 | 理解开放目标识别的最小任务。 | 若选此任务，闭环前读 |
| [Solve Equation](https://robodojo-benchmark.com/doc/sim-tasks/solve-equation/) | 挑选缺失数字/运算符补全等式。 | 理解符号识别和关系推理。 | 若选此任务，闭环前读 |
| [Stack Blocks By Language](https://robodojo-benchmark.com/doc/sim-tasks/stack-blocks-by-language/) | 按指定颜色顺序叠积木。 | 核对每个episode的语言与历史状态是否刷新。 | 若选此任务，闭环前读 |
| [Classify Objects By Language](https://robodojo-benchmark.com/doc/sim-tasks/classify-objects-by-language/) | 按语言指定的左右中篮子进行三类分拣。 | 区别任意篮子分类与指定映射。 | 若选此任务，闭环前读 |
| [Pick From Conveyor By Image](https://robodojo-benchmark.com/doc/sim-tasks/pick-from-conveyor-by-image/) | 根据示例图在传送带取物并放入抬起的篮子。 | 理解图像条件而非只有文本的目标。 | 若选此任务，闭环前读 |
| [Store Tools In Toolbox](https://robodojo-benchmark.com/doc/sim-tasks/store-tools-in-toolbox/) | 把四件工具放入对应形状槽位。 | 理解形状匹配与未见物体操作。 | 若选此任务，闭环前读 |
| [Pour By Language](https://robodojo-benchmark.com/doc/sim-tasks/pour-by-language/) | 按语言给出的颜色配对与顺序完成三次倾倒。 | 理解语言绑定和顺序要求。 | 若选此任务，闭环前读 |

### DLC：1 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [DLC](https://robodojo-benchmark.com/doc/sim-tasks/dlc/) | 在杂乱桌面把字母排成 RoboDojo；页面用途标 Train。 | 额外训练数据条目，不计入42基础任务/54评测配置。 | 需要扩充训练数据时 |

## 真机任务页：18 页

全部标注 Teleop 与 Train & Eval。每种机器人6任务；这些不是18个任务各跑三遍。初期仿真闭环无需先逐一实施真机操作，按未来目标选择阅读。

### Piper X：6 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Disassemble LEGO](https://robodojo-benchmark.com/doc/real-tasks/disassemble-lego/) | 拆开乐高并逐件放碗；末件还有换手过程要求。 | 学习接触较强的拆解任务和过程评分。 | 规划/申请该真机任务时 |
| [Cap Pen](https://robodojo-benchmark.com/doc/real-tasks/cap-pen/) | 双手拿笔与笔帽并套合。 | 理解小物体对准。 | 规划/申请该真机任务时 |
| [Classify Objects](https://robodojo-benchmark.com/doc/real-tasks/classify-objects/) | 将两类物体分入两个篮子。 | 与仿真三类/三篮设置区分。 | 规划/申请该真机任务时 |
| [Hang Mugs](https://robodojo-benchmark.com/doc/real-tasks/hang-mugs/) | 把三个杯子挂到架上。 | 看真实挂放与阶段分数。 | 规划/申请该真机任务时 |
| [Sweep Blocks](https://robodojo-benchmark.com/doc/real-tasks/sweep-blocks/) | 交接扫帚并扫入簸箕。 | 比较仿真与现实的工具操作。 | 规划/申请该真机任务时 |
| [Pack Objects Into Backpack](https://robodojo-benchmark.com/doc/real-tasks/pack-objects-into-backpack/) | 将三件物品依次装进背包。 | 认识柔性容器的真实收纳。 | 规划/申请该真机任务时 |

### Piper：6 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Fill Pen Holder](https://robodojo-benchmark.com/doc/real-tasks/fill-pen-holder/) | 拿起笔筒，逐支插笔，再放下。 | 核对真实收尾步骤与仿真差别。 | 规划/申请该真机任务时 |
| [Put Objects Into Basket](https://robodojo-benchmark.com/doc/real-tasks/put-objects-into-basket/) | 将所有目标物放入篮子。 | 简单收纳任务的全成全败评分。 | 规划/申请该真机任务时 |
| [Stack And Cover Blocks](https://robodojo-benchmark.com/doc/real-tasks/stack-and-cover-blocks/) | 先叠三块，再用杯子罩住。 | 串联两个子目标。 | 规划/申请该真机任务时 |
| [Stack Bowls](https://robodojo-benchmark.com/doc/real-tasks/stack-bowls/) | 在中央叠三只碗。 | 同名任务真实分档0/0.3/1与仿真不同。 | 规划/申请该真机任务时 |
| [Stand Up Bottles](https://robodojo-benchmark.com/doc/real-tasks/stand-up-bottles/) | 把瓶子立起；评分表按一/二/三瓶计。 | 标题和简述不能替代具体计分表。 | 规划/申请该真机任务时 |
| [Insert Charger](https://robodojo-benchmark.com/doc/real-tasks/insert-charger/) | 先插充电头，再连接充电线。 | 比仿真同类插头任务多一个连接阶段。 | 规划/申请该真机任务时 |

### ARX X5：6 页

| 官方页面 | 这一页讲什么 | 对当前目的有什么用 | 何时读 |
|---|---|---|---|
| [Insert Tubes](https://robodojo-benchmark.com/doc/real-tasks/insert-tubes/) | 把三支试管插到底。 | 理解真实插入深度和完成数。 | 规划/申请该真机任务时 |
| [Make Bread](https://robodojo-benchmark.com/doc/real-tasks/make-bread/) | 放两片面包入烤机，再把碗放到盘上。 | 不可直接等同仿真make_toast。 | 规划/申请该真机任务时 |
| [Make Food](https://robodojo-benchmark.com/doc/real-tasks/make-food/) | 摆砧板食材、装锅、上炉、加盖。 | 理解真实长流程和阶段验收。 | 规划/申请该真机任务时 |
| [Pack And Pour Fruit](https://robodojo-benchmark.com/doc/real-tasks/pack-and-pour-fruit/) | 水果逐个装小碗，再整体倒进大碗。 | 组合抓取和倾倒两种操作。 | 规划/申请该真机任务时 |
| [Cover Blocks](https://robodojo-benchmark.com/doc/real-tasks/cover-blocks/) | 遮住三色积木，再按指定颜色顺序揭开。 | 真实记忆任务与对应过程分。 | 规划/申请该真机任务时 |
| [Store In Safe](https://robodojo-benchmark.com/doc/real-tasks/store-in-safe/) | 玩偶入保险箱，再移至中央并关盖。 | 收纳结束还有位置与盖子要求。 | 规划/申请该真机任务时 |

## 已发现的链接错误与读取边界

- 递归遍历遇到77个候选URL：75个HTTP 200且非空正文；2个404来自 Submission 页末尾的错误相对链接。正确的目标页已成功读取，所以有效文档页没有因这两条错误而遗漏。
- 404：`/doc/usage/robodojo-submission/quick-evaluation/`；应为 [Quick Evaluation](https://robodojo-benchmark.com/doc/usage/quick-evaluation/)。
- 404：`/doc/usage/robodojo-submission/xpolicylab/`；应为 [XPolicyLab](https://robodojo-benchmark.com/doc/usage/xpolicylab/)。
- `/doc/sitemap.xml`、`/doc/sitemap-index.xml`、`/doc/sitemap-0.xml` 均404；站点级 sitemap 可读，但不是完整文档清单。覆盖以当前完整侧栏和递归正文链接为准；不声称发现没有公开链接的孤立页。
- web工具读取首页/protocol超时、parallel页不可访问；标准HTTPS请求成功回收全部75页。protocol的首个HTML只有应用壳，正文由官方`/assets/index-oIWaVVE1.js`中的协议数据对象取得。未提交任何表单。
- 安装页推荐驱动570/580，安装故障页转述Isaac 5.1 tested 580系列；以所锁定Isaac版本的官方硬件要求核验，不能只取较宽松的一句。
- 并行页与配置页写发布默认 `num_envs: 1`，但本轮直接读取固定SHA `726e9aab…` 及main的[sim_config.yml](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/env_cfg/sim/sim_config.yml#L5)均为10。运行前应核独立checkout最终值；先前导览将网页说法直接称当前默认，已在本次实施前纠正。
- 首页摘要写30 policies，XPolicyLab页当前写46；前者是论文/主页摘要，后者是更新后的适配清单，不等于每个模型都经过相同版本验证。
- 任务页描述与评分表偶有精细差别（例如organize-table、press-by-number、真机stand-up-bottles）。执行时以锁定源码与实际协议为依据，导览保留这些提示。

## 本地证据索引

- 完整URL/状态/标题/文件/媒体清单（完整本地证据未随公开版发布）
- 原始HTML目录（完整本地证据未随公开版发布）
- 逐页正文目录（完整本地证据未随公开版发布）
- 协议正文来源记录（完整本地证据未随公开版发布）
- 抓取脚本（完整本地证据未随公开版发布）

本地未运行网页中的安装、下载模型、训练或仿真命令；抓取只下载网页文本，不下载任务视频或大资产。
