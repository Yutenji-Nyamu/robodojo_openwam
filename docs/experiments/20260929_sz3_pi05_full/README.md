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

本次run：`sz3_pi05_official_6300_n4_dual_20260929`；控制器位于`$PROJECT/scripts/pi05_formal_20260929/`，端口计划39800–39807。外层读取`dojo_sweep.config.json`，依次完成资产、权重与配置核验、暂停四组RLT、全量评测、归还GPU并恢复RLT。

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

细粒度原始命令/stdout/stderr/退出回执：E盘`exp2-research/implementation-sz3-20260929/steps/p001-*`起。公开版本仅发布脱敏配置、控制器、日志摘要和轻量证据；运行期间维持部署源码不变。
