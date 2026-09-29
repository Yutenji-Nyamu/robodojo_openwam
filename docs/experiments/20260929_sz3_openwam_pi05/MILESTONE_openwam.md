# SZ3 OpenWAM × RoboDojo 成功推理

Run `sz3_pair_20260929_143536_openwam` 正常退出（exit=0）；原生结果包含成功回合。按回合编号取首次成功：episode 0，layout 0，success=true，原生单回合 score=1.0。

任务 `stack_bowls`，机器人 `arx_x5`，seed=0，动作 `ee`，环境数 1。该 run 共记录 1 回合，success_rate=1.0，汇总 score=100.0；这些是本次运行数据，不代表完整基准。

[原生结果（仅脱敏）](evidence/openwam/result.json) · [同名运行日志](evidence/openwam/sz3_pair_20260929_143536_openwam.log) · [命令](evidence/openwam/command.sh) · [实配](evidence/openwam/sim_config.yml) · [源码版本](evidence/openwam/source-refs.json) · [来源与校验](evidence/openwam/provenance.json)

- [头部相机](media/openwam/episode_0000000_cam_head_success.mp4) · [视频信息](media/openwam/episode_0000000_cam_head_success.ffprobe.json)
- [左腕相机](media/openwam/episode_0000000_cam_left_wrist_success.mp4) · [视频信息](media/openwam/episode_0000000_cam_left_wrist_success.ffprobe.json)
- [右腕相机](media/openwam/episode_0000000_cam_right_wrist_success.mp4) · [视频信息](media/openwam/episode_0000000_cam_right_wrist_success.ffprobe.json)

录像按原始字节复制，三路均通过 ffprobe 检查；文本中的私有路径、IP及凭据形式字段已脱敏。原始实验产物保持不变。

[官方评测说明](https://robodojo-benchmark.com/doc/usage/quick-evaluation/) · [官方策略适配](https://github.com/XPolicyLab/XPolicyLab/tree/10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4/policy/OpenWAM)
