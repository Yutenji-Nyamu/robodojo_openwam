# 深圳3 π0.5 × RoboDojo 完整官方评测

2026-09-29 用户授权：参考深圳2启动正式全面评测，暂借本人GPU4–7，结束后自动从最新有效checkpoint恢复原RLT；同步粗细日志并推同仓库SZ3分支。

## 固定评测口径

| 项目 | 配置与依据 |
|---|---|
| 任务预算 | 官方54可执行配置，seed0/1/2，原生25/50回合，每seed2100，总6300 |
| 权重 | 官方Pi_05三个训练seed分别配环境seed0/1/2，均step59999；revision `35efbc7dedfdbeeb6e95fb749bd885d73d483e41` |
| 动作与模型 | 官方joint，14维双臂关节/夹爪；默认chunk50、采样10步，JAX内存比例0.3 |
| 并行 | 参考SZ2：GPU4/5/6/7，每卡2独立worker，每worker4环境，共32环境；正式启动后核真实资源与动作 |
| 任务来源 | 官方task_inventory及_task.yml，官方耗时权重算法分8组；不挑seed或排除困难任务 |
| 源码起点 | SZ3首次成功commit `d82ad41399e13177c381d937d6a7fa4321577d47`；XPolicyLab `10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4` |
| 仿真 | 成功的Isaac5.1、本机EGL/动态库登记、进程级595 Vulkan兼容；num_envs仅1→4 |
| 资产 | 固定revision `43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab`；15365文件，共41,269,513,111字节 |
| 停止条件 | 全量结束、控制器中断或基础设施错误后清理本批；确认进程与GPU释放后恢复RLT。无10小时/30分钟实验截止 |

π0.5的官方多环境接口逐环境调用模型，与OpenWAM的批量前向不同；32并发是资源安排，不宣称已证实相同吞吐。当前缺少跨任务速度，正式运行后再估时；不沿用OpenWAM的20–40小时为π0.5实测结论。

官方依据：[完整评测与25/50预算](https://robodojo-benchmark.com/doc/usage/quick-evaluation/#complete-evaluation)、[并行环境](https://robodojo-benchmark.com/doc/sim-tasks/parallel-environments/)、[Pi05官方适配](https://github.com/XPolicyLab/XPolicyLab/tree/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/Pi_05)。本轮已用内置浏览器核对完整评测页。

## 现场与必要适配

- 15:00 SZ3：GPU4–7仍为上轮自动恢复的四组RLT，0–3空闲；内存可用约1.73TiB，数据盘可用约6.92TiB，根约9.45GiB。模型、资产、缓存和输出继续进自己的数据盘项目。
- 15:02 SZ2只读参考：旧_r2控制器已进入CLEANUP_FAILED/RESOURCE_RETURN_NEEDS_ATTENTION，原因是扫描本批开始后出现的同UID但environ不可读进程时抛PermissionError；卡上仍有评测进程。不能将该批记成正在健康推进。本轮不重放其派发或启停操作。
- SZ3复用官方server/client、任务分组、满预算验收和精确清理；进程扫描修正为：未证明归属的无关不可读进程不作为本批目标；已记录归属或本控制器后代不可读仍报错，恢复前仍核GPU真实释放。增加对应CPU回归检查。
- 本次RLT来源是上次Dojo归还后的新run，不能读取原deployment索引后重停旧driver。新的借卡cycle精确引用前次恢复路由；若新run尚无checkpoint，校验并沿用它实际加载的checkpoint，而非重开Stage2。累计目标3000与全部算法/预算参数保持。

## 命令、输出和当前路由

部署项目：`/data/chenyiteng/projects/robodojo-openwam-sz3`；源码在内部`RoboDojo/`，分支`codex/sz3-dojo-openwam-pi05`。

当前run：`sz3_pi05_official_6300_n4_dual_20260929_r2`；控制器位于`$PROJECT/scripts/pi05_formal_20260929_r2/`，端口63080–63087。外层读取`dojo_sweep.config.json`，依次完成资产、权重与配置核验、暂停四组RLT、全量评测、归还GPU并恢复RLT。原无后缀attempt因端口冲突退出；_r1在仿真启动时遇到瞬时进程权限读取竞态，均回合0，单独保留。

实际任务入口形状：

```bash
bash scripts/robodojo.sh server --policy-dir XPolicyLab/policy/Pi_05 \
  --ckpt sim --action-type joint --env-cfg arx_x5 --seed <0|1|2> \
  --task <本worker首任务> --policy-env uv --policy-gpu <4|5|6|7> \
  --policy-port <独立端口> --bind-host 127.0.0.1
bash scripts/robodojo.sh client --policy-dir XPolicyLab/policy/Pi_05 \
  --ckpt sim --action-type joint --env-cfg arx_x5 --seed <0|1|2> \
  --task <官方任务> --eval-num native --env-gpu <4|5|6|7> \
  --policy-host 127.0.0.1 --policy-port <对应端口>
```

结果按seed/任务/本次唯一run-id保存原生_result.json和三路视频；控制器保留每worker日志、资源JSONL、三seed summary及最终result-audit。仅满预算、唯一布局、三路非空录像齐全才计任务完成，失败回合正常计入预算。

## 粗日志

- p001–003：核验两机身份、源码、GPU和SZ2控制器终态，确定需适配Pi05以及无关不可读进程的清理问题。
- p004–006：后台补齐官方seed1/2推理文件，复用成功的分块/逐文件hash下载器；从SZ2固定官方Git/LFS对象只读导入全资产，SZ3逐文件校验。下载期间RLT继续。
- p007：10项Dojo检查、10项RLT检查全部通过。p008准备原始索引时误将Stage1角色纳入，匹配检查提前拒绝，未停训练；p010仅限定原clean/combo两角色后，真实四组prepare通过。
- p011–013：资产传输遇到Paramiko rekey超时，保留已验证文件和partial；按唯一PID/start/命令精确结束本次传输，改为每连接最多256MiB，续传与最终hash检查仍保留，没有改SSH安全设置。资产run为`full-assets-sz3-20260929-r2`。
- p014–016：增加后续seed权重就绪校验和PID复用回归，最终Dojo侧13项、RLT侧10项CPU检查通过。54配置、三seed布局、2100/6300预算及8组官方分工的真实plan-only通过。

seed0权重已完整验证，先运行seed0；seed1/2后台下载固定官方revision，进入各seed前检查ready回执、固定manifest和实际文件。不会把seed0权重代替其他训练seed；下载失败会中止本批并走资源归还。等待权重最多6小时，仅限制无模型可运行的等待，不给正式回合加墙钟截止。

15:47更新：seed1于15:41:35、seed2于15:41:53全部文件hash通过并写ready；现在三个seed权重和全部资产都已齐全，无需再等待下载。

细粒度原始命令/stdout/stderr/退出回执：E盘`exp2-research/implementation-sz3-20260929/steps/p001-*`起。公开版本仅发布脱敏配置、控制器、日志摘要和轻量证据；运行期间维持部署源码不变。

## 发布与借卡

- p018–022：全资产15:25完成，15365/15365文件、41,269,513,111字节核验成功。p020公开JSON的CRLF被Git格式检查拒绝，修为LF后p021通过，未改变JSON语义。
- p023：15:27准备记录推送SZ3分支，commit `50aab2b28298db42c4b25c59c8967eae8d91e84c`，新增10、修改1、删除0；SSH远端SHA和内置浏览器均核验。实际代码配置仅num_envs1→4。运行源码锁此commit，后续状态在独立发布checkout记录。
- p024：15:28四组RLT精确停止，真实checkpoint校验后均从CP25恢复；共享Ray未操作。
- p025：GPU4空闲reset成功；GPU5被共享Ray Dashboard监控句柄占用，预检查拒绝reset，未向该进程发信号。p026仅对剩余5–7尝试等待空闲句柄后逐卡reset；不能确认空闲的卡保留原状。
- p026实测：共享监控句柄自行释放后，5/6/7均reset成功；未停共享Ray。
- p027–029：15:30首次正式控制器启动，但在任何worker启动前因`39806 Address already in use`退出。官方任务回合0；清理与GPU释放检查通过，15:30:54自动从CP25派发恢复四组RLT。39800段落在本机临时端口32768–60999内；这次固定端口选择有缺陷。
- p030–032：在独立publication checkout保留运行源码HEAD。新attempt为`sz3_pi05_official_6300_n4_dual_20260929_r1`，改用已核验空闲且在临时端口范围外的63080–63087，Ray固定worker端口26400–26599也不冲突。新借卡cycle=`rlt-cycle-sz3-pi05-full-r1`，精确引用刚恢复的四个run。旧pipeline仅停止只读首轮观察；训练由新cycle检查身份后停止。模型、任务、预算、并发均未修改。
- p033–036：4–7空闲reset均exit0。15:37:02启动_r1，外层PID2325558/start663844612，真实进入EVALUATING；8份Pi05服务加载开始，每卡约49,749MiB，仿真当时尚未启动。p035只读状态脚本访问尚未初始化的complete_tasks键失败，修为缺省0；评测进程未受影响。p036健康快照正常。
- p037–038：8个Pi05服务全部ready；随后两个worker在检查其他刚exec的本批进程时遇到`/proc/PID/environ` PermissionError，控制器中止全部worker，尚无任务回合。精确清理、GPU释放和RLT自动恢复派发再次通过。
- p039–040：首个只读身份采样只覆盖fork后瞬间，400次无复现；改为覆盖整个exec转换期后，400次出现49次PermissionError，全部带`/proc/PID/environ`路径，确认是Linux exec瞬时权限竞态。
- p041–042：进程身份读取增加50ms间隔、最多10次的有界重试，每次重新读取身份，不用旧身份发信号；持续不可读仍报错。相同400次并发exec测试0错误；13项控制器检查通过。worker错误同时保留完整traceback。使用新控制器目录保留旧失败代码快照。
- p043：_r2继承相同任务/seed/权重/并行和63080端口，借卡cycle=`rlt-cycle-sz3-pi05-full-r2`精确引用_r1归还后新恢复的四组RLT。固定环境和RoboDojo部署HEAD不变。
- p044–048：第三次精确切卡和4–7逐卡reset均通过；15:46:45启动_r2，外层PID3373285/start663902919。15:47:55八服务已加载且八任务进入仿真初始化，RUNNING8/PENDING46，所有seed权重ready。此时尚未落盘回合。
- p049–052：八个Isaac App均完成初始化，随后载入资产/reset。15:50四卡各约58.5–58.9GiB，主机可用1738GiB；每卡明确为两个Pi05服务（各24866MiB）及两个仿真进程。服务日志的`InvalidMessage: did not receive a valid HTTP request`来自官方scripts/robodojo.sh:69的`/dev/tcp`空连接探测；服务仍存活，不将这条探测日志误判为模型退出。pour_by_language另有官方酒瓶资产RigidBody层级警告，原样保留，后续用真实回合判断影响。
- p053–056：15:53确认8个worker全进入实际动作循环，首批步骤为45/68/22/107/165/52/61/107，8任务RUNNING、46待调度。四卡显存71713/74234/71890/71981MiB，主机可用1692.75GiB；暂无完整回合落盘，此为全量评测健康启动，不是完整benchmark结果。
- p057–060：全部worker持续推进；p058公开状态校验被ANSI颜色码解析问题挡住，p059逐条确认env0–3均正常。只读快照解析改用去颜色后的文本，评测进程和结果未改。


21:03后GPU7故障及21:23续评记录见 [单卡恢复与原回合保留](../20260929_sz3_gpu7_recovery/README.md)。
