# SZ2 Dojo evaluation recovery — 2026-09-30

Dojo evaluation is continuing. One simultaneous worker per GPU, four environments per worker; the user approved this reduction from two workers per GPU. The original model/checkpoints, 54 task configurations, seeds 0/1/2, native 25/50 episodes, and total budget of 6300 are unchanged.

The live verification recorded **2696/6300** completed native episodes, with **8** additional episodes after preparation. All **2688** previously saved episode details were compared and retained. This is a partial evaluation, not a full benchmark result or a claim of long-run stability.

## Diagnosis

Historical fault-card memory: 77341 / 81559 MiB (94.8%), followed by PhysX CUDA 700. High memory pressure is a supported contributor; CUDA 700 alone does not establish an OOM root cause. After lowering concurrency, the old faulted GPU still produced Xid109/DEVICE_LOST before scene construction at roughly 24 GiB. Reducing concurrency alone did not clear the prior device fault.

The first continuation retained the original fallback. A fresh borrowing cycle then verified GPU release and absence of user device-file holders, reset only GPU7, and continued the same native result folders. Other GPUs were not reset. No global driver, Isaac version, physics, task budget, or RLT training settings were changed.

## Recovery behavior

- A per-GPU lock limits the original eight task groups to four simultaneous workers.
- Each incomplete task has at most three controller-level attempts. A known GPU fatal plus 120 seconds without actual action/episode progress, or 1800 seconds without progress otherwise, triggers exact cleanup and retry of that task and its matching policy process.
- Completed results and resume manifests are checked before retry; attempts have separate logs and process receipts. Exhausted attempts exit explicitly instead of silently advancing through missing tasks.
- The independent observer now follows each retry's log and generation. Dojo exit is still followed by exact cleanup, GPU release verification, restoration of the original four RLT runs, and first-round observation. An ownership/release failure remains a visible blocked return instead of taking another workload's GPU.

## Verification and reproduction

Six CPU checks passed on each server, including concurrency exclusion, warning-only stalls, fatal timeouts, real progress, fresh retry timers, and incomplete-budget handling. See `validation.json` for live post-reset progress and memory. The controller patches use zero context: inspect the baseline and use `git apply --unidiff-zero`. Full supporting files are snapshots of the deployed continuation; they are not a generic cluster launcher. Older paused/failed records remain historical evidence.

The SZ2 toast log also contained a property-window `scroll_y_max` AttributeError in `omni.kit.window.property`, followed by continuing real evaluation actions. This separate UI callback error is retained in verification evidence when present; it is not classified as a GPU fatal or silently treated as an error-free log.

## Primary-source leads

- [NVIDIA Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html): Xid31/109 are symptoms with several possible causes.
- [Isaac Sim 5.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html): H100 lacks RT cores and is outside official rendering support.
- [RoboDojo evaluation source](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/main/src/eval_client/main.py): existing native PhysX crash/resume support does not cover every blocked native call.
- [AllenAI integration PR101](https://github.com/allenai/vla-evaluation-harness/pull/101): reports RoboDojo environment teardown hanging; related evidence, not proof of our memory root cause.
- [NVTT multi-GPU issue1074](https://github.com/NVIDIAGameWorks/rtx-remix/issues/1074) and [595-driver discussion](https://forums.developer.nvidia.com/t/isaac-sim-6-0-1-gpu-crash-on-dgx-spark-gb10-arm64-driver-595-71-05/376418): different applications/platforms; no unverified driver or device-selection patch was applied.

Only this lightweight source/documentation bundle was uploaded. Models, assets, videos, private environment files and raw operations logs stay on the server.
