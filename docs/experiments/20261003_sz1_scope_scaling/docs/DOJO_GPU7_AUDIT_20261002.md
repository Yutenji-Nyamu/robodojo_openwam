# Dojo GPU7首错与既有修复审计 · 2026-10-02

> 发布副本：以下保留来源文件各时间点的历史记录；未刷新服务器状态，未新增运行或 smoke 验收结论。个人路径以通用标识替代；本地证据与历史公开仓库附件未随包提供。
> [返回索引](../README.md)

当前结论：**还没有一项修复被证明根治历史GPU700。部分改动确实修复了独立错误，不应全部回滚。** 本次把7卡故障从笼统的“CUDA700”收敛到：首批真实动作398→399附近，env3笔记本世界坐标先发散，之后多环境物体坏姿态，最后关闭/重建过程报告700。尚未找到最先产生坏状态的动作或原生物理步骤。

**10月3日11:33复核：续评已连续推进超过13小时，根因修复仍未证实。** 7卡原随机笔记本seed0的25个layout全部完成（成功0/25），已进入后续fasten_screws；新7续评目录10份日志约11.6MB，扫描Invalid PhysX transform/CUDA700/ERROR_DEVICE_LOST等签名无命中。四卡仍Dojo、recovery None；OpenWAM4248/6300、成功463/4248=10.9%，Pi05 3206/6300、成功198/3206=6.2%。数据均为已完成部分，不是全量最终成绩。k002–k004现场回执。

最新改动归类：昨晚没有新增正式物理/动作/相机/策略补丁；已有相机关闭修复继续保留。实际修补是新7 RLT helper将无身份的`resume_alive`设为None，以及CP625独立恢复副本补齐3554条缺失原payload。独立trace诊断完成后卸载，正式客户端仍原路径。新cycle尚未终态，因此恢复副本目前仅通过严格CPU检查，不能称已实测归还首轮。此前相机215bad21已经推送并再核远端；最新审计原先只写本地，现于11:43补推`codex/dojo-gpu7-audit-20261003@a0833dd543249df9c456aba24192fc30535ca8b8`，远端SHA核同。新增3份轻量记录/修改0/删除0：本轮报告及验收（历史公开仓库来源未随包提供；个人账号地址已脱敏），未把服务器专用owner、模型或原日志视频复制进库；回执k007。

21:00现场：物理4/5 OpenWAM、6 π0.5仍运行；累计3444/6300、2456/6300，本机分别新增209、143回合。6卡井字棋第843/1100步，日志新鲜。7卡原RLT driver599576在20:52独立确认已612轮。此次审计没有修改正式Dojo源码、启停GPU任务或重置GPU。

## 1. 更正此前错误判断

旧h085截断日志只保留致命错误附近，导致“首次reset未动作、四环境都是耳机报错”的判断错误。完整144952字节日志显示：

| 北京时间 | 首次可见现象 | 能证明什么 |
| --- | --- | --- |
| 18:08:57，动作398后 | env3 laptop3多个部件同一世界坐标约(1.14e11, 1.23e12, -1.24e11) | 相机关闭前，场景状态已异常；不是正常离屏停放的1e5米 |
| 18:08:58，动作399 | env3积木、env0玩具飞机、env1/2耳机Invalid PhysX transform | 坏状态已影响多个环境，不能只归因耳机资产 |
| 随后 | 上游逻辑abandon seeds0–3、refill4–7，开始相机清理 | 此时发生的detach警告晚于首次坐标发散 |
| 18:09:00 | cudaMainGjkEpa / Narrowphase700、后续分配与CUDA context失败 | 错误在GPU物理/清理路径被报告；异步报错不能定位最早非法访问 |

完整原始日志（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/gpu7-investigation/original-client.log`，未随包提供）。没有故障前逐动作数值或逐物理步轨迹；本次Pi05失败目录未保留可回放视频，因此不能从旧记录还原第一次速度突增。

历史有相似链条：9月29日robot/link、9月30日bread曾先Invalid transform、后700，但间隔分别约25分42秒、47分44秒。另9月30日13:30吐司首700前的现存片段未发现同类姿态警告。**相似症状不等于已证实同一根因**；未找到旧笔记本同坐标发散的直接复现证据。历史首错取证（包外本地来源：`LOCAL_EVIDENCE/dojo-fix-review/steps/g003-toast-first-fault-sz2/stdout.log`，未随包提供）

## 2. 到底有哪些自己的改动

现场RoboDojo为`6dddac88`，分支`codex/sz1-dojo-continuation-20261001`。与固定上游`726e9aa`比较，物理、机器人动作、控制器、对象、场景及任务源码diff为空；没有自行改力、刚度、步长、碰撞器或求解器。XPolicyLab虽然从bb9a0b5更新至10ab265，但Pi_05目录diff为空，当前也无Pi_05 dirty源码。其OpenWAM目录只有LRU两行逻辑修复。

实际新增仿真源码主要为相机关闭2文件20+/7-、吐司限定隔离，以及原部署N4配置与启动脚本。原版已有的Invalid→abandon/refill、普通异常后eval_step、PhysX监控和三次原生重启，并非我们添加。SZ1启动配置已把fatal重启计数预置上限、bash限制一次，外层遇fatal立即停止；不能把参数count=3误读为“允许再试三次”。

完整部署差异（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g016-upstream-diff/stdout.log`，未随包提供）、Pi05版本核对（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g017-version-video-audit/stdout.log`，未随包提供）。curobo版本指针有变，属于规划器依赖；当前Pi05 joint动作不调用该IK规划路径，不能把它说成最近添加的物理修复。

## 3. 历次措施的去留

| 措施 | 决定 | 实际价值及限制 |
| --- | --- | --- |
| GLU/EGL/CUDA/NVML依赖、PyYAML、兼容Hub依赖、端口检查 | 保留实测必需项 | 分别有缺库、缺模块、依赖冲突或端口占用证据。保证能启动，不声称治700 |
| OpenWAM LRU两行修复 | 保留 | 原缓存淘汰可复现KeyError；修复后100次淘汰检查通过。Pi05不走此代码 |
| 相机关闭2文件20+/7- | 保留 | 修创建/清理字段错位、实际解绑、唯一销毁、清空引用；同N4两轮RGB/reset/close通过。旧验收没有加载策略或动作，不能推导物理长跑稳定 |
| W2→W1 | 保留 | SZ3实测NVTT cudaMalloc失败且显存约80GB；降低副本占用有依据。SZ2约38GiB也700，故不是完整答案 |
| 单GPU渲染约束、结果/布局保护、精确清理、短输出名、逐卡归还 | 保留 | 保证共享资源边界、保护已完成数据和恢复RLT。本次7卡结束后4/5/6仍推进，归还首轮也有证明 |
| Watchdog、独立lane | 保留既有的一套 | 前者防原生卡死无限占卡，后者避免健康卡等待；不计作底层修复，不再叠加新恢复层 |
| 吐司每个正常batch换sim | 限定保留，待受控对照 | 有真实换PID/精确续队列/seed完成25回合证据，但未证明降低故障率。只限OpenWAM/随机吐司/N4；本次Pi05笔记本未启用。相机修复后有无必要仍待A/B |
| Vulkan595分配上限兼容 | 按驱动条件保留 | SZ2/3有启动失败→通过证据。SZ1是575.57.08，wrapper的595条件不满足，覆盖层自动禁用；不是7卡当前有效变量 |
| 致命GPU错误后多层同卡重启 | 退出正式路径；SZ1已做到 | 不把污染上下文的反复重启当根治。旧reset曾恢复设备，但本轮不自动reset |
| TAA/关闭DL去噪、120行readback guard、PR58/60/61、旧大相机候选 | 留独立诊断归档，正式不采用 | 没有对上本次首错的因果证据；改变图像或调用路径的候选不能混入正式分数。此前就未部署，不能虚报“现已删掉正式补丁” |
| 旧owner/准备/一次性恢复入口 | 隔离旧入口，保留冻结证据和依赖 | 当前只读active pointer；已停进程不重放。删除整个旧目录会损坏恢复脚本和可追溯性，不做批量删除 |
| RLT身份文件未生成即报退出 | 一行修补已进入新7 cycle | `resume_alive`在无身份时为unknown，而非False。g022服务器CPU验证原误报可复现、未知等待、存活等待、真正退出仍失败，共4项通过。10月2日新7 helper采用`identity is not None`；原4/5/6冻结helper保持，新7尚未终态归还，不能称本次真实归还已验收 |

因此不是“大部分补丁都在当前仿真里而且该删”，而是**过去大量工作属于启动、结果保护与恢复，未触及首个GPU故障；应纠正成果归类，减少候选和重复入口**。本轮没有依据回滚已经验证的依赖、LRU或相机关闭修复。

一行状态候选（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/gpu7-investigation/rlt-status-startup-race.diff`，未随包提供）、4项服务器CPU回执（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g022-rlt-race-cpu/stdout.log`，未随包提供）。这是归还状态误判修复，不能算GPU700修复。

## 4. 本轮深入核查及排除

实际服务器只读源码、USD CPU解析，没有启动SimulationApp或分配测试GPU：

- 第一批4布局的46个rigid/articulation项位置有限、四元数正常；这不排除接触重叠或后续动作导致穿透。
- 三种笔记本都是浮动两link关节物体，hinge drive最大力1、刚度0、阻尼3；X5本来已有力/速度限制，不能再补“缺失的限幅”。
- 笔记本触控板SDF网格闭合、流形、面方向一致，8点6面，无退化三角形。未命中新版PhysX“SDF面方向异常”修复条件，故不借此盲升级。
- 安装版本已有跨环境碰撞过滤路径；未证明漏过滤，不添加第二套filter。
- 配置中的CPU指张量/后端设置；源码显式强制GPU PhysX。不能把这次说成CPU物理崩溃。
- action校验只有键和shape，未记录本次原始动作，无法排除有限但极端的策略目标，也不能断言发生过NaN输入。
- 笔记本质量/惯量由运行时根据碰撞几何和密度计算，静态USD未写MassAPI不等于质量为0。还缺实际link质量/惯量、接触与首个速度跳变记录。

证据：源码与布局（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g002-root-source-log-audit/stdout.log`，未随包提供）、USD属性（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g010-usd-cpu-static/stdout.log`，未随包提供）、SDF拓扑（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g013-sdf-topology-cpu/stdout.log`，未随包提供）。

## 5. 官方/社区线索如何收敛

| 一手来源 | 与本例的关系 | 采用边界 |
| --- | --- | --- |
| [NVIDIA Invalid PhysX transform答复](https://forums.developer.nvidia.com/t/invalid-physx-transform-detected/265626) | 数值不稳定/NaN可表现为坏姿态 | 支持先抓物理状态，不把700行直接当根因 |
| [RTX4060也有坏姿态→Narrowphase700报告](https://forums.developer.nvidia.com/t/disappears-when-an-object-collides/338690) | 类似链条并非H100独有 | 未解决个案，不证明与我们同因 |
| [107.3 articulation稳定性指南](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/articulation_stability_guide.html)、[PhysX5.6.1 drive稳定性](https://nvidia-omniverse.github.io/PhysX/physx/5.6.1/docs/Articulations.html#articulation-drive-stability) | 接触、drive、关节限位及质量惯量可共同造成刚性约束失稳 | 优先记录夹碰/限位/速度；不盲目增迭代或调刚度 |
| [107.3接触求解顺序](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/articulation_stability_guide.html#articulation-solver-order) | `solveArticulationContactLast`专门针对夹持中接触约束 | 仅当固定动作复现显示接触异常后做单项A/B；目前未启用，未声称已修好 |
| [110.3发行记录](https://docs.omniverse.nvidia.com/dev-guide/latest/release-notes/110_3.html) | 修复不一致winding的旋转SDF问题 | 我们已查的触控板不匹配；不据此整体升级 |
| [官方5.1 CameraView](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/extensions/isaacsim.sensors.camera/isaacsim/sensors/camera/camera_view.py)、[解绑/销毁成功反馈](https://forums.developer.nvidia.com/t/how-to-destroy-a-render-product/255637) | 先detach再destroy再清引用是同版本原生清理方式 | 支持保留最小关闭修复，不支持称其能治动作期物理发散 |
| [OmniPVD](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/ux/source/omni.physx.pvd/docs/dev_guide/physx_visual_debugger.html)、[Compute Sanitizer](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html#memcheck-tool) | 物理轨迹和更早非法访问的诊断工具 | 先低开销逐步记录，重工具用于已有稳定复现，避免直接拖慢正式评估 |
| [Isaac5.1硬件要求](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html) | H100仍不在支持的渲染GPU范围 | 平台风险仍在；现有证据不足以把本次唯一归因H100或595驱动 |

还检索了上游RoboDojo laptop相关issue、PhysX/IsaacLab关节爆炸、接触/限位及CUDA context案例。本轮未找到与本任务/资产/版本完全匹配且已有成功复现的直接补丁；泛泛调参建议不进入正式源码。

## 6. 下一次最小诊断与当前限制

22:25进一步实核：7卡正式首批关闭后成功重建，第二批184/800步；这补足了独立诊断exit85没有覆盖的close/重建观察，但仍只是一次实际跨批通过，不能外推长期无GPU故障。j027现场四卡继续Dojo，累计OW3549/Pi2475。

**22:23正式新增回合验收完成：** GPU7正式原laptop任务首批layout0–3已4回合完整落盘，三路RGB首条视频各801帧，中帧CPU解码为480×640×3；实际正式路径无诊断hook、原物理配置。四卡均Dojo、recovery None；7卡进入下一批重建。证据j025–j026，结果与独立诊断严格分开。此次恢复评估已实现，尚不能宣称历史GPU700根治。

**22:11首批诊断实际通过运行完整性验收，22:14已进入原正式动作。** 四环境layout0–3各800动作，共8000物理tick（每动作10×0.004s），12视频/4条结果完整，任务成功0/4；无范围停止或CUDA700。退出85后精确清理，GPU7实测空闲7MiB/recovery None，继而exec原正式Sweep，诊断数据未并成绩。原正式仍沿同一结果ID/W1/N4/6300，新物理补丁为0。j019完整首批、j020状态汇总、j021正式动作留证。

本轮记录800次原始action，数值有限，最大绝对值2.438；四laptop最大根速度0.417–0.710m/s、最大位移0.119–0.338m，未复现历史万亿坐标。实际惯量特征值全正2.69e-4–9.33e-4，各矩阵条件数3.204/3.093，排除这批入口零质量、奇异惯量、两link参数悬殊。**没有稳定复现就不能认定根因已修复，也没有依据添加接触顺序或碰撞器改动。**

逐动作复现限制已核源码与权重：当前Pi05为JAX params分支，默认`key(0)`，每次infer split；CLI seed选权重，没有传入policy RNG，reset只清观测而不复位RNG。历史同server先跑nestingdolls再跑laptop，本轮独立先跑laptop，推理调用历史不同；输入RGB及读状态同步也可能影响轨迹。只能称同checkpoint/layout/配置重跑，不能称历史动作回放，不能断言这次具体哪一步动作不同。现在保留的raw action可供后续同动作对照，不为诊断擅自修改正式seed规则。小源码`gpu7-investigation/{pi05-model.py,openpi-policy.py,openpi-policy-config.py,openpi-pi0.py}`，实测后端见j020。

**22:04更新：用户已授权本次GPU7重新上Dojo，定时任务已删除。** 已先补齐CP625独立恢复副本：83554条索引/80000原文件，3554条缺失payload全部从原CP575按完整entry匹配补回；保留最新模型、优化器、RNG和计数，严格原检查器通过。新GPU7 owner于21:59启动，22:02实核四环境真实动作41步/800，原配置未改。独立trace已捕捉四laptop实际两link质量0.250259/0.244225kg，惯量矩阵有限、对称，初始化位置/速度正常；静态USD缺质量字段不能再作为零质量依据。诊断CPU检查增至15项，恢复选择拒绝旧CP回退3项通过；j005–j014留证。首批观察不证明close/重建或长期稳定，不能将一次未复现称为修好。

安装版本已现场核实`omni.physx107.3.26`，已包含107.3.25 `setInertia`主轴修复及107.3.24接触求解顺序选项。旧GPU primitive/非GPU凸体CPU fallback崩溃修复更早属于PhysX5.5/106.4，当前已含；相似warning不足以套用旧bug。新增线索仅保留接触顺序单bool对照，以及首坏碰撞确认box↔box时才相关的5.9 edge-edge漏接触修复，均未进正式。[固定107.3/PhysX5.6.1变更记录](https://raw.githubusercontent.com/NVIDIA-Omniverse/PhysX/107.3-physx-5.6.1/physx/CHANGELOG.md)、[OmniPhysics版本记录](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/ux/source/omni.physx.bundle/docs/CHANGELOG.html)。

独立诊断只观察原场景、N4、seed0首批layout0–3、原Pi05 joint动作。生产源码保持；记录未修改的输入动作及每物理步前后laptop根姿态/速度/关节状态，首次非有限或明显越界即保存证据并退出，不进入补种子循环。正常初始化会临时将对象移到1e5米，因此阈值必须在run_eval动作阶段才启用。阈值是诊断停止条件，不是夹断动作或修复物理。Getter会增加同步，可能影响时序，不能把一次未复现当修复成功。

20:57独立hook与fake对象检查已放到服务器`diagnostics/gpu7-20261002-v1`，12项纯CPU检查通过，正式源码未修改、GPU复现尚未启动。检查覆盖初始化远移不误停、原动作对象/参数/返回不变、原调用仅一次、坏输入不送物理、首次越界/读取异常落盘退出、首批完成退出85、诊断失败退出86。内部20分钟/1GiB限额不保证截断持有GIL的原生卡死，实际借卡启动仍需外部超时及既有精确收尾；不能凭CPU检查宣称GPU诊断已验收。诊断源码（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/gpu7-investigation/trace_hook.py`，未随包提供）、12项服务器回执（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g024-trace-cpu-check/stderr.log`，未随包提供）。

先复现，再按证据仅改一项：若是坏输入，定位生产该目标的adapter；若是接触/关节约束失稳，固定原动作回放做单参数对照；若状态读取前已原生非法访问，再走原生GPU诊断。更换碰撞器、质量、相机画面或布局均不直接并入正式评分。

**20:44–20:45恢复点核查阻止了冒进借卡。** GPU7 RLT当前global_step_600的索引/metadata为80494，真实replay文件80000，缺494、额外0、零字节0，严格恢复校验失败。这不是只有helper误报的身份文件竞态。没有停止当前RLT、没有改检查点、没有静默回退575。需要先获得可靠新恢复点，或明确决定如何处理回退，才能借7卡做短GPU复现；4/5/6健康评估不为此中断。

恢复点校验（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g018-checkpoint-readonly/stdout.log`，未随包提供）、精确缺项计数（包外本地来源：`LOCAL_EVIDENCE/dojo-sz1/steps/g019-checkpoint-index-readonly/stdout.log`，未随包提供）。两次均CPU只读，CUDA未初始化。
