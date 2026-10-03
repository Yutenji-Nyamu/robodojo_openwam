"""CPU-only contract checks for trace_hook, using no project/Isaac imports."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import trace_hook as hook


class FakeTimer:
    def __init__(self, seconds, callback):
        self.seconds, self.callback = seconds, callback
        self.started = self.cancelled = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


class FakeArticulationView:
    def __init__(self):
        self.body_names = ["base", "lid"]
        self.masses = [[0.8, 0.2]]
        self.inertias = [[[0.01, 0, 0, 0, 0.02, 0, 0, 0, 0.03]] * 2]
        self.calls = []

    def get_body_masses(self, clone=True):
        self.calls.append(("masses", clone))
        return self.masses

    def get_body_inertias(self, clone=True):
        self.calls.append(("inertias", clone))
        return self.inertias


class FakeObject:
    category_name = "laptop"

    def __init__(self):
        self.pose = ([0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 0.0])
        self.velocity = [0.0, 0.0, 0.0]
        self.angular_velocity = [0.0, 0.0, 0.0]
        self.joint_positions = [0.0]
        self.joint_velocities = [0.0]
        self._articulation_view = FakeArticulationView()

    def get_world_pose(self):
        return self.pose

    def get_linear_velocity(self):
        return self.velocity

    def get_angular_velocity(self):
        return self.angular_velocity

    def get_joint_positions(self):
        return self.joint_positions

    def get_joint_velocities(self):
        return self.joint_velocities


class FakeScene:
    def __init__(self):
        self.articulations = {
            f"env{i}_articulation_laptop_3_{i}": FakeObject() for i in range(4)
        }
        self.rigids = {"env0_rigid_headset_9_18": FakeObject()}

    def get_objects(self, object_type=None):
        return {"articulation": self.articulations, "rigid": self.rigids}[object_type]


class FakeEnv:
    def __init__(self):
        self.num_envs, self.env_seeds, self.eval_seed = 4, [0, 1, 2, 3], 0
        self.current_env_seed_map = {i: i for i in range(4)}
        self.policy_name = "Pi_05"
        self.task_name = "store_laptop_and_headphones_random"
        self.run_id = "diag-gpu7-cpu-contract"
        self.sim_cfg = SimpleNamespace(decimation=1)
        self.scene_manager = FakeScene()
        keys = []
        for _ in range(2):
            data = SimpleNamespace(**{
                name: [[0.0, 0.0] for _ in range(4)] for name in
                ("joint_pos", "joint_vel", "joint_pos_target", "joint_vel_target")
            })
            keys.append(SimpleNamespace(data=data))
        self.robot_manager = SimpleNamespace(
            robot_key=keys,
            robot_list=[SimpleNamespace(arm_name="left_arm"),
                        SimpleNamespace(arm_name="right_arm")],
        )
        self.actions = [{"left_arm": [0.1, 0.2], "left_gripper": [0.5]}
                        for _ in range(4)]
        self.run_calls, self.action_calls, self.step_calls = [], [], []
        self.step_result, self.action_result = object(), object()
        self.after_step = self.action_impl = self.run_impl = None
        self.returned_action = self.returned_step = None

    def sim_step(self, *args, **kwargs):
        self.step_calls.append((args, kwargs))
        if self.after_step:
            self.after_step()
        return self.step_result

    def take_action_batch(self, actions, *args, **kwargs):
        self.action_calls.append((actions, args, kwargs))
        if self.action_impl:
            self.action_impl(actions)
        self.returned_step = self.sim_step("step-arg", sample=False)
        return self.action_result

    def run_eval(self, *args, **kwargs):
        self.run_calls.append((args, kwargs))
        if self.run_impl:
            return self.run_impl()
        self.returned_action = self.take_action_batch(
            self.actions, env_idx_list=[0, 1, 2, 3])
        return "batch-result"


class TraceContracts(unittest.TestCase):
    def make_env(self, **options):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        env, codes = FakeEnv(), []
        output = Path(root.name) / "diagnostic"
        hook.instrument(env, output, codes.append, timer_factory=FakeTimer, **options)
        self.addCleanup(env._dojo_diagnostic_trace.close)
        return env, codes, output

    def stopped(self, env, codes, output, expected, *args, **kwargs):
        with self.assertRaises(hook.DiagnosticStopped) as stopped:
            env.run_eval(*args, **kwargs)
        self.assertEqual(stopped.exception.args, (expected,))
        self.assertEqual(codes, [expected])
        receipt = json.loads((output / "terminal.json").read_text())
        self.assertEqual(receipt["exit_code"], expected)
        self.assertFalse(env._dojo_diagnostic_trace.enabled)
        self.assertTrue(env._dojo_diagnostic_trace.timer.cancelled)
        rows = [json.loads(line) for line in
                (output / "trace.jsonl").read_text().splitlines()]
        return receipt, rows

    def test_healthy_first_batch_preserves_calls_arguments_and_values(self):
        env, codes, output = self.make_env()
        original_actions = copy.deepcopy(env.actions)
        receipt, rows = self.stopped(env, codes, output, 85, "run-arg", flag=True)
        self.assertEqual(receipt["kind"], "diagnostic_complete")
        self.assertEqual(len(env.run_calls), 1)
        self.assertEqual(env.run_calls[0], (("run-arg",), {"flag": True}))
        self.assertEqual(len(env.action_calls), 1)
        self.assertIs(env.action_calls[0][0], env.actions)
        self.assertEqual(env.action_calls[0][2], {"env_idx_list": [0, 1, 2, 3]})
        self.assertEqual(env.actions, original_actions)
        self.assertEqual(env.step_calls, [(("step-arg",), {"sample": False})])
        self.assertIs(env.returned_action, env.action_result)
        self.assertIs(env.returned_step, env.step_result)
        phases = [r["phase"] for r in rows if r["kind"] == "physics_state"]
        self.assertEqual(phases, ["batch_entry", "before_action",
                                 "before_physics_step", "after_physics_step",
                                 "after_action", "batch_return"])
        for row in rows:
            if row.get("phase") in ("before_physics_step", "after_physics_step"):
                self.assertEqual(len(row["objects"]), 4)
        self.assertEqual(receipt["tick"], 1)

    def test_reset_steps_are_passthrough_even_for_offscreen_objects(self):
        env, codes, output = self.make_env()
        laptop = next(iter(env.scene_manager.articulations.values()))
        laptop.pose[0][0] = 100000.0
        self.assertIs(env.sim_step("reset"), env.step_result)
        self.assertEqual(codes, [])
        self.assertEqual((output / "trace.jsonl").stat().st_size, 0)
        laptop.pose[0][0] = 0.0
        self.stopped(env, codes, output, 85)
        self.assertEqual(len(env.step_calls), 2)

    def test_original_action_snapshot_is_detached(self):
        env, codes, output = self.make_env()
        original = copy.deepcopy(env.actions)
        env.action_impl = lambda actions: actions[0]["left_arm"].__setitem__(0, 9.0)
        _, rows = self.stopped(env, codes, output, 85)
        action_row = next(r for r in rows if r["kind"] == "policy_action")
        self.assertEqual(action_row["actions"], original)
        self.assertIs(env.action_calls[0][0], env.actions)
        self.assertEqual(env.actions[0]["left_arm"][0], 9.0)

    def test_scope_rejected_before_original_run(self):
        for field, value in (("num_envs", 1), ("env_seeds", [4, 5, 6, 7]),
                             ("eval_seed", 1), ("policy_name", "OpenWAM"),
                             ("run_id", "formal")):
            with self.subTest(field=field):
                env, codes, output = self.make_env()
                setattr(env, field, value)
                receipt, _ = self.stopped(env, codes, output, 86)
                self.assertEqual(receipt["kind"], "diagnostic_failed")
                self.assertEqual(env.run_calls, [])
        env, codes, output = self.make_env()
        env.sim_cfg.decimation = 2
        self.stopped(env, codes, output, 86)
        self.assertEqual(env.run_calls, [])

    def test_missing_getter_none_exception_and_robot_field_fail_closed(self):
        def broken_getter():
            raise RuntimeError("read failure")

        for corruption in ("missing_getter", "none_result", "exception", "robot_field"):
            with self.subTest(corruption=corruption):
                env, codes, output = self.make_env()
                laptop = next(iter(env.scene_manager.articulations.values()))
                if corruption == "missing_getter":
                    laptop.get_linear_velocity = None
                elif corruption == "none_result":
                    laptop.get_linear_velocity = lambda: None
                elif corruption == "exception":
                    laptop.get_linear_velocity = broken_getter
                else:
                    del env.robot_manager.robot_key[0].data.joint_pos_target
                receipt, _ = self.stopped(env, codes, output, 86)
                self.assertEqual(receipt["kind"], "diagnostic_failed")
                self.assertEqual(receipt["phase"], "run_eval")
                self.assertEqual(env.run_calls, [])
                self.assertEqual(env.action_calls, [])

    def test_requires_four_laptops(self):
        env, codes, output = self.make_env()
        env.scene_manager.articulations.pop("env3_articulation_laptop_3_3")
        receipt, _ = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["kind"], "diagnostic_failed")
        self.assertIn("exactly one laptop", receipt["exception"])
        self.assertEqual(env.run_calls, [])

    def test_link_properties_are_read_once_before_first_action(self):
        env, codes, output = self.make_env()
        _, rows = self.stopped(env, codes, output, 85)
        properties = [row for row in rows if row["kind"] == "link_properties"]
        self.assertEqual(len(properties), 4)
        for row in properties:
            self.assertEqual(row["action"], 0)
            self.assertEqual(row["body_names"], ["base", "lid"])
            self.assertEqual(row["masses"], [[0.8, 0.2]])
            self.assertEqual(len(row["inertias"][0]), 2)
        for laptop in env.scene_manager.articulations.values():
            self.assertEqual(laptop._articulation_view.calls,
                             [("masses", True), ("inertias", True)])

    def test_link_properties_missing_failure_and_shape_stop_before_actions(self):
        def failed_read(**kwargs):
            raise RuntimeError("mass read failed")

        for corruption in ("missing", "none", "exception", "mass_shape", "inertia_shape", "nonfinite"):
            with self.subTest(corruption=corruption):
                env, codes, output = self.make_env()
                view = next(iter(env.scene_manager.articulations.values()))._articulation_view
                if corruption == "missing":
                    view.get_body_masses = None
                elif corruption == "none":
                    view.get_body_masses = lambda **kwargs: None
                elif corruption == "exception":
                    view.get_body_masses = failed_read
                elif corruption == "mass_shape":
                    view.masses = [[0.8]]
                elif corruption == "inertia_shape":
                    view.inertias = [[[1, 2, 3], [1, 2, 3]]]
                else:
                    view.masses = [[float("nan"), 0.2]]
                receipt, _ = self.stopped(env, codes, output, 86)
                self.assertEqual(receipt["kind"], "diagnostic_failed")
                self.assertIn("link_properties", receipt["exception"])
                self.assertEqual(env.run_calls, [])
                self.assertEqual(env.action_calls, [])

    def test_later_getter_failure_preserves_already_read_states(self):
        env, codes, output = self.make_env()

        def failed_read():
            raise RuntimeError("late GPU read failed")

        def corrupt_after_step():
            env.scene_manager.articulations["env0_articulation_laptop_3_0"].pose[0][0] = 1e12
            env.scene_manager.articulations["env3_articulation_laptop_3_3"].get_world_pose = failed_read

        env.after_step = corrupt_after_step
        receipt, rows = self.stopped(env, codes, output, 86)
        partial = next(row for row in rows if row["kind"] == "physics_state_partial")
        self.assertEqual(partial["phase"], "after_physics_step")
        self.assertEqual(len(partial["objects"]), 3)
        self.assertEqual(partial["objects"]["env0_articulation_laptop_3_0"]["pose"][0][0], 1e12)
        self.assertEqual(receipt["phase"], "sim_step")
        self.assertEqual(len(env.step_calls), 1)

    def test_nonfinite_action_is_logged_and_never_applied(self):
        env, codes, output = self.make_env()
        env.actions[0]["left_arm"][0] = float("nan")
        receipt, rows = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["reason"], "nonfinite_policy_action")
        action_row = next(r for r in rows if r["kind"] == "policy_action")
        self.assertEqual(action_row["actions"][0]["left_arm"][0], "NaN")
        self.assertEqual(env.action_calls, [])
        self.assertEqual(env.step_calls, [])

    def test_first_post_step_divergence_stops_before_more_actions(self):
        env, codes, output = self.make_env()
        laptop = env.scene_manager.articulations["env3_articulation_laptop_3_3"]
        env.after_step = lambda: laptop.pose[0].__setitem__(0, 1e12)
        receipt, rows = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["reason"], "diagnostic_range_crossed")
        self.assertEqual(receipt["phase"], "after_physics_step")
        self.assertEqual(receipt["object"], "env3_articulation_laptop_3_3")
        self.assertEqual(receipt["tick"], 1)
        self.assertEqual(len(env.action_calls), 1)
        self.assertEqual(len(env.step_calls), 1)
        self.assertFalse(any(r.get("phase") == "after_action" for r in rows))

    def test_original_action_exception_does_not_enter_outer_retry(self):
        env, codes, output = self.make_env()

        def broken_action(_):
            raise RuntimeError("original action failed")

        env.action_impl = broken_action
        receipt, _ = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["kind"], "diagnostic_failed")
        self.assertEqual(receipt["phase"], "take_action_batch")
        self.assertEqual(receipt["exception"], "original action failed")
        self.assertEqual(len(env.action_calls), 1)
        self.assertEqual(env.step_calls, [])

    def test_size_bound_reserves_terminal_receipt(self):
        bound = hook.RECEIPT_RESERVE + 32
        env, codes, output = self.make_env(max_bytes=bound)
        receipt, _ = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["reason"], "trace_size_limit")
        self.assertLessEqual(sum(p.stat().st_size for p in output.iterdir()), bound)
        self.assertEqual(env.run_calls, [])

    def test_time_bound_and_timer_have_failure_receipts(self):
        now = [0.0]
        env, codes, output = self.make_env(clock=lambda: now[0], max_seconds=2)
        now[0] = 2.0
        receipt, _ = self.stopped(env, codes, output, 86)
        self.assertEqual(receipt["reason"], "time_limit")
        self.assertEqual(env.run_calls, [])
        env, codes, output = self.make_env(max_seconds=2)
        with self.assertRaises(hook.DiagnosticStopped):
            env._dojo_diagnostic_trace.timer.callback()
        self.assertEqual(codes, [86])
        receipt = json.loads((output / "terminal.json").read_text())
        self.assertEqual(receipt["reason"], "time_limit")

    def test_limits_and_factory_guard_fail_before_factory_or_output(self):
        for max_bytes, max_seconds in ((hook.MAX_BYTES + 1, 1),
                                       (hook.RECEIPT_RESERVE, 1),
                                       (hook.MAX_BYTES, hook.MAX_SECONDS + 1),
                                       (hook.MAX_BYTES, float("nan"))):
            with self.subTest(max_bytes=max_bytes, max_seconds=max_seconds):
                with self.assertRaises(ValueError):
                    hook.validate_limits(max_bytes, max_seconds)
        calls = []
        factory = hook.wrap_factory(lambda: calls.append(True))
        with patch.dict("os.environ", {"ROBODOJO_RUN_ID": "formal"}, clear=True):
            with self.assertRaises(ValueError):
                factory()
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
