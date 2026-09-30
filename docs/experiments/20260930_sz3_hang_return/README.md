# Dojo stall detection and RLT return — 2026-09-30

Dojo remained alive after simulator/GPU faults, so the existing exit/cleanup/finally path never returned its GPUs to RLT. Both affected sweeps are now paused and their original four RLT jobs have resumed. All eight jobs produced a real post-checkpoint round; the stage and training budget were preserved. See [STATUS.json](STATUS.json) for this server's timestamped evidence.

The retained partial evaluation counts are **2688/6300 (SZ2 OpenWAM)** and **1606/6300 (SZ3 pi0.5)**. Every previously saved episode detail was compared with its pre-stop snapshot and preserved. These are partial results, not a full benchmark score.

## Changes

- An independent [watchdog](hang_watchdog.py) observes each RUNNING task's real action steps and completed episodes every 30 seconds. Repeated warning output is not progress. After 5 minutes without progress with a GPU-fatal marker, or 30 minutes without progress otherwise, it sends TERM to the exact owned Dojo controller. The existing outer pipeline still owns cleanup, GPU-release checks, and RLT restoration.
- The watchdog checks the parent/child identities, UID, PID start time, command digest, frozen controller, active continuation, and stopped-RLT receipt. It stays idle during RLT. Completed workers and stale attempts are excluded. A cleanup/identity failure is recorded for attention instead of bypassing ownership checks.
- SZ3 hit a second fault while restoring: repeated `after-dojo` suffixes made new output names 259/265 bytes long, beyond NAME_MAX=255. No training had been dispatched. Only the four never-created output names and corresponding six output/config bookkeeping fields were corrected, with backups; original checkpoints and algorithms remained unchanged.
- [Bounded output naming](bounded_resume_name.py) and [the small helper patch](resume-naming.patch) prevent this growth in the next prepared borrowing cycle. Current running frozen helpers were not hot-edited.

## Validation and scope

Both servers passed 12 [targeted CPU tests](test_hang_watchdog.py), including an exact-child TERM test that leaves a neighboring process alive. Recorded real controller bindings were replayed. Real fault logs triggered the new detector for the three GPU-fatal stalls and the separate no-progress xylophone stall. Original episode details were verified unchanged. First-round proof comes from real resumed training logs and metrics, not dispatch alone.

The watchdog is deployed as a detached user process for each existing run and its subsequent continuations. It is not a boot service; a reboot or a different run path needs explicit redeployment. If the controller ignores TERM, or ownership/cleanup checks fail, the watchdog reports attention; it does not reset GPUs, kill shared Ray, or launch duplicate training jobs.

## Prior occurrence and source limits

Similar Xid31/109 failures occurred on September 29. A localized GPU reset allowed evaluation to run again but did not establish a root-cause fix; the failure recurred on SZ2 and appeared on a different SZ3 GPU. This repair fixes resource return and output naming. It does **not** claim the simulator/GPU fault is solved.

- [NVIDIA Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html): Xid31 is a GPU memory page fault; application, driver, and hardware causes are possible. Xid109 is a context-switch timeout, with GPU reset listed as an immediate recovery action and further investigation still required.
- [RoboDojo evaluation client](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/main/src/eval_client/main.py): upstream catches PhysX fatal errors and persists progress before restart/exit. Inference: that exception path cannot execute while a native call never returns, motivating an external progress observer.
- [Omniverse headless/zenity troubleshooting](https://docs.omniverse.nvidia.com/dsx/latest/troubleshooting.html) describes a distinct initialization/IOMMU-dialog hang. These runs had already evaluated many episodes before Xid errors; `zenity: not found` alone does not establish that diagnosis.
- [IsaacSim issue 713](https://github.com/isaac-sim/IsaacSim/issues/713) and [NVIDIA Xid109 discussion](https://forums.developer.nvidia.com/t/xid109-ctx-switch-timeout-driver-crashes-in-many-applications/283722) show related symptoms on different configurations. No verified drop-in fix for this H100 workload was found; unrelated driver, BIOS, concurrency, or benchmark changes were not applied.
