# 深圳1 Dojo续评 · 2026-10-01

> 发布副本：以下保留来源文件各时间点的历史记录；未刷新服务器状态，未新增运行或 smoke 验收结论。个人路径以通用标识替代；本地证据与历史公开仓库附件未随包提供。
> [返回索引](../README.md)

**20:14:55四卡恢复验收完成：** 4卡N16十六环境各20步、6卡π0.5 N4累计5209动作并跨批；5卡正式插充电器306/400，7卡已完成general_pickup新批次并切随机吐司。全卡C/G表0–3均无进程，4–7仿真只在自身物理卡。测试仍执行中，正常完成后自动原W1/N4续评。当前唯一owner与路径见下一段，最末证据s047/s048；RLT低优先级保持原链。记录已本地保存，本次新辅助源码/文档尚未发布Git。

**10月3日20:10用户最新优先Dojo：** GPU0附带EGL问题已通过账户图形配置及私有单卡标记修复验证；4短诊断4回合/1669动作/真实RGB完成，20:05–20:11全卡C/G表0–3均无进程。现在4卡OpenWAM N16→25→36已重新派发（原N9完整50保留，原N16中断记录不作完整对比）；6卡π0.5 N4→9→16→25→36已真实动作，5/7正式原W1/N4续评。4/5新唯一owner3580494/start391608903，O/active-gpu4-maintenance.json指向runs/gpu4-scope-maintenance-20261003-v2；6新owner3544747/start391527513，7新owner3550893/start391545546，各原owner-dir/status.json为当前权威。旧owner/旧准备/旧diagnostic禁止重放。测试健康结束后自动回原Dojo；RLT低优先级，原周期/helper/CP/队列未改，未运行额外RLT试验。新只读入口dojo-sz1/scope-current.sh；旧gpu4-borrow-status不覆盖新路由。SSH93792，应用定时任务仍取消。见[卡位修复与双模型测试](GPU_SCOPE_FIX_20261003.md)。

**10月3日17:44用户改为只占4–7：** 3卡测试已精确停止释放，4卡正式已保存结果并暂停，改跑独立N9/16/25/36扩容，测完健康释放后自动按原W1/N4续评；5/6/7继续。4/5唯一监督已交接为3283651/start390732435，旧3881745已退役，不重放/CONT；仍复用原O/status.json、原RLT cycles，O/active-gpu4-scaling.json指向本次目录。探针owner3284935，输出`runs/sz1-gpu4-scaling-20261003-v1`。应用定时任务保持取消。现场与归还边界见[GPU4借测专题](SCALING_GPU4_20261003.md)。

15:44 GPU3对照两份轻量记录已推独立分支`codex/dojo-parallel-gpu3-20261003@7f887c4`并核远端，正式源码/main未改，见[对照专题](PARALLEL_GPU3_20261003.md)。

**10月3日15:38额外GPU3并行对照完成：** 同9布局OpenWAM标准叠碗，W1/N9=12分15秒/37.39GiB/9成功，W1/N4=18分45秒/36.06GiB/8成功；动作3133/3782，不能全把速度差归因于并行。两组退出0、54视频完整，3卡最终3MiB/recovery None/所属进程0；原3卡Stage1已完成，没有RLT借还。正式4–7配置/源码未改，继续OW4469/Pi3373。独立试验目录`runs/sz1-gpu3-parallel-20261003-v1`，原计数器ANSI假失败保留，独立观测核实；最终以comparison/final-released/verified-results为准，不重放probe。见[并行对照](PARALLEL_GPU3_20261003.md)，证据m028–m030。

13:23今日全景已推`codex/dojo-gpu7-audit-20261003@c3d9931`并核远端，新增报告、54配置覆盖表、轻量验收JSON三份记录；前次相机/审计提交均保留。回执l013，正式参数与运行源码无改动。

**10月3日13:06–13:17全面只读核查：** 13:06 OW4311/6300（seed0/1各2100、seed2=111），Pi05 3260/6300（seed0=2100、seed1=1160）；13:11继续增至4317/3264，四卡仍Dojo/recovery None。W1/N4，运行显存36–40GiB/卡，整机MemAvailable1917/2016GiB。7卡新owner15h10、正式续评近15h，未新增物理补丁。两模型seed0按官方五维等权Score/SR为16.65/11.68%与12.71/7.95%，仅一seed且2086/2100布局相同；未完成直接成功率不当官方总分。13:10共7577有效回合、22731非空三路录像无缺项，13:17共7588记录均找到官方layout文件。完整记录及54配置表见[今日全景](REVIEW_20261003.md)。SSH56170失效，按原授权固定身份重登录为93792；仅现场读与轻量Git发布，评估配置/进程原状，定时任务保持删除。

**10月3日11:30–11:33只读复核：四卡继续正式Dojo。** OpenWAM4248/6300（67.4%，已完成部分463成功/10.9%），Pi05 3206/6300（50.9%，198成功/6.2%）。7卡同一owner已运行13小时32分，原失败随机笔记本seed0/layout0–24全部完成（0/25成功），正在fasten_screws；新7正式目录10份日志未检出本轮扫描的坏姿态/CUDA700/设备丢失签名，四卡recovery None。**续评有效，尚不能归功于新的物理修复：昨晚正式物理/动作/相机/策略源码增量为0。** 新增的是独立诊断、CP625完整恢复副本及新7 helper身份未知状态修补；新cycle尚未终态归还RLT，不能预称恢复首轮验收通过。证据k002–k004；详细结论见[GPU7审计](DOJO_GPU7_AUDIT_20261002.md)。本轮未启停或修改正式任务。

SSH1415已失效，本轮按原授权重新登录，同一固定host-key和SERVER_USER/SERVER_GROUP/SERVER_UID核验通过；现控制终端56170，密码仍仅进程内。自动任务保持删除，原服务器owner继续。**11:43最新Git记录已推送并核远端：`codex/dojo-gpu7-audit-20261003@a0833dd543249df9c456aba24192fc30535ca8b8`**，继承已推相机215bad21；新增3份轻量记录（报告、验收JSON、一行状态差异），修改/删除0，main和运行源码保持。远端本轮报告（历史公开仓库来源未随包提供；个人账号地址已脱敏）。本地Git凭据工具无法启动sh，已复用既有SZ2独立publication库推送5.8KB bundle；只操作Git发布目录，未碰该机实验。回执k007。

**22:25收尾现场：7卡已完成正式首批关闭/重建，第二批184/800步；4/5/6/7继续Dojo，四卡recovery None。** OpenWAM3549/6300、Pi05 2475/6300。本次重新上卡与首批新增回合验收完成，服务器owner继续正式队列及终态RLT归还，应用定时任务保持删除。证据j027；未承诺历史故障根治。

**22:23本轮验收：物理4/5 OpenWAM、6/7 Pi05均为正式Dojo；7卡原失败任务新增4回合已落盘，三路RGB均801帧且中帧解码480×640×3通过。** 原seed0/layout0–3完整800动作，无CUDA700；7卡正在下一批场景重建。当前累计OpenWAM3545/6300（本机+310）、Pi05 2475/6300（+162）；4卡683/800、5卡417/1050、6卡789/1100，日志均新鲜，四GPU recovery None。证据j025首批验收、j026四卡现场。`gpu7-new-formal-batch-verified.json`在新owner下。定时任务删除已完成；各卡终态后仍由原服务器owner精确释放并归还RLT，7卡绑定完整CP625，不依赖应用heartbeat。GPU根因仍未唯一确定，本轮未部署猜测性的物理改动；已有有效修复保留。

**22:18：4/5/6/7均为Dojo正式路径，7卡已432/800步。** 22:11独立诊断四环境800步/8000tick与4结果/12视频完整，成功率0/4，无发散；退出后精确清理至7MiB/recovery None，自动exec原正式Sweep，当前正式客户端无trace hook。原始动作/逐物理步记录只在独立诊断目录，未并正式分数。本轮正式物理/相机/策略源码未改；相机关闭等已有有效修复保留，无证据的求解器候选未加入。22:18累计OW3541/6300、Pi2471/6300，7卡正式首批结果待完成；归还仍由唯一新owner负责，CP625保护已验证。证据j019–j023；根因仍未唯一定位，不能把这次未复现叫根治。

**22:00 GPU7受控诊断已启动，4/5/6既有Dojo保持。** 新唯一owner `gpu7-physics-v1` PID1088548/start383629585，指针`active-gpu7-continuation.json`仅覆盖7卡；6仍由`pi05-yamlfix`管理。新cycle`rlt-cycle-gpu7-physics-v1-gpu7`已精确撤原7卡RLT，从625轮独立完整副本保障归还（83554条索引、补齐3554条同entry原数据，模型/优化器/RNG/计数未改，j005–j007 CPU验证）。首批`diag-gpu7-20261002-laptop-v1`原Pi05/N4/seed0/layout0–3、物理参数未改；最多1200秒，记录真实动作与每物理步状态，异常先留证据并终止。四回合完整且卡健康空闲才exec原正式续评；失败由新owner归还RLT并核首轮。j008启动；22:00 policy与client均已启动，尚待实际动作。诊断结果独立，不并正式成绩。监测入口`gpu7-probe-status.sh`，通用summary/observe已识别新指针。定时任务仍已删除。

**10月2日21:45新授权：用户要求取消定时任务，深入定位后让4/5/6/7均运行Dojo，单卡故障后仍由服务器owner归还RLT。应用自动任务`1-dojo-rlt`已删除。** 4/5/6现有Dojo继续；7卡新增受控复现与续评在准备，未停止其RLT。先以当前最新模型/优化器/计数和原CP575中逐项一致的数据建立独立可恢复副本，原检查点保持。独立诊断只观察原失败首批，不混入正式成绩；有证据后才采用最小修复。以下定时监控与“不自动重启7卡”均为旧范围，不覆盖本次明确授权。

21:18自动只读刷新：4/5/6继续Dojo，OpenWAM3464/6300（本机+229）、π0.5 2460/6300（+147）；较21:03分别新增16、4回合。4卡390/550步、5卡288/700步、6卡井字棋新一批627/1100步，日志均为现场当秒，未发现新故障。21:18独立核7卡RLT driver身份仍匹配、存活、online=1，已619轮，首轮证明继续有效；四卡恢复动作None。证据h108–h109。原owner与pi05-yamlfix仍未全部终态，自动任务保持；未启停或修改正式任务。

**10月2日20:52诊断更新：4/5/6仍Dojo，7卡原RLT已612轮、身份与首轮均实核。** 20:46 OpenWAM3428/6300（本机+193）、π0.5 2456/6300（+143）。本轮没有改正式源码或启停GPU。7卡完整首错、历次补丁去留、实际部署diff与官方线索集中在[GPU7与修复审计](DOJO_GPU7_AUDIT_20261002.md)。最早可见坏状态是动作398→399时env3 laptop坐标发散，不能继续写“首次reset未动作”；此前camera补丁仅修关闭，未证实根治700。当前物理/动作源码相对固定上游无改动，Pi05代码亦无差异，575上595覆盖层自动禁用。

**7卡重新借做诊断前须处理恢复点限制：** 新CP600索引80494、文件80000，实缺494；g018严格检查失败，g019定位缺项。当前RLT继续，不停、不回退575、不补造检查点、不重放旧cycle。独立CPU诊断准备不进入正式评估；4/5/6无需中断。RLT身份未出现即报退出的一行候选经g022四项CPU检查通过，运行中冻结helper未改，独立观察回执仍是7卡首轮依据。后续自动任务保持原续评/终态逐卡归还范围，不自动重启7卡Dojo。

**10月2日20:09当前状态：4/5/6卡继续Dojo，7卡RLT推进至601轮。** OpenWAM3389/6300（本机+154），π0.5 2443/6300（本机+130）；较20:00两模型各新增8回合。4卡insert_tubes已完成40回合、当前批363/500步，5卡随机套娃已完成24回合、正初始化seed24末批；6卡push_T已完成16回合、当前批208/600步，三卡日志新鲜。GPU7 driver599576身份相同且存活、online=1，600轮critic更新755次，独立首轮证明仍有效。四卡recovery action均None。证据`steps/h104–h105`；本轮未启停任何服务器任务。

**SSH控制入口已更换为session_id=1415**：19:14旧43661返回Unknown process id；已按既有授权重新登录，host-key和SERVER_USER/SERVER_GROUP/SERVER_UID校验通过。新终端运行同一`dojo-sz1/session.py`，请求格式与本地helper均保持，凭据仅进程内。自动任务`1-dojo-rlt`已通过应用工具更新到新session及当前4/5、6/7路由，周期仍15分钟；勿再向43661发送请求。连接恢复未影响服务器Dojo或RLT。若以后终端再次失效，先尝试既有固定host-key登录，无法连接时报告真实阻碍，不重放远端owner。

**20:15完整日志纠正：此前“首次重置、未动作、四环境均耳机坏姿态”判断错误，原因是旧h085只截取致命错误附近。** GPU7在`store_laptop_and_headphones_random/seed0`已执行至398→399/800步；18:08:57首先观察到env3 laptop3世界坐标约(1.14e11, 1.23e12, -1.24e11)，18:08:58依次为env3积木、env0玩具飞机、env1/2耳机报Invalid PhysX transform。随后丢弃seeds0–3补4–7，进入相机清理，再于18:09:00出现`cudaMainGjkEpa`及CUDA700。故关闭前物理/场景状态已经发散，尚不能认定谁最先产生坏状态或归因相机/H100。完整证据`dojo-sz1/gpu7-investigation/original-client.log`与`steps/g002`；本轮正核查资产/动作/物理源码。Dojo终态和精确归还RLT事实保持，不在同卡重试、不reset。

GPU7 RLT已由既有接续控制器自动调起；18:18独立核验driver599576/start382248975、namespace`dr-sz1-rlt-cycle-pi05-yamlfix-gpu7-g7`存活，完整CP575→实际576轮，online=1、critic_updates_run=690。**控制器原始`NEEDS_ATTENTION: Resumed RLT exited...`是过早取样造成的状态误判**：`status()`在driver身份文件尚未产生时把未知写成`resume_alive=false`，owner立即停止了该卡的后续验证。实际进程没有退出，未为修监控而重启RLT。原始状态保留；独立完成回执为`pi05-yamlfix/gpu7-rlt-observed-first-round.json`，最新观测为`gpu7-rlt-observed.json`。

后续每次先执行`evaluation-progress-summary.sh`；出现归还/NEEDS_ATTENTION时再执行只读`observe-rlt-returns.sh`，按精确release/cycle调用原冻结helper的status并保存独立观测。状态摘要保留原owner错误，同时展示独立首轮证明。**不要因7卡这条已核实的旧误判重复恢复或重启；自动任务最终完成判断应接受该卡独立首轮回执，其他卡仍需逐一验证。** h086四张卡新视频均解码成功；7卡CUDA故障、RLT归还和四卡启动验收已于本轮通知，不重复报告。

**10月2日17:57：四张卡均已进入真实评估。** 4/5卡OpenWAM累计3259/6300（本机新增24：make_kong +4、stack_blocks_by_language +20），已产出可解码的480×640三通道实际视频。6卡π0.5 sweep_blocks_random的四环境均154/1000步；7卡sort_nesting_dolls_by_size的剩余最后一个layout已434/1050步，原预算25已完成24，因此该批仅1个有效环境。π0.5仍2313/6300，首批回合待结束。四卡recovery action均None。145.61GB迁移、三环境、准备核验均已完成；不再估算下载剩余时间。

6/7首次因base Python缺PyYAML、尚未进入推理即退出；自动归还RLT后两卡均验证真实首轮。补依赖后已分别完成模型加载、场景创建并开始动作。首轮RLT回执属于第一次归还，不代表现在RLT仍占6/7卡。

根因是启动脚本先用Miniforge base Python解析`deploy.yml`，此前环境检查只覆盖uv模型环境。已仅在该账号base补同版PyYAML6.0.2，实际配置解析和uv路径检查通过；模型/仿真源码不变。初次错误未进入GPU推理，不是CUDA700；当前没有新GPU故障证据。

当前GPU4/5仍由原owner3881745/start379867940负责；GPU6/7由其目录内 **`pi05-yamlfix`** 接续控制器556492/start382138424唯一负责，父owner的6/7 `RLT_RESTORED`是上一轮终态，不能覆盖新路由。权威指针`runs/sz1-dojo-continuation-20261002-v1/active-pi05-continuation.json`；新配置/日志在`pi05-yamlfix/configs/gpu{6,7}.json`和`pi05-yamlfix/lanes/gpu{6,7}`，新RLT回收cycle为`rlt-cycle-pi05-yamlfix-gpu{6,7}`。只在旧两卡首轮归还完成后交接；4/5 PID及源码/配置保持。不要重放旧owner、旧release或旧停止动作。

接续复用原控制器，仅限定6/7、单独控制日志目录，并让RLT准备读取刚恢复的上一cycle身份/实配/最新完整checkpoint；累计3000及Dojo W1/N4、54任务/3seed/6300、结果ID保持。服务器9项CPU边界检查、真实两卡plan-only及恢复源准备通过；`scripts/rlt/pi-yamlfix`与小配置留`source-frozen.json`。启动命令：原RLT Python运行该目录`owner_sz1.py --project <P> --owner-dir <原owner>/pi05-yamlfix --launch`。终态仍按精确清理→健康空闲卡→原RLT接回→首轮验证；不自动重试GPU致命错误。

刷新用本地`evaluation-progress-summary.sh`（累计/新增回合、每卡动作、当前owner/RLT首轮）和`evaluation-startup-status.sh`（最新日志），均已识别新指针。下一步确认π0.5新增回合及最终视频；`verify-new-rgb.sh`只解码已完成`episode_*.mp4`中的一帧，不读哈希。h080最初选中π0.5正在写入的`_stream/*.tmp.mp4`，其moov未完成不能解码属于未封装状态，不是视频损坏；helper已排除。自动任务完成条件同时检查原owner的4/5及`pi05-yamlfix`的6/7。证据`steps/h063–h081`。以下17:29、16:15和WAITING记录均为历史状态。

**17:29：145.61GB迁移已完整结束，安装收尾与部署核验均退出0，`deployment-ready.json`已生成。** 资产15365文件、OpenWAM9文件、π0.5 61文件和原两组结果全部到齐，轻量大小/源码/续评协议核验通过。唯一owner3881745进入`PREPARING_RLT_CYCLES`；17:30已完成GPU4/5/6原RLT恢复准备，GPU7正在准备，尚未用进程启动替代真实动作验收。既有owner随后逐卡精确停原RLT、启动4/5 OpenWAM与6/7 π0.5；不要再运行“等待期间原RLT必须全部存活”的断言脚本判断切换后状态。使用`deployment-boundary-status.sh`和`evaluation-startup-status.sh`刷新。证据`steps/h061–h062`。

**10月2日16:15：数据116.77/145.61GB（含partial和本机复用）；π0.5三seed权重61文件已全部到齐并通过大小检查，三环境已安装。Dojo尚未启动，原四RLT继续。** 资产34.90/41.27GB、OpenWAM23.75/24.84GB、旧结果/视频20.80/42.18GB。扣除现成manifest确定的重复资产，未提交到完整文件的网络数据约25.69GB（不扣正在传的分片），最近总入站约6.24MB/s。估计再1.5–2.5小时进入准备核验，约17:45–18:45；视频仍为主要剩余项，正式GPU启动时间取决于核验与加载。当前迁移、收尾、核验和唯一owner均存活，无未恢复的传输错误；两组视频持续增长。证据`steps/u012–u015`。

用户11:32重新授权，随后要求简化验收；大资产、权重、视频不再逐份读盘计算哈希，改为固定版本、文件数量与大小，启动后确认实际加载、RGB、动作和新增回合。少量源码/配置与结果JSON保护检查保留。已有partial接续，重复资产用现成manifest标识分组后本机复制；41.27GB资产含约12.75GB重复内容，无需重复走网络。

以下是迁移期间的历史：唯一owner3881745/start379867940，`runs/sz1-dojo-continuation-20261002-v1`，当时为`WAITING_FOR_PREPARATION`。当前迁移**261165/start381385413**（`runs/import-sz1-20261002`，15:45采用批量视频与小文件连接复用后接续），安装收尾3947292/start380038909（`runs/install-sz1-20261002-v2`，三环境ready，等资产改路径），准备核验3947295/start380038914（`runs/deployment-preparation-sz1-20261002-v2`）。旧安装3886851已结束：sim/π0.5成功，旧OpenWAM失败已由v2独立修复；不能把旧exit=1当当前失败。准备成功后4/5 OpenWAM、6/7 π0.5，W1/N4、原6300/模型；Dojo逐卡终态由同owner精确清理，健康空闲后恢复原RLT并核首轮。旧取消回执保留，其他窗口不要并行恢复SZ1或重放旧owner。

### 15:50：本轮最快传法与依据

短暂停止唯一迁移后，按相同文件/字节数串行比较，避免八路下载相互争带宽。1机只有公网eno1/default路由，另两物理口无carrier；三机无公网IPv6，既有私网探测不通。没有改网卡、路由、代理、驱动或共享训练。

|类别|受控样本结果（MB/s）|实际采用|
|---|---|---|
|资产|原生SSH7.10、Paramiko5.84、HF镜像4.25；官方HF连接重置|源机直传；同manifest重复内容本机复制；32MiB以下直传文件复用原有连接，每256MiB空闲换连接|
|OpenWAM|原生SSH7.26、Paramiko5.84、HF镜像4.50；官方失败|保留直传、既有partial与双分片；短时突发速度不能当长期速率|
|π0.5|原生SSH6.20、Paramiko5.84、HF镜像4.00；官方失败|保留固定版本直传与断点|
|SZ2旧视频|逐文件原生1.72、Paramiko1.47；复用5.91，rsync6.34（前一组复用6.28、rsync6.09）|按既有manifest精确批量rsync|
|SZ3旧视频|逐文件原生1.24、Paramiko0.30；复用4.84，rsync6.68|按既有manifest精确批量rsync|
|环境/SDK/普通安装包|已完成；此前对照选择源码/SDK复用、清华镜像、两份原机缓存|直接复用完成成果|

生产改动仅迁移helper：新增`bulk_results.py`，`peer_import_20261002.py`调用它搬尚缺视频；`route_transfer.py`将选中SSH的中小文件交给已有复用连接实现。rsync仅从清单读原视频、只核大小、保留partial、没有delete选项；源机不写入。源码、结果协议、四卡owner及RLT均保持。服务器CPU实际类复用/256MiB换连接/断点检查通过，原截断与软链检查、失败回退检查也通过；32份对照视频经大小核对进入正式目标目录。

15:46:58→15:49:34，实际增加**92个完整视频、226MB**；合计逻辑落盘增加1.129GB/156秒=7.22MB/s，包含本机重复复制，**公网总入站仍6.24MB/s**。因此改善的是小文件连接开销及最后视频阶段的速度，不能说整体网络快了四倍。当前资产32.43/41.27、OpenWAM21.79/24.84、π0.5 34.90/37.32、旧结果18.42/42.18GB。剩余逻辑38.06GB，其中还含可本机复用资产；估计还需约2–3小时进入准备核验，随阶段带宽重分配更新，不把16MiB突发样本当持续速率。

额外试了已有样本的zstd一级压缩：OpenWAM体积78.3%、资产87.1%、π0.5与视频约100%。这是小样本压缩率，不是端到端测速；当前未启用压缩。先保持已接续、已验证的生产传输，不继续反复停迁移做边际测速。

回执`steps/n002–n022`；完整受控报告`runs/routes-controlled-sz1-20261002-v1/report.json`与`v2/report.json`。v1测试副本从data到home使用rename发生跨盘错误，finally已自动接回原迁移；v2改为目标盘临时复制再原子发布，完整对照退出0，生产结果未损坏。旧迁移177959、239919、250362已精确停止并分别归档，不得重放。当前两组rsync及原RLT身份已实查；后续除主PID还应看两组`video_batch_*`、文件数/字节增长及失败回执，不能只凭主PID活着判断全部传输健康。批量/断点选项依据[rsync官方手册](https://download.samba.org/pub/rsync/rsync.1)，固定版本下载依据[HF官方文档](https://huggingface.co/docs/huggingface_hub/guides/download)。

### 15:10及此前的传输记录

本轮106大文件逐一比较固定版本HF官方、HF镜像、原生SSH与Paramiko，另有三次64MiB测试；官方HF连接重置，镜像约2.7–4.1MB/s、直传约3–6MB/s。短测受并发竞争，不能当总吞吐。小文件复用连接，OpenWAM单大文件两段并行，其余动态分配，合计八路。源码/SDK复用；普通安装包采用实测清华镜像，缺失且原机有缓存的两包直接传。15:10资产28.36/41.27、OpenWAM19.15/24.84、π0.5 30.21/37.32、旧结果/视频15.98/42.18GB。14:21→15:01合计增长约5.88MB/s（含本机复用）；安装包不在分母。旧视频为主要尾项；粗估完整迁移还需3–5小时，约18–20点进入启动准备，前提是其他传输完成后释放的带宽能用于视频。不能将合计速度直接等同所有单项完成速度；核心权重按近期单项速度约1–2小时。

15:00:54一份π0.5旧视频在0.28秒内连续三次原生SSH失败，单条结果迁移停止，其他传输继续。原文件存在、大小3177320正确，15:05直接读取成功；具体SSH拒绝原因未保留，不能断言服务端根因。只修改`route_transfer.py`：失败后等待1/2秒并交替原生SSH/Paramiko，记录简短错误，复用已有测速结论；仍保留三次上限和固定host-key。针对性CPU检查通过，只精确停止旧迁移3947169，所有partial保留；15:09新迁移177959接续。15:10该失败文件完整落盘、后续27段已成功，准备失败为空，RLT/owner/安装收尾没有重启。证据`steps/u007–u011`；旧日志留`runs/import-sz1-20261002/before-route-fallback-1506`。

仿真固定源机296项依赖；IsaacSim实际版本5.1.0.0，准备检查同步修正。OpenWAM保持原Torch2.7.1/Transformers5.17/Diffusers0.40；源机hub0.34.4本身不满足这两库的依赖，1机仅将hub对齐已安装且兼容的1.33.0，`pip check`为0，原冻结清单另存。π0.5按原uv.lock完成；sim和π0.5仅接受与源机相同的已知元数据冲突。服务器结果续评16项、传输断点/截断/软链3项检查通过。证据`dojo-sz1/steps/b044–b051`；测速`route-report.json`及服务器`runs/routes{,-detail}-sz1-20261002`。

本聊天自动跟进`1-dojo-rlt`已启用，每15分钟检查准备/真实启动/归还，健康推进静默。SSH控制session43661的凭据仅进程内；每次先读现场，失效不编造状态。详细命令和回执留本地任务目录，跨窗口不频繁发消息。

15:01复核：唯一owner与四条原RLT的UID/PID/start均相同且存活，准备失败回执不存在；15:08迁移恢复操作明确`rlt_mutated=false`。网卡总入站仍约6.24MB/s，包含本机其他流量，作为带宽观测而非单项资产速度。当前回执`steps/u004–u011`；定时检查`h001–h034`保留各阶段真实进度。健康推进不重复通知。

**以下00:39为保留的取消历史，已由上述本轮授权接续。**

**10月2日00:39用户明确中止，已执行。** Dojo安装、迁移、原版本对齐、准备核验与自动借还owner五组进程及其子进程全部停止；自动切换已取消。原GPU4–7四条RLT driver3025595/3025671/3025604/3025672的UID、PID/start与实际命令再次核同，均继续运行，未暂停或重启。已传文件、partial、环境与分支保留；原结果未修改。此前启动时间估计作废。终态`CANCELLED_BY_USER`，回执`runs/cancelled-by-user-20261002/receipt.json`与本地`steps/a059-cancel-preserve-rlt`；后续须新授权，不能重放已退出owner或旧ready。

以下为中止前的方案与进度记录，不代表仍在执行。

中止后00:42快照：已落盘17.41GB，包含未完成的partial文件，全部保留；`CANCELLED_BY_USER`、`rlt_untouched=true`。精确进度见`steps/a060-cancel-progress/stdout.log`，停止回执已下载为本地`cancel-receipt.json`。

用户授权：在深圳1安装Dojo；物理GPU4/5运行OpenWAM、6/7运行π0.5，接续原正式结果。安装期间原RLT继续；准备验收后逐卡借出；每卡Dojo完成或失败后，由本次唯一owner精确清理并恢复该卡原RLT。跨窗口仅一次交接通知，后续读共享记录和现场。

## 协议与资源

|项目|配置|
|---|---|
|项目|`SERVER_PROJECT`|
|缓存/视频|`SERVER_CACHE`，项目内软链接|
|源码|已实测相机修复`6dddac88a4fb9a72cbb9d39a90a9850e2ea811a8`；XPolicyLab `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4`|
|1机分支|RoboDojo `codex/sz1-dojo-continuation-20261001`；XPolicyLab `codex/sz1-openwam-lru-20261001`，均已在服务器建立|
|仿真|IsaacSim5.1.0，N4，每卡W1，原相机/渲染与动作协议|
|OpenWAM|GPU4/5，原固定权重`2c1302294e3ba8319bbdb2c803b7a27de9292d03`|
|π0.5|GPU6/7，原三seed权重`35efbc7dedfdbeeb6e95fb749bd885d73d483e41`|
|评估|每模型54任务×3seed、6300回合；已完成回合保留，只运行剩余布局|
|端口|OpenWAM63140–63147；π0.5 63160–63167|
|原RLT|GPU4/5 place_phone_stand clean/combo；GPU6/7 pick_dual_bottles clean/combo，累计3000轮不变|
|平台|8×H100；驱动575.57.08保持，系统CUDA12.9保持|

保留旧结果ID：`sz2_openwam_official_6300_n4_dual_20260929_r2`与`sz3_pi05_official_6300_n4_dual_20260929_r2`。GPU重新分组不改变task/seed/result身份。两模型各两卡，不等价于历史四卡吞吐；任务与预算不变。

## 自动流程与停止条件

1. 固定host-key与身份核验后，只读导入2/3机固定源码、资产、推理权重、结果和恢复清单。按用户10月2日要求，大数据只核固定版本、文件数和大小，不重复计算每份哈希；三套环境在1机新目录重建，准备期间RLT继续。
2. 服务器CPU检查、完整正式plan、结果/恢复清单验收通过后才生成`deployment-ready.json`。唯一owner等待该回执；准备失败或超时，原RLT继续。
3. 四条RLT分别冻结实际命令、PID/start/namespace、原配置和完整checkpoint。缺失replay payload或DCP越界的checkpoint不能使用；没有完整checkpoint则拒绝撤卡，不fresh、不重训Stage1。
4. 逐卡停止精确原RLT并确认空闲，然后启动该卡私有Dojo controller。相机关闭补丁与正常吐司批次隔离沿用；GPU fatal后停止该卡，不在故障卡多层重启。普通无进展仍为原1800秒。
5. 每卡终态精确清理owned进程；原RLT只在该卡无进程、`gpu_recovery_action=None`后恢复。恢复后必须核验checkpoint加载与真实首轮推进。设备需要恢复、归属不明或checkpoint异常则记录NEEDS_ATTENTION，其他卡继续。

不修改共享Ray、其他用户、0–3卡训练安排或2/3机当前WM/EXPO。H100原生RTX/MMU历史故障仍未确定根因；本次运行不把CPU通过或启动完成当作GPU长期稳定证明。

## 当前实测阶段

- **00:28传输盘点（GB为10⁹字节）**：资产6.09/41.27，OpenWAM2.86/24.84，π0.5 5.72/37.32；待搬原结果/视频42.18。合计已落盘14.66/145.61GB（约10.1%，含未传完的partial）；剩余130.95GB。另有安装包并行下载，不并入服务器间搬运进度。
- 00:26:32→00:28:03的90.81秒内新增375.21MB，合计4.13MB/s；资产2.10、OpenWAM0.55、π0.5 1.48MB/s。按合计速率纯数据还需约8.8小时，但OpenWAM单大文件更慢、旧视频后搬，不能把合计速度直接当每阶段速度。暂估10月2日14–18点进入Dojo（安装/校验正常且带宽相近）；这是启动时间估计，评估完成时间待真实回合速率。回执`a056-transfer-sample1`、`a057-results-sz2-size`/`sz3-size`、`a058-transfer-sample2`。
- **10月2日00:13：自动流程已启动，处于`WAITING_FOR_PREPARATION`，正式Dojo尚未开始。** 原四RLT driver 3025595／3025671／3025604／3025672的UID、PID/start和实际命令均核对通过；watch原任务与namespace保持，`rlt_untouched=true`。
- 安装与迁移结束后，由既有后台程序自动完成准备核验、逐卡撤RLT、Dojo续评、终态单卡归还。安装等待上限36小时；准备失败或超时保留原RLT，不重放旧启动。
- 后台：迁移2408605（00:21）；初次依赖安装2260260；原版本对齐2352023（等待初次安装退出）；部署检查2364666；唯一借还owner2364673/start375714163。owner目录`runs/sz1-dojo-continuation-20261001-v1`，部署检查目录`runs/deployment-preparation-sz1-20261001`，只读状态见各自JSON/log。
- 服务器CPU已通过：单卡RLT9项、两模型lane各10项、owner8项、真实结果/续评边界16项、依赖冲突分类10项。只覆盖这些边界，不代报GPU评估成功。
- 00:05剩余空间约data817GiB、home469GiB。迁移已有9000个文件通过校验；权重大文件仍为partial。00:05→00:08，OpenWAM同一partial从2,185,232,384增加到2,332,033,024字节，传输继续。IsaacSim扩展SDK与π0.5依赖仍下载中。
- 首次OpenWAM安装完成后发现Transformers随新安装升到5.18.0；后继安装按2机112项源环境约束恢复5.17.0，保持原Torch。π0.5沿原`uv.lock`。只接受源环境已实证的固定元数据冲突，保留真实`pip check`返回码与报告；未知冲突阻断ready。
- 迁移出现SSH重协商默认30秒超时；延长等待后00:16仍复发。因此保留正确关闭路径，累计传256MiB后在下一段开始前关闭空闲连接，下一段最大128MiB，避开在读取大段时撞上原512MiB重协商阈值。原host-key、加密、重协商阈值、hash、每段四次上限保持。仅精确停止本次旧迁移2277152/2363042，保留所有已校验/partial文件；00:21迁移2408605接续，没有操作RLT或Ray。实际Transfer类的断点/完整hash/换连接和关闭异常两项服务器CPU检查通过；真实大文件完成仍待验证。[Paramiko等待源码](https://github.com/paramiko/paramiko/blob/5.0.0/paramiko/transport.py#L1670-L1694)、[阈值源码](https://github.com/paramiko/paramiko/blob/5.0.0/paramiko/packet.py#L66-L75)。
- 本轮关键回执：`steps/a037-create-sz1-branch`、`a039-final-cpu`、`a040-launch-installer-v2`、`a043-transfer-precise-repair`、`a044-resume-peer-import`、`a045-arm-deployment-owner`、`a046-armed-status`、`a047-prep-progress`、`a050-original-rlt-verified`、`a052-bound-transfer-connections`、`a053-transfer-cpu`、`a054-resume-bounded-transfer`。

以下为准备过程早期快照：

- 22:14独立项目与缓存已创建；1机到2/3机公网SSH可达，私网路径不通，采用公网只读迁移。
- 22:50单卡RLT helper服务器9项CPU检查通过，CUDA未初始化、未发信号、未连接Ray、未启动训练；575的GPU恢复状态查询可用。
- 22:57两套conda Python环境创建完成；Torch原版本安装已后台启动，PID2227460。原四RLT尚未暂停。
- 安装、结果迁移、正式launch与归还均需各自新回执；不能以以上准备证据代报正式评估已开始。

本地源码/现场回执入口：`LOCAL_EVIDENCE/dojo-sz1`。此目录保留轻量command/receipt及候选源码；模型和视频留服务器。
