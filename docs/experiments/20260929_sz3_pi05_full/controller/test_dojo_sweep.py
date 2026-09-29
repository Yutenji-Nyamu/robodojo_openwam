"""CPU-only checks; run with the existing server Python, never starts Isaac."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

from dojo_sweep import result_check, Sweep, sha
from process_guard import ProcessGuard, atomic_json


class ResultChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / "_result.json"
        self.value = {"eval_time": 2, "success_rate": 0.5, "score": 50.0, "details": {
            "0": {"layout_id": 3, "success": True, "score": 1.0},
            "1": {"layout_id": 7, "success": False, "score": 0.0}}}
        for episode in (0, 1):
            for camera in ("head", "left_wrist", "right_wrist"):
                (self.folder / f"episode_{episode:07d}_cam_{camera}_success.mp4").write_bytes(b"coverage-fixture")
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.path.write_text(json.dumps(self.value))

    def test_full_budget_counts_failed_episode_and_three_cameras(self):
        self.assertTrue(result_check(self.path, 2)["complete"])
        self.assertFalse(result_check(self.path, 25)["complete"])

    def test_eval_time_alone_does_not_prove_complete(self):
        self.value["eval_time"] = 25
        self.write()
        self.assertEqual(result_check(self.path, 25)["reason"], "native_budget_incomplete")

    def test_duplicate_layout_is_rejected(self):
        self.value["details"]["1"]["layout_id"] = 3
        self.write()
        self.assertFalse(result_check(self.path, 2)["complete"])

    def test_missing_camera_is_not_complete(self):
        next(self.folder.glob("*right_wrist*")).unlink()
        self.assertEqual(result_check(self.path, 2)["reason"], "missing_camera_videos")

    def test_malformed_score_is_rejected(self):
        self.value["details"]["0"]["score"] = float("nan")
        self.write()
        self.assertFalse(result_check(self.path, 2)["complete"])

class CheckpointChecks(unittest.TestCase):
    def fixture(self, root):
        import threading
        checkpoint = root/'RoboDojo-sim-arx_x5-joint-1/59999'
        (checkpoint/'.download-pi05').mkdir(parents=True)
        (checkpoint/'params.bin').write_bytes(b'weights')
        manifest = checkpoint/'.download-pi05/manifest.json'
        manifest.write_text('{}')
        rows = [{'path':'params.bin','size':7,'sha256':sha(checkpoint/'params.bin')}]
        ready = {'status':'ready','revision':'fixed-official','files':[{**r,'verified':True} for r in rows]}
        (checkpoint/'pi05-inference-ready.json').write_text(json.dumps(ready))
        sweep = object.__new__(Sweep)
        sweep.cfg = {'checkpoint':str(root),'project':str(root),'checkpoint_revision':'fixed-official'}
        sweep.plan = {'checkpoint_manifest_sha256':{'1':sha(manifest)},'checkpoint_files':{'1':rows}}
        sweep.stop = threading.Event()
        sweep.event = lambda *args,**kwargs:None
        return sweep,checkpoint,ready

    def test_later_seed_starts_only_with_matching_verified_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            sweep,checkpoint,ready = self.fixture(Path(directory))
            sweep.wait_checkpoint(1)
            ready['files'][0]['sha256'] = 'another-seed'
            (checkpoint/'pi05-inference-ready.json').write_text(json.dumps(ready))
            with self.assertRaises(RuntimeError):sweep.wait_checkpoint(1)

    def test_removed_weight_cannot_pass_ready_marker_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            sweep,checkpoint,ready = self.fixture(Path(directory))
            (checkpoint/'params.bin').unlink()
            with self.assertRaises(RuntimeError):sweep.wait_checkpoint(1)


@unittest.skipUnless(sys.platform == "linux", "Linux /proc identity test")
class GuardChecks(unittest.TestCase):
    def test_reused_unrelated_pid_is_not_owned_by_old_start_tick(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = ProcessGuard('guard-reuse-test', os.getuid(), Path(directory)/'receipts')
            parent = os.getppid()
            start = int((Path('/proc')/str(parent)/'stat').read_text().rsplit(')',1)[1].split()[19])
            guard.anchor['start_ticks'] = 0
            guard.remember(parent, start-1)
            with self.denied_environment(parent):
                self.assertIsNone(guard.identity(parent))

    def test_unrelated_unreadable_same_uid_process_does_not_abort_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = ProcessGuard('guard-unrelated-test', os.getuid(), Path(directory)/'receipts')
            guard.anchor['start_ticks'] = 0
            parent = os.getppid()
            with self.denied_environment(parent):
                self.assertIsNone(guard.identity(parent))

    def denied_environment(self, pid):
        original = Path.read_bytes
        target = Path('/proc') / str(pid) / 'environ'
        def read_bytes(path):
            if path == target:
                raise PermissionError('fixture: same-UID environment is unreadable')
            return original(path)
        return patch.object(Path, 'read_bytes', read_bytes)

    def test_older_unowned_unreadable_process_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = ProcessGuard('guard-old-test', os.getuid(), Path(directory)/'receipts')
            # The synthetic boundary makes this PID strictly older than sweep.
            guard.anchor['start_ticks'] += 1
            with self.denied_environment(os.getpid()):
                self.assertIsNone(guard.identity(os.getpid()))

    def test_same_age_or_newer_unreadable_process_still_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = ProcessGuard('guard-new-test', os.getuid(), Path(directory)/'receipts')
            with self.denied_environment(os.getpid()):
                with self.assertRaises(PermissionError):
                    guard.identity(os.getpid())
                guard.anchor['start_ticks'] -= 1
                with self.assertRaises(PermissionError):
                    guard.identity(os.getpid())

    def test_persistent_anchor_and_known_pid_prevent_later_exemption(self):
        with tempfile.TemporaryDirectory() as directory:
            receipts = Path(directory)/'receipts'
            guard = ProcessGuard('guard-known-test', os.getuid(), receipts)
            guard.remember(os.getpid(), guard.anchor['start_ticks'])
            guard.anchor['start_ticks'] += 1
            atomic_json(receipts/'ownership-anchor.json', guard.anchor)
            resumed = ProcessGuard('guard-known-test', os.getuid(), receipts)
            self.assertEqual(resumed.anchor, guard.anchor)
            with self.denied_environment(os.getpid()):
                with self.assertRaises(PermissionError):
                    resumed.identity(os.getpid())

    def test_exact_identity_and_detached_child_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sweep = "dojo-controller-test-" + uuid.uuid4().hex
            run = sweep + "_one"
            guard = ProcessGuard(sweep, os.getuid(), folder / "receipts")
            own_env = dict(os.environ, DOJO_SWEEP_ID=sweep, ROBODOJO_RUN_ID=run, DOJO_ROLE="test")
            unrelated_env = dict(os.environ)
            for key in ("DOJO_SWEEP_ID", "ROBODOJO_RUN_ID", "DOJO_ROLE"):
                unrelated_env.pop(key, None)
            unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"], env=unrelated_env)
            child_pid_file = folder / "detached.pid"
            code = (
                "import pathlib,subprocess,sys;"
                "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True);"
                f"pathlib.Path({str(child_pid_file)!r}).write_text(str(p.pid))"
            )
            try:
                subprocess.run([sys.executable, "-c", code], env=own_env, check=True)
                child_pid = int(child_pid_file.read_text())
                target = guard.identity(child_pid)
                self.assertIsNotNone(target)
                stale = dict(target, start_ticks=target["start_ticks"] + 1)
                self.assertIsNone(guard.send(stale, signal.SIGTERM))
                self.assertIsNotNone(guard.identity(child_pid))
                receipt = json.loads(Path(guard.cleanup(run, "unit-test", grace=2)).read_text())
                self.assertEqual(receipt["remaining"], [])
                self.assertTrue(any(row["pid"] == child_pid for row in receipt["actions"]))
                self.assertIsNone(unrelated.poll(), "untagged same-UID process must remain untouched")
            finally:
                try:
                    guard.cleanup(run, "unit-test-finally", grace=1)
                finally:
                    unrelated.terminate()
                    unrelated.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
