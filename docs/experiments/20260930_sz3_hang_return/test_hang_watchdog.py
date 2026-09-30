"""CPU-only targeted regression tests, run on the servers."""
import json, os, signal, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from hang_watchdog import Progress, identity, signal_bound, task_rows, bound_run
from bounded_resume_name import resumed_name

class ProgressTests(unittest.TestCase):
    def test_repeated_warning_is_not_progress(self):
        p=Progress(0);p.observe('env0 step: 86 / 1100\n',28,1)
        for t in range(2,1802):p.observe('sh: 1: zenity: not found\n',28,t)
        self.assertEqual(p.failure(1801),'no_action_or_episode_progress')
    def test_actual_steps_allow_unlimited_task_duration(self):
        p=Progress(0)
        for t in range(1,10000):
            p.observe(f'env0 step: {t%1100} / 1100\n',0,t*20)
            self.assertIsNone(p.failure(t*20))
    def test_fatal_gets_shorter_stall_but_can_recover(self):
        p=Progress(0);p.observe('GPU crash dump is successfully written\n',0,20)
        self.assertIsNone(p.failure(299));self.assertEqual(p.failure(300),'gpu_fatal_and_no_progress')
        p.observe('env0 step: 1 / 500\n',0,301);self.assertIsNone(p.failure(400))
    def test_completed_episode_is_progress_without_log_steps(self):
        p=Progress(0);p.observe('',4,900);self.assertIsNone(p.failure(2000))
    def test_split_carriage_return_steps_and_warning_mtime(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/'log';log.write_text('env0 step: 8')
            p=Progress(0);p.poll(log,0,1)
            with log.open('a') as f:f.write('6 / 1100\r')
            p.poll(log,0,2);self.assertEqual(p.steps['0'],(86,1100))
            with log.open('a') as f:f.write('sh: 1: zenity: not found\n')
            p.poll(log,0,1802);self.assertEqual(p.failure(1802),'no_action_or_episode_progress')
    def test_pid_reuse_fails_before_signal(self):
        with self.assertRaises(AssertionError):identity(os.getpid(),identity(os.getpid())['start']+1)
    def test_exact_child_term_does_not_touch_other_child(self):
        children=[subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']) for _ in range(2)]
        try:
            time.sleep(.05);bound={'parent':identity(os.getpid()),'controller':identity(children[0].pid)}
            with patch('hang_watchdog.bound_run',return_value=bound):signal_bound(Path('/unused'),bound,signal.SIGTERM)
            children[0].wait(timeout=3);self.assertIsNone(children[1].poll())
        finally:
            for child in children:
                if child.poll() is None:child.terminate()
                child.wait(timeout=3)
    def test_parent_change_refuses_signal(self):
        bound={'parent':{'pid':1},'controller':{'pid':2}}
        with patch('hang_watchdog.bound_run',return_value={'parent':{'pid':3},'controller':{'pid':2}}),patch('os.pidfd_open') as op:
            with self.assertRaises(AssertionError):signal_bound(Path('/unused'),bound,signal.SIGTERM)
            op.assert_not_called()
    def test_rlt_phase_is_inactive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pipeline-current.json').write_text(json.dumps({'phase':'RLT_RESTORE_DISPATCHED'}))
            self.assertIsNone(bound_run(root))
    def test_completed_workers_and_old_attempts_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'seed0').mkdir()
            rows={'done':{'status':'COMPLETE'},'old':{'status':'RUNNING','seed':0,'worker':1,'started_at':1}}
            (root/'seed0/summary.json').write_text(json.dumps({'results':rows}))
            self.assertEqual(task_rows(root,{'token':'123','started_at':2}),[])
    def test_repeated_recovery_names_stay_bounded_and_unique(self):
        old='pi05-rlt-move_pillbottle_pad-clean-n8full-3000-20260929-sz3-v1';seen=set()
        for n in range(100):
            old=resumed_name(old,'rlt-cycle-sz3-pi05-gpu7-v1')
            self.assertLessEqual(len(old.encode()),180);self.assertNotIn(old,seen);seen.add(old)
    def test_unicode_name_bound(self):
        self.assertLessEqual(len(resumed_name('训练'*200,'周期'*100).encode()),180)

if __name__=='__main__':unittest.main(verbosity=2)
