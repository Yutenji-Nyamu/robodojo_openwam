"""One authorized asset-gated Dojo sweep and exact RLT resource return."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from process_guard import atomic_json

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, required=True)
parser.add_argument('--cycle-dir', type=Path, required=True)
args = parser.parse_args()
cfg = json.loads(args.config.read_text())
assert os.getuid() == cfg['uid'] == 20001
project = Path(cfg['project'])
run = project / 'runs' / cfg['run_id']
run.mkdir(parents=True, exist_ok=True)
lock = (run / 'pipeline.lock').open('a+')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert not (run / 'pipeline-final.json').exists(), 'Completed dispatch must not be replayed'
policy = str(Path(cfg['sim_env']) / 'bin/python')
rlt_python = '/home/chenyiteng/venvs/rlinf-7d07-openpi-robotwin/bin/python'
scripts = Path(__file__).parent
rlt = [rlt_python, '-u', '-B', str(args.cycle_dir/'rlt_cycle_sz3.py'), '--cycle-dir', str(args.cycle_dir)]
dojo = [policy, '-u', '-B', str(scripts/'dojo_sweep.py'), '--config', str(args.config)]
stop_requested = False
child = None

def signal_stop(signum, frame):
    global stop_requested
    stop_requested = True

signal.signal(signal.SIGTERM, signal_stop)
signal.signal(signal.SIGINT, signal_stop)

def state(phase, **values):
    record = dict(time=time.time(), phase=phase, run_id=cfg['run_id'], pid=os.getpid(), **values)
    atomic_json(run/'pipeline-current.json', record)
    with (run/'pipeline-events.jsonl').open('a') as stream:
        stream.write(json.dumps(record)+'\n')
    print(json.dumps(record), flush=True)

def command(argv, label, interruptible=False):
    global child
    with (run/(label+'.log')).open('ab') as output:
        child = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
        pid = child.pid
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        atomic_json(run/(label+'-identity.json'), {'pid':pid,'uid':os.getuid(),'start':int(fields[19])})
        terminated = False
        while child.poll() is None:
            if interruptible and stop_requested and not terminated:
                child.terminate()
                terminated = True
            time.sleep(1)
        rc = child.returncode
        child = None
    atomic_json(run/(label+'-exit.json'), {'time':time.time(),'exit_code':rc,'argv':argv})
    return rc

def managed_identities():
    found = {}
    def add(row):
        if isinstance(row, dict) and row.get('uid') == 20001 and 'pid' in row:
            start = row.get('start', row.get('start_ticks'))
            if start is not None:
                found[(row['pid'],start)] = {'pid':row['pid'],'uid':20001,'start':start}
    p = run/'dojo-controller-identity.json'
    if p.is_file(): add(json.loads(p.read_text()))
    for path in run.glob('seed*/worker*/**/process-*.json'):
        add(json.loads(path.read_text()))
    for path in (run/'cleanup').glob('*.json'):
        data = json.loads(path.read_text())
        for row in data.get('initial_targets',[]) + data.get('actions',[]): add(row)
    return list(found.values())


def publication_gate():
    global cfg
    path = run/'publication-ready.json'
    state('WAITING_FOR_PUBLICATION', receipt=str(path))
    while not path.is_file():
        if stop_requested: raise RuntimeError('Stop requested before publication gate')
        time.sleep(5)
    publication = json.loads(path.read_text())
    updated = json.loads(args.config.read_text())
    assert {k:v for k,v in updated.items() if k!='dojo_head'} == {
        k:v for k,v in cfg.items() if k!='dojo_head'
    }, 'Only dojo_head may change while the pipeline waits for publication'
    current_head = subprocess.check_output(
        ['git','-C',updated['repo'],'rev-parse','HEAD'], text=True, timeout=30).strip()
    assert publication['commit'] == updated['dojo_head'] == current_head, 'Publication/config/HEAD mismatch'
    if 'run_id' in publication:
        assert publication['run_id'] == cfg['run_id'], 'Publication belongs to another sweep'
    cfg = updated
    accepted = {'time':time.time(), 'run_id':cfg['run_id'], 'commit':current_head,
                'config_sha256':hashlib.sha256(args.config.read_bytes()).hexdigest(),
                'publication':publication}
    atomic_json(run/'publication-accepted.json', accepted)
    state('PUBLICATION_VERIFIED', commit=current_head)


def verify_rlt_first_round():
    """Observe only; a timeout never stops or relaunches the restored training."""
    started = time.monotonic()
    deadline = started + 1800
    attempt, latest, latest_error = 0, None, None
    while time.monotonic() < deadline and not stop_requested:
        attempted_at = time.monotonic()
        attempt += 1
        status_command = rlt + ['status']
        try:
            response = subprocess.run(status_command, capture_output=True, text=True,
                                      timeout=min(55, max(1, deadline-time.monotonic())))
            (run/f'rlt-status-{attempt:03d}.log').write_text(response.stdout+'\nSTDERR:\n'+response.stderr)
            if response.returncode != 0:
                raise RuntimeError(f'RLT status exit={response.returncode}; see attempt {attempt}')
            parsed = None
            for line in reversed(response.stdout.splitlines()):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and 'all_first_rounds_verified' in value and 'runs' in value:
                    parsed = value
                    break
            assert parsed and parsed['cycle_id'] == args.cycle_dir.name, 'Missing or mismatched RLT status'
            assert set(parsed['runs']) == {'gpu4','gpu5','gpu6','gpu7'}, 'Unexpected restored run set'
            latest, latest_error = parsed, None
            verified = parsed['all_first_rounds_verified'] is True and all(
                row['first_round_verified'] is True for row in parsed['runs'].values())
            record = {'time':time.time(), 'state':'verified' if verified else 'pending',
                      'attempts':attempt, 'elapsed_seconds':time.monotonic()-started,
                      'status':latest, 'error':None, 'training_action':'none; read-only observation'}
            atomic_json(run/'rlt-first-round.json', record)
            if verified:
                state('RLT_FIRST_ROUNDS_VERIFIED', attempts=attempt)
                return record
        except Exception as exc:
            latest_error = repr(exc)
            atomic_json(run/'rlt-first-round.json', {
                'time':time.time(), 'state':'pending', 'attempts':attempt,
                'elapsed_seconds':time.monotonic()-started, 'status':latest,
                'error':latest_error, 'training_action':'none; read-only observation'})
        next_poll = min(deadline, attempted_at+60)
        while time.monotonic() < next_poll and not stop_requested:
            time.sleep(max(0, min(1, next_poll-time.monotonic())))
    pending = {'time':time.time(), 'state':'pending', 'attempts':attempt,
               'elapsed_seconds':time.monotonic()-started, 'status':latest,
               'error':latest_error, 'reason':'observer_stop_requested' if stop_requested else '30_minute_observation_window_ended',
               'training_action':'none; restored training remains running'}
    atomic_json(run/'rlt-first-round.json', pending)
    state('RLT_FIRST_ROUNDS_PENDING', reason=pending['reason'])
    return pending

terminal, error, dojo_code = 'not_started', None, None
try:
    state('WAITING_FOR_OFFICIAL_ASSETS', asset_revision=cfg['asset_revision'])
    assets = project/'runs'/cfg.get('asset_run_directory', 'full-assets-20260929')
    while not (assets/'exit.txt').exists():
        if stop_requested: raise RuntimeError('Stop requested before borrowing GPUs')
        time.sleep(15)
    assert (assets/'exit.txt').read_text().strip() == '0', 'Asset preparation failed; see its log'
    verified = json.loads((assets/'ready.json').read_text())
    assert verified['revision'] == cfg['asset_revision'] and not verified['errors']
    assert verified['files'] == verified['verified'] and verified['files'] > 0
    state('ASSETS_VERIFIED', files=verified['verified'], bytes=verified['bytes'])
    publication_gate()
    assert command(dojo+['--plan-only'], 'final-preflight') == 0, 'Dojo final preflight failed'
    if stop_requested: raise RuntimeError('Stop requested before borrowing GPUs')
    state('STOPPING_FOUR_RLT_RUNS')
    assert command(rlt+['stop'], 'rlt-stop') == 0, 'RLT stop incomplete; inspect receipt'
    if stop_requested: raise RuntimeError('Stop requested after borrowing GPUs')
    state('EVALUATING', gpus=[4,5,6,7], workers=8, environments_per_worker=4,
          expected_episodes=6300, seeds=[0,1,2], wall_time_limit=None)
    dojo_code = command(dojo, 'dojo-controller', interruptible=True)
    terminal = 'completed' if dojo_code == 0 else 'failed'
except Exception as exc:
    error = repr(exc)
    state('PIPELINE_ERROR', error=error)
finally:
    if (args.cycle_dir/'rlt-stopped.json').exists():
        try:
            state('CLEANING_THIS_DOJO_SWEEP', dojo_exit_code=dojo_code)
            assert command(dojo+['--cleanup-only'], 'dojo-cleanup') == 0, 'Dojo cleanup failed'
            clean = json.loads((run/'cleanup-only-latest.json').read_text())
            assert clean['processes_clear'] and clean['gpus_released']
            release = {'cycle_id':args.cycle_dir.name, 'terminal_status':terminal,
                       'all_workers_stopped':True, 'managed_processes':managed_identities(),
                       'cleanup_receipt':clean, 'time':time.time()}
            atomic_json(run/'dojo-release.json', release)
            state('RESTORING_FOUR_RLT_RUNS', terminal_status=terminal)
            assert command(rlt+['resume','--release-receipt',str(run/'dojo-release.json')], 'rlt-resume') == 0, 'RLT restore dispatch failed'
            state('RLT_RESTORE_DISPATCHED', dojo_exit_code=dojo_code)
            verify_rlt_first_round()
        except Exception as exc:
            error = (error or '') + '; resource return: ' + repr(exc)
            state('RESOURCE_RETURN_NEEDS_ATTENTION', error=error)
    elif (args.cycle_dir/'stop-attempt.json').exists():
        # Signals may have been sent before checkpoint/release validation failed.
        # The RLT cycle intentionally requires inspection of this partial state.
        error = (error or '') + '; RLT stop started but no complete stop receipt; inspect cycle before restore'
        state('RESOURCE_RETURN_NEEDS_ATTENTION', error=error,
              stop_attempt=str(args.cycle_dir/'stop-attempt.json'))
    first_round = run/'rlt-first-round.json'
    final = {'time':time.time(),'terminal_status':terminal,'dojo_exit_code':dojo_code,
             'error':error,'rlt_dispatched':(args.cycle_dir/'resumed-dispatched.json').exists(),
             'rlt_first_round':json.loads(first_round.read_text()) if first_round.is_file() else None}
    atomic_json(run/'pipeline-final.json', final)
    print(json.dumps(final), flush=True)
sys.exit(0 if terminal=='completed' and not error else 1)
