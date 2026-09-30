"""Server CPU regression: rc97 always leaves the task for global fallback."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from eval_recovery import run_client


class TestBatchReturn(unittest.TestCase):
    def test_integrity_refusal_never_retries_or_accepts_full_results(self):
        class Proc:
            returncode = 97

            def poll(self):
                return self.returncode

            def wait(self, timeout):
                return self.returncode

        class Guard:
            def __init__(self):
                self.calls = []

            def cleanup(self, run_id, reason):
                self.calls.append((run_id, reason))
                return 'exact-task-cleanup-receipt'

        class Stop:
            def is_set(self):
                return False

            def wait(self, timeout):
                return False

        class Sweep:
            def __init__(self, root):
                self.repo = root
                self.stop = Stop()
                self.guard = Guard()
                self.attempt = 'test'
                self.cfg = {'sim_env': 'sim'}
                self.plan = {'budgets': {'make_toast_random': 25}, 'groups': [{'port': 1234}]}
                self.launches, self.updates, self.events, self.server_waits = [], [], [], []

            def task_id(self, *args):
                return 'exact-toast-run'

            def result_path(self, *args):
                return self.repo / '_result.json'

            def verify_sources(self):
                pass

            def update(self, *args, **values):
                self.updates.append(values)

            def event(self, name, **values):
                self.events.append((name, values))

            def launch(self, *args):
                self.launches.append(args)
                return Proc()

            def wait_server(self, *args):
                self.server_waits.append(args)

        for complete in (False, True):
            with self.subTest(result_complete=complete), TemporaryDirectory() as directory:
                root = Path(directory)
                sweep = Sweep(root)
                with patch('resume_results.prepare_result', return_value={'action': 'fresh'}), \
                        patch('dojo_sweep.result_check', return_value={'complete': complete, 'eval_time': 25}) as check:
                    with self.assertRaisesRegex(RuntimeError, 'integrity refused.*exit 97'):
                        run_client(sweep, 1, 'make_toast_random', 0, 7, ['client'], root,
                                   Proc(), 'exact-policy-run', ['server'], 'policy')
                self.assertEqual(len(sweep.launches), 1)
                self.assertEqual(sweep.guard.calls, [('exact-toast-run', 'task_attempt_finished_or_stalled')])
                self.assertEqual(sweep.server_waits, [])
                check.assert_not_called()
                self.assertFalse(any(row.get('status') == 'COMPLETE' for row in sweep.updates))
                self.assertEqual(sweep.updates[-1]['status'], 'ERROR')
                self.assertEqual(sweep.updates[-1]['exit_code'], 97)
                self.assertEqual(sweep.events[-1][0], 'task_integrity_refused')
                self.assertFalse(any(name == 'task_retry' for name, _ in sweep.events))


if __name__ == '__main__':
    unittest.main()
