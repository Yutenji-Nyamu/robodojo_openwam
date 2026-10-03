"""Small CPU-only fail-closed checks for the candidate SZ1 recovery selector.

Run beside rlt_cycle_sz1.py, or pass --helper /path/to/candidate/rlt_cycle_sz1.py.
All server-state and checkpoint inspection dependencies are mocked.
"""
import argparse
import importlib.util
from pathlib import Path
import unittest
from unittest import mock


HELPER = None


class RecoverySelectionTests(unittest.TestCase):
    def setUp(self):
        self.run = HELPER.RECOVERED_RLT_RUN
        self.cp = HELPER.RECOVERED_CHECKPOINT
        self.source = self.run / self.run.name / 'checkpoints' / self.cp.name
        self.donor = '/srv/research/frozen/global_step_575'
        self.cfg = {'runner': {'resume_dir': self.donor}}
        self.manifest = {
            'complete': True,
            'full_coverage': True,
            'source_unchanged': True,
            'indices_pruned': False,
            'original_checkpoint': str(self.source),
        }

    def assert_rejected_before_fallback(self, error, *, manifest=None, read_error=None):
        # A fallback would succeed if invoked; assertRaises therefore detects it.
        fallback = {'path': self.donor, 'step': 575}
        with mock.patch.object(HELPER, 'checkpoint_candidates', return_value=[self.source]), \
             mock.patch.object(HELPER, 'checked_dir', return_value=self.cp), \
             mock.patch.object(HELPER, 'read', return_value=manifest,
                               side_effect=read_error) as read, \
             mock.patch.object(HELPER, 'inspect_checkpoint', return_value=fallback) as inspect:
            with self.assertRaises(error):
                HELPER.select_recovery(self.run, self.cfg, Path('/unused/repo'))
            read.assert_called_once_with(self.cp / 'repair-manifest.json')
            inspect.assert_not_called()

    def test_missing_manifest_refuses_old_checkpoint_fallback(self):
        self.assert_rejected_before_fallback(
            FileNotFoundError, read_error=FileNotFoundError('repair-manifest.json'))

    def test_incomplete_manifest_refuses_old_checkpoint_fallback(self):
        self.manifest['complete'] = False
        self.assert_rejected_before_fallback(AssertionError, manifest=self.manifest)

    def test_foreign_source_checkpoint_refuses_old_checkpoint_fallback(self):
        self.manifest['original_checkpoint'] = str(self.source.parent / 'global_step_600')
        self.assert_rejected_before_fallback(AssertionError, manifest=self.manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper', type=Path,
                        default=Path(__file__).with_name('rlt_cycle_sz1.py'))
    args, remaining = parser.parse_known_args()
    spec = importlib.util.spec_from_file_location('candidate_sz1_rlt', args.helper)
    HELPER = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(HELPER)
    unittest.main(argv=[__file__, *remaining])
