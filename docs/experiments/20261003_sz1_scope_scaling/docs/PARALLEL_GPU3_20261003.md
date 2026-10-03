# 深圳1 GPU3：W1/N9与W1/N4容量及吞吐对照

> 发布副本：以下保留来源文件各时间点的历史记录；未刷新服务器状态，未新增运行或 smoke 验收结论。个人路径以通用标识替代；本地证据与历史公开仓库附件未随包提供。
> [返回索引](../README.md)

15:44轻量记录已推送并核远端：`codex/dojo-parallel-gpu3-20261003@7f887c401af31c2c19ddb60140bb068d1955d092`。新增报告/验收JSON两份，修改/删除0；未发布诊断辅助脚本，main和运行checkout保持。远端报告（历史公开仓库来源未随包提供；个人账号地址已脱敏），发布回执m031。

**15:37–15:38已完成与释放。** 两组均同seed0/layout0–8、9回合，退出0；没有GPU致命错误。正式4–7继续，OW4469/Pi3373（各/6300）。3卡已为3MiB/recovery None、所属进程0，无需恢复原3卡任务。

| 配置 | 完成/成功 | 总墙时 | 显存峰值 | 动作总数 |
|---|---|---|---|---|
| W1/N4 | 9/8 | 18分45秒 | 36.06GiB | 3782 |
| W1/N9 | 9/9 | 12分15秒 | 37.39GiB | 3133 |

N9多1.33GiB，本次耗时少34.7%、回合吞吐1.53倍。N4的layout4达到800步失败，两次轨迹和动作总量不同，不能把全部耗时差归因于并行，也不能断言N9提高成功率。每组27份视频、全部640×480且有帧，抽4份解码通过，N9首尾布局头图目视正常。正式源码/配置小摘要复核保持。接受N9已证明显存可用、这组样本有提速；尚未验证复杂/random和π0.5，不直接修改正式4–7。

最终依据：`comparison.json`、`final-released.json`和`verified-results.json`；N9原ANSI观测假失败保留，独立`observed-complete.json`核准，不是重跑或GPU故障。现场证据m028–m030。

用户2026-10-03授权额外使用3卡试并行，正式4–7保持W1/N4。14:57现场GPU3为1MiB、无计算进程、recovery None；click_bell Stage1已COMPLETE，后续队列仅使用6/7，非批次间瞬时空闲。原4–7 Dojo继续，原RLT归还owner不变。

## 本次执行

- 同一物理GPU3，OpenWAM模型与仿真同卡，一worker；先9环境、后4环境，每组9回合，标准stack_bowls/seed0，从layout0开始。
- 当前已运行源码/权重、arx_x5、三路640×480、25Hz、dt0.004、chunk32、denoise10保持。用独立eval_policy.sh副本仅替换脚本root及num_envs，正式配置/源码不写入。
- 使用独立run-id和输出，不混入6300正式成绩。原生不稳定场景替补照常保留；实际layout集合若不同，报告差异。两次采样轨迹可能不同，成功率差不用于证明并行优劣。
- 每组最多1800秒；GPU致命错误/坏姿态、GPU recovery非None、显存超过78GiB或超时即停止，不重试、不reset。沿用当前ProcessGuard按唯一owner/run/PID身份清理本probe。
- 输出：`SERVER_PROJECT/runs/sz1-gpu3-parallel-20261003-v1`。命令：`envs/openwam/bin/python -u diagnostics/parallel-gpu3-20261003/probe.py`。每2秒记录显存/利用率/实际动作；验收9条结果、录像、真实env0–8动作、退出和GPU释放。

## 历史并发解释

旧正式每卡2worker×4环境，共8环境，复杂场景曾接近80GiB并OOM；简单叠碗双N4约68.39GiB。两个worker重复加载两套模型及仿真，单workerN9仅一套模型，不能直接套用其显存。

可确证的OOM为深圳3 π0.5 GPU5，2026-09-29 23:59:44；当时两worker分别在随机排列数字/随机套娃。NVTT `cudaMalloc → cudaErrorMemoryAllocation`，崩前最近79369/81559MiB，两小时峰80712MiB（99%，只余847MiB）。故障证据（包外本地来源：`EVALUATION_RECOVERY_20260930.md:7`，未随包提供）、两任务现场（包外本地来源：`../server-admin/EXPERIMENT_REFRESH_CURRENT_20260930_1057.md:21`，未随包提供）。低占用时的CUDA700则属于另一类故障，不能用降显存解释全部。

旧单workerN16叠碗曾完成，43.28GiB，5.18动作/秒；双N4为8.52动作/秒。但布局集合、步数不一致，只是容量线索。旧未测单workerN9，本轮补同9回合对照。见旧测试（包外本地来源：`PARALLEL_TEST_20260928.md`，未随包提供）。

官方random任务默认把环境数封顶5；本轮标准叠碗不受此限制。依据：[固定版函数](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/726e9aabfaa642203722eb126f5eaf0f37f3e1ad/utils/pipeline_utils.py#L51)。

15:05:34已启动：probe owner PID2985517/start389785349，N9先执行，独立端口43923。Stage1完成回执为10月2日22:32:08、global_step_2000；GPU3确已释放。本probe未停止RLT或其他实验，不需要恢复原GPU3工作。结果待实测，不能提前判断N9更快或全任务稳定。

准备与启动证据：`dojo-sz1/steps/m002-gpu3-preflight`、`m003-gpu3-source`、`m005-launch-gpu3`。N9实际环境数以env0–8动作验收；GPU错误无进程内重试（独立环境restart count置当前cap3）。

15:10–15:13已观察env0–8均真实动作，15:13各169步，采样显存38216MiB（37.32GiB）。初版计数器漏过滤ANSI颜色、误报动作0；不重启评估，另起只读观察器修正统计。N9原控制器将因“未观察到环境”留下假失败，独立观察仅在client退出0、9回合/视频完整、env0–8动作可核、无fatal及原控制器已清理释放后接受，并继续N4。原状态完整保留，最终以`comparison.json`及`final-released.json`为准；观察/接续PID3005577。此修正只涉及测试计数器，正式与仿真源码无变化。
