> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# 粗粒度进度日志

2026-09-28实施收尾：深圳2真实OpenWAM＋RoboDojo的`stack_bowls`、seed0、layout0单回合成功，第三轮1944退出0，23项产物大小/SHA核对通过。三路录像元数据及主控抽帧目视核验已完成，头部末帧可见碗已叠起。这是一个回合的运行结果，不是全基准成功率1.0。

## 2026-09-28 18:00起：深圳2开始官方真实模型推理部署

用户授权直接按官方安装和评测流程实施，遇到本地问题再查COLLABORATOR环境；取消独立RGB/dummy/连续reset前置阶段。

18:00只读现场：深圳2 GPU0–3无计算进程，4–7保持现役；data余约7.1TiB。计划policy GPU3、sim GPU2；官方示例stack_bowls，seed0，num_envs1，eval_num1，原生ee和OpenWAM发布配置。目标是真实模型完整推理及任务结果/视频，失败如实保留，不加RL或全任务评测。单次评测最多30分钟，启动异常/持续无进展则保留日志定位，仅处理本run的进程。

项目位置 `/path/to/robodojo-openwam`；源码独立分支 `codex/openwam-robodojo`，Dojo固定726e9aab；官方安装器、资产与模型包按其入口运行并记录实际解析版本。Python依赖/下载缓存/临时文件均落数据盘。下面按时间保留准备、失败、修复和最终单回合结果。

18:11遇到第一类本地问题：PyPI官方文件下载约35–100kB/s；官方base_deps安装停在大包下载。仅终止本次安装进程树，保留日志，从官方`--from base_deps`继续，包约束不变、索引改为清华镜像。独立policy环境的默认pip索引也设此镜像，PyTorch仍按官方明确指定cu128源。权重单连接5–10MB/s，官方源已验证HTTP206，保留连续前缀后改6路分段续传，最终仍必须匹配官方SHA256。

18:28进展：sim基础依赖完成，进入官方子模块克隆；policy仍下载官方Torch/CUDA包。HF权重发生SSL EOF，已完成分块和连续前缀保留，修复续传重试后继续。官方资产网络下载慢，SZ1 COLLABORATOR同源LFS缓存11611对象/28.52GB可读；按本轮授权只读复制到自己cache，再由固定版本官方入口补齐。复制助手起初因本机/data符号链接、GNU tar两参数互斥退出，均0字节；按实际解析路径和tar语义修正，第三次开始传输，源端未写入。

截至18:28未出现H100仿真报错，当时尚未启动GPU推理。源码审查确认CUDA mask不约束Vulkan多GPU，需要在本run指定单GPU渲染以避开4–7卡现役实验；仅记录此必要本地设置，任务/动作/模型配置仍沿官方。

18:42资产准备收敛：全库38.4GiB/15365文件不是单回合必要条件。读取官方55份stack_bowls seed0布局，并用SZ1既有USD库只读解析11个入口；284份官方文件（573,739,871 bytes）覆盖可提供的任务本地依赖，含完整55布局。材质预览缩略图和原资产已有的远程/绝对路径引用另记审计，不擅自改USD。先准备此集合，未声称安装了全基准资产。跨机复制实测从3.82MiB/s降至0.08MiB/s，未把提高SSH窗口当作已证实加速；已停止本次复制，保留有效缓存及中断对象，改官方Git LFS只补缺的任务对象。任务配置/随机种子/评分不改。

18:33自己的源码仅两处运行资源设置：sim_config num_envs10→1，eval_policy KIT_ARGS显式单GPU渲染及目标渲染卡。差异保留`logs/local-single-env-render.patch`，bash语法检查通过。实际子模块XPolicyLab10ab265、IsaacLabafca7b09、cuRobo895c651，与官方安装器`--remote`解析结果一致。

18:48完成项：OpenWAM官方policy安装exit0；按project-env启用PYTHONNOUSERSITE后pip check无冲突，Torch2.7.1+cu128/NumPy2.2.6/Transformers5.17.0/Diffusers0.40.0/Hub1.33.0可导入。一次直接调用解释器未加载project-env，读到了用户旧Hub0.34.4而报错；已用实际隔离启动环境重查通过，未改用户旧包。任务资产284/284逐文件大小/官方hash通过，官方路径更新生成自己的x5/curobo.yml；剩仿真安装与权重，尚未启动评测。

19:00完整模型包完成：24,813,767,464B主权重SHA256匹配官方78ca4ef5…f40abb，config/stats/tokenizer全部hash通过，`ALL_FILES_VERIFIED`，下载exit0。仿真Torch2.7.0+cu128完成，继续官方IsaacSim5.1/IsaacLab/cuRobo阶段。19:04仍是依赖安装阶段，尚未启动真实模型评测。

19:16:57官方仿真安装完成：`install-mirror.exit=0`，官方`--from base_deps`流程结束，经过IsaacSim5.1、IsaacLab和cuRobo安装。期间只读检查发现当前shell找不到`nvcc`；系统实际有CUDA12.2/13.2，cuRobo当前源码默认使用cuda.core运行时编译，未据此切换系统CUDA或另装工具链。19:20仿真环境`pip check`仍报告两项约束冲突：IsaacLab0.54.3要求starlette0.49.1、实际0.45.3；httpx2要求idna>=3.18、实际3.10。该检查组合命令末尾的`bash -n`返回0，不能当成pip check通过；两项告警保留，未在首次运行前擅自调整版本。

19:20:48启动首次真实OpenWAM评测，run_id为`sz2_openwam_stack_bowls_s0_20260928_1921`，policy GPU3、sim/render GPU2；启动前两卡均4MiB、0%且无计算进程，4–7卡已有训练保持。官方入口参数为stack_bowls、arx_x5、ee、seed0、eval_num1，配置num_envs1，真实checkpoint且禁止dummy；单次上限1800秒。启动PID1274045，policy服务PID1274132，端口44457。19:21:23日志已进入CUDA权重加载、等待policy服务30/600秒；此时尚无退出文件、任务结果或视频，不能称为完成回合。运行证据与后续输出位于`/path/to/robodojo-openwam/runs/sz2_openwam_stack_bowls_s0_20260928_1921`，本地回执见细日志073–087；本段记录截止首次启动，后续问题和修复另行追加。

19:24:14首次运行以139退出：真实OpenWAM已打印`initialized`并进入仿真启动，Vulkan设备表明确GPU2为Active；随后日志出现`libGLU.so.1`缺失、`libneuray.so`加载失败和MDL-SDK失败，仿真客户端发生segmentation fault。没有任务结果或成功率。19:24:35检查本run的PGID1274116已无进程，policy服务树已退出；15项运行记录已收回E盘并逐项核对manifest大小/SHA256，包含211,829B完整主日志、退出码、命令与配置。GLU是已观察到的依赖缺口，尚不能认定它是全部崩溃的唯一原因。

19:25–19:26按上述明确缺口修复：只在自己`eval_policy.sh`前置`${CONDA_PREFIX}/lib`到`LD_LIBRARY_PATH`，补丁保存`logs/local-sim-libraries.patch`；只对自己的RoboDojo环境执行`conda install --freeze-installed ... libglu=9.0.3`。实际新增libglu9.0.3、libglvnd1.7.0、libopengl1.7.0，同时将OpenSSL3.5.8更新为3.6.4，不能把`--freeze-installed`描述成零其他包变化；19:25:48安装exit0，19:26:12 ctypes加载`libGLU.so.1`通过。随后以相同任务、seed、模型及GPU配置启动第二轮`sz2_openwam_stack_bowls_s0_20260928_1926`（PID1819995），截止step098尚无结果，等待真实重跑验证；未把动态库修复解释成增加H100硬件RT能力。

19:29:23第二轮1926仍以139退出，没有任务结果。真实OpenWAM再次初始化完成，完整日志已不再出现GLU缺失或MDL加载失败，但仍在`librtx.scenedb.plugin.so!carbOnPluginStartup+0x3b4de`崩溃。15项产物已回收E盘，大小/SHA256复核15/15通过，主日志210,419B。由此确认补GLU解决了该缺库报错，未解决后续仿真启动崩溃；GPU2/3随后回到5/4MiB。

19:32:45执行一次针对已发生崩溃的独立SimulationApp诊断：不加载OpenWAM或Dojo任务，取消`CUDA_VISIBLE_DEVICES`，显式`active_gpu=2`、`physics_gpu=2`、`multi_gpu=False`，再禁用multiGpu自动启用并设maxGpuCount=1，超时上限120秒。约35秒后仍以139退出，只有Kit的`app ready`，没有行首`SIMULATION_APP_*`返回标记；日志回显的Python源码不能当作标记已执行。CUDA mask和bad state警告消失，崩溃仍在相同插件/偏移，说明复现不依赖OpenWAM和Dojo任务。结束后GPU2/3回基线，本次没有改驱动。

19:34归因收窄：现场IsaacSim5.1＋驱动595.71.05＋上述崩溃栈，与NVIDIA官方仓库中的公开[Discussion648](https://github.com/isaac-sim/IsaacSim/discussions/648)和[Issue677](https://github.com/isaac-sim/IsaacSim/issues/677)复现报告高度吻合。648评论者vick-yu称其为已知兼容问题，但API association为NONE，未核实其NVIDIA维护者身份；此前“维护回复”措辞已更正，不把官方仓库中的评论当作NVIDIA正式确认或背书。这里是基于现场复现和公开报告的高相关判断，尚未进行本机驱动切换A/B，不能写成已证明单一因果。

深圳1仅做备用路线只读核查：19:33驱动575.57.08，GPU0–3低占用/0%快照，data余590G、home余467G；19:34确认本人已有`/home/USER/miniforge3`，`sudo -n`返回1仅表示本次非交互sudo未通过。step109后用户明确要求尽量留在深圳2，因此继续深圳2排障，不转为跨机部署。已解释COLLABORATOR的深圳1现场使用不同驱动；Conda/Isaac用户环境及下载包可以多套保留，活跃内核GPU驱动由整机共享。随后核查RoboDawn针对Isaac5.1＋595的用户态shim，过程见下；未在深圳1部署或启动仿真。

19:35–19:39保存本sim的pip freeze、Conda显式包清单和源码差异后，审查并固定RoboDawn版本`9247f366cd31f278e10f2fbe5fe8469b5f1b5b94`的两个兼容脚本与MIT许可证，按原源码目录放入自己项目`third_party/RoboDawn`。19:39:29原生只读Vulkan探测得到8张H100均为595.71.05，`maxMemoryAllocationSize=18446744073709551615`（UINT64_MAX），匹配该脚本限定的适用条件；这只是选择候选方案的依据，尚非修复验收。

19:40服务器在线`--prepare`返回HTTP403；Windows PowerShell下载也遇TLS失败。改用本地bundled Python urllib＋Mozilla/5.0，从脚本原定的LunarG/Ubuntu两个官方URL取得HTTP200，两个deb大小和SHA256与脚本固定值一致，原始URL/结果/hash回执保留E盘。上传到本项目后，19:42:17离线`--prepare`成功，只在`third_party/RoboDawn/.cache/robodojo-vulkan`解包兼容层和依赖，没有apt安装或替换系统驱动。19:42:29启动PID3551319的`sim-compat`测试：沿用step105的最小SimulationApp与GPU2/120秒设置，仅外包该兼容wrapper。截止step115等待结果，不能据prepare成功称Isaac或真实任务已跑通。

19:43读取兼容层最小测试结果：19:42:54退出0，真实行首`SIMULATION_APP_CONSTRUCTOR_RETURNED`与`SIMULATION_APP_UPDATES_RETURNED`均出现，构造及5次update已执行；`app.close()`阶段正常结束进程，没有打印CLOSED标记，不补记为已打印。相较step105，最小程序/设备/时限相同，只增加兼容wrapper；其属性校验通过，`maxMemoryAllocationSize`从UINT64_MAX限定为4292870144，原启动崩溃未在本次短测试复现。这支持局部兼容层在该最小案例有效，尚不是完整任务或长期运行验收；日志仍有RequestsDependencyWarning。

19:44:07将可选wrapper仅接在仿真客户端命令外，真实策略仍在GPU3、仿真GPU2；`eval_policy.sh`和`eval_single.sh`语法通过，补丁保留`logs/local-vulkan-compat.patch`，运行记录另存自身脚本、兼容脚本SHA和层包信息。启动第三轮`sz2_openwam_stack_bowls_s0_20260928_1944`，PID3657210；模型仍加载中，任务、seed、checkpoint和单环境参数不变，尚无任务结果。

19:45–19:49第三轮经过权重加载、仿真启动和首次任务reset/warmup等待后正常推进，期间没有新增源码/环境修改。19:47已打印Simulation App Startup Complete，19:49:47已推进到step96；19:50:45核对完整日志最后进度为`env0 step: 319 / 800`，日志连续记录step1至319。最终`Success nums: 1, Fail nums: 0, Unstable nums: 0`，三相机视频已保存；日志记载每路320帧、640×480、25FPS，帧数不等同于动作计数。run从19:44:08到19:50:45，397秒，退出0。

19:51:14核对正式`_result.json`：`eval_time=1`、`success_rate=1.0`、`score=100.0`；唯一details项为layout0、`success=true`、`score=1.0`。模型与仿真相关PID已退出，GPU2/3回到6/4MiB，4–7现役保持。第三轮23项产物已收回E盘，逐项大小/SHA256核对23/23通过，包含结果JSON、三路MP4和60,857B完整主日志；两轮失败记录继续保留。至此完成本次指定单任务、单种子、单环境的真实推理成功回合，不外推到全基准、多种子稳定性或在线RL。此时完成数值和文件完整性核验，后续媒体核验见下。

19:53–19:54媒体回收：首次用远端ffmpeg生成PNG、base64经stdout返回，远端退出0，但SSH输出被截断导致本地JSONDecodeError，未成功回收图像。随后只在本项目`runs/success-preview`写7张抽帧和1份元数据，再用SFTP回收8项，manifest大小/SHA核对8/8通过。ffprobe确认头部和左右腕三路MP4均320帧、640×480、25FPS、12.8秒；主控已通过view_image查看head的0/12.7秒和左右腕的12.7秒抽帧，可见真实RGB，头部末帧碗已叠起。这里是抽帧目视，不声称完整视频逐帧审阅。[头部完整录像](media/stack_bowls_head.mp4)及三相机预览保留E盘，未再启动实验。

