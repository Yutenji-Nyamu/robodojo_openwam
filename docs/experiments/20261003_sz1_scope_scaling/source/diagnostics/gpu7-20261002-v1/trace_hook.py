"""Independent first-batch observer; never edits actions or production sources.

Range limits stop a diagnostic run; they are not a simulator repair. Exit 85
means the first batch returned normally, 86 means anomaly/diagnostic failure.
The external owner is responsible for exact process cleanup and GPU return.
"""
import json
import math
import os
from pathlib import Path
import re
import threading
import time

MAX_BYTES = 1024 ** 3
MAX_SECONDS = 20 * 60
RECEIPT_RESERVE = 65536


class DiagnosticStopped(BaseException):
    """Only reachable if an injected exit callback returns (CPU tests)."""


def plain(value):
    """Make a detached snapshot, preserving nonfinite numbers for checks."""
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"Unsupported diagnostic value type: {type(value).__name__}")


def numbers(value):
    if isinstance(value, dict):
        return [n for v in value.values() for n in numbers(v)]
    if isinstance(value, (list, tuple)):
        return [n for v in value for n in numbers(v)]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [float(value)]
    raise TypeError(f"Expected a numeric value, got {type(value).__name__}")


def json_safe(value):
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("+Inf" if value > 0 else "-Inf")
    return value


def encoded(value):
    return (json.dumps(json_safe(plain(value)), allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def validate_limits(max_bytes, max_seconds):
    if type(max_bytes) is not int or not RECEIPT_RESERVE < max_bytes <= MAX_BYTES:
        raise ValueError("Trace byte limit must be >64 KiB and <=1 GiB")
    if not isinstance(max_seconds, (int, float)) or isinstance(max_seconds, bool):
        raise ValueError("Diagnostic time limit must be numeric")
    if not math.isfinite(max_seconds) or not 0 < max_seconds <= MAX_SECONDS:
        raise ValueError("Diagnostic time limit must be >0 and <=1200 seconds")


class Trace:
    def __init__(self, env, output, stop=None, *, max_bytes=MAX_BYTES,
                 max_seconds=MAX_SECONDS, clock=time.monotonic,
                 timer_factory=threading.Timer):
        validate_limits(max_bytes, max_seconds)
        self.env, self.stop = env, stop or os._exit
        self.path = Path(output)
        self.path.mkdir(parents=True, exist_ok=False)
        self.log = (self.path / "trace.jsonl").open("xb")
        self.lock = threading.RLock()
        self.clock, self.started = clock, clock()
        self.max_bytes, self.max_seconds = max_bytes, max_seconds
        self.bytes_written = 0
        self.tick = self.action = 0
        self.enabled = self.entered = self.finished = False
        self.last_actions = None
        # Includes reset/setup after factory return. The eventual launcher also
        # needs an outer deadline for native calls that hold the Python GIL.
        # os._exit bypasses main's retry/seed handlers.
        self.timer = timer_factory(max_seconds, lambda: self.halt("time_limit", kind="diagnostic_limit"))
        self.timer.daemon = True
        self.timer.start()

    def close(self):
        self.timer.cancel()
        with self.lock:
            if not self.log.closed:
                self.log.close()

    def check_time(self):
        if self.clock() - self.started >= self.max_seconds:
            self.halt("time_limit", kind="diagnostic_limit")

    def write(self, kind, **data):
        self.check_time()
        row = dict(kind=kind, time=time.time(), tick=self.tick, action=self.action, **data)
        payload = encoded(row)
        with self.lock:
            if self.bytes_written + len(payload) > self.max_bytes - RECEIPT_RESERVE:
                self.halt("trace_size_limit", kind="diagnostic_limit")
            self.log.write(payload)
            self.log.flush()
            self.bytes_written += len(payload)

    def finish(self, code, kind, reason, **data):
        with self.lock:
            if self.finished:
                raise DiagnosticStopped(code)
            self.finished, self.enabled = True, False
            self.timer.cancel()
            row = dict(kind=kind, reason=reason, exit_code=code, tick=self.tick,
                       action=self.action, elapsed_s=self.clock() - self.started,
                       latest_actions=self.last_actions, **data)
            payload = encoded(row)
            if len(payload) > RECEIPT_RESERVE:
                payload = encoded(dict(kind=kind, reason=reason, exit_code=code,
                                       tick=self.tick, action=self.action,
                                       details_omitted="terminal receipt exceeds 64 KiB"))
            temporary = self.path / "terminal.json.tmp"
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path / "terminal.json")
            self.log.flush()
            os.fsync(self.log.fileno())
            self.log.close()
        self.stop(code)
        raise DiagnosticStopped(code)

    def halt(self, reason, *, kind="first_anomaly", **data):
        self.finish(86, kind, reason, **data)

    def failed(self, phase, exc):
        self.halt("diagnostic_read_or_execution_failed", kind="diagnostic_failed",
                  phase=phase, exception_type=type(exc).__name__, exception=str(exc))

    def scope(self):
        env = self.env
        if (env.num_envs != 4 or list(env.env_seeds) != [0, 1, 2, 3]
                or env.current_env_seed_map != {i: i for i in range(4)}
                or env.eval_seed != 0 or env.policy_name != "Pi_05"
                or env.task_name != "store_laptop_and_headphones_random"
                or env.sim_cfg.decimation != 1
                or not env.run_id.startswith("diag-gpu7-")):
            raise ValueError("Requires diagnostic Pi05/N4/seed0/layout0-3/decimation1 first batch")

    def required(self, obj, method, **kwargs):
        fn = getattr(obj, method, None)
        if not callable(fn):
            raise TypeError(f"Missing required getter {method}")
        value = plain(fn(**kwargs))
        if value is None or not numbers(value):
            raise ValueError(f"Missing/empty result from {method}")
        return value

    def object_state(self, obj, articulation):
        state = {"pose": self.required(obj, "get_world_pose"),
                 "linear_velocity": self.required(obj, "get_linear_velocity"),
                 "angular_velocity": self.required(obj, "get_angular_velocity")}
        pose = state["pose"]
        if (not isinstance(pose, list) or len(pose) != 2
                or len(pose[0]) != 3 or len(pose[1]) != 4
                or len(state["linear_velocity"]) != 3
                or len(state["angular_velocity"]) != 3):
            raise ValueError("Unexpected root state dimensions")
        if articulation:
            state["joint_positions"] = self.required(obj, "get_joint_positions")
            state["joint_velocities"] = self.required(obj, "get_joint_velocities")
        return state

    def sample(self, phase, include_rigid=False):
        manager = self.env.scene_manager
        articulations = manager.get_objects(object_type="articulation")
        laptops = {k: v for k, v in articulations.items() if v.category_name == "laptop"}
        indices = []
        for key in laptops:
            match = re.match(r"^env([0-3])_articulation_", key)
            if match is None:
                raise ValueError(f"Unexpected laptop key {key}")
            indices.append(int(match.group(1)))
        if sorted(indices) != [0, 1, 2, 3]:
            raise ValueError("Diagnostic requires exactly one laptop in each of four environments")
        states, robots = {}, {}
        try:
            for key, obj in laptops.items():
                states[key] = self.object_state(obj, True)
            if include_rigid:
                for key, obj in manager.get_objects(object_type="rigid").items():
                    states[key] = self.object_state(obj, False)
            manager = self.env.robot_manager
            if not manager.robot_key or len(manager.robot_key) != len(manager.robot_list):
                raise ValueError("Missing/mismatched robot objects")
            for index, (robot, key) in enumerate(zip(manager.robot_list, manager.robot_key)):
                state = {name: plain(getattr(key.data, name)) for name in
                         ("joint_pos", "joint_vel", "joint_pos_target", "joint_vel_target")}
                if any(not isinstance(v, list) or len(v) != 4 or not numbers(v) for v in state.values()):
                    raise ValueError("Missing/invalid four-environment robot data")
                robots[f"robot{index}:{robot.arm_name}"] = state
        except Exception as exc:
            self.write("physics_state_partial", phase=phase, objects=states,
                       robots=robots, exception_type=type(exc).__name__, exception=str(exc))
            raise
        self.write("physics_state", phase=phase, objects=states, robots=robots)
        for name, state in states.items():
            if any(not math.isfinite(v) for v in numbers(state)):
                self.halt("nonfinite_state", phase=phase, object=name, state=state)
            if (max(abs(v) for v in numbers(state["pose"][0])) > 100
                    or max(abs(v) for v in numbers(state["linear_velocity"])) > 100):
                self.halt("diagnostic_range_crossed", phase=phase, object=name, state=state)
        for name, state in robots.items():
            if any(not math.isfinite(v) for v in numbers(state)):
                self.halt("nonfinite_robot_state", phase=phase, robot=name, state=state)
        if phase == "batch_entry":
            for key, obj in laptops.items():
                try:
                    view = obj._articulation_view
                    names = list(view.body_names)
                    if not names or any(not isinstance(name, str) or not name for name in names):
                        raise ValueError("Missing/invalid body_names")
                    masses = self.required(view, "get_body_masses", clone=True)
                    inertias = self.required(view, "get_body_inertias", clone=True)
                    self.write("link_properties", object=key, body_names=names,
                               masses=masses, inertias=inertias)
                    count = len(names)
                    if (len(masses) != 1 or len(masses[0]) != count
                            or len(inertias) != 1 or len(inertias[0]) != count
                            or any(len(matrix) != 9 for matrix in inertias[0])):
                        raise ValueError("Expected link masses (1,K) and inertias (1,K,9)")
                    if any(not math.isfinite(v) for v in numbers([masses, inertias])):
                        raise ValueError("Nonfinite link mass/inertia")
                except Exception as exc:
                    raise RuntimeError(f"{key} link_properties: {type(exc).__name__}: {exc}") from exc


def instrument(env, output, stop=None, **trace_options):
    if hasattr(env, "_dojo_diagnostic_trace"):
        raise ValueError("Environment is already instrumented")
    trace = Trace(env, output, stop, **trace_options)
    run, step, act = env.run_eval, env.sim_step, env.take_action_batch

    def observed_run(*args, **kwargs):
        try:
            if trace.entered:
                raise ValueError("Only the first batch is permitted")
            trace.scope()
            trace.entered = trace.enabled = True
            trace.sample("batch_entry", include_rigid=True)
            result = run(*args, **kwargs)
            trace.sample("batch_return", include_rigid=True)
        except Exception as exc:
            trace.failed("run_eval", exc)
        finally:
            trace.enabled = False
        trace.finish(85, "diagnostic_complete", "first_batch_returned_normally")
        return result  # os._exit / DiagnosticStopped above never returns

    def observed_step(*args, **kwargs):
        if not trace.enabled:
            return step(*args, **kwargs)
        try:
            trace.sample("before_physics_step")
            result = step(*args, **kwargs)
            trace.tick += 1
            trace.sample("after_physics_step")
            return result
        except Exception as exc:
            trace.failed("sim_step", exc)

    def observed_action(actions, *args, **kwargs):
        if not trace.enabled:
            return act(actions, *args, **kwargs)
        try:
            trace.action += 1
            trace.last_actions = plain(actions)
            trace.write("policy_action", actions=trace.last_actions, args=args, kwargs=kwargs)
            if not numbers(trace.last_actions):
                raise ValueError("Empty policy action")
            if any(not math.isfinite(v) for v in numbers(trace.last_actions)):
                trace.halt("nonfinite_policy_action")
            trace.sample("before_action", include_rigid=True)
            result = act(actions, *args, **kwargs)
            trace.sample("after_action", include_rigid=True)
            return result
        except Exception as exc:
            trace.failed("take_action_batch", exc)

    env.run_eval, env.sim_step, env.take_action_batch = observed_run, observed_step, observed_action
    env._dojo_diagnostic_trace = trace
    return env


def wrap_factory(factory):
    def wrapped(*args, **kwargs):
        if not os.environ.get("ROBODOJO_RUN_ID", "").startswith("diag-gpu7-"):
            raise ValueError("Diagnostic run ID required")
        output = os.environ["DOJO_DIAGNOSTIC_TRACE"]
        limits = dict(max_bytes=int(os.environ.get("DOJO_DIAGNOSTIC_MAX_BYTES", MAX_BYTES)),
                      max_seconds=float(os.environ.get("DOJO_DIAGNOSTIC_MAX_SECONDS", MAX_SECONDS)))
        validate_limits(**limits)
        return instrument(factory(*args, **kwargs), output, **limits)
    return wrapped
