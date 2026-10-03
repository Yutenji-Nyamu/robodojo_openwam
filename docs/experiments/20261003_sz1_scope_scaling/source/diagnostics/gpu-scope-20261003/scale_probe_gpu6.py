"""Bounded GPU6 Pi05 scaling; independent results, exact cleanup, no RLT actions.

The outer owner supplies a frozen source tree, a verified GPU isolation command
prefix, and a pause receipt. SIGTERM/SIGINT cancel this probe and release its own
processes; only the outer owner decides whether to resume formal Dojo or RLT.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import signal
import socket
import subprocess
import sys
import time

P = Path('/srv/dojo')
RUN = P / 'runs/sz1-gpu6-pi05-scaling-20261003-v1'
GPU, UUID = 6, 'GPU-daa75ed0-9080-a1fc-cb5c-f779251d88d2'
TASK, EPISODES, ORDER = 'put_bottles_into_dustbin', 50, (4, 9, 16, 25, 36)
DEADLINE, VRAM_STOP_MIB, RAM_HEADROOM_KIB = 5400, 70 * 1024, 128 * 1024 * 1024
cancelled = False


class OperatorStop(RuntimeError):
    pass


def request_stop(*_):
    global cancelled
    cancelled = True


def check_stop():
    if cancelled:
        raise OperatorStop('Operator cancelled probe')


def gpu():
    row = next(csv.reader(io.StringIO(subprocess.check_output([
        'nvidia-smi', '-i', str(GPU),
        '--query-gpu=uuid,memory.used,utilization.gpu,gpu_recovery_action',
        '--format=csv,noheader,nounits'], text=True, timeout=15))))
    return dict(gpu=GPU, uuid=row[0].strip(), memory_mib=int(row[1]),
                utilization=int(row[2]), recovery=row[3].strip())


def require_idle():
    snapshot = gpu()
    apps = subprocess.check_output(['nvidia-smi', '-i', str(GPU), '--query-compute-apps=pid',
                                    '--format=csv,noheader'], text=True, timeout=15).strip()
    if (snapshot['uuid'] != UUID or snapshot['memory_mib'] > 512
            or snapshot['recovery'] != 'None' or apps):
        raise RuntimeError('GPU6 not empty/healthy: ' + json.dumps(snapshot))
    return snapshot


def listen(port):
    return any(int(line.split()[1].rsplit(':', 1)[1], 16) == port and line.split()[3] == '0A'
               for name in ('tcp', 'tcp6')
               for line in Path('/proc/net/' + name).read_text().splitlines()[1:])


def ram():
    rss = pss = cpu_ticks = 0
    missing = []
    rows = guard.scan()
    for row in rows:
        proc = Path('/proc') / str(row['pid'])
        try:
            fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[19]) != row['start_ticks']:
                continue
            cpu_ticks += int(fields[11]) + int(fields[12])
            for line in (proc / 'smaps_rollup').read_text().splitlines():
                if line.startswith('Rss:'):
                    rss += int(line.split()[1])
                if line.startswith('Pss:'):
                    pss += int(line.split()[1])
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as error:
            missing.append(dict(pid=row['pid'], error=type(error).__name__))
    node = {key: int(value.split()[0]) for line in Path('/proc/meminfo').read_text().splitlines()
            for key, value in [line.split(':', 1)] if key in ('MemTotal', 'MemAvailable')}
    return dict(rss_kib=rss, pss_kib=pss, cpu_ticks=cpu_ticks,
                pids=len(rows), node_kib=node, missing=missing)


def verify_sources():
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest
           for path, digest in source_hashes.items()):
        raise RuntimeError('Frozen probe source changed')


def launch(argv, rid, role, work):
    check_stop()
    exports = dict(DOJO_SWEEP_ID=RUN.name, ROBODOJO_RUN_ID=rid, DOJO_ROLE=role,
                   EVAL_ENV_TYPE='sim', EVAL_NUM=str(EPISODES),
                   ROBODOJO_RENDER_GPU=str(args.render_gpu), ROBODOJO_MAX_BASH_RETRIES='1',
                   ROBODOJO_FATAL_RESTART_COUNT='3', PYTHONUNBUFFERED='1',
                   ROBODOJO_VULKAN_COMPAT_SCRIPT=str(args.compat_script))
    command = launch_prefix + ['env', f'ROBODOJO_RENDER_GPU={args.render_gpu}', *argv]
    script = ('set -eo pipefail\nsource ' + shlex.quote(str(P / 'project-env.sh'))
              + '\nsource /home/researcher/miniforge3/etc/profile.d/conda.sh\nconda activate '
              + shlex.quote(str(P / 'envs/RoboDojo')) + '\nunset CUDA_VISIBLE_DEVICES\n'
              + '\n'.join('export ' + key + '=' + shlex.quote(value) for key, value in exports.items())
              + '\ncd ' + shlex.quote(str(R)) + '\nexec ' + shlex.join(command) + '\n')
    shell, log = work / (role + '.sh'), work / (role + '.log')
    shell.write_text(script)
    with log.open('wb') as output:
        proc = subprocess.Popen(['bash', str(shell)], env={**os.environ, **exports}, cwd=R,
                                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    atomic_json(work / (role + '-process.json'), guard.identity(proc.pid))
    return proc, log


def case(n):
    check_stop()
    verify_sources()
    work = RUN / f'n{n}'
    work.mkdir()
    rid = RUN.name + f'-n{n}'
    result = (R / f'eval_result/RoboDojo/{TASK}/Pi_05/arx_x5/0_ckpt_name=sim,action_type=joint'
              / rid / '_result.json')
    if result.parent.exists():
        raise RuntimeError('Result identity already exists')
    source = args.eval_source.read_text()
    root_anchor = 'PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"'
    if source.count(root_anchor) != 1:
        raise RuntimeError('Unexpected eval shell root assignment')
    source = source.replace(root_anchor, 'PROJECT_ROOT=' + shlex.quote(str(R)))
    source, count = re.subn(r'^num_envs=.*$', f'num_envs={n}', source, flags=re.M)
    if count != 1:
        raise RuntimeError('Unexpected eval shell num_envs assignment')
    copied = work / 'eval_policy.sh'
    copied.write_text(source)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    report = dict(num_envs=n, episodes=EPISODES, task=TASK, seed=0, run_id=rid,
                  result=str(result), gpu_before=require_idle(), start=time.time())
    started = time.monotonic()
    server = client = None
    offsets, carry, previous = {}, {}, {}
    total_actions, peak = 0, 0
    first = last = None
    utils, seen = [], set()
    completed = False
    ram_due = 0
    rss_peak = pss_peak = 0
    available_min = None

    def consume(log, final=False):
        nonlocal total_actions, first, last
        with log.open('rb') as stream:
            stream.seek(offsets.get(log, 0))
            raw = stream.read()
            offsets[log] = stream.tell()
        text = carry.get(log, '') + raw.decode(errors='replace')
        if final:
            carry[log] = ''
        else:
            split = max(text.rfind('\n'), text.rfind('\r'))
            carry[log], text = text[split + 1:], text[:split + 1]
        text = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
        if FATAL.search(text) or 'Invalid PhysX transform' in text:
            report['fatal'] = True
            raise RuntimeError('GPU/physics failure; no retry')
        steps = []
        for env, step, budget in re.findall(r'env(\d+) step:\s*(\d+)\s*/\s*(\d+)', text):
            env, step, budget = int(env), int(step), int(budget)
            old = previous.get(env, 0)
            seen.add(env)
            total_actions += step - old if step >= old else step
            previous[env] = step
            steps.append([env, step, budget])
            first = first or time.time()
            last = time.time()
        return steps

    def sample():
        nonlocal peak, ram_due, rss_peak, pss_peak, available_min
        snapshot = gpu()
        peak = max(peak, snapshot['memory_mib'])
        if snapshot['uuid'] != UUID or snapshot['recovery'] != 'None' or snapshot['memory_mib'] > VRAM_STOP_MIB:
            raise RuntimeError('GPU health/capacity stop')
        memory = None
        if time.monotonic() >= ram_due:
            memory = ram()
            ram_due = time.monotonic() + 20
            rss_peak = max(rss_peak, memory['rss_kib'])
            pss_peak = max(pss_peak, memory['pss_kib'])
            available = memory['node_kib']['MemAvailable']
            available_min = available if available_min is None else min(available_min, available)
            if available < RAM_HEADROOM_KIB:
                raise RuntimeError('Node memory headroom stop')
        return snapshot, memory

    try:
        server, slog = launch(['bash', 'scripts/robodojo.sh', 'server', '--policy-dir', 'XPolicyLab/policy/Pi_05',
                               '--task', TASK, '--ckpt', 'sim', '--env-cfg', 'arx_x5', '--action-type', 'joint',
                               '--seed', '0', '--policy-env', 'uv', '--policy-gpu', str(GPU),
                               '--policy-port', str(port), '--bind-host', '127.0.0.1'], rid + '-server', 'server', work)
        with (work / 'startup-resources.jsonl').open('w') as metrics:
            while not listen(port):
                check_stop()
                consume(slog)
                if server.poll() is not None or time.monotonic() - started > 600:
                    raise RuntimeError('Policy startup failed/timed out')
                snapshot, memory = sample()
                metrics.write(json.dumps(dict(time=time.time(), gpu=snapshot, ram=memory)) + '\n')
                metrics.flush()
                time.sleep(1)
        report['server_ready'] = time.time()
        client, clog = launch(['bash', str(copied), '--root_dir', str(R), '--task_name', TASK,
                              '--env_cfg_type', 'arx_x5', '--device_id', str(GPU), '--policy_name', 'Pi_05',
                              '--port', str(port), '--host', '127.0.0.1', '--protocol', 'ws',
                              '--additional_info', 'ckpt_name=sim,action_type=joint', '--seed', '0'], rid, 'client', work)
        with (work / 'resources.jsonl').open('w') as metrics:
            while True:
                check_stop()
                steps = consume(clog) + consume(slog)
                snapshot, memory = sample()
                if first is not None:
                    utils.append(snapshot['utilization'])
                metrics.write(json.dumps(dict(time=time.time(), gpu=snapshot, ram=memory,
                                             steps=steps, actions=total_actions)) + '\n')
                metrics.flush()
                atomic_json(work / 'status.json', {**report, 'state': 'RUNNING', 'time': time.time(),
                            'steps': previous, 'actions': total_actions, 'peak_mib': peak, 'pss_peak_kib': pss_peak})
                if client.poll() is not None:
                    break
                if server.poll() is not None:
                    raise RuntimeError('Policy exited before client')
                if time.monotonic() - started > DEADLINE:
                    raise RuntimeError('Case deadline reached')
                time.sleep(2)
        consume(clog, final=True)
        consume(slog, final=True)
        report['check'] = result_check(result, EPISODES)
        report['expected_layouts'] = sorted(report['check'].get('layout_ids', [])) == list(range(EPISODES))
        completed = client.returncode == 0 and report['check'].get('complete') is True and seen == set(range(n))
        if not completed:
            raise RuntimeError('Complete results and active environments not verified')
    except Exception as error:
        report['error'] = repr(error)
        completed = False
    finally:
        report.update(end=time.time(), elapsed_s=time.monotonic() - started, peak_mib=peak,
                      actions=total_actions, first_action=first, last_action=last,
                      observed_envs=sorted(seen), rss_peak_kib=rss_peak, pss_peak_kib=pss_peak,
                      node_available_min_kib=available_min,
                      action_gpu_util_mean=sum(utils) / len(utils) if utils else None)
        report['cleanup'] = []
        for identity, proc in ((rid, client), (rid + '-server', server)):
            try:
                report['cleanup'].append(guard.cleanup(identity, 'bounded_probe_finished'))
                if proc is not None:
                    proc.wait(timeout=10)
            except Exception as error:
                report.setdefault('cleanup_errors', []).append(repr(error))
                completed = False
        # A fatal may arrive after cancellation or the final completed episode.
        for log in (work / 'client.log', work / 'server.log'):
            if log.exists():
                try:
                    consume(log, final=True)
                except Exception as error:
                    report.setdefault('final_log_errors', []).append(repr(error))
                    completed = False
        report['client_exit'] = client.returncode if client is not None else None
        report['server_exit'] = server.returncode if server is not None else None
        report.update(actions=total_actions, first_action=first, last_action=last,
                      observed_envs=sorted(seen))
        if report['client_exit'] in (99, 134, 139, -6, -11):
            report['fatal'] = True
            completed = False
        try:
            if guard.scan():
                raise RuntimeError('Probe processes remain')
            time.sleep(2)
            report['gpu_after'] = require_idle()
        except Exception as error:
            report.setdefault('cleanup_errors', []).append(repr(error))
            completed = False
        report['state'] = 'COMPLETE' if completed else ('INTERRUPTED' if cancelled else 'FAILED')
        atomic_json(work / 'status.json', report)
    return report


def main():
    global args, R, guard, source_hashes, launch_prefix, ProcessGuard, atomic_json, result_check, FATAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--eval-source', type=Path)
    parser.add_argument('--lane-source', type=Path, default=P / 'scripts/lanes/pi05')
    parser.add_argument('--launch-prefix-json', required=True, help='Nonempty isolation wrapper argv, prepended to both actual commands')
    parser.add_argument('--render-gpu', type=int, choices=(0, GPU), default=GPU,
                        help='Vulkan renderer index after the verified isolation wrapper')
    parser.add_argument('--pause-proof', type=Path, required=True, help='Owner JSON: gpu object with gpu=6 and matching uuid')
    parser.add_argument('--compat-script', type=Path, default=P / 'third_party/RoboDawn/scripts/robodojo/compat/vulkan_driver_compat.py')
    parser.add_argument('--check', action='store_true', help='Check CPU sources/configuration and GPU vacancy, then exit without creating a run')
    args = parser.parse_args()
    if os.getuid() != 1003:
        raise RuntimeError('Wrong UID')
    R = args.repo.resolve(strict=True)
    args.eval_source = (args.eval_source or R / 'scripts/eval_policy.sh').resolve(strict=True)
    launch_prefix = json.loads(args.launch_prefix_json)
    if not isinstance(launch_prefix, list) or not launch_prefix or any(not isinstance(x, str) or not x or '\0' in x for x in launch_prefix):
        raise ValueError('Expected nonempty isolation wrapper argv list')
    pause = json.loads(args.pause_proof.read_text())['gpu']
    if pause['gpu'] != GPU or pause['uuid'] != UUID:
        raise RuntimeError('Pause receipt does not identify GPU6')
    require_idle()
    sys.path.insert(0, str(args.lane_source))
    from process_guard import ProcessGuard, atomic_json
    from dojo_sweep import result_check
    from eval_recovery import FATAL
    import yaml
    deploy = yaml.safe_load((R / 'XPolicyLab/policy/Pi_05/deploy.yml').read_text())
    if (deploy.get('eval_batch') is not True or deploy.get('action_type') != 'joint'
            or deploy.get('checkpoint_num') != 59999
            or deploy.get('train_config_name') != 'pi05_base_aloha_full_sim_arx-x5_seed_0'):
        raise RuntimeError('Pi05 deployment differs from the seed0 formal configuration')
    task_config = yaml.safe_load((R / 'task/RoboDojo/config/_task.yml').read_text())
    native = (task_config['tasks'].get(TASK) or {}).get('eval_nums', task_config['common']['eval_nums'])
    if native != EPISODES:
        raise RuntimeError('Task native budget differs from 50')
    for layout in range(EPISODES):
        if not (R / f'Assets/Eval_Layout/RoboDojo/arx_x5/0/{TASK}_{layout}.json').is_file():
            raise RuntimeError('Native seed0 layout missing')
    paths = [R / name for name in ('env_cfg/arx_x5.yml', 'env_cfg/sim/sim_config.yml',
             'scripts/robodojo.sh', 'scripts/eval_policy.sh', 'src/eval_client/main.py',
             'XPolicyLab/policy/Pi_05/deploy.yml', 'XPolicyLab/policy/Pi_05/model.py',
             'XPolicyLab/policy/Pi_05/deploy.py', 'XPolicyLab/policy/Pi_05/setup_eval_policy_server.sh')]
    paths += [args.eval_source, args.compat_script, P / 'project-env.sh']
    paths += [Path(value) for value in launch_prefix if value.startswith('/') and Path(value).is_file()]
    source_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    plan = dict(order=ORDER, gpu=GPU, gpu_uuid=UUID, task=TASK,
                episodes_per_case=EPISODES, seed=0, policy='Pi_05', ckpt='sim', checkpoint_num=59999,
                action_type='joint', inherited_action_horizon=50, inherited_denoise_steps=10,
                policy_inference_overrides={}, deadline_per_case_s=DEADLINE,
                capacity_stop_mib=VRAM_STOP_MIB, node_available_stop_kib=RAM_HEADROOM_KIB,
                ram_sample_s=20, source_sha256=source_hashes, repo=str(R),
                launch_prefix=launch_prefix, render_gpu=args.render_gpu,
                pause_proof=str(args.pause_proof), formal_untouched=True)
    if RUN.exists():
        raise RuntimeError('Probe run already exists; do not replay')
    if args.check:
        print(json.dumps({'check': 'PASS', 'plan': plan}))
        return 0
    RUN.mkdir(exist_ok=False)
    guard = ProcessGuard(RUN.name, 1003, RUN / 'cleanup')
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, request_stop)
    atomic_json(RUN / 'plan.json', plan)
    atomic_json(RUN / 'owner.json', dict(pid=os.getpid(), proc_stat=Path('/proc/self/stat').read_text(), uid=os.getuid()))
    reports = []
    error = None
    released = False
    try:
        for n in ORDER:
            check_stop()
            report = case(n)
            reports.append(report)
            atomic_json(RUN / 'summary.json', dict(cases=reports,
                        finished=len(reports) == len(ORDER) or report['state'] != 'COMPLETE'))
            if report['state'] != 'COMPLETE':
                break
    except Exception as caught:
        error = repr(caught)
    finally:
        try:
            guard.cleanup(None, 'probe_terminal_cleanup')
            if guard.scan():
                raise RuntimeError('Owned probe processes remain')
            verify_sources()
            snapshot = require_idle()
            atomic_json(RUN / 'released.json', dict(time=time.time(), gpu=snapshot,
                        owned_processes=[], source_unchanged=True, cancelled=cancelled))
            released = True
        except Exception as caught:
            error = (error + '; ' if error else '') + repr(caught)
        complete = len(reports) == len(ORDER) and all(row['state'] == 'COMPLETE' for row in reports)
        state = 'COMPLETE' if complete and released and not error else ('INTERRUPTED' if cancelled else 'FAILED')
        atomic_json(RUN / 'summary.json', dict(cases=reports, finished=True, state=state,
                    cancelled=cancelled, released=released, error=error, time=time.time()))
    return 0 if state == 'COMPLETE' else (5 if not released else 3 if cancelled else 2)


if __name__ == '__main__':
    sys.exit(main())
