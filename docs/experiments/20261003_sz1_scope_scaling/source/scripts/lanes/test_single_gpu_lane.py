"""Run only on target Linux with PYTHONPATH pointing to openwam/ or pi05/.

CPU checks use owned temporary files and two small owned CPU subprocesses.
No simulator, model, GPU allocation, Ray stop, or RLT operation is performed.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import Mock, patch

import dojo_sweep
import eval_recovery


class Proc:
    def __init__(self, rc=0, log=None):
        self.returncode = rc
        self.pid = os.getpid()
        self.dojo_log_path = log
    def poll(self): return self.returncode
    def wait(self, timeout=None): return self.returncode


class SingleGpuLane(unittest.TestCase):
    def config(self, root, gpu=None):
        gpu = min(dojo_sweep.GPUS) if gpu is None else gpu
        return {'repo': str(root / 'repo'), 'project': str(root), 'run_id': 'old_formal_run',
                'uid': os.getuid(), 'lane_gpu': gpu,
                'control_dir': str(root / 'runs' / 'old_formal_run' / 'lanes' / f'gpu{gpu}'),
                'ports': list(range(63080, 63088)), 'sim_env': str(root / 'sim'),
                'project_env': str(root / 'project.env'), 'conda_profile': str(root / 'conda.sh'),
                'checkpoint': str(root / 'checkpoint'), 'compat_script': str(root / 'compat.sh')}

    def plan(self, cfg):
        tasks = [f'task{i}' for i in range(54)]
        budgets = {name: 25 if i < 24 else 50 for i, name in enumerate(tasks)}
        return {'config': cfg, 'tasks': tasks, 'budgets': budgets, 'episode_total': 6300,
                'max_inproc_restarts': 3, 'source_sha256': {},
                'groups': [{'worker': i, 'gpu': gpu, 'port': cfg['ports'][i],
                            'tasks': [{'task': task} for task in tasks[i::8]]}
                           for i, gpu in enumerate(dojo_sweep.GPUS)]}

    def test_mapping_retains_eight_groups_and_two_physical_gpus(self):
        first = min(dojo_sweep.GPUS)
        self.assertEqual(dojo_sweep.GPUS, [first, first, first+1, first+1,
                                         first, first, first+1, first+1])

    def test_control_path_and_result_identity_are_separate(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            sweeps = [dojo_sweep.Sweep(self.config(root, gpu), None)
                      for gpu in sorted(set(dojo_sweep.GPUS))]
            self.assertNotEqual(sweeps[0].run, sweeps[1].run)
            self.assertNotEqual(sweeps[0].ownership_id, sweeps[1].ownership_id)
            for sweep in sweeps:
                self.assertEqual(sweep.task_id(2, 'task'), 'old_formal_run_s2_task')
                self.assertEqual(set(sweep.gpu_slots), {sweep.gpu})

    def test_guard_rejects_neighbor_lane_owned_cpu_process(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            sweeps = [dojo_sweep.Sweep(self.config(root, gpu), None)
                      for gpu in sorted(set(dojo_sweep.GPUS))]
            children = []
            try:
                for sweep in sweeps:
                    env = dict(os.environ, DOJO_SWEEP_ID=sweep.ownership_id,
                               ROBODOJO_RUN_ID='old_formal_run_s0_task', DOJO_ROLE='cpu_test')
                    children.append(subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                                                     env=env, stdout=subprocess.DEVNULL,
                                                     stderr=subprocess.DEVNULL))
                time.sleep(.1)
                for index, sweep in enumerate(sweeps):
                    self.assertIsNotNone(sweep.guard.identity(children[index].pid))
                    self.assertIsNone(sweep.guard.identity(children[1-index].pid))
            finally:
                for child in children:
                    child.terminate()
                    child.wait(timeout=5)

    def test_only_own_four_groups_run_once_per_seed(self):
        with TemporaryDirectory() as folder:
            cfg = self.config(Path(folder))
            sweep = dojo_sweep.Sweep(cfg, self.plan(cfg))
            calls = []
            sweep.event = lambda *args, **kwargs: None
            sweep.wait_checkpoint = lambda seed: None
            sweep.worker_body = lambda seed, group: calls.append((seed, group['worker'], group['gpu']))
            sweep.gpu_lane(sweep.gpu)
            expected = {(seed, group['worker'], sweep.gpu) for seed in (0, 1, 2)
                        for group in sweep.plan['groups'] if group['gpu'] == sweep.gpu}
            self.assertEqual(len(calls), 12)
            self.assertEqual(set(calls), expected)
            with self.assertRaisesRegex(RuntimeError, 'four distinct groups'):
                sweep.gpu_lane(max(dojo_sweep.GPUS))

    def test_native_restart_limit_is_read_and_unknown_values_fail_closed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'src/eval_client/main.py'
            source.parent.mkdir(parents=True)
            source.write_text('MAX_INPROC_RESTARTS = 3\n')
            self.assertEqual(dojo_sweep.inproc_restart_cap(root), 3)
            for content in ('MAX_INPROC_RESTARTS = int("3")\n', 'MAX_INPROC_RESTARTS = True\n', ''):
                source.write_text(content)
                with self.assertRaises(RuntimeError): dojo_sweep.inproc_restart_cap(root)

    def test_gpu_snapshot_contains_only_target_card(self):
        rows = '4, id4, 100, 0\n5, id5, 70000, 99\n6, id6, 10, 0\n7, id7, 65000, 90\n'
        with patch.object(dojo_sweep.subprocess, 'check_output', return_value=rows):
            result = dojo_sweep.gpu_snapshot(min(dojo_sweep.GPUS))
        self.assertEqual([row['gpu'] for row in result], [min(dojo_sweep.GPUS)])

    def test_launch_exports_lane_ownership_and_no_fatal_restart(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.config(root)
            sweep = dojo_sweep.Sweep(cfg, self.plan(cfg))
            sweep.guard = Mock()
            sweep.guard.identity.return_value = None
            with patch.object(dojo_sweep.subprocess, 'Popen', return_value=Proc()) as popen:
                process = sweep.launch(['bash', 'scripts/robodojo.sh'], 'old_formal_run_s0_task',
                                       'client', sweep.gpu, cfg['sim_env'], root / 'command')
                with self.assertRaisesRegex(RuntimeError, 'outside this GPU lane'):
                    sweep.launch([], 'id', 'client', sweep.gpu+1, cfg['sim_env'], root / 'rejected')
            self.assertEqual(popen.call_count, 1)
            text = (root / 'command' / f'command-{sweep.attempt}.sh').read_text()
            self.assertIn('export ROBODOJO_MAX_BASH_RETRIES=1\n', text)
            self.assertIn('export ROBODOJO_FATAL_RESTART_COUNT=3\n', text)
            self.assertIn('export ROBODOJO_RUN_ID=old_formal_run_s0_task\n', text)
            self.assertIn(sweep.ownership_id, text)
            self.assertEqual(process.dojo_log_path.parent, root / 'command')
            if dojo_sweep.POLICY == 'OpenWAM':
                self.assertIn('export ROBODOJO_ISOLATE_TOAST_BATCHES=1\n', text)

    def test_lane_complete_does_not_claim_full_6300_or_check_neighbor_gpu(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = self.config(root)
            sweep = dojo_sweep.Sweep(cfg, self.plan(cfg))
            sweep.guard = Mock()
            sweep.guard.scan.return_value = []
            sweep.guard.cleanup.return_value = {'cpu_mock': True}
            sweep.telemetry = lambda: None
            called = []
            sweep.gpu_lane = lambda gpu: called.append(gpu)
            sweep.official_summary = lambda checks: None
            old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
            try:
                with patch.object(dojo_sweep, 'gpu_snapshot', return_value=[{'gpu': sweep.gpu, 'memory_mib': 0}]) as query, \
                     patch.object(dojo_sweep.socket, 'socket'), \
                     patch.object(dojo_sweep, 'result_check', side_effect=lambda path, expected: {'complete': True, 'eval_time': expected}):
                    code = sweep.run_all()
            finally:
                for sig, handler in old_handlers.items(): signal.signal(sig, handler)
            self.assertEqual(code, 0)
            self.assertEqual(called, [sweep.gpu])
            self.assertTrue(all(call.args == (sweep.gpu,) for call in query.call_args_list))
            self.assertEqual(sweep.plan['episode_total'], 6300)
            self.assertEqual(len(sweep.plan['tasks']), 54)
            self.assertEqual(len(json.loads((sweep.run / 'result-audit.json').read_text())), len(sweep.lane_tasks)*3)
            final = json.loads((sweep.run / 'final.json').read_text())
            self.assertEqual(final['completion_scope'], 'single_gpu_lane')
            self.assertEqual(final['full_benchmark_episodes'], 6300)

    def client_case(self, root, text='', rc=0, server_text=None):
        sweep = Mock()
        sweep.stop = threading.Event()
        sweep.repo = root
        sweep.attempt = 'test'
        sweep.cfg = {'sim_env': 'sim'}
        sweep.plan = {'budgets': {'task': 25}, 'groups': [{'port': 63080}]}
        sweep.task_id.return_value = 'old_formal_run_s0_task'
        sweep.result_path.return_value = root / '_result.json'
        server_log = root / 'server.log'
        server_log.write_text(server_text or '')
        def launch(command, run_id, role, gpu, env, directory):
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'stdout-test.log').write_text(text)
            return Proc(rc)
        sweep.launch.side_effect = launch
        return sweep, Proc(None, server_log)

    def test_fast_fatal_tail_even_after_full_result_never_retries(self):
        cases = [('ordinary\n'*150000+'ERROR_DEVICE_LOST', 0, None),
                 ('', 99, None), ('', 134, None), ('', 139, None),
                 ('', 0, 'RuntimeError: CUDA error: an illegal memory access was encountered')]
        for text, rc, server_text in cases:
            with self.subTest(rc=rc, policy_fatal=bool(server_text)), TemporaryDirectory() as folder:
                root = Path(folder)
                sweep, server = self.client_case(root, text, rc, server_text)
                with patch('resume_results.prepare_result', return_value={'action': 'fresh'}), \
                     patch('dojo_sweep.result_check', return_value={'complete': True}) as check:
                    with self.assertRaisesRegex(RuntimeError, 'no same-card retry'):
                        eval_recovery.run_client(sweep, 0, 'task', 0, min(dojo_sweep.GPUS), [],
                                                 root, server, 'server_id', [], 'policy')
                self.assertEqual(sweep.launch.call_count, 1)
                check.assert_not_called()

    def test_planned_batch_message_and_clean_complete_are_accepted(self):
        progress = eval_recovery.Progress(0)
        progress.observe('[eval_policy] planned batch restart count=1; fatal_attempts=0\n', 1, 1)
        self.assertFalse(progress.fatal)
        with TemporaryDirectory() as folder:
            root = Path(folder)
            sweep, server = self.client_case(root, 'env0 step: 200 / 200\n', 0)
            with patch('resume_results.prepare_result', return_value={'action': 'fresh'}), \
                 patch('dojo_sweep.result_check', return_value={'complete': True, 'eval_time': 25}):
                result = eval_recovery.run_client(sweep, 0, 'task', 0, min(dojo_sweep.GPUS), [],
                                                 root, server, 'server_id', [], 'policy')
            self.assertIs(result, server)
            self.assertEqual(sweep.launch.call_count, 1)


if __name__ == '__main__':
    if sys.platform != 'linux': raise SystemExit('Run project checks only on target Linux server')
    unittest.main()
