> 公开归档版，记录截至2026-09-28；主机地址、账号和绝对私有路径已脱敏。历史过程不代表当前下一步，复用先看 [RUNBOOK.md](RUNBOOK.md)。

# OpenWAM：模型、研究结论与 RoboDojo 的关系

核查日期：2026-09-28。本文是论文和当前官方源码的研究说明，没有部署、训练或运行仿真。对应项目是 [OpenWAM-Official/OpenWAM](https://github.com/OpenWAM-Official/OpenWAM)，论文是 [OpenWAM: An Open, Modular Exploration Towards Systematic World–Action Model Pretraining](https://arxiv.org/abs/2609.07398)，arXiv v1 为 2026-09-07。不要与其他同名仓库混用。

## 1. framework、Study、α 各是什么

| 名称 | 可以怎样理解 | 实际内容 |
|---|---|---|
| OpenWAM-Infra / framework | 可更换部件的研究和运行框架 | 数据读取、视觉编码器、视频骨干、动作骨干、架构组合、训练和部署 |
| OpenWAM-Study | 在同一框架里做控制变量实验 | 比较视觉表示、模型规模、视频与动作交互、预训练数据和推理方式 |
| OpenWAM-α | 根据研究选择配方后训练的具体模型 | Wan2.2-TI2V-5B + 约 1B ActionDiT，约 6,400 小时预训练，再针对各环境微调 |

因此，“框架支持某个 backbone”不等于“α 使用它”；“Study 试过某种连接”不等于“发布 checkpoint 就是这种结构”。三者之间是实现工具、研究过程、最终模型的关系。[论文第 3–5 节](https://arxiv.org/pdf/2609.07398)、[官方 README](https://github.com/OpenWAM-Official/OpenWAM/blob/main/README.md)

## 2. 从 π0、π0.5、FastWAM 理解它

| 模型 | 主要知识来源与机制 | 推理时做什么 | 对我们的直接含义 |
|---|---|---|---|
| π0 | 预训练 VLM + 连续动作 flow matching | 看图、读指令和状态，逐步去噪生成动作块 | 语义理解与动作生成结合；不是默认同时预测未来视频 |
| π0.5 | 延续 π0，增加异构数据共同训练、高层语义任务等 | 将视觉、语言与动作知识用于新环境任务 | 成熟的 VLA 比较对象；“0.5”不代表与 WAM 同一种升级路线 |
| FastWAM | 训练时共同学习视频和动作，利用世界知识 | 原论文主路线省去测试时未来生成，以减少开销 | 更贴近我们已有 FastWAM 的执行成本思路 |
| OpenWAM-α | 视频世界模型和动作模型在层间交换特征，共同 flow matching | 当前观测条件下，同步去噪未来视频潜变量和动作块 | 推理仍保留未来潜变量计算，适合研究视频—动作耦合 |

π0 v1 为 2024-10-31，π0.5 为 2025-04-22，FastWAM 为 2026-03-17；OpenWAM 确实更晚。发布时间不能推出统一性能顺序。[π0](https://arxiv.org/abs/2410.24164)、[π0.5](https://arxiv.org/abs/2504.16054)、[FastWAM](https://arxiv.org/abs/2603.16666)

## 3. α 一次推理如何流动

```text
头部 RGB + 左腕 RGB + 右腕 RGB ──拼接、预处理──> 冻结 Wan VAE ──> 当前视觉潜变量
语言指令 ──> 冻结 umT5 文本编码器 ──> 文本条件
当前机器人状态 ──坐标、维度、归一化适配──> proprio 条件
                         ↓
               带噪未来视频 + 带噪动作
                         ↓
          Wan 世界 DiT ←─混合注意力─→ ActionDiT
                30 层配对交换，默认 10 次去噪
                         ↓
             未来视频潜变量 + 32 步动作块
                         ↓
    反归一化、提取机器人有效维度、转回 RoboDojo 的绝对末端目标
                         ↓
        环境执行动作 → 得到新观测 → 再推理下一个动作块
```

α 是 **Dual-System Joint Self-Attention**：视频与动作有各自参数，但在桥接层通过注意力交换信息；发布配置使用双向 `mutual` 交互。它不是“先完整想好一段视频，再用逆动力学翻译成动作”的固定两阶段系统，也不是 α 自带一个 Qwen VLM 指挥模块。α 的语言编码器是 umT5；Qwen3-VL 属于框架可选的 Tri-System 研究分支。[架构说明](https://github.com/OpenWAM-Official/OpenWAM/blob/main/assets/openwam_usage_docs/architecture-extension.md)、[RoboDojo 发布配置](https://huggingface.co/OpenWAM/OpenWAM-Alpha-Sim-RoboDojo/blob/main/config.yaml)

内部统一动作/状态空间是 80 维，适配不同机器人时只使用有效位置。RoboDojo 仿真发布包是 `arx_x5`、`action_mode: eef`，双臂末端 20 维映射至 `0–9` 和 `34–43`，每臂为 xyz、6D rotation、夹爪。外部 RoboDojo 仍按其位姿/夹爪协议执行；不能把内部 80 维直接喂给模拟器。XPolicyLab 当前适配限定双 X5，并负责环境坐标与机器人基座坐标转换。[适配代码](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/model.py)

有两个容易混淆的“同步”：

- `denoise_mode=sync`：视频和动作的去噪时间表同步。
- `inference_mode=sync`：执行完计划动作后再等待一次推理；与异步预取下一动作块相对应。

此外，`decode_video: false` 只是不把最终视频潜变量解码成可观看像素，**未来视频潜变量的去噪仍存在**，不能等同于 FastWAM 省去未来生成的路线。当前 XPolicyLab 还会强制关闭 DiT cache、compile、视频解码，并使用同步执行。因此论文在 RTX 5090 上约 170 ms/chunk 的优化结果，不能直接当成深圳 H100 的批量推理时延。[部署配置](https://github.com/OpenWAM-Official/OpenWAM/blob/main/configs/deploy.yaml)、[XPolicyLab 模型说明](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/README.md)

## 4. 框架究竟开放了哪些研究选择

| 层 | 可替换内容 | α 的选择 |
|---|---|---|
| 视觉表示 | Wan/FLUX 的像素 VAE；DINOv3/V-JEPA2.1 语义特征；可用 S-VAE 压缩 | Wan2.2 VAE |
| 世界骨干 | 框架支持 Wan2.1 VACE 1.3B、Cosmos-Predict2.5 2B、Cosmos3-Edge 4B、Wan2.2 5B、Wan2.1 14B | Wan2.2-TI2V-5B |
| 架构 | Single、Single-MoE；Dual 联合自注意力、交叉注意力、IDM；Tri 联合注意力 | Dual 联合自注意力 |
| 模态交互 | 隔离、仅视频看动作、仅动作看视频、双向 | 双向 |
| 数据和损失 | 视频样本、带动作机器人样本；缺失动作维度/标签采用 mask | 人类视频与机器人数据共同训练 |

论文骨干控制实验比较了四个模型，框架当前支持五个；Cosmos3 的代码支持不能冒充已经进入那张控制实验表。架构主变体有六类；交叉注意力加 detach 的额外实验，使结果表出现七行，也不表示七种并列的主框架。[架构扩展文档](https://github.com/OpenWAM-Official/OpenWAM/blob/main/assets/openwam_usage_docs/architecture-extension.md)

代码阅读顺序建议：先看 `configs/model/` 和发布的 `config.yaml` 知道实际选项，再看 `openwam/model/architectures/` 的层间交互，最后看 `openwam/deploy/model_loader.py`、`engine.py` 理解加载和推理。研究视频或动作骨干时再进入对应 backbone 目录；先把整体闭环读通，比一开始逐个读注意力实现更有效。[训练部署指南](https://github.com/OpenWAM-Official/OpenWAM/blob/main/assets/openwam_usage_docs/train-and-deploy.md)

## 5. Study 得出的结论，应怎样使用

下表均是论文特定设置的比较，不是跨所有任务的定律。Study 主要以 RoboTwin 2.0 Full 和 Clean2Random 为控制实验场景。[论文第 4 节及附录](https://arxiv.org/pdf/2609.07398)

| 问题 | 证据 | 合理理解 |
|---|---|---|
| 世界模型越大是否更好 | 四骨干平均成功率为 90.14、91.64、92.39、93.79 | 规模有收益；骨干架构/预训练数据也变化，不是纯参数缩放定律。5B 是效能折中 |
| 语义特征一定更好吗 | 未压缩 DINO/V-JEPA 为 76.42/80.91；S-VAE 后 90.18/88.46；Wan VAE 90.30 | 紧凑、适合生成建模的表示很重要；不能概括为“语义特征没用” |
| 动作和世界怎么连 | Single 85.50，Dual 联合自注意力 92.36，Tri 92.60 | 分开参数、充分共享中间信息很有效；α 选择复杂度更低的 Dual，不是每项最高都选 |
| 谁应该看谁 | 隔离 87.41；仅视频看动作 87.63；动作看视频 92.39；双向 92.15 | 世界信息进入动作流是关键；预训练后双向略优，改善幅度较小 |
| 是否必须先想视频再动作 | 所测去噪调度中，同步去噪达到 93.0，领先/滞后调度更低 | 支持联合细化；不构成“所有任务上分阶段规划都不好”的证据 |
| 人类视频有什么作用 | 600h 受控实验：从零 ID/OOD 87.0/14.5；人类+机器人共同训练 87.68/26.62 | 主要收益出现在分布外场景；两阶段训练与共同训练在该实验中接近 |

正式 α 的数据规模是 518.5M 帧、6,369 小时，按帧占比人类 30%、仿真机器人 30%、真实机器人 40%。论文的完整预训练用了 128 张 H200、约 7 天；这是理解训练投入的背景，不是我们复现已发布推理所需要重做的步骤。RoboDojo 下游微调为 60k steps；发布配置里的 `batch_size: 4` 是单进程配置，不能把它与论文 global batch 256 当成同一口径。[论文第 5 节、附录 B](https://arxiv.org/pdf/2609.07398)

## 6. RoboDojo 上强到什么程度

| 同一论文 RoboDojo 仿真结果 | 平均成功率 SR | 平均进度分数 Score |
|---|---:|---:|
| FastWAM | 2.03 | 3.48 |
| π0.5 | 6.91 | 11.41 |
| OpenWAM-α | 11.92 | 17.18 |
| Xiaomi-Robotics-1 | 13.93 | 20.07 |
| Galaxea G0.5 | 14.88 | 20.23 |
| DM0.5 | 19.34 | 24.90 |

OpenWAM 是该表较强的 WAM，值得作为新的 WAM 基线；整个表的最好模型不是它，而且它的绝对成功率仍低。Open 子集 OpenWAM SR 1.08，低于 π0.5 的 1.67；不能把总体更好理解为每种难点都更好。[官方 RoboDojo 完整结果表](https://github.com/OpenWAM-Official/OpenWAM/blob/main/benchmarks/robodojo/README.md)

它在 LIBERO 达到 99.3，但 LIBERO-Plus 是 69.2，低于 π0.5 的 84.4；相机扰动和视觉噪声仍是弱项。RoboTwin Clean2Random 的 69.0 是 ID/OOD 合并平均，不应误称 OOD 成功率；对应 randomized/OOD 是 48.7。RoboCasa365 的 38.2 也不是该表最高。不同 benchmark 的训练量、任务和评估协议不同，无法把这些数字合成一个“全局 SOTA 排名”。[论文主结果与附录](https://arxiv.org/pdf/2609.07398)

## 7. 与我们当前工作的关系

**先复现已发布 OpenWAM+RoboDojo 推理，工程入口已经存在。** 官方 OpenWAM 主仓负责模型与数据训练，RoboDojo 评估明确转到 XPolicyLab。后者包含专用坐标/动作适配、批量策略接口和启动脚本；不是要我们从零写模型服务。[官方 RoboDojo 入口](https://github.com/OpenWAM-Official/OpenWAM/blob/main/benchmarks/robodojo/README.md)、[XPolicyLab OpenWAM](https://github.com/XPolicyLab/XPolicyLab/blob/main/policy/OpenWAM/README.md)

**在线 RL 则仍是后续集成工作。** 截至核查日，RLinf [OpenWAM PR #1597](https://github.com/RLinf/RLinf/pull/1597) 未合并，只开放 SFT 和评估，配置明确拒绝 RL；RoboDojo 环境桥也仍是待合并工作。XPolicyLab 推理成功只证明观测到动作这条线成立，不会自动提供 rollout 概率、梯度、value head、奖励与权重同步。

因此，不需要把“先 π0.5→RLinf→RoboDojo”加成当前 OpenWAM 复现的必修路线。若下一目标是先验证 RLinf 的 RoboDojo 环境接口，成熟 π0.5 actor 可帮助隔离环境问题；但它使用的 14 维关节/50 步动作契约不同于这里的绝对末端/32 步，不能原样替换。详见 [接入核查](./RLINF_RPENT_REUSE.md) 和 [官方复现准备流程](./OFFICIAL_RUNBOOK.md)。

## 证据存档

原论文 43 页 PDF、全文提取、官方与 XPolicyLab 关键文件、HF API 文件大小/版本、实际 safetensors header 已保存至：

`<LOCAL_ARCHIVE>`

`source-manifest.json` 保存本轮主要下载 URL、文件字节数与 SHA256。本文没有下载 24.8GB 全量权重；完整性判断来自远端实际文件清单、配置、模型加载分支和权重头部，而不是 README 的一句宣传。
