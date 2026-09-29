import json,tempfile,unittest
from pathlib import Path
from resume_results import prepare_result

class ResumeResultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)/'repo'
        self.base=self.repo/'eval_result/RoboDojo/task/Pi_05/arx_x5/0_ckpt_name=sim,action_type=joint'
        self.folder=self.base/'run';self.folder.mkdir(parents=True)
        layouts=self.repo/'Assets/Eval_Layout/RoboDojo/arx_x5/0';layouts.mkdir(parents=True)
        self.details={'0':{'layout_id':0,'success':False,'score':.25},'1':{'layout_id':2,'success':True,'score':1.}}
        self.result=self.folder/'_result.json'
        self.result.write_text(json.dumps({'eval_time':2,'success_rate':.5,'score':62.5,'details':self.details}))
        for key,value in self.details.items():
            (layouts/f'task_{value["layout_id"]}.json').write_text('{}')
            for cam in ['head','left_wrist','right_wrist']:
                (self.folder/f'episode_{int(key):07d}_cam_{cam}_success.mp4').write_bytes(b'video-fixture')
    def tearDown(self):self.temp.cleanup()
    def test_rebuild_preserves_failures_scores_layouts_and_result_bytes(self):
        before=self.result.read_bytes()
        report=prepare_result(self.repo,'task',0,'run',4,Path(self.temp.name)/'archive',True)
        manifest=json.loads((self.base/'_resume_run.json').read_text())
        self.assertEqual(report['action'],'rebuild_missing_manifest')
        self.assertEqual(manifest['details'],self.details)
        self.assertEqual((manifest['success_nums'],manifest['fail_nums'],manifest['total_score']),(1,1,1.25))
        self.assertEqual(manifest['completed_layout_ids'],[0,2])
        self.assertEqual(self.result.read_bytes(),before)
        self.assertEqual(prepare_result(self.repo,'task',0,'run',4,Path(self.temp.name)/'unused')['action'],'reuse_manifest')
    def test_full_result_skipped_without_manifest_or_new_evaluation(self):
        report=prepare_result(self.repo,'task',0,'run',2,Path(self.temp.name)/'archive',True)
        self.assertEqual(report['action'],'skip_complete')
        self.assertFalse((self.base/'_resume_run.json').exists())
    def test_disagreeing_resume_is_rejected(self):
        prepare_result(self.repo,'task',0,'run',4,Path(self.temp.name)/'archive',True)
        path=self.base/'_resume_run.json';d=json.loads(path.read_text());d['fail_nums']=0;path.write_text(json.dumps(d))
        with self.assertRaises(AssertionError):prepare_result(self.repo,'task',0,'run',4,Path(self.temp.name)/'unused')
    def test_missing_video_rejects_preservation_as_complete(self):
        next(self.folder.glob('*right_wrist*')).unlink()
        with self.assertRaises(AssertionError):prepare_result(self.repo,'task',0,'run',4,Path(self.temp.name)/'unused')

if __name__=='__main__':unittest.main()
