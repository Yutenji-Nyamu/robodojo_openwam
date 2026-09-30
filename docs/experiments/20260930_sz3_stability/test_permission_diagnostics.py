"""Focused server-only CPU checks. No server connections or GPU processes."""
import errno
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

from process_guard import ProcessGuard, error_context


class TestPermissionDiagnostics(unittest.TestCase):
    def bare_guard(self, directory):
        guard = ProcessGuard.__new__(ProcessGuard)
        guard.receipts = Path(directory)
        guard.sweep_id = 'test-permission-diagnostics'
        guard.uid = 20001
        guard.boot_id = 'test-boot'
        guard.known_pids = set()
        guard.known_lock = threading.Lock()
        guard.termination_pending = {}
        return guard

    def test_initial_scan_failure_has_receipt_and_does_not_signal(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch.object(guard, 'scan', side_effect=denied), patch.object(guard, 'send') as send:
                with self.assertRaises(PermissionError):
                    guard.cleanup('exact-run-id', 'before_same_task_retry')
                send.assert_not_called()
            receipts = list(Path(directory).glob('*.json'))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(receipt['state'], 'ERROR')
            self.assertEqual(receipt['run_id'], 'exact-run-id')
            self.assertEqual(receipt['initial_targets'], [])
            self.assertFalse(receipt['initial_scan_complete'])
            self.assertEqual(receipt['actions'], [])
            self.assertEqual(receipt['error']['filename'], '/proc/123/environ')
            self.assertIn('PermissionError', receipt['error']['traceback'])

    def test_transient_denial_rechecks_identity_without_claiming_ownership(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch.object(guard, '_identity_once', side_effect=[denied, None]) as identify, \
                    patch('process_guard.time.sleep'), patch.object(guard, 'record_permission_error') as record:
                self.assertIsNone(guard.identity(123))
                self.assertEqual(identify.call_count, 2)
                record.assert_not_called()

    def test_unknown_persistent_denial_remains_failure(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch.object(guard, '_identity_once', side_effect=denied) as identify, \
                    patch('process_guard.time.sleep'), patch.object(guard, 'record_permission_error') as record:
                with self.assertRaises(PermissionError) as raised:
                    guard.identity(123)
                self.assertIs(raised.exception, denied)
                self.assertEqual(identify.call_count, 10)
                record.assert_called_once_with(123, denied)

    def test_error_context_retains_path_and_stage(self):
        denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
        denied.process_guard_pid = 123
        denied.process_guard_operation = 'proc_environ'
        row = error_context(denied)
        self.assertEqual(row['pid'], 123)
        self.assertEqual(row['operation'], 'proc_environ')
        self.assertEqual(row['filename'], '/proc/123/environ')
        self.assertIn('/proc/123/environ', row['message'])

    def test_signalled_exit_gets_fresh_reads_not_stale_identity(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch.object(guard, '_identity_once', side_effect=[denied] * 12 + [None]) as identify, \
                    patch('process_guard.time.sleep'), patch.object(guard, 'exit_read_retry_allowed', return_value=True), \
                    patch.object(guard, 'record_permission_error') as record, patch.object(guard, 'send') as send:
                self.assertIsNone(guard.identity(123))
                self.assertEqual(identify.call_count, 13)
                record.assert_not_called()
                send.assert_not_called()

    def test_signalled_exit_still_fails_at_deadline(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch.object(guard, '_identity_once', side_effect=denied) as identify, \
                    patch('process_guard.time.sleep'), patch.object(guard, 'exit_read_retry_allowed', side_effect=[True, False]), \
                    patch.object(guard, 'record_permission_error') as record:
                with self.assertRaises(PermissionError):
                    guard.identity(123)
                self.assertEqual(identify.call_count, 11)
                record.assert_called_once_with(123, denied)

    def test_exit_wait_requires_exact_signalled_pid_start_and_proc_path(self):
        with TemporaryDirectory() as directory:
            guard = self.bare_guard(directory)
            guard.termination_pending[(123, 42)] = 108
            fields = ['S'] + ['0'] * 18 + ['42']
            stat = '123 (test) ' + ' '.join(fields)
            denied = PermissionError(errno.EACCES, 'Permission denied', '/proc/123/environ')
            with patch('process_guard.time.monotonic', return_value=103), patch.object(Path, 'read_text', return_value=stat):
                self.assertTrue(guard.exit_read_retry_allowed(123, denied))
                self.assertFalse(guard.exit_read_retry_allowed(124, denied))
                disk_error = PermissionError(errno.EACCES, 'Permission denied', '/tmp/ownership-known.jsonl')
                self.assertFalse(guard.exit_read_retry_allowed(123, disk_error))
            with patch('process_guard.time.monotonic', return_value=108), patch.object(Path, 'read_text', return_value=stat):
                self.assertFalse(guard.exit_read_retry_allowed(123, denied))
            reused = '123 (test) ' + ' '.join(fields[:-1] + ['43'])
            with patch('process_guard.time.monotonic', return_value=103), patch.object(Path, 'read_text', return_value=reused):
                self.assertFalse(guard.exit_read_retry_allowed(123, denied))


if __name__ == '__main__':
    unittest.main()
