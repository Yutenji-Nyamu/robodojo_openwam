# Recovery scope

The planned rc98 path validates the durable manifest and preserves its exact queue. This claim does not extend to every legacy fatal path: the upstream manifest loader can ignore a malformed manifest, and ordinary fatal persistence can replace planned metadata with the older manifest format. Any such event needs a separate integrity audit. Neither occurred in the short live validation of the first planned transition.

The native task budget is read from the frozen plan and controls the main evaluation loop. The environment object's saved eval_num can retain the upstream default 50 because its config was copied earlier; this internal snapshot does not override the main loop's native 25-episode toast budget. Planned restarts are capped at 8 by the deployed launcher.

The toast instruction is a single fixed template. Description selection reseeds at its existing entry points, and the policy server remains resident across the new simulator connection. No model, observation, action, camera, physics or native seed-budget change was introduced. Existing completed and abandoned layout IDs are carried forward; a historical abandoned layout is not relabeled as a successful episode.

The last full-budget close and simulator startup still use bounded external progress supervision. Cross-batch process isolation reduces shared simulator state, but does not establish a unique cause or a permanent cure for CUDA700/Xid failures.
