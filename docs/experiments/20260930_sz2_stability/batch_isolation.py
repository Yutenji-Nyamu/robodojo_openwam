"""Opt-in batch process isolation; no simulator or policy imports."""
import hashlib
import json
import os
from pathlib import Path

KEY = "planned_batch_isolation_v1"
FLAG = "ROBODOJO_ISOLATE_TOAST_BATCHES"


def enabled(env):
    return (os.environ.get(FLAG) == "1" and env.task_name == "make_toast_random"
            and env.policy_name == "OpenWAM" and env.num_envs == 4)


def layout_map_digest(manager):
    encoded = json.dumps(manager.seed_info, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def queue_digest(data):
    return hashlib.sha256(json.dumps({k: data[k] for k in ("seed_list", "idx", "st_idx", "ed_idx", "num_envs")}, sort_keys=True).encode()).hexdigest()


def manifest_digest(state):
    return hashlib.sha256(json.dumps({k: v for k, v in state.items() if k != KEY}, sort_keys=True).encode()).hexdigest()


def restore(env, state):
    data = (state or {}).get(KEY)
    if data is None:
        return
    if not enabled(env):
        raise RuntimeError("planned queue present but isolation scope/flag differs")
    if (data["eval_num"] != env.eval_num or any(state.get(k) != getattr(env, k)
            for k in ("run_id", "task_name", "policy_name", "config_name", "eval_seed", "additional_info"))):
        raise RuntimeError("planned run identity or evaluation budget mismatch")
    if data["manifest_sha256"] != manifest_digest(state):
        raise RuntimeError("planned manifest checksum mismatch")
    if type(data["generation"]) is not int or data["generation"] < 0:
        raise RuntimeError("invalid planned restart generation")
    if type(data["fatal_restart_count"]) is not int or data["fatal_restart_count"] < 0:
        raise RuntimeError("invalid carried fatal restart count")
    manager = env.seed_manager
    queue, index = data["seed_list"], data["idx"]
    if (data["num_envs"] != 4 or data["layout_map_sha256"] != layout_map_digest(manager)
            or not isinstance(queue, list) or any(type(i) is not int for i in queue)
            or queue != sorted(set(queue)) or not set(queue) <= set(manager.seed_info)
            or type(index) is not int or not 0 <= index <= len(queue)
            or data["st_idx"] != 0 or data["ed_idx"] != len(queue)
            or data["queue_sha256"] != queue_digest(data)):
        raise RuntimeError("planned seed queue or layout mapping mismatch")
    excluded = set(state["completed_layout_ids"]) | set(state["abandoned_layout_ids"])
    if set(queue[index:]) & excluded or not (set(manager.seed_info) - set(queue)) <= excluded:
        raise RuntimeError("planned queue would replay completed/abandoned layouts")
    unstable = state["unstable_nums"]
    if type(unstable) is not int or unstable < 0:
        raise RuntimeError("invalid unstable count")
    manager.seed_list, manager.idx = list(queue), index
    manager.st_idx, manager.ed_idx = data["st_idx"], data["ed_idx"]
    manager._current_batch_seeds = None
    env.unstable_nums = unstable
    env._planned_batch_generation = data["generation"] + 1
    os.environ["ROBODOJO_FATAL_RESTART_COUNT"] = str(data["fatal_restart_count"])
    print(f"[batch-isolation] restored queue idx={index}/{len(queue)}, unstable={unstable}", flush=True)


def prepare_exit(env, previous_total):
    """Only called after run_eval + eval_step return normally; returns rc98-ready."""
    manager = env.seed_manager
    total = env.success_nums + env.fail_nums
    if not enabled(env) or total >= env.eval_num or manager.idx >= manager.ed_idx:
        return False
    if total <= previous_total:
        return False
    if manager._current_batch_seeds is not None or env.video_writers:
        raise RuntimeError("batch still has active seeds or video writers")
    expected = getattr(env, "_planned_batch_videos", [])
    if not expected or any(not Path(p).is_file() or Path(p).stat().st_size == 0 for p in expected):
        raise RuntimeError("batch video commit incomplete")
    normalised = json.loads(json.dumps(env.eval_result, default=str))
    if json.loads((Path(env.save_dir) / "_result.json").read_text(encoding="utf-8")) != normalised:
        raise RuntimeError("saved result differs from live committed result")
    details = normalised["details"]
    if len(details) != total or set(details) != {str(i) for i in range(total)}:
        raise RuntimeError("non-contiguous result index or count mismatch")
    ids = [v["layout_id"] for v in details.values()]
    if len(ids) != len(set(ids)) or sum(v["success"] is True for v in details.values()) != env.success_nums:
        raise RuntimeError("duplicated layout or success count mismatch")
    for i in range(previous_total, total):
        if not any(Path(p).name.startswith(f"episode_{i:07d}_") for p in expected):
            raise RuntimeError(f"episode {i} has no committed video")
    # run_eval already persists the base manifest. Do not overwrite it twice.
    path = Path(env.resume_manifest_path())
    state = json.loads(path.read_text(encoding="utf-8"))
    if (state["details"] != details or state["success_nums"] != env.success_nums
            or state["fail_nums"] != env.fail_nums or state["unstable_nums"] != env.unstable_nums
            or state["completed_layout_ids"] != sorted(ids)
            or state["total_score"] != env.total_score
            or state["abandoned_layout_ids"] != sorted(env.abandoned_seeds)
            or any(state.get(k) != getattr(env, k) for k in
                   ("run_id", "task_name", "policy_name", "config_name", "eval_seed", "save_dir", "additional_info"))):
        raise RuntimeError("authoritative resume manifest mismatch")
    state[KEY] = {"seed_list": list(manager.seed_list), "idx": manager.idx,
                  "st_idx": manager.st_idx, "ed_idx": manager.ed_idx,
                  "num_envs": manager.num_envs, "layout_map_sha256": layout_map_digest(manager),
                  "generation": getattr(env, "_planned_batch_generation", 0), "eval_num": env.eval_num,
                  "manifest_sha256": manifest_digest(state),
                  "fatal_restart_count": int(os.environ.get("ROBODOJO_FATAL_RESTART_COUNT", "0"))}
    state[KEY]["queue_sha256"] = queue_digest(state[KEY])
    temporary = path.with_name(path.name + ".planned.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if json.loads(path.read_text(encoding="utf-8")) != state:
        raise RuntimeError("planned manifest readback mismatch")
    cameras = sum(len(c) for c in getattr(env.camera_manager, "cameras", []))
    products = len(getattr(env.capture_manager, "tiled_render_products", []))
    print(f"[batch-isolation] committed episodes={total}; queue idx={manager.idx}/{manager.ed_idx}; "
          f"next={manager.seed_list[manager.idx:manager.idx + 4]}; cameras={cameras}; "
          f"render_products={products}; generation={state[KEY]['generation']}; rc=98", flush=True)
    return True
