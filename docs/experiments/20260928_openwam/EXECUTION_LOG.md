> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# 细粒度检查与执行日志

截至step129及随后媒体核验：第三轮1944完成`stack_bowls` seed0/layout0真实单回合，结果success=true、退出0；23项回收产物大小/SHA256全部通过。三路视频ffprobe核对及主控四张抽帧目视已完成，头部末帧碗已叠起；以下保留两次失败和修复链。

## 2026-09-28 18:00起：实际实施记录

本次授权已进入安装和真实推理，以下旧章节的“未部署”仅指先前调研阶段。逐条命令、stdout/stderr、返回码、时间和命令SHA写入：

`<LOCAL_ARCHIVE>`

`live.py`保持固定host-key Paramiko连接和USER身份校验，密码仅进程中。每个step一个独立目录，文件为command.sh、stdout.log、stderr.log、receipt.json。长安装任务另保存远端日志、PID和exit文件。

| step | 动作 | 结果 |
|---|---|---|
| 001-live-inventory | GPU/磁盘/内存/依赖/官方站连通 | rc0；0–3空、4–7现役；三站HTTP200 |
| 002-locate-runtime | 查用户data与opt的Conda | rc1；未找到现成Conda，opt查找返回非0，后续单独确认 |
| 003-home-runtime | 查真实home目录与工具 | home为数据盘符号链接；无用户Conda；git-lfs存在，uv无，末命令rc1 |
| 004-bootstrap-official | 创建自己项目、官方clone、独立分支、启动官方install.sh -i | 执行日志与PID见step回执及项目logs；安装完成状态后续核验 |
| 005-assets-and-model | 官方init_assets.sh固定HF HEAD；专用checkpoint固定revision下载 | 两个后台PID与各自log/exit；模型逐文件size/SHA验证 |
| 006/009-install-status | 查看四项安装下载进度 | 官方Conda已创建；base依赖/策略Torch/资产/权重下载中 |
| 007-policy-official | 官方独立openwam Python3.10+torch2.7.1 cu128，再adapter install.sh | 后台PID1984702；不与sim torch2.7.0环境混用 |
| 008-download-range-support | 同一官方HF文件读取1MiB Range | HTTP206、Content-Range及长度正确，可分段续传 |
| 010-network-and-progress | 子进程树/资产体积/镜像连通 | 用于定位下载瓶颈，结果在step回执 |
| 011-pypi-mirror-resume | 仅本安装PID1668240及后代停止，官方--from base_deps重启 | rc0；新PID2398428，install-mirror.log/exit；project-env增加PIP_INDEX_URL，包约束未改 |
| 012-install-status | 检查下载与依赖进度 | 记录原PyPI35–100kB/s、模型约3.17GB；未启动GPU推理 |
| 013-model-range-resume | 终止本checkpoint下载树，保留连续前缀，6路同源Range继续 | 停止/前缀回执checkpoint-download-superseded.json；新checkpoint-ranges.log/exit，最终SHA校验 |
| 014-policy-pip-source | 仅openwam环境pip.conf设置清华默认索引 | 不改变PyTorch显式cu128源或其他环境 |
| 015–018/023/026 | 安装、官方资产LFS、权重进度 | 每次独立回执；18:20镜像完成open3d，18:26进入子模块；权重18:25 SSL异常退出1 |
| 019-sz1-asset-cache | 固定身份sudo只读COLLABORATOR官方LFS目录 | 11611对象、28,522,339,309 bytes；旧官方资产revision a14409d7 |
| 020-transfer-deps | 查system Paramiko与尚未生成的IsaacLab | 无Paramiko、子模块不存在，均保留stderr；没有当成安装完成 |
| 021-install-transfer-helper-deps | pip --target own cache/transfer-python安装Paramiko | rc0；不写sim/policy site-packages；pip提示尚在安装中的policy依赖未齐 |
| 022-stop-own-assets-download | 精确核PID/所属用户/脚本及子树，停止本次HF资产下载 | 仅1776466/1776491/1776960/1776961/1776962；原日志保留，assets-official-cache-stop.json记录 |
| 024/025-resolve-data-path | 核对源/目标真实路径 | SZ2 /data→/home/nvme/team-data；SZ1/data为真实目录 |
| asset-cache-transfer.log | SZ2经固定hostkey/UID连接SZ1，sudo只读tar流传普通哈希对象 | 首次/data symlink拒绝，第二次tar互斥参数退出，均0bytes；修正后第三次传输进行中；只写自己cache |
| 027-checkpoint-retry-error | 保留失败trace与状态 | 3次SSL EOF/短206；ranges state保留完成块，不把稀疏文件大小当下载完成 |
| 028-install-base-finished | 查安装进度/进程 | base_deps已过、子模块接收中；现场无rg导致查询rc127，后续用Python/grep |
| 029/030-network-interface | 只读两台网络接口 | SZ1无可用私网互联接口；当前经原指定公网SSH传同源资产 |
| 031/036/039/046/047/049 | 下载/安装/版本刷新 | 记录固定三子模块实际SHA和阶段；无GPU推理启动 |
| 032-checkpoint-resume-v2 | 失败后从已有completed状态恢复 | PID276497；12次网络重试/退避至30s/块内offset续传；block256MiB/6threads/模型SHA不变；脚本SHA550c7956 |
| 033-stop-cache-for-larger-window | 精确本helper PID4053005中断，准备32MiB SSH窗口 | rc0；传输最终1.104GB/275.53s，缓存/原日志保留；没有声称调窗口一定加速 |
| 034-check-partial-cache | SHA校验已落盘缓存 | 8177文件，8176有效、1中断对象；初版HEAD清单误包括非Assets，随后修正只Assets/** |
| 035/040/041/042 | 只读发现并加载SZ1 USD Python库 | 默认无pxr，首次缺libusd_tf，补同环境LD路径后导入成功；未导入Isaac/Kit、未启动GPU |
| 037/038 | 阅读并设置自己eval入口 | num_envs1、单GPU KIT_ARGS；bash -n通过；GPU2/3仍4MiB；patch完整保存 |
| 043-stack-bowls-usd-dependencies | 只读解析55布局、11 USD、MDL/URDF | rc0；已解析本地依赖都在284官方文件中；39纹理/20mesh齐，11缩略图注解；原资产外部引用见专项审计 |
| 044-assets-official-state | 读取官方资产准备/路径更新逻辑 | 未有Assets链接；官方无task subset开关，采用相同Git LFS来源准备精确任务文件 |
| 045-preserve-one-incomplete-object | 按精确路径/size/SHA核对后移本次中断对象至自己cache/transfer-incomplete | 仅97b776…，3112960B，未删除；原始receipt保留 |
| asset-cache-transfer后续 | 190唯一OID任务子集传输，32MiB窗口 | 153秒仅12.77MB，均是缓存传输；源端只读；最终按实际网络速度转官方LFS |
| 050-stop-slow-task-cache-transfer | 精确PID1214361中断 | rc0，已退出；最后不完整对象由准备脚本核对hash/size后保留隔离 |
| 051-official-task-assets | 官方git lfs fetch精确缺失对象→restore/checkout284文件→逐文件hash→官方路径更新 | PID1524438，task-assets.log/exit；ready.json仅在全部验证后产生，未声称全Assets完成 |
| 052/053/056 | 进度与对象计数 | policy18:43:48官方安装exit0；任务190唯一LFS对象已全部补齐 |
| 054-policy-dependencies-check | 未source project-env直接检查 | rc1，误加载用户.local的旧Hub0.34.4；不是隔离环境安装失败 |
| 055-policy-isolated-check | source实际project-env后pip check和版本导入 | rc0，无依赖冲突；Hub1.33.0来自本项目envs/openwam；不修改用户.local |
| 057/058-asset-restore | 定位git restore pathspec失败 | 旧sparse-checkout中断留下仅根目录模式；HEAD实际有文件；官方git restore支持--ignore-skip-worktree-bits |
| 059-materialize-task-assets | 使用上述Git原生选项恢复指定文件、LFS checkout、逐文件hash、官方配置路径更新 | rc0；284/284、573739871B；task-assets.ready.json，1个x5/curobo.yml生成；首次失败log保留 |
| 060–069/071/072 | 紧凑状态和大包字节增长 | policy/task始终exit0；Torch包460MB→719MB→下载完成；IsaacKit3.02GB包19:04收到1.84GB；根余15GB/data约7TiB |
| 061-eval-script-syntax | 本run官方CLI包装bash -n | rc0；尚未执行评测。保存唯一runid、PGID、命令、版本、配置、资源及退出码；不加常驻守卫 |
| 070-model-complete | 直接读最终校验记录 | 18:59:44主权重SHA正确，18:59:54全包ALL_FILES_VERIFIED，checkpoint-ranges-v2.exit0 |
| 073–079-progress-compact | 19:06–19:15读取官方安装进度 | IsaacSim5.1的Kit SDK/ROS2依赖下载、包安装，随后进入IsaacLab依赖；policy/模型/任务资产退出码持续为0，仿真安装当时尚未结束 |
| 080-install-stage | 检查IsaacLab构建与cuRobo阶段、查询nvcc | IsaacLab相关editable构建完成，安装器进入cuRobo；当前shell的nvcc查询报command not found；这是检查命令的stderr，未据此判定安装失败 |
| 081–083-cuda/curobo | 只读检查系统CUDA位置、cuRobo setup.py与官方安装入口 | 系统有CUDA12.2/13.2；cuRobo默认CUROBO_USE_PYBIND=0，使用cuda.core运行时编译；官方安装使用.[cu12]，未切换系统CUDA或新增工具链 |
| 084-curobo-current | 19:19读取最终安装日志、版本和退出文件 | 官方安装于19:16:57结束，install-mirror.exit=0；Dojo726e9aab、XPolicyLab10ab265、IsaacLabafca7b09、cuRobo895c651；另有误查RoboDojo/curobo/setup.py的sed错误，真实路径为third_party/curobo，未影响既有安装结果 |
| 085-sim-check-gpu | 仿真环境pip check、启动前GPU快照、eval_single.sh语法检查 | pip check报告两项冲突：isaaclab0.54.3要求starlette==0.49.1、实际0.45.3；httpx2 2.13.1要求idna>=3.18、实际3.10。step总rc0来自末条bash -n，不能作为pip check通过。GPU2/3均4MiB、0%、无计算进程，4–7现役 |
| 086-launch-real-episode | 19:20:48 nohup启动本run的eval_single.sh | 启动查询rc0；run_id=sz2_openwam_stack_bowls_s0_20260928_1921，父PID1274045、policy PID1274132、socket44457；进入官方真实OpenWAM服务初始化，此返回码不是评测完成码 |
| 087-model-start-log | 19:21:23读取首次模型日志及尚未生成的exit.txt | 日志显示CUDA权重加载、等待服务30/600秒；cat缺失exit.txt使本查询rc1，不是模型运行退出1；截止此处未产出任务结果或视频 |
| 088–091-model/episode-progress | 19:21–19:23读取模型加载、GPU/进程与仿真启动日志 | 真实OpenWAM完成initialized并启动仿真客户端，后续092保留初始化行；不能仅据模型初始化判定完成任务 |
| 092-isaac-device-errors | 提取初始化、Vulkan与错误行 | OpenWAM denoise_steps10/sync，num_frames33、video_num_frames9；仿真报libGLU.so.1缺失、libneuray.so加载失败、MDL-SDK失败 |
| 093-device-table-and-tail | 读取Vulkan设备表、主日志末尾与timeout身份 | 设备表GPU2 Active=Yes:0；仿真客户端segmentation fault，官方入口结束并清理policy树，RUN_EXIT=139；run end.txt为19:24:14，无任务结果 |
| 094-first-failure-context | 19:24:35读取错误上下文、查询PGID1274116及本环境GLU文件 | 本run进程组查询无进程，本sim环境无匹配GLU库；保留崩溃信息，未认定GLU是唯一根因 |
| 095-eval-libpath-location | 只读定位eval入口与环境动态库处理位置 | 确定修复限于自己eval_policy.sh和RoboDojo环境，不调整系统动态库或其他用户环境 |
| 096-fix-sim-glu | 为自己eval_policy.sh前置CONDA_PREFIX/lib，保存补丁并启动install_glu.sh | bash -n通过，local-sim-libraries.patch保存；conda命令为install -y --freeze-installed -p本sim环境 -c conda-forge libglu=9.0.3，后台安装单独记录exit |
| 097-glu-install-status | 读取Conda事务与退出文件、GPU快照 | 19:25:48安装exit0；实际新增libglu9.0.3/libglvnd1.7.0/libopengl1.7.0，OpenSSL3.5.8→3.6.4；如实记录freeze-installed仍发生的包变更 |
| 098-retry-after-glu | 指定本sim库路径，ctypes.CDLL验证GLU，再启动相同评测 | GLU_LOAD_OK；19:26:12启动run_id=sz2_openwam_stack_bowls_s0_20260928_1926，PID1819995；任务/seed/模型/GPU配置沿首轮，截止此步无结果 |
| 099–101-retry-progress | 19:27–19:29读取第二轮模型/仿真加载与GPU | OpenWAM再次initialized，仿真启动继续；还不是回合完成 |
| 102-task-init-progress | 19:29:49读取第二轮结束日志和GPU | 第二轮1926已于19:29:23结束、RUN_EXIT=139，无任务结果；同一librtx.scenedb.plugin.so!carbOnPluginStartup+0x3b4de崩溃；GPU2/3为5/4MiB |
| 103-second-crash-detail | 读取完整错误附近、Python崩溃栈及相关进程 | 第二轮仍有CUDA_VISIBLE_DEVICES与bad state警告；完整回收日志无GLU缺失/MDL失败。末条ps查两指定PID无进程使查询rc1，不是新增运行退出码 |
| 104-simapp-gpu-config-source | 只读检查SimulationApp的GPU配置实现与现场GPU | 确认active_gpu、physics_gpu、multi_gpu和extra_args入口，用于隔离CUDA mask因素 |
| 105-launch-unmasked-diagnosis | 19:32:45启动独立diagnose_sim_unmasked.sh | 取消CVD，只实例化SimulationApp；headless、active_gpu2、physics_gpu2、multi_gpuFalse、autoEnablefalse、maxGpuCount1；上限120秒，既有GLU库路径保留；不加载OpenWAM或Dojo任务 |
| 106-sz1-fallback-inventory | 19:33:10仅只读SZ1身份、GPU/驱动、本人磁盘/目录 | 驱动575.57.08；GPU0–3为73/8/8/8MiB且0%，4–7现役；data余590G、home余467G。仅为当时快照，未部署 |
| 107-unmasked-result | 19:33:23读取独立测试输出及exit | 实际19:33:20结束，约35秒、rc139，未触及120秒上限；宽松grep也命中崩溃时回显的print源码，不能当作构造/更新/关闭成功标记 |
| 108-unmasked-confirm-and-clean | 用行首锚定^SIMULATION_APP复核，并查警告/崩溃栈与GPU | 无返回marker，只有[16.418s] app ready；CVD/bad state警告消失，仍是carbOnPluginStartup+0x3b4de；exit139，所查旧run PGID1834092为空，GPU2/3回5/4MiB |
| 109-sz1-local-copy-feasibility | 19:34:19仅只读检查本人Conda路径和sudo -n | 本人miniforge3目录存在；sudo_noninteractive_rc=1，未执行环境复制/安装/仿真启动；后续路线已询问用户、等待选择 |
| 110-preserve-sim-state | 保存本sim pip freeze、Conda explicit及查看源码diff/相关进程 | 两份包清单写入本项目logs；diff含安装器解析的子模块及既有运行设置；末条grep无匹配使总rc1，不代表前两份清单失败 |
| 111-stage-compat-source-dir | 19:39:23建立自己项目的RoboDawn兼容源码目录 | 保持scripts/robodojo/compat原结构；固定9247f366cd31f278e10f2fbe5fe8469b5f1b5b94，两个脚本与MIT已审查，E盘source-manifest保留各文件hash |
| 112-vulkan-native-probe | 运行兼容脚本--probe，只读查询原生Vulkan属性 | 8张H100全部driver595.71.05、maxMemoryAllocationSize=18446744073709551615；other_devices为空，满足该脚本要求所有物理GPU同为595和UINT64_MAX的条件 |
| 113-prepare-local-vulkan-layer | 服务器按原脚本在线--prepare | rc2、HTTP403，未准备成功；随后Windows PowerShell同源下载TLS失败，均不作成功记录 |
| 113→114本地下载回退 | bundled Python urllib＋Mozilla/5.0请求原LunarG/Ubuntu URL | 两包HTTP200，vulkan-profiles575090B、libjsoncpp79966B；SHA256均匹配源码固定值，*.deb.receipt.json保留原URL/finalURL/time/hash |
| 114-local-layer-offline-prepare | 上传上述已核验包后传--package/--jsoncpp-package执行本项目--prepare | 19:42:17 rc0，只在本项目third_party/RoboDawn/.cache/robodojo-vulkan解包；libVkLayer_khronos_profiles.so prepared，不执行apt或系统驱动替换 |
| 115-launch-compat-diagnosis | 19:42:29启动diagnose_sim_compat.sh | PID3551319；沿105的最小SimulationApp与GPU2/120秒配置，仅增加vulkan_driver_compat.py --isaac51 --gpu-index 2 wrapper；sim-compat.log/exit独立记录，截止此步结果待查 |
| 116-compat-diagnosis-progress | 19:43:04读取兼容层最小测试的锚定marker、日志和exit | 19:42:54结束、exit0；属性校验后cap为4292870144，真实CONSTRUCTOR_RETURNED和UPDATES_RETURNED均出现；app.close阶段进程结束，CLOSED未打印。RequestsDependencyWarning仍保留；仅证明最小启动/5次update/退出通过，不是任务成功 |
| 117-eval-wrapper-location | 只读确定真实eval的可选wrapper接入位置，刷新GPU | GPU2/3为5/4MiB、0%；仅在sim客户端命令外添加可选wrapper，policy入口保持 |
| 118-real-run-with-compat | 19:44:07补入sim_cmd可选wrapper、检查语法、保存补丁、启动第三轮 | 两脚本bash -n通过；local-vulkan-compat.patch保存；run_id=sz2_openwam_stack_bowls_s0_20260928_1944，PID3657210，policy3/sim2及同任务/seed/checkpoint；启动脚本新增自身快照、compat SHA、layer package_info记录，真实模型仍加载中，尚无任务结果 |
| 119–120-third-run-model-progress | 19:45–19:46读取权重加载、等待端口40699与policy进程 | 首次加载仍在推进，等待提示到120/600秒；未改参数或重启 |
| 121-third-run-sim-status | 19:47:20读取模型和仿真初始化结果 | OpenWAM initialized、兼容cap启用，Simulation App Startup Complete；尚未把仿真启动当任务成功 |
| 122–124-task-load/reset | 19:47–19:49检查任务导入、首轮reset/warmup和进程 | 等待首次场景/材质准备后继续运行；日志保留MDL编译警告，未新增源码/环境修复；后续实际动作推进确认不是永久挂起 |
| 125-reset-process-state | 19:49:46–47查询仿真进程与末尾进度 | 真实动作已推进，查询末尾到step96；只是读取状态，没有挂接采样器或改运行 |
| 126-real-action-progress | 19:50:45读取末尾行动、视频写出和退出码 | 最后step319/800；Success1、Fail0、Unstable0；三路视频各320帧、640×480、25FPS为日志记载。wall_clock397s，RUN_EXIT=0，exit.txt=0 |
| 127-success-json-and-cleanup | 19:51:14读取正式结果JSON、查询三个本run PID、刷新GPU | eval_time1、success_rate1.0、score100；details[0]为layout0/success=true/score1；3657210/3657291/3967922均无进程，GPU2/3回6/4MiB，4–7现役 |
| 128-success-media-frames | 19:53:08远端ffprobe三路录像，ffmpeg抽帧后base64经stdout回传 | 远端rc0，但SSH stdout截断，本地JSONDecodeError；不能把远端成功当作图像已完整回收 |
| 129-save-success-preview | 19:54:27仅在自己runs/success-preview保存7张PNG＋1份metadata，再SFTP回收 | 远端rc0，8项回收manifest齐全且本地大小/SHA核对8/8通过；ffprobe三路均320帧、640×480、25/1FPS、12.800000秒 |

首次启动使用`bash scripts/robodojo.sh eval`，参数为`--policy-dir XPolicyLab/policy/OpenWAM --task stack_bowls --ckpt OpenWAM-Alpha-Sim-RoboDojo --env-cfg arx_x5 --action-type ee --seed 0 --eval-num 1 --policy-gpu 3 --env-gpu 2`，另显式指定本项目独立policy/sim环境；配置`num_envs=1`、`ROBODOJO_RENDER_GPU=2`、`OPENWAM_ALLOW_DUMMY_POLICY=false`。外层`timeout --signal=TERM --kill-after=30s 1800s`限定本次运行。启动脚本保存命令、源码/子模块版本、配置补丁、GPU快照、PID与开始时间；运行结束后才写`exit.txt`和`end.txt`。

远端run目录：`/path/to/robodojo-openwam/runs/sz2_openwam_stack_bowls_s0_20260928_1921`；主日志：`/path/to/robodojo-openwam/logs/sz2_openwam_stack_bowls_s0_20260928_1921.log`。本段只记到step087的首次启动/权重加载状态，后续诊断和修复单独追加。关键原始证据：[安装完成084](evidence/steps/084-curobo-current/stdout.log)、[依赖和GPU085](evidence/steps/085-sim-check-gpu/stdout.log)、[首次启动086](evidence/steps/086-launch-real-episode/stdout.log)、[权重加载087](evidence/steps/087-model-start-log/stdout.log)。

一次将较长JSON命令直接送入PTY被行长度限制截断，JSON解析失败，没有远端执行；已改为短文件路径请求，完整shell源码在本地文件及step快照中。

首次run1921的15项证据已完整收回本地manifest（完整本地证据未随公开版发布），本地逐项大小/SHA256核对15/15通过；[完整主日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1921/sz2_openwam_stack_bowls_s0_20260928_1921.log)为211829B，保留GLU/MDL错误与崩溃上下文。GLU缺失是已确认问题，补齐并通过ctypes加载仅验证动态库可加载，不能据此判定segfault已全部解决，也不改变H100硬件RT能力。修复证据见[097包变更与安装结果](evidence/steps/097-glu-install-status/stdout.log)、[098库加载与第二次启动](evidence/steps/098-retry-after-glu/stdout.log)。第二轮输出使用同项目`runs/sz2_openwam_stack_bowls_s0_20260928_1926`和`logs/sz2_openwam_stack_bowls_s0_20260928_1926.log`，不覆盖首轮记录。

第二轮1926的15项产物manifest（完整本地证据未随公开版发布）已逐项核对大小/SHA256，15/15通过；[完整主日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1926/sz2_openwam_stack_bowls_s0_20260928_1926.log)210419B、退出139，GLU相关命中0、MDL加载失败命中0、initialized命中1，相同插件崩溃偏移命中1。独立测试证据见[107原输出](evidence/steps/107-unmasked-result/stdout.log)与[108锚定复核](evidence/steps/108-unmasked-confirm-and-clean/stdout.log)。这证明同类崩溃可在不加载OpenWAM/Dojo任务时复现，且取消CVD警告后仍存在。

公开来源核查：NVIDIA官方仓库的[Discussion648](https://github.com/isaac-sim/IsaacSim/discussions/648)报告Isaac5.1、驱动595.71.05和同一`carbOnPluginStartup+0x3b4de`栈；评论者vick-yu称其为已知兼容问题，但API association为NONE，其NVIDIA维护者身份未核实，故更正此前“维护回复”表述，不当作NVIDIA正式确认或背书。[Issue677](https://github.com/isaac-sim/IsaacSim/issues/677)也是同驱动、同偏移、独立headless SimulationApp启动崩溃的公开复现报告。两例GPU与本机不同，作为高相关公开证据；本机尚未做驱动切换A/B，不把归因写成已验证的单一因果。截止step109只完成SZ1备用路线只读核查，向用户提出SZ1仿真/SZ2策略沿用5.1与SZ2独立Isaac6环境两选项，尚未执行任一路线。

step109后的用户决定：尽量继续深圳2。已说明SZ1的COLLABORATOR历史现场驱动575.57.08与SZ2的595.71.05不同；Isaac/Conda用户态环境及下载包可多套保留，活跃内核GPU驱动整机共享。后续限定本项目准备RoboDawn用户态兼容方案并启动最小测试，见110–115；未改系统驱动，也未在SZ1部署。不再以等待跨机路线选择作为当前状态。

兼容候选资料：固定源码manifest（完整本地证据未随公开版发布）、LunarG包下载回执（完整本地证据未随公开版发布）、Ubuntu包下载回执（完整本地证据未随公开版发布）。原生探测见[112输出](evidence/steps/112-vulkan-native-probe/stdout.log)，离线准备见[114输出](evidence/steps/114-local-layer-offline-prepare/stdout.log)。第三方脚本仅作为经审查的局部候选；prepared与后台启动都不是SimulationApp返回、任务成功或驱动因果验收。

后续[116最小测试回执](evidence/steps/116-compat-diagnosis-progress/stdout.log)已明确记录构造返回、5次update返回与退出0。step105/115的程序、GPU和时限保持一致，只增加进程级兼容wrapper；它先核对Vulkan属性变化范围，再启动原Python程序，报告UINT64_MAX→4292870144。该对照支持兼容层对当前最小案例有效，不能外推完整任务、长跑或驱动更换的因果结论。E盘4份固定源码/许可证/README及2个包再次核对manifest大小/SHA，6/6通过；真实第三轮的新增可选入口和启动命令保存在[118 command.sh](evidence/steps/118-real-run-with-compat/command.sh)。

第三轮1944独立回收核对：23项产物manifest（完整本地证据未随公开版发布）中的每项大小与SHA256全部一致；包括三路MP4、`_result.json`、运行脚本/配置/兼容层身份、开始结束时间和[60857B完整主日志](evidence/sz2_openwam_stack_bowls_s0_20260928_1944/sz2_openwam_stack_bowls_s0_20260928_1944.log)。独立解析主日志去除ANSI后，动作进度恰有319条，step1至319连续、最后319/800；三路录像记录为各320帧，不把录像帧数当动作计数。`start.txt=19:44:08`、`end.txt=19:50:45`，时间差397秒与主日志一致；退出码0。JSON与现场进程回执见[127结果及清理输出](evidence/steps/127-success-json-and-cleanup/stdout.log)。此段是数值与文件完整性核验，随后完成的媒体核验见下；结果范围是stack_bowls/seed0/layout0的一个回合，不能将`success_rate=1.0`解释成全基准或多种子成功率。

媒体收尾证据：8项预览回收manifest（完整本地证据未随公开版发布）及[ffprobe元数据](media/metadata.json)已核对。主控通过view_image实际检查head_0、head_12.7、left_wrist_12.7、right_wrist_12.7四张PNG：均为真实RGB，头部末帧显示碗已叠起。未声称逐帧观看整段视频。[头部录像](media/stack_bowls_head.mp4)、[头部末帧](media/head_12.7.png)与左右腕完整录像/抽帧均在同一success目录。step128原始截断输出保留，step129回收结果没有覆盖失败证据；媒体阶段只读取既有录像并生成预览，未新增实验。

以下章节记录18:00前的调研和只读检查；当时没有远端部署，后续实施见上方实际记录。以下为当时实际检查脚本、参数和产物索引，没有把未来命令模板写成已执行。所有密码通过进程内getpass/stdin使用，未写入脚本或日志。

