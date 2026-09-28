# 脚本清单

[check_evidence.py](scripts/check_evidence.py) 只做离线证据一致性核查。

- [dojo_sweep.py](scripts/dojo_sweep.py)
- [process_guard.py](scripts/process_guard.py)
- [dojo_sweep.config.example.json](scripts/dojo_sweep.config.example.json)


## 正式 launcher 的复用

这三个文件放在同一目录，使用 Linux 的 OpenWAM Python 环境运行。配置示例中的 `/path/to/...`、UID、run-id、固定部署 commit 和端口须对应自己的机器。`dojo_head` 是实际部署源码 commit；不要把旧 commit 锁误解为当前公开仓库 HEAD。源码同时固定 GPU4–7、每卡双 worker 和 seed0/1/2，先确认这些卡可用。

```bash
python dojo_sweep.py --config dojo_sweep.config.example.json --plan-only
python dojo_sweep.py --config dojo_sweep.config.example.json
```

plan-only 只检查和生成计划，不启动 GPU 工作。正式模式采用上游任务清单及权重分组、官方 server/client；添加本地进程回执、完整预算验收与独立结果选择。这是实验控制脚本，不能称作未经修改的官方调度器。部署前还需 canonical arx_x5 的 num_envs=4、已存在的两个环境、固定权重/完整资产、有效进程级兼容层。

它不操作其他训练任务；外部资源交接属于机器本地管理，不随公开脚本分发。正式已验证到哪一步以 STATUS.json 为准。
