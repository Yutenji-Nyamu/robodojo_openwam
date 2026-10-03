"""Small CPU checks for the deployed SZ1 owner; no real GPU, Ray or RLT action."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def load(path):
    spec = importlib.util.spec_from_file_location('owner_under_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OwnerChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dojo-owner-cpu-')
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.directory = self.project / 'runs/owner-cpu-check'
        self.directory.mkdir(parents=True)
        self.cfg = {}
        for gpu in M.GPUS:
            self.cfg[gpu] = {'lane_gpu': gpu, 'uid': os.getuid(), 'workers_per_gpu': 1,
                'project': str(self.project), 'control_dir': str(self.project / f'runs/check/gpu{gpu}'),
                'run_id': 'old-openwam' if gpu < 6 else 'old-pi05'}
        for path in M.required_files(self.project):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.cfg[int(path.stem[-1])]) if path.name.startswith('gpu') else 'CPU fixture\n')
        self.ready = {'ready': True, 'host': 'admin', 'uid': os.getuid(),
            'checks': [{'name': name, 'passed': True} for name in sorted(M.CHECKS)],
            'files': [{'path': str(path), 'sha256': M.sha(path)} for path in M.required_files(self.project)]}

    def test_valid_ready_freezes_all_four_lanes(self):
        with patch.object(M, 'UID', os.getuid()):
            self.assertEqual(set(M.validate_ready(self.project, self.ready)), {4, 5, 6, 7})

    def test_missing_check_blocks_cutover(self):
        self.ready['checks'] = [row for row in self.ready['checks'] if row['name'] != 'resume_results']
        with patch.object(M, 'UID', os.getuid()), self.assertRaises(RuntimeError):
            M.validate_ready(self.project, self.ready)

    def test_modified_config_blocks_cutover(self):
        M.required_files(self.project)[-1].write_text('{}')
        with patch.object(M, 'UID', os.getuid()), self.assertRaises(RuntimeError):
            M.validate_ready(self.project, self.ready)

    def test_neighbor_card_mapping_blocks_cutover(self):
        path = self.project / 'scripts/lanes/configs/gpu4.json'
        changed = dict(self.cfg[4], lane_gpu=5)
        path.write_text(json.dumps(changed))
        for row in self.ready['files']:
            if row['path'] == str(path): row['sha256'] = M.sha(path)
        with patch.object(M, 'UID', os.getuid()), self.assertRaises(RuntimeError):
            M.validate_ready(self.project, self.ready)

    def test_pid_reuse_is_not_same_owner(self):
        previous = {'pid': 99, 'uid': 1003, 'start_ticks': 123}
        with patch.object(M, 'identity', return_value=dict(previous, start_ticks=124)):
            self.assertFalse(M.same(previous))

    def gpu_mock(self, pid='', action='None', memory=69):
        process = f'<process_info><pid>{pid}</pid></process_info>' if pid else ''
        xml = f'<nvidia_smi_log><gpu><uuid>test-only</uuid><fb_memory_usage><used>{memory} MiB</used></fb_memory_usage><processes>{process}</processes></gpu></nvidia_smi_log>'
        return [xml, action]

    def test_gpu_health_rejects_busy_recovery_and_high_memory(self):
        for values in (self.gpu_mock(pid='901'), self.gpu_mock(action='Reset'), self.gpu_mock(memory=513)):
            with patch.object(M.subprocess, 'check_output', side_effect=values), self.assertRaises(RuntimeError):
                M.gpu_health(4)
        with patch.object(M.subprocess, 'check_output', side_effect=self.gpu_mock()) as command:
            self.assertEqual(M.gpu_health(4)['gpu_recovery_action'], 'None')
            for call in command.call_args_list:
                argv = call.args[0]
                self.assertEqual(argv[argv.index('-i') + 1], '4')

    def test_not_started_release_is_single_card_and_resumes_once(self):
        owner = M.Owner(self.project, self.directory)
        owner.configs = self.cfg
        calls = []
        with patch.object(M, 'gpu_health', return_value={'gpu': 4, 'gpu_recovery_action': 'None'}), \
             patch.object(owner, 'helper_call', side_effect=lambda *a: calls.append(a) or {'dispatched': True}):
            owner.return_lane(4, 'not_started')
        receipt = M.read(self.directory / 'gpu4-release.json')
        self.assertEqual(receipt['gpus'], [4])
        self.assertEqual(receipt['managed_processes'], [])
        self.assertEqual(owner.state['lanes']['4']['state'], 'RLT_VERIFYING')
        self.assertEqual(calls[0][:2], (4, 'resume'))
        self.assertEqual(len(calls), 1)
        self.assertEqual(owner.state['lanes']['5']['state'], 'WAITING')

    def test_failed_second_cutover_returns_first_and_keeps_other_cards(self):
        owner = M.Owner(self.project, self.directory)
        owner.configs = self.cfg
        calls = []
        class Exited:
            pid = 99999999
            def poll(self): return 3
        def helper(gpu, action, *extra):
            calls.append((gpu, action))
            if (gpu, action) == (5, 'stop'): raise RuntimeError('test stop failure')
            return {'prepared': True}
        def start(gpu):
            owner.processes[gpu] = Exited()
            owner.state['lanes'][str(gpu)]['state'] = 'DOJO_RUNNING'
        def give_back(gpu, terminal):
            calls.append((gpu, 'return'))
            owner.state['lanes'][str(gpu)]['state'] = 'RLT_RESTORED'
        with patch.object(owner, 'wait_ready'), patch.object(owner, 'preflight_lanes'), patch.object(owner, 'helper_call', side_effect=helper), \
             patch.object(owner, 'start_lane', side_effect=start), patch.object(owner, 'return_lane', side_effect=give_back), \
             patch.object(owner, 'verify_returns'), patch.object(M.signal, 'signal'):
            self.assertEqual(owner.run(1), 2)
        self.assertEqual(calls[:4], [(4, 'prepare'), (5, 'prepare'), (6, 'prepare'), (7, 'prepare')])
        self.assertIn((4, 'return'), calls)
        self.assertNotIn((6, 'stop'), calls)
        self.assertNotIn((7, 'stop'), calls)
        self.assertEqual(owner.state['stage'], 'CUTOVER_ABORTED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    M = load(args.owner)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OwnerChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'passed': result.wasSuccessful(), 'tests': result.testsRun,
               'owner_path': str(args.owner), 'owner_sha256': M.sha(args.owner),
               'gpu_used': False, 'ray_used': False, 'rlt_mutated': False}
    if args.receipt: M.atomic(args.receipt, receipt)
    raise SystemExit(0 if result.wasSuccessful() else 1)
