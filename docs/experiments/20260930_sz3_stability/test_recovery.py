"""Focused CPU tests; executed only on the target Linux servers."""
import json,threading,time,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import dojo_sweep
from eval_recovery import Progress,run_client

class TestRecovery(unittest.TestCase):
    def test_warning_writes_are_not_progress(self):
        p=Progress(0);p.observe('sh: 1: zenity: not found\n',None,1799)
        self.assertEqual(p.failure(1800),'no_action_or_episode_progress_1800s')
    def test_oom_and_illegal_address_bounded(self):
        for error in ('cudaErrorMemoryAllocation','PhysX Internal CUDA error','ERROR_DEVICE_LOST'):
            p=Progress(0);p.observe(error,None,1)
            self.assertIsNone(p.failure(119));self.assertEqual(p.failure(120),'fatal_without_progress_120s')
    def test_real_steps_and_episode_progress(self):
        p=Progress(0);p.observe('env0 step: \x1b[92m1 / 100\x1b[0m',3,100)
        p.observe('env0 step: 1 / 100',3,200);self.assertEqual(p.last,100)
        p.observe('',4,300);self.assertEqual(p.last,300)
    def test_retries_have_fresh_progress_state(self):
        p=Progress(1000);p.observe('',12,1010);self.assertIsNone(p.failure(1300))
    def test_one_worker_per_gpu(self):
        s=dojo_sweep.Sweep.__new__(dojo_sweep.Sweep);s.stop=threading.Event()
        s.gpu_slots={4:threading.Lock(),5:threading.Lock()}
        active={4:0,5:0};peak={4:0,5:0};lock=threading.Lock()
        def body(seed,group):
            gpu=group['gpu']
            with lock:active[gpu]+=1;peak[gpu]=max(peak[gpu],active[gpu])
            time.sleep(.02)
            with lock:active[gpu]-=1
        s.worker_body=body
        threads=[threading.Thread(target=s.worker,args=(0,{'gpu':g})) for g in (4,4,5,5)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(peak,{4:1,5:1})
    def test_incomplete_cannot_advance_to_next_task(self):
        class Proc:
            returncode=1
            def poll(self):return 1
            def wait(self,timeout):return 1
        class Guard:
            def cleanup(self,*a):return 'receipt'
        class Stop:
            def is_set(self):return False
            def wait(self,t):return False
        class Sweep:
            def __init__(self,root):
                self.stop=Stop();self.repo=root;self.attempt='test';self.guard=Guard();self.cfg={'sim_env':'sim'}
                self.plan={'budgets':{'task':25},'groups':[{'port':1234}]};self.calls=[]
            def task_id(self,*a):return 'test_task'
            def result_path(self,*a):return self.repo/'_result.json'
            def verify_sources(self):pass
            def update(self,*a,**k):self.calls.append(k)
            def event(self,*a,**k):pass
            def launch(self,*a):return Proc()
            def wait_server(self,*a):pass
        with TemporaryDirectory() as d:
            s=Sweep(Path(d))
            with patch('resume_results.prepare_result',return_value={'action':'fresh'}),patch('dojo_sweep.result_check',return_value={'complete':False,'eval_time':0}):
                with self.assertRaisesRegex(RuntimeError,'three incomplete attempts'):
                    run_client(s,0,'task',0,4,[],Path(d),Proc(),'server',[],'policy')
            self.assertEqual(sum(r.get('status')=='RUNNING' for r in s.calls),3)
            self.assertFalse(any(r.get('status')=='COMPLETE' for r in s.calls))

if __name__=='__main__':unittest.main()
