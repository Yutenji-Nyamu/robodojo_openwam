"""CPU-only checks; run with the existing server Python, never starts Isaac."""
import json
import os
import pwd
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import uuid

from dojo_sweep import result_check, verify_ports_available
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


@unittest.skipUnless(sys.platform == "linux", "Linux /proc identity test")
class GuardChecks(unittest.TestCase):
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

    def test_owned_process_exiting_between_stat_and_environ_is_dead(self):
        with tempfile.TemporaryDirectory() as directory:
            guard=ProcessGuard('guard-exit-race',os.getuid(),Path(directory)/'receipts')
            guard.remember(os.getpid(),guard.anchor['start_ticks'])
            target=Path('/proc')/str(os.getpid())/'stat'
            original=Path.read_text;calls=[0]
            def text(path,*args,**kwargs):
                value=original(path,*args,**kwargs)
                if path==target:
                    calls[0]+=1
                    if calls[0]>1:
                        head,tail=value.rsplit(')',1);fields=tail.split();fields[0]='Z'
                        return head+') '+' '.join(fields)
                return value
            with self.denied_environment(os.getpid()),patch.object(Path,'read_text',text):
                self.assertIsNone(guard.identity(os.getpid()))

    def test_exec_transition_retries_a_fresh_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            guard=ProcessGuard('guard-exec-test',os.getuid(),Path(directory)/'receipts')
            result={'pid':123,'verified':'new read'}
            with patch.object(guard,'_identity_once',side_effect=[PermissionError('exec'),result]) as read:
                self.assertEqual(guard.identity(123),result)
                self.assertEqual(read.call_count,2)

    def test_live_listener_is_still_rejected(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            server.bind(('127.0.0.1',0));server.listen();port=server.getsockname()[1]
            with self.assertRaises(OSError):verify_ports_available([port])

    def test_reusable_time_wait_does_not_block_restart(self):
        with socket.socket() as server,socket.socket() as client:
            server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            server.bind(('127.0.0.1',0));server.listen();port=server.getsockname()[1]
            client.connect(('127.0.0.1',port));conn,_=server.accept()
            conn.shutdown(socket.SHUT_WR);conn.close();client.recv(1)
        verify_ports_available([port])

    def test_new_root_supervised_ssh_is_excluded_but_owned_or_fake_is_not(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = ProcessGuard('guard-ssh-test', os.getuid(), Path(directory)/'receipts')
            pid, start, parent = 987654321, guard.anchor['start_ticks'] + 1, 987654320
            child_path, parent_path = Path('/proc')/str(pid), Path('/proc')/str(parent)
            username = pwd.getpwuid(os.getuid()).pw_name
            parent_uid = [0]
            def stat(path):
                return SimpleNamespace(st_uid=parent_uid[0] if path == parent_path else os.getuid())
            def text(path):
                if path.name == 'comm': return 'sshd\n'
                if path == child_path/'stat':
                    fields = ['S', str(parent)] + ['0'] * 17 + [str(start)]
                    return f'{pid} (sshd) ' + ' '.join(fields)
                raise AssertionError(path)
            def data(path):
                if path.name == 'environ': raise PermissionError('protected login')
                if path == child_path/'cmdline': return f'sshd: {username}@notty'.encode()+b'\0'
                if path == parent_path/'cmdline': return f'sshd: {username} [priv]'.encode()+b'\0'
                raise AssertionError(path)
            with patch.object(Path,'stat',stat), patch.object(Path,'read_text',text), patch.object(Path,'read_bytes',data):
                self.assertIsNone(guard.identity(pid))
                parent_uid[0] = os.getuid()
                with self.assertRaises(PermissionError): guard.identity(pid)
                parent_uid[0] = 0
                guard.known_pids.add((pid,start))
                with self.assertRaises(PermissionError): guard.identity(pid)
                guard.known_pids = {(pid,start-1)}
                self.assertIsNone(guard.identity(pid), 'reused PID is a different process')

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
