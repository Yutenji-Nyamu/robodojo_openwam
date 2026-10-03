"""CPU-only acceptance of actual imported-result reconciliation boundaries.

Run on SZ1 with the original RLT Python. Fixtures stay under a temporary
directory; this imports the real producer and the real lane result validators.
No subprocess, CUDA, Ray, SSH, or production result mutation is performed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ARGS = None


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ResultBoundary(unittest.TestCase):
    model = 'openwam'

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='dojo-producer-cpu-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'project'
        self.repo = self.project / 'RoboDojo'
        self.out = self.project / 'runs/deployment-preparation'
        self.import_dir = self.project / 'runs/import'
        self.out.mkdir(parents=True)
        spec = importlib.util.spec_from_file_location('producer_boundary', ARGS.producer)
        self.producer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.producer)
        self.producer.P, self.producer.OUT, self.producer.IMPORT = self.project, self.out, self.import_dir
        self.task, self.seed = 'stack_bowls_random', 0
        self.policy = 'OpenWAM' if self.model == 'openwam' else 'Pi_05'
        self.info = ('ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee'
                     if self.model == 'openwam' else 'ckpt_name=sim,action_type=joint')
        self.run_id = self.producer.RUNS[self.model] + '_s0_' + self.task
        self.base = self.repo / f'eval_result/RoboDojo/{self.task}/{self.policy}/arx_x5/0_{self.info}'
        self.result = self.base / self.run_id / '_result.json'
        self.resume = self.base / ('_resume_' + self.run_id + '.json')
        tasks = [self.task] + [f'fresh_fixture_{i}' for i in range(53)]
        gpu = 4 if self.model == 'openwam' else 6
        write_json(self.out / f'gpu{gpu}-plan.json', {'tasks': tasks, 'budgets': {task: 25 for task in tasks}})
        host = 'sz2' if self.model == 'openwam' else 'sz3'
        write_json(self.import_dir / f'results-{host}-ready.json', {
            'all_sizes_verified': True, 'no_result_values_changed': True,
            'run_id': self.producer.RUNS[self.model], 'policy': self.policy})
        # Each model has its real policy-specific result path. Avoid a Python
        # import cache binding the second model to the first model's validator.
        for name in ('resume_results', 'dojo_sweep', 'process_guard', 'eval_recovery'):
            sys.modules.pop(name, None)
        sys.path.insert(0, str(ARGS.lane_root / self.model))
        self.addCleanup(lambda: sys.path.remove(str(ARGS.lane_root / self.model)))

    def fixture(self, count, manifest=True, absolute=True):
        details = {str(i): {'layout_id': i, 'success': i % 2 == 0,
                            'score': 0.75 if i % 2 == 0 else 0.25} for i in range(count)}
        successes = sum(row['success'] for row in details.values())
        total = math.fsum(row['score'] for row in details.values())
        write_json(self.result, {'eval_time': count, 'success_rate': successes / count,
                                'score': total / count * 100, 'details': details})
        for i in range(count):
            layout = self.repo / f'Assets/Eval_Layout/RoboDojo/arx_x5/0/{self.task}_{i}.json'
            write_json(layout, {})
            for camera in ('head', 'left_wrist', 'right_wrist'):
                (self.result.parent / f'episode_{i}_cam_{camera}_fixture.mp4').write_bytes(b'fixture-video')
        old_repo = Path('/srv/research/projects/robodojo-openwam' +
                        ('' if self.model == 'openwam' else '-sz3')) / 'RoboDojo'
        relative = self.result.parent.relative_to(self.repo)
        row = {'run_id': self.run_id, 'save_dir': str(old_repo / relative) if absolute else str(relative),
               'task_name': self.task, 'policy_name': self.policy, 'config_name': 'arx_x5',
               'eval_seed': 0, 'additional_info': self.info, 'success_nums': successes,
               'fail_nums': count - successes, 'unstable_nums': 2, 'total_score': total,
               'completed_layout_ids': list(range(count)), 'abandoned_layout_ids': [99],
               'details': details, 'restart_count': 17}
        if manifest:
            write_json(self.resume, row)
        self.original_result = self.result.read_bytes()
        return row

    def audit(self):
        self.producer.audit_model(self.model)
        self.assertEqual(self.result.read_bytes(), self.original_result)
        report = json.loads((self.out / f'{self.model}-resume-verified.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['tasks_seeds'], 162)
        return report, next(row for row in report['rows'] if row['run_id'] == self.run_id)

    def rejected(self):
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            self.producer.audit_model(self.model)
        self.assertEqual(self.result.read_bytes(), self.original_result)
        self.assertFalse((self.out / f'{self.model}-resume-verified.json').exists())

    def test_complete_absolute_manifest_rebases_without_episode_changes(self):
        original = self.fixture(25)
        old_bytes = self.resume.read_bytes()
        report, row = self.audit()
        changed = json.loads(self.resume.read_text())
        expected = copy.deepcopy(original)
        expected['save_dir'] = str(self.result.parent.relative_to(self.repo))
        self.assertEqual(changed, expected)
        self.assertEqual(row['action'], 'skip_complete')
        self.assertEqual(report['completed_episodes'], 25)
        saved = self.out / 'resume-rebase-originals' / self.model / 'seed0' / self.task / 'resume-original.json'
        self.assertEqual(saved.read_bytes(), old_bytes)

    def test_partial_absolute_manifest_keeps_full_resume_history(self):
        original = self.fixture(2)
        report, row = self.audit()
        changed = json.loads(self.resume.read_text())
        original['save_dir'] = str(self.result.parent.relative_to(self.repo))
        self.assertEqual(changed, original)
        self.assertEqual(row['action'], 'reuse_manifest')
        self.assertFalse(row['full_budget_complete'])
        self.assertEqual(report['completed_episodes'], 2)

    def test_partial_relative_manifest_remains_byte_identical(self):
        self.fixture(2, absolute=False)
        before = sha(self.resume)
        self.audit()
        self.assertEqual(sha(self.resume), before)

    def test_missing_partial_manifest_recovers_only_persisted_layouts(self):
        self.fixture(2, manifest=False)
        _, row = self.audit()
        rebuilt = json.loads(self.resume.read_text())
        self.assertEqual(row['action'], 'rebuild_missing_manifest')
        self.assertEqual(rebuilt['completed_layout_ids'], [0, 1])
        self.assertEqual(rebuilt['abandoned_layout_ids'], [])
        self.assertEqual(rebuilt['unstable_nums'], 0)
        self.assertEqual(rebuilt['restart_count'], 0)

    def test_complete_manifest_disagreement_is_rejected_before_skip(self):
        manifest = self.fixture(25)
        manifest['total_score'] += 1
        write_json(self.resume, manifest)
        self.rejected()

    def test_old_absolute_path_with_wrong_suffix_is_rejected(self):
        manifest = self.fixture(2)
        manifest['save_dir'] += '-other-run'
        write_json(self.resume, manifest)
        original_resume = self.resume.read_bytes()
        self.rejected()
        self.assertEqual(self.resume.read_bytes(), original_resume)

    def test_completed_and_abandoned_layout_overlap_is_rejected(self):
        manifest = self.fixture(2)
        manifest['abandoned_layout_ids'] = [1, 99]
        write_json(self.resume, manifest)
        self.rejected()

    def test_missing_camera_evidence_is_rejected_without_new_result(self):
        self.fixture(2)
        (self.result.parent / 'episode_1_cam_head_fixture.mp4').unlink()
        self.rejected()


class Pi05Boundary(ResultBoundary):
    model = 'pi05'


def main():
    global ARGS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--lane-root', type=Path, required=True)
    ARGS = parser.parse_args()
    assert sys.platform.startswith('linux'), 'Run project checks on a server'
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (ResultBoundary, Pi05Boundary))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'passed': result.wasSuccessful(), 'tests': result.testsRun,
                      'models': ['openwam', 'pi05'], 'gpu_used': False,
                      'production_files_mutated': False}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
