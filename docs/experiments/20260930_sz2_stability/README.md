# SZ2 Dojo stability work — 2026-09-30

At **2026-09-30T08:24:27+00:00**, evaluation was progressing on **all four GPUs 4–7**, with one worker per GPU and four environments per worker. The snapshot recorded **2737/6300** completed native episodes, **25** more than this continuation's preserved baseline. All **2712** baseline episode details were retained. These are partial live results; neither CPU checks nor this short observation establish that the GPU fault has been eliminated.

## Changes and boundaries

- Four GPU lanes now independently continue through seeds 0, 1, and 2. Each lane retains its original task groups, GPU, worker ID, port, result paths, and seed-specific checkpoint. This removes the cross-GPU seed barrier that left healthy cards waiting. It does not dynamically move tasks between GPUs.
- Process cleanup retains exact ownership, UID, start-time, command and run checks. Previously proved cleanup targets get bounded fresh identity reads during exit; unknown permission failures remain visible. Diagnostic receipts preserve the failed operation, PID/path, errno and traceback without copying full process environments.
- The original model, layouts, N4, camera/physics/action settings, 54 configurations, three seeds, native 25/50 budgets, and total 6300 episodes remain unchanged. A fault is not counted as success and missing layouts are not silently removed.
- Dojo exit still triggers exact cleanup and GPU-release verification before restoring the original four RLT runs. Ownership or release uncertainty fails closed. This remains a whole-four-GPU return, not per-card RLT preemption.

## Toast fault isolation

The live receipt verified a durable planned-batch manifest, the restored-queue marker, and a new simulator PID/start identity with the same policy-server identity. The new simulator was observed taking actions. Completion of the following batch is not yet established; long-run stability remains under evaluation.

SZ2 alone opts make_toast_random/OpenWAM/N4 into a fresh simulator process after a validated, normally completed batch while the policy server remains running. The exact queue/cursor, completed and abandoned layouts, unstable count, fatal-restart count, native result details, and video evidence are preserved and checked. Planned exits have a separate bounded allowance; integrity refusal exits 97 and cannot be accepted or retried as an ordinary partial result. The production diff is limited to the four paths recorded in source-references.json. GPU7 was reset only through the fresh cycle empty-card gate; no global driver change was made.

## Evidence and primary-source leads

`validation.json` contains sanitized live counters, four worker/seed/action snapshots, and CPU-check outcomes. `source-references.json` pins the deployed source and the v2 patch baseline. The runtime patches and full guard/tests are lightweight source snapshots; they are not a generic launcher. Raw operation logs, private config/environment files, model weights, assets and videos remain on the server.

For CPU reproduction, start from an isolated copy of the same-host v2 runtime and its dependencies, apply the three zero-context runtime patches with `git apply --unidiff-zero`, and replace the guard with this snapshot. Copy the three core test files and run each with the target Linux environment Python. For the toast checks, prepare a RoboDojo checkout at the recorded base commit and apply production-toast-isolation.patch with `git apply --unidiff-zero`, then run python -B test_batch_isolation.py --repo-root /path/to/that/checkout. The required candidate/scripts/eval_policy.sh is included here; test_batch_return.py additionally uses the patched runtime eval_recovery.py.

- [RoboDojo issue 10](https://github.com/RoboDojo-Benchmark/RoboDojo/issues/10) reports the same random-toast task hanging around a layout transition on a different GPU and N1. This is a close lead, not proof that our later CUDA700 has the same cause.
- [RoboDojo PR60](https://github.com/RoboDojo-Benchmark/RoboDojo/pull/60) addresses `/Room` versus `/Rooms` cleanup in another reset path.
- [RoboDojo PR61](https://github.com/RoboDojo-Benchmark/RoboDojo/pull/61) addresses repeated camera/render-product setup during soft reset. The inspected production path closes the environment and recreates the USD stage each batch, so these two PRs were not blindly applied and their reported resource growth is not asserted as our measured leak.

The working diagnosis remains incomplete. Continue measuring completed native episodes, genuine action progress, precise error receipts, and GPU faults across task/batch transitions; do not use GPU occupancy alone as a stability claim.
