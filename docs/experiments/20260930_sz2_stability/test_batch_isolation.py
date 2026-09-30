"""Run on the server CPU: python test_batch_isolation.py --repo-root /path/to/RoboDojo.

No simulator/model import, no GPU use. Uses actual SeedManager queue methods and
the candidate's exact Bash retry loop with a fake child process.
"""
import argparse
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument("--repo-root", type=Path, required=True)
args, remaining = parser.parse_known_args()
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("isolation", HERE / "batch_isolation.py")
iso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iso)
tree = ast.parse((args.repo_root / "env/seed_manager/seed_manager.py").read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SeedManager")
methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in {"get_seeds", "eval_step"}]
namespace = {"List": list, "deepcopy": copy.deepcopy}
exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), "actual_seed_manager_methods", "exec"), namespace)


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.flag = patch.dict(os.environ, {iso.FLAG: "1"})
        self.flag.start()
        self.manager = SimpleNamespace(num_envs=4, seed_list=list(range(12)), idx=5,
            st_idx=0, ed_idx=12, _current_batch_seeds=None,
            seed_info={i: {"scene_layout": f"layout_{i}.json"} for i in range(12)})
        self.manager.get_seeds = namespace["get_seeds"].__get__(self.manager)
        self.manager.eval_step = namespace["eval_step"].__get__(self.manager)
        details = {i: {"layout_id": i, "success": i < 2, "score": float(i < 2)} for i in range(4)}
        self.env = SimpleNamespace(task_name="make_toast_random", policy_name="OpenWAM", num_envs=4,
            run_id="fixture", config_name="fixture", eval_seed=1, additional_info="fixture",
            seed_manager=self.manager, success_nums=2, fail_nums=2, unstable_nums=1, eval_num=50,
            total_score=2., abandoned_seeds=set(),
            video_writers={}, eval_result={"details": details, "eval_time": 4, "success_rate": .5, "score": 50.},
            save_dir=str(self.root), camera_manager=SimpleNamespace(cameras=[[1, 2]] * 4),
            capture_manager=SimpleNamespace(tiled_render_products=[1, 2]), _planned_batch_videos=[])
        self.manifest = self.root / "resume.json"
        self.env.resume_manifest_path = lambda: str(self.manifest)
        for i in range(4):
            path = self.root / f"episode_{i:07d}_head_{'success' if i < 2 else 'fail'}.mp4"
            path.write_bytes(b"closed-video-fixture")
            self.env._planned_batch_videos.append(str(path))
        self.save()

    def tearDown(self):
        self.flag.stop()
        self.tmp.cleanup()

    def save(self):
        (self.root / "_result.json").write_text(json.dumps(self.env.eval_result))
        state = {"details": self.env.eval_result["details"], "success_nums": self.env.success_nums,
            "fail_nums": self.env.fail_nums, "unstable_nums": self.env.unstable_nums,
            "completed_layout_ids": [0, 1, 2, 3], "abandoned_layout_ids": []}
        state.update({k: getattr(self.env, k) for k in ("run_id", "task_name", "policy_name", "config_name", "eval_seed", "save_dir", "additional_info", "total_score")})
        self.manifest.write_text(json.dumps(state))

    def planned(self):
        self.assertTrue(iso.prepare_exit(self.env, 0))
        return json.loads(self.manifest.read_text())

    def test_exact_queue_retains_consumed_unstable_and_fresh_shell_generation(self):
        state = self.planned()
        self.manager.seed_list, self.manager.idx, self.manager.ed_idx = list(range(4, 12)), 0, 8
        self.env.unstable_nums = 0
        iso.restore(self.env, state)
        self.assertEqual(self.env.unstable_nums, 1)
        self.assertEqual(self.env._planned_batch_generation, 1)
        self.assertEqual(self.manager.get_seeds(max_count=46), [5, 6, 7, 8])
        self.assertEqual(self.manager.idx, 9)

    def test_old_resume_noop(self):
        iso.restore(self.env, {"unstable_nums": 11})
        self.assertEqual(self.env.unstable_nums, 1)

    def test_fatal_restart_count_survives_planned_shell_restart(self):
        os.environ["ROBODOJO_FATAL_RESTART_COUNT"] = "2"
        state = self.planned()
        os.environ["ROBODOJO_FATAL_RESTART_COUNT"] = "0"
        iso.restore(self.env, state)
        self.assertEqual(os.environ["ROBODOJO_FATAL_RESTART_COUNT"], "2")

    def test_scope_noop(self):
        for attr, value in [("task_name", "other"), ("policy_name", "Other"), ("num_envs", 8)]:
            old = getattr(self.env, attr)
            setattr(self.env, attr, value)
            self.assertFalse(iso.prepare_exit(self.env, 0))
            setattr(self.env, attr, old)
        os.environ[iso.FLAG] = "0"
        self.assertFalse(iso.prepare_exit(self.env, 0))

    def test_complete_exhausted_or_zero_progress_noop(self):
        self.assertFalse(iso.prepare_exit(self.env, 4))
        self.env.eval_num = 4
        self.assertFalse(iso.prepare_exit(self.env, 0))
        self.env.eval_num = 50
        self.manager.idx = 12
        self.assertFalse(iso.prepare_exit(self.env, 0))

    def test_video_missing(self):
        Path(self.env._planned_batch_videos[0]).unlink()
        with self.assertRaises(RuntimeError): iso.prepare_exit(self.env, 0)

    def test_video_empty(self):
        Path(self.env._planned_batch_videos[0]).write_bytes(b"")
        with self.assertRaises(RuntimeError): iso.prepare_exit(self.env, 0)

    def test_missing_episode_camera_receipt(self):
        self.env._planned_batch_videos.pop()
        with self.assertRaises(RuntimeError): iso.prepare_exit(self.env, 0)

    def test_active_batch_refused(self):
        self.manager._current_batch_seeds = [0, 1, 2, 3]
        with self.assertRaises(RuntimeError): iso.prepare_exit(self.env, 0)

    def test_result_manifest_count_and_duplicate_layout_refused(self):
        for mutate in [lambda: (self.root / "_result.json").write_text("{}"),
                       lambda: self.manifest.write_text("{}"),
                       lambda: self.env.eval_result["details"][1].update(layout_id=0)]:
            self.save()
            mutate()
            with self.assertRaises((RuntimeError, KeyError)): iso.prepare_exit(self.env, 0)

    def test_queue_corruption_refused(self):
        state = self.planned()
        for mutate in [lambda d: d[iso.KEY].update(idx=-1),
                       lambda d: d[iso.KEY]["seed_list"].pop(),
                       lambda d: d[iso.KEY].update(layout_map_sha256="wrong")]:
            changed = copy.deepcopy(state)
            mutate(changed)
            with self.assertRaises(RuntimeError): iso.restore(self.env, changed)

    def test_missing_uncompleted_layout_even_rehashed_refused(self):
        state = self.planned()
        state[iso.KEY]["seed_list"].pop()
        state[iso.KEY]["ed_idx"] -= 1
        state[iso.KEY]["queue_sha256"] = iso.queue_digest(state[iso.KEY])
        with self.assertRaises(RuntimeError): iso.restore(self.env, state)

    def test_completed_tail_replay_refused(self):
        state = self.planned()
        state["completed_layout_ids"].append(8)
        with self.assertRaises(RuntimeError): iso.restore(self.env, state)

    def test_atomic_replace_failure_retains_previous_manifest(self):
        original = self.manifest.read_bytes()
        result_before = (self.root / "_result.json").read_bytes()
        with patch.object(iso.os, "replace", side_effect=OSError("fixture disk error")):
            with self.assertRaises(OSError): iso.prepare_exit(self.env, 0)
        self.assertEqual(original, self.manifest.read_bytes())
        self.assertEqual(result_before, (self.root / "_result.json").read_bytes())

    def test_changed_identity_or_budget_refused(self):
        state = self.planned()
        for mutate in [lambda d: d.update(run_id="other"), lambda d: d[iso.KEY].update(eval_num=51)]:
            changed = copy.deepcopy(state)
            mutate(changed)
            with self.assertRaises(RuntimeError): iso.restore(self.env, changed)

    def test_committed_identity_score_and_abandoned_mismatch_refused(self):
        for key, value in [("run_id", "other"), ("save_dir", "/different"), ("total_score", 3.), ("abandoned_layout_ids", [8])]:
            self.save()
            state = json.loads(self.manifest.read_text())
            state[key] = value
            self.manifest.write_text(json.dumps(state))
            with self.assertRaises(RuntimeError): iso.prepare_exit(self.env, 0)

    def test_saved_planned_state_refuses_disabled_scope(self):
        state = self.planned()
        os.environ[iso.FLAG] = "0"
        with self.assertRaises(RuntimeError): iso.restore(self.env, state)

    def shell(self, codes, flag="1", cap="100"):
        script = (HERE / "candidate/scripts/eval_policy.sh").read_text()
        loop = script[script.index('MAX_BASH_RETRIES='):]
        child = self.root / "child.py"
        counter = self.root / "child.count"
        child.write_text("import pathlib,sys\np=pathlib.Path(sys.argv[1]); n=int(p.read_text()) if p.exists() else 0\np.write_text(str(n+1))\nc=" + repr(codes) + "\nsys.exit(c[min(n,len(c)-1)])\n")
        prefix = '\n'.join(["set -euo pipefail", f"sim_cmd=({sys.executable!r} {str(child)!r} {str(counter)!r})",
            "task_name=make_toast_random; policy_name=OpenWAM; num_envs=4; env_cfg_type=fixture; device_id=7; KIT_ARGS=; port=1; protocol=ws; policy_server_url=fixture; additional_info=fixture; seed=1; host=localhost; extra_args=()",
            "export ROBODOJO_RUN_ID=fixture", f"export ROBODOJO_ISOLATE_TOAST_BATCHES={flag}",
            f"export ROBODOJO_MAX_PLANNED_BATCH_RESTARTS={cap}", "sleep() { :; }", ""])
        return subprocess.run(["bash", "-c", prefix + loop], capture_output=True, text=True, timeout=15)

    def test_shell_planned_does_not_consume_fatal_budget(self):
        result = self.shell([98, 99, 0])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fatal_attempts=0", result.stderr)
        self.assertIn("restarting (1/10", result.stderr)

    def test_shell_planned_has_independent_bound(self):
        self.assertEqual(self.shell([98], cap="1").returncode, 97)

    def test_shell_unexpected_planned_code_refused(self):
        self.assertEqual(self.shell([98], flag="0").returncode, 97)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *remaining])
