"""Run on SZ1 with the original RLT Python; no GPU, Ray, signals, or drivers."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import types
from unittest import mock


def expect_failure(call, text):
    try:
        call()
    except (AssertionError, RuntimeError) as error:
        assert text in str(error), (text, str(error))
    else:
        raise AssertionError('Expected rejection: '+text)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper',required=True)
    args=parser.parse_args()
    assert socket.gethostname()=='admin' and os.getuid()==1003
    path=Path(args.helper).resolve()
    spec=importlib.util.spec_from_file_location('rlt_cycle_sz1_cpu',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    import torch
    from torch.distributed import checkpoint as dcp
    assert not torch.cuda.is_initialized()
    passed=[]

    def accept(cp, cfg, repo):
        if cp.name=='global_step_800':
            raise AssertionError('Missing indexed replay sample')
        return {'path':str(cp),'step':500}

    with mock.patch.object(m,'checkpoint_candidates',return_value=[Path('/x/global_step_800'),Path('/x/global_step_500')]), \
         mock.patch.object(m,'inspect_checkpoint',side_effect=accept):
        recovery=m.select_recovery('/x',{'runner':{}},'/repo')
        assert recovery['checkpoint']['step']==500 and recovery['mode']=='resume_checkpoint'
        assert len(recovery['newer_rejected'])==1
    passed.append('newest_invalid_checkpoint_skipped_for_complete_older_checkpoint')
    with mock.patch.object(m,'checkpoint_candidates',return_value=[]):
        expect_failure(lambda:m.select_recovery('/x',{'runner':{}},'/repo'),'refusing fresh Stage2')
    passed.append('absent_checkpoint_refuses_fresh_stage2')
    with mock.patch.object(m,'checkpoint_candidates',return_value=[Path('/x/global_step_800')]), \
         mock.patch.object(m,'inspect_checkpoint',side_effect=AssertionError('invalid payload')):
        expect_failure(lambda:m.select_recovery('/x',{'runner':{}},'/repo'),'none validate')
    passed.append('wholly_invalid_checkpoints_refuse_fresh_stage2')

    old=Path('/srv/research/results/rlinf-rlt/old-run')
    new=old.with_name('new-run')
    config={'algorithm':{'unchanged':True},'runner':{'max_steps':3000,'max_epochs':3000,
        'logger':{'log_path':str(old),'experiment_name':old.name},'resume_dir':None},
        'env':{'train':{'task_config':{'save_path':str(old/'train')}},
               'eval':{'video_cfg':{'video_base_dir':str(old/'video')}}}}
    resumed,changes=m.resumed_config(config,old,new,old/'checkpoints/global_step_500')
    assert resumed['algorithm']==config['algorithm'] and resumed['runner']['max_steps']==3000
    assert resumed['runner']['max_epochs']==3000 and 'runner.resume_dir' in changes
    assert config['runner']['resume_dir'] is None
    passed.append('resume_preserves_method_and_cumulative_3000_budget')

    calls=[]
    def gpu_processes(gpus):
        calls.append(list(gpus));assert gpus==[5];return []
    def command(argv):
        assert argv==['nvidia-smi','-i','5','--query-gpu=gpu_recovery_action','--format=csv,noheader']
        return 'None'
    with mock.patch.object(m,'gpu_processes',side_effect=gpu_processes),mock.patch.object(m,'command',side_effect=command):
        m.assert_gpu_released({'gpus':[5]})
    assert calls==[[5]]
    passed.append('release_checks_only_selected_gpu')
    with mock.patch.object(m,'gpu_processes',return_value=[]),mock.patch.object(m,'command',return_value='Reset'):
        expect_failure(lambda:m.assert_gpu_released({'gpus':[5]}),'GPU recovery required')
    passed.append('unhealthy_gpu_refuses_rlt_resume')

    root=path.parent
    assert root.is_relative_to(m.ROOT.resolve()) and root.stat().st_uid==m.UID
    with tempfile.TemporaryDirectory(prefix='rlt-cpu-check-',dir=root) as temporary:
        cp=Path(temporary)/'global_step_500';actor=cp/'actor'
        state_dir=actor/'sac_components/rlt_trainer_state'
        marker={'complete':True,'schema_version':1,'actor_world_size':1,'saved_runner_step':500,
            'rank_files':['checkpoint_rank_0.pt'],'rlt_resume_contract_sha256':'test-digest','update_step':7}
        write(state_dir/'complete.json',marker)
        (state_dir/'checkpoint_rank_0.pt').write_bytes(b'x')
        state={k:v for k,v in marker.items() if k not in ('complete','rank_files')}
        state.update(rank=0,rlt_resume_contract='test-contract',local_total_transitions_added=2,
            local_total_episodes_added=2,global_warmup_ready_total_transitions=None,
            global_warmup_ready_total_episodes=None)
        dcp_dir=actor/'dcp_checkpoint';dcp_dir.mkdir()
        (dcp_dir/'.metadata').write_bytes(b'x');(dcp_dir/'payload.pt').write_bytes(b'x'*16)
        target=actor/'sac_components/target_model/checkpoint_rank_0.pt'
        target.parent.mkdir(parents=True);target.write_bytes(b'x')
        replay=actor/'sac_components/replay_buffer/rank_0'
        write(replay/'metadata.json',{'size':2,'total_samples':2})
        index={'trajectory_index':{str(i):{'trajectory_id':i,'num_samples':1,'model_weights_id':'m1'} for i in (1,2)},
            'trajectory_id_list':[1,2]}
        write(replay/'trajectory_index.json',index)
        for i in (1,2):(replay/f'trajectory_{i}_m1.pt').write_bytes(b'x')
        storage=types.SimpleNamespace(relative_path='payload.pt',offset=0,length=16)
        metadata=types.SimpleNamespace(state_dict_metadata={k+'.x':None for k in ('model','optimizers','lr_schedulers','rng')},
            storage_data={'payload':storage})
        reader=types.SimpleNamespace(read_metadata=lambda:metadata)
        cfg={'algorithm':{'rlt_resume':{'enable':True}},'actor':{'fsdp_config':{'use_orig_params':False}}}
        with mock.patch.object(m,'runtime_contract',return_value=('test-contract','test-digest')), \
             mock.patch.object(torch,'load',return_value=state),mock.patch.object(dcp,'FileSystemReader',return_value=reader):
            checked=m.inspect_checkpoint(cp,cfg,'/unused')
            assert checked['step']==500 and checked['replay_samples']==2 and checked['gpu_used_for_check'] is False
            passed.append('complete_checkpoint_index_and_payload_validation')
            (replay/'trajectory_2_m1.pt').rename(replay/'trajectory_999_m1.pt')
            expect_failure(lambda:m.inspect_checkpoint(cp,cfg,'/unused'),'Missing indexed replay sample')
            passed.append('equal_payload_count_with_missing_indexed_sample_is_rejected')
            (replay/'trajectory_999_m1.pt').rename(replay/'trajectory_2_m1.pt')
            storage.length=17
            expect_failure(lambda:m.inspect_checkpoint(cp,cfg,'/unused'),'')
            passed.append('dcp_shard_out_of_bounds_is_rejected')

    assert not torch.cuda.is_initialized()
    print(json.dumps({'passed':True,'checks':passed,'count':len(passed),'cuda_initialized':False,
        'helper_sha256':m.sha(path),'signals_sent':0,'ray_connections':0,'training_started':False},ensure_ascii=False))


if __name__=='__main__':main()
