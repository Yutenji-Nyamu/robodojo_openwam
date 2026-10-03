"""One SZ1 owner: wait for preparation, borrow four GPUs, return each independently.

No GPU reset, shared-Ray lifecycle operation, fatal Dojo restart, or broad kill.
Run with the original RLT Python. All helper operations are serialized here.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

UID = 1003
GPUS = (6, 7)
ALL_GPUS = (4, 5, 6, 7)
RLT_PYTHON = '/home/researcher/venvs/rlinf-7d07-openpi-robotwin/bin/python'
CACHE = Path('/home/researcher/cache/dojo-sz1-20261001')
CHECKS = {'source', 'assets', 'checkpoints', 'environments', 'resume_results',
          'lane_cpu', 'rlt_cpu', 'plan_only'}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    with temporary.open('x') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def identity(pid):
    try:
        path = Path('/proc') / str(pid)
        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] in ('Z', 'X'):
            return None
        return {'pid': pid, 'uid': path.stat().st_uid, 'start_ticks': int(fields[19]),
                'cmdline_sha256': hashlib.sha256((path / 'cmdline').read_bytes()).hexdigest()}
    except (FileNotFoundError, ProcessLookupError):
        return None


def same(previous):
    current = identity(previous['pid'])
    return bool(current and all(current[k] == previous[k] for k in ('pid', 'uid', 'start_ticks')))


def required_files(project):
    paths = [project / 'scripts/rlt/owner_sz1.py', project / 'scripts/rlt/rlt_cycle_sz1.py']
    for model in ('openwam', 'pi05'):
        paths.extend(project / 'scripts/lanes' / model / name for name in
                     ('dojo_sweep.py', 'process_guard.py', 'eval_recovery.py', 'resume_results.py'))
    paths.extend(project / f'scripts/lanes/configs/gpu{gpu}.json' for gpu in ALL_GPUS)
    return paths


def validate_ready(project, payload):
    if payload.get('ready') is not True or payload.get('host') != 'admin' or payload.get('uid') != UID:
        raise RuntimeError('Deployment readiness host/account/ready mismatch')
    checks = payload.get('checks', [])
    if not isinstance(checks, list) or any(row.get('passed') is not True for row in checks):
        raise RuntimeError('A deployment check failed or is incomplete')
    if not CHECKS <= {row.get('name') for row in checks}:
        raise RuntimeError('Deployment is missing required check categories')
    rows = payload.get('files', [])
    if not isinstance(rows, list):
        raise RuntimeError('Missing deployment file manifest')
    claimed = {}
    for row in rows:
        path = Path(row['path'])
        if (not path.is_absolute() or path.is_symlink()
                or not any(path.resolve().is_relative_to(root) for root in (project, CACHE))):
            raise RuntimeError('Readiness file escapes the project or is a symlink: ' + str(path))
        if path.stat().st_uid != UID or path in claimed or sha(path) != row['sha256']:
            raise RuntimeError('Readiness file identity/SHA differs: ' + str(path))
        claimed[path] = row['sha256']
    if not set(required_files(project)) <= set(claimed):
        raise RuntimeError('Readiness manifest does not freeze every owner/helper/lane/config source')
    configs = {}
    for gpu in ALL_GPUS:
        cfg = read(project / f'scripts/lanes/configs/gpu{gpu}.json')
        control = Path(cfg['control_dir'])
        if (cfg['lane_gpu'] != gpu or cfg['uid'] != UID or cfg['workers_per_gpu'] != 1
                or Path(cfg['project']).resolve() != project or control.name != f'gpu{gpu}'
                or not control.resolve().is_relative_to(project / 'runs')):
            raise RuntimeError('Invalid approved single-card configuration')
        configs[gpu] = cfg
    if len({cfg['control_dir'] for cfg in configs.values()}) != 4:
        raise RuntimeError('Control directories overlap')
    if configs[4]['run_id'] != configs[5]['run_id'] or configs[6]['run_id'] != configs[7]['run_id']:
        raise RuntimeError('The two cards of a model must retain its previous result identity')
    return configs


def gpu_health(gpu, memory_limit=512):
    raw = subprocess.check_output(['nvidia-smi', '-q', '-x', '-i', str(gpu)], text=True, timeout=30)
    tree = ET.fromstring(raw)
    devices = tree.findall('gpu')
    if len(devices) != 1:
        raise RuntimeError('GPU query did not return exactly the assigned device')
    device = devices[0]
    processes = [int(row.findtext('pid')) for row in device.findall('./processes/process_info')
                 if (row.findtext('pid') or '').isdigit()]
    action = subprocess.check_output(['nvidia-smi', '-i', str(gpu),
        '--query-gpu=gpu_recovery_action', '--format=csv,noheader'], text=True, timeout=30).strip()
    memory_text = device.findtext('./fb_memory_usage/used', '')
    memory = int(memory_text.split()[0])
    result = {'gpu': gpu, 'uuid': device.findtext('uuid'), 'processes': processes,
              'gpu_recovery_action': action, 'memory_mib': memory, 'checked_at': time.time()}
    if processes or action != 'None' or memory > memory_limit:
        raise RuntimeError('GPU not empty and healthy; no automatic reset: ' + json.dumps(result))
    return result


class Owner:
    def __init__(self, project, directory):
        self.project, self.directory = project, directory
        self.helper = project / 'scripts/rlt/pi-yamlfix/rlt_cycle_sz1.py'
        self.previous_owner = project / 'runs/sz1-dojo-continuation-20261002-v1'
        self.state = {'owner_id': directory.name, 'host': 'admin', 'uid': UID,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'identity': identity(os.getpid()), 'created_at': time.time(),
            'stage': 'WAITING_FOR_PREPARATION', 'rlt_untouched': True,
            'lanes': {str(gpu): {'gpu': gpu, 'state': 'WAITING'} for gpu in GPUS}}
        self.processes, self.guards, self.configs = {}, {}, {}
        self.interrupted = False
        self.cutover_failed = False

    def save(self):
        self.state['updated_at'] = time.time()
        atomic(self.directory / 'status.json', self.state)

    def event(self, kind, **fields):
        row = {'time': time.time(), 'event': kind, **fields}
        with (self.directory / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n'); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps(row, ensure_ascii=False), flush=True)

    def cycle(self, gpu):
        return self.project / ('rlt-cycle-' + self.directory.name + '-gpu' + str(gpu))

    def helper_call(self, gpu, action, *extra):
        stage = self.cycle(gpu)
        script = self.helper if action == 'prepare' else stage / 'rlt_cycle_sz1.py'
        if action == 'prepare':
            old = self.project / ('rlt-cycle-' + self.previous_owner.name + '-gpu' + str(gpu))
            extra = (*extra, '--previous-cycle', str(old))
        argv = [RLT_PYTHON, '-u', '-B', str(script), '--cycle-dir', str(stage), action, *extra]
        log = self.directory / f'gpu{gpu}-{action}-{time.time_ns()}.log'
        self.event('rlt_helper_started', gpu=gpu, action=action, argv=argv, log=str(log))
        with log.open('wb') as stream:
            result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=900 if action != 'status' else 120)
        if result.returncode:
            raise RuntimeError(f'GPU{gpu} RLT {action} failed ({result.returncode}); inspect {log}')
        lines = log.read_text().splitlines()
        if not lines:
            raise RuntimeError('Helper returned no receipt')
        return json.loads(lines[-1])

    def wait_ready(self, seconds):
        deadline = time.monotonic() + seconds
        ready = self.project / 'deployment-ready.json'
        while not self.interrupted and time.monotonic() < deadline:
            failure = self.project / 'deployment-preparation-failed.json'
            if failure.is_file():
                raise RuntimeError('Deployment preparation failed; original RLT remains unchanged: ' + str(failure))
            if ready.is_file():
                payload = read(ready)
                original_configs = validate_ready(self.project, payload)
                prior = read(self.previous_owner/'status.json')
                assert prior['boot_id'] == self.state['boot_id']
                for gpu in GPUS:
                    assert prior['lanes'][str(gpu)]['state'] == 'RLT_RESTORED'
                    proof = read(self.previous_owner/f'gpu{gpu}-rlt-first-round.json')
                    assert proof['all_first_rounds_verified'] is True
                    original = original_configs[gpu]
                    cfg = read(self.directory/f'configs/gpu{gpu}.json')
                    assert {k:v for k,v in cfg.items() if k != 'control_dir'} == {k:v for k,v in original.items() if k != 'control_dir'}
                    assert Path(cfg['control_dir']) == self.directory/f'lanes/gpu{gpu}'
                    self.configs[gpu] = cfg
                self.state['previous_owner'] = str(self.previous_owner)
                self.state['deployment'] = {'path': str(ready), 'sha256': sha(ready)}
                atomic(self.directory / 'deployment-ready-frozen.json', payload)
                return
            time.sleep(10)
        raise RuntimeError('Preparation interrupted or exceeded deadline; original RLT remains unchanged')

    def preflight_lanes(self):
        ports = []
        for gpu in GPUS:
            cfg = self.configs[gpu]
            model = 'openwam' if gpu < 6 else 'pi05'
            source = self.project / 'scripts/lanes' / model / 'dojo_sweep.py'
            argv = [str(Path(cfg['policy_env']) / 'bin/python'), '-u', '-B', str(source),
                    '--config', str(self.directory / f'configs/gpu{gpu}.json'), '--plan-only']
            path = self.directory / f'gpu{gpu}-fresh-plan.json'
            with path.open('wb') as stream:
                result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
            if result.returncode: raise RuntimeError('Fresh lane preflight failed: ' + str(path))
            plan = read(path)
            if plan['episode_total'] != 6300 or plan['seeds'] != [0, 1, 2] or plan['num_envs'] != 4:
                raise RuntimeError('Formal episode/seed/environment protocol differs')
            ports.extend(int(group['port']) for group in plan['groups'] if group['gpu'] == gpu)
            action = subprocess.check_output(['nvidia-smi', '-i', str(gpu),
                '--query-gpu=gpu_recovery_action', '--format=csv,noheader'], text=True, timeout=30).strip()
            if action != 'None': raise RuntimeError(f'GPU{gpu} already requires recovery before borrowing: {action}')
        if len(ports) != 8 or len(set(ports)) != len(ports):
            raise RuntimeError('Assigned model/lane ports overlap or groups are missing')
        for port in ports:
            with socket.socket() as check:
                check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                check.bind(('127.0.0.1', port))
        self.state['fresh_preflight_at'] = time.time(); self.save()

    def start_lane(self, gpu):
        cfg = self.configs[gpu]
        model = 'openwam' if gpu in (4, 5) else 'pi05'
        source = self.project / 'scripts/lanes' / model
        module_path = source / 'process_guard.py'
        spec = importlib.util.spec_from_file_location(f'guard_gpu{gpu}', module_path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        sweep_id = f"{cfg['run_id']}:sz1:gpu{gpu}"
        guard = module.ProcessGuard(sweep_id, UID, Path(cfg['control_dir']) / 'cleanup')
        self.guards[gpu] = guard
        gpu_health(gpu, cfg.get('idle_gpu_memory_mib', 512))
        script = source / 'dojo_sweep.py'
        config_path = self.directory / f'configs/gpu{gpu}.json'
        # Hold the child before exec so even an immediate preflight failure has a
        # recorded PID/start identity. This pipe carries one byte, never a secret.
        gate_read, gate_write = os.pipe()
        wrapper = ('import os,sys; fd=int(sys.argv[1]); b=os.read(fd,1); os.close(fd); '
                   'b==b"G" or sys.exit(125); os.execv(sys.argv[2],sys.argv[2:])')
        python = str(Path(cfg['policy_env']) / 'bin/python')
        argv = [python, '-u', '-B', str(script), '--config', str(config_path)]
        env = os.environ.copy()
        env.update(DOJO_SWEEP_ID=sweep_id, ROBODOJO_RUN_ID=cfg['run_id'], DOJO_ROLE='controller')
        log = self.directory / f'gpu{gpu}-dojo.log'
        try:
            with log.open('wb') as stream:
                child = subprocess.Popen([RLT_PYTHON, '-u', '-B', '-c', wrapper, str(gate_read), *argv],
                    env=env, cwd=self.project, stdout=stream, stderr=subprocess.STDOUT,
                    start_new_session=True, pass_fds=(gate_read,))
            os.close(gate_read); gate_read = None
            target = guard.identity(child.pid)
            if target is None:
                raise RuntimeError('Gated controller identity unavailable')
            lane = self.state['lanes'][str(gpu)]
            lane.update(state='DOJO_RUNNING', sweep_id=sweep_id, managed_processes=[target],
                        controller_argv=argv, controller_log=str(log), started_at=time.time())
            self.processes[gpu] = child
            self.save()
            os.write(gate_write, b'G')
        finally:
            if gate_read is not None: os.close(gate_read)
            os.close(gate_write)
        self.event('dojo_started', gpu=gpu, pid=child.pid, log=str(log))

    def return_lane(self, gpu, terminal):
        lane = self.state['lanes'][str(gpu)]
        cfg = self.configs[gpu]
        managed = list(lane.get('managed_processes', []))
        guard = self.guards.get(gpu)
        if guard:
            cleanup = guard.cleanup(None, 'sz1_owner_lane_terminal', grace=20)
            if guard.scan(): raise RuntimeError('Owned Dojo processes remain')
            history = guard.known_path
            if history.exists():
                managed.extend(json.loads(line) for line in history.read_text().splitlines())
            lane['owner_cleanup_receipt'] = cleanup
        if any(same(row) for row in managed):
            raise RuntimeError('An exact managed controller/worker identity remains alive')
        health = gpu_health(gpu, cfg.get('idle_gpu_memory_mib', 512))
        final_path = Path(cfg['control_dir']) / 'final.json'
        final = read(final_path) if final_path.exists() else None
        # A success claim requires the exact lane's terminal proof; failure or
        # interruption can use the independently proven owner cleanup instead.
        if terminal == 'completed' and (not final or final.get('state') != 'COMPLETE'
                or final.get('lane_gpu') != gpu or final.get('processes_clear') is not True
                or final.get('gpus_released') is not True):
            terminal = 'failed'
        unique = {(row['pid'], row.get('start', row.get('start_ticks'))): row for row in managed}
        receipt = {'cycle_id': self.cycle(gpu).name, 'gpus': [gpu], 'terminal_status': terminal,
            'all_workers_stopped': True, 'managed_processes': list(unique.values()),
            'gpu_recovery_action': health['gpu_recovery_action'], 'gpu_health': health,
            'sweep_id': lane.get('sweep_id'), 'owner_id': self.directory.name,
            'boot_id': self.state['boot_id'], 'finished_at': time.time(),
            'lane_final': {'path': str(final_path), 'sha256': sha(final_path)} if final else None}
        release_path = self.directory / f'gpu{gpu}-release.json'
        atomic(release_path, receipt)
        lane.update(state='RLT_RETURNING', dojo_terminal=terminal, release_receipt=str(release_path))
        self.save()
        result = self.helper_call(gpu, 'resume', '--release-receipt', str(release_path))
        lane.update(state='RLT_VERIFYING', resumed_at=time.time(), resume_receipt=result)
        self.save(); self.event('rlt_dispatched', gpu=gpu, terminal=terminal)

    def verify_returns(self):
        for gpu in GPUS:
            lane = self.state['lanes'][str(gpu)]
            if lane['state'] != 'RLT_VERIFYING': continue
            try:
                receipt = self.helper_call(gpu, 'status')
                atomic(self.directory / f'gpu{gpu}-rlt-status.json', receipt)
                if receipt.get('all_first_rounds_verified') is True:
                    lane.update(state='RLT_RESTORED', verified_at=time.time())
                    atomic(self.directory / f'gpu{gpu}-rlt-first-round.json', receipt)
                    self.event('rlt_first_round_verified', gpu=gpu)
                elif any(row.get('finished') or row.get('resume_alive') is False
                         for row in receipt.get('runs', {}).values()):
                    raise RuntimeError('Resumed RLT exited before first true collection round')
                elif time.time() - lane['resumed_at'] > 3600:
                    raise RuntimeError('RLT first-round verification exceeded one hour')
            except Exception as error:
                lane.update(state='NEEDS_ATTENTION', error=repr(error))
                self.event('rlt_verification_failed', gpu=gpu, error=repr(error))
            self.save()

    def run(self, wait_seconds):
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, lambda *_: setattr(self, 'interrupted', True))
        self.save()
        try:
            self.wait_ready(wait_seconds)
            self.preflight_lanes()
            self.state['stage'] = 'PREPARING_RLT_CYCLES'; self.save()
            # Freeze all current configurations/checkpoints before touching a GPU.
            for gpu in GPUS:
                self.helper_call(gpu, 'prepare', '--gpu', str(gpu))
                self.state['lanes'][str(gpu)]['state'] = 'PREPARED'; self.save()
            self.state['stage'] = 'RUNNING'; self.save()
            for gpu in GPUS:
                if self.interrupted: break
                lane = self.state['lanes'][str(gpu)]
                lane['state'] = 'RLT_STOPPING'; self.save()
                try:
                    self.helper_call(gpu, 'stop')
                    lane['state'] = 'RLT_STOPPED'; self.state['rlt_untouched'] = False; self.save()
                    self.start_lane(gpu)
                except Exception as error:
                    self.cutover_failed = True
                    self.interrupted = True
                    lane['error'] = repr(error)
                    self.event('cutover_failed', gpu=gpu, error=repr(error))
                    if (self.cycle(gpu) / 'rlt-stopped.json').exists():
                        try: self.return_lane(gpu, 'failed' if gpu in self.processes else 'not_started')
                        except Exception as restore_error:
                            lane.update(state='NEEDS_ATTENTION', restore_error=repr(restore_error))
                        finally: self.processes.pop(gpu, None)
                    else:
                        lane['state'] = 'NEEDS_ATTENTION' if (self.cycle(gpu) / 'stop-attempt.json').exists() else 'RLT_UNTOUCHED'
                    self.save()
                    # Stop dispatching further cards after an uncertain stop.
                    break
            while True:
                for gpu, process in list(self.processes.items()):
                    if self.interrupted and process.poll() is None:
                        guard = self.guards[gpu]
                        current = guard.identity(process.pid)
                        if current: guard.send(current, signal.SIGTERM)
                    code = process.poll()
                    if code is None: continue
                    del self.processes[gpu]
                    try:
                        self.return_lane(gpu, 'completed' if code == 0 else 'failed')
                    except Exception as error:
                        self.state['lanes'][str(gpu)].update(state='NEEDS_ATTENTION', error=repr(error))
                        self.event('gpu_return_failed', gpu=gpu, error=repr(error)); self.save()
                self.verify_returns()
                if not self.processes and not any(row['state'] == 'RLT_VERIFYING' for row in self.state['lanes'].values()):
                    break
                time.sleep(20)
            states = {row['state'] for row in self.state['lanes'].values()}
            self.state['stage'] = ('NEEDS_ATTENTION' if 'NEEDS_ATTENTION' in states
                else 'CUTOVER_ABORTED' if self.cutover_failed
                else 'INTERRUPTED_AND_RETURNED' if self.interrupted else 'FINISHED')
        except Exception as error:
            self.state.update(stage='PREPARATION_FAILED' if self.state['rlt_untouched'] else 'NEEDS_ATTENTION', error=repr(error))
            self.event('owner_failed', error=repr(error))
            # Unexpected owner errors still return every verified stopped card;
            # an uncertain partial RLT stop remains fail-closed for inspection.
            for gpu, process in list(self.processes.items()):
                try:
                    self.guards[gpu].cleanup(None, 'sz1_owner_exception', grace=20)
                    process.wait(timeout=10)
                    del self.processes[gpu]
                    if (self.cycle(gpu) / 'rlt-stopped.json').exists(): self.return_lane(gpu, 'failed')
                except Exception as restore_error:
                    self.state['lanes'][str(gpu)].update(state='NEEDS_ATTENTION', restore_error=repr(restore_error))
            while any(row['state'] == 'RLT_VERIFYING' for row in self.state['lanes'].values()):
                self.verify_returns()
                if any(row['state'] == 'RLT_VERIFYING' for row in self.state['lanes'].values()): time.sleep(20)
        finally:
            self.state['finished_at'] = time.time(); self.save()
        return 0 if self.state['stage'] == 'FINISHED' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--owner-dir', type=Path, required=True)
    parser.add_argument('--wait-hours', type=float, default=36)
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    if os.getuid() != UID or socket.gethostname() != 'admin':
        raise RuntimeError('Wrong host/account')
    project, directory = args.project.resolve(), args.owner_dir.resolve()
    if (not project.is_relative_to(Path('/srv/research/projects'))
            or not directory.is_relative_to(project / 'runs') or directory == project / 'runs'
            or not 0 < args.wait_hours <= 36):
        raise RuntimeError('Unsafe project/owner path or wait deadline')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.stat().st_uid != UID: raise RuntimeError('Wrong owner-directory UID')
    if args.launch:
        status = directory / 'status.json'
        if status.exists():
            prior = read(status)
            if prior['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip() and same(prior['identity']):
                print(json.dumps({'already_running': True, 'identity': prior['identity'], 'status': str(status)})); return
            raise RuntimeError('Existing owner has exited; do not repeat prepare/stop/dispatch')
        argv = [sys.executable, '-u', '-B', str(Path(__file__).resolve()), '--project', str(project),
                '--owner-dir', str(directory), '--wait-hours', str(args.wait_hours)]
        with (directory / 'owner.log').open('ab') as stream:
            process = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        for _ in range(50):
            if status.exists():
                print(json.dumps({'launched': True, 'identity': read(status)['identity'], 'status': str(status)})); return
            if process.poll() is not None: raise RuntimeError('Owner startup failed; inspect owner.log')
            time.sleep(.1)
        raise RuntimeError('Owner did not write its startup identity')
    with (directory / 'owner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (directory / 'status.json').exists():
            raise RuntimeError('Owner directory already used; automatic replay is forbidden')
        return Owner(project, directory).run(args.wait_hours * 3600)


if __name__ == '__main__':
    sys.exit(main())
