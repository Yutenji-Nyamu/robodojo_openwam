"""Reuse the tested GPU4 probe with private isolation and a fresh result ID.

Supported stages: N4 x 4 episodes for isolation, then N16/25/36 x 50 episodes.
No formal configuration, RLT cycle, or completed N9 result is modified.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys
import time

P = Path('/srv/dojo')
UUID = 'GPU-9200fbe8-fdd0-93ae-c221-5f0e9d318bf5'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-script', type=Path, required=True,
                        help='Existing unmodified scale_probe_gpu4.py')
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--order', type=int, nargs='+', required=True)
    parser.add_argument('--episodes', type=int, choices=(4, 50), required=True)
    parser.add_argument('--pause-proof', type=Path, required=True)
    parser.add_argument('--launch-prefix-json', required=True)
    parser.add_argument('--render-gpu', type=int, choices=(0, 4), default=4)
    parser.add_argument('--check', action='store_true', help='CPU/source and vacancy preflight only; creates no run')
    args = parser.parse_args()
    if os.getuid() != 1003:
        raise RuntimeError('Wrong UID')
    if not re.fullmatch(r'sz1-gpu4-[A-Za-z0-9_.-]{1,90}', args.run_name):
        raise ValueError('Expected a new isolated sz1-gpu4-* run name')
    order = tuple(args.order)
    if (args.episodes, order) not in ((4, (4,)), (50, (16, 25, 36))):
        raise ValueError('Use N4/4 episodes or N16,25,36/50 episodes; completed N9 is excluded')
    prefix = json.loads(args.launch_prefix_json)
    if not isinstance(prefix, list) or not prefix or any(not isinstance(x, str) or not x or '\0' in x for x in prefix):
        raise ValueError('Expected a nonempty isolation command prefix')
    pause = json.loads(args.pause_proof.read_text())['gpu']
    if pause['gpu'] != 4 or pause['uuid'] != UUID:
        raise RuntimeError('Pause receipt does not identify GPU4')
    repo = args.repo.resolve(strict=True)
    base_source = args.base_script.resolve(strict=True)
    run = P / 'runs' / args.run_name
    if run.exists():
        raise RuntimeError('Run already exists; no replay')
    spec = importlib.util.spec_from_file_location('tested_gpu4_probe', base_source)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.R, base.RUN, base.EPISODES, base.ORDER = repo, run, args.episodes, order
    base.require_idle()
    import yaml
    task_config = yaml.safe_load((repo / 'task/RoboDojo/config/_task.yml').read_text())
    native = (task_config['tasks'].get(base.TASK) or {}).get('eval_nums', task_config['common']['eval_nums'])
    if native != 50 or base.DEADLINE != 5400:
        raise RuntimeError('Native task budget or tested deadline changed')
    for layout in range(args.episodes):
        if not (repo / f'Assets/Eval_Layout/RoboDojo/arx_x5/0/{base.TASK}_{layout}.json').is_file():
            raise RuntimeError('Required seed0 layout missing')
    eval_source = (repo / 'scripts/eval_policy.sh').read_text()
    root_anchor = 'PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"'
    if eval_source.count(root_anchor) != 1 or len(re.findall(r'^num_envs=.*$', eval_source, re.M)) != 1:
        raise RuntimeError('Unexpected eval shell; refuse broad rewriting')
    paths = [base_source, P / 'project-env.sh'] + [repo / rel for rel in (
        'env_cfg/arx_x5.yml', 'env_cfg/sim/sim_config.yml', 'scripts/robodojo.sh',
        'scripts/eval_policy.sh', 'src/eval_client/main.py', 'task/RoboDojo/config/_task.yml',
        'XPolicyLab/policy/OpenWAM/deploy.yml', 'XPolicyLab/policy/OpenWAM/model.py',
        'XPolicyLab/policy/OpenWAM/deploy.py')]
    paths += [Path(value) for value in prefix if value.startswith('/') and Path(value).is_file()]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}

    def verify_sources():
        if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest for path, digest in hashes.items()):
            raise RuntimeError('Pinned probe source changed')

    original_launch = base.launch

    def scoped_launch(argv, rid, role, work):
        # The inherited shell sets physical CUDA visibility. The verified scope
        # wrapper runs afterwards; renderer index is explicit in that scope.
        return original_launch(prefix + ['env', f'ROBODOJO_RENDER_GPU={args.render_gpu}', *argv],
                               rid, role, work)

    base.launch = scoped_launch
    plan = dict(gpu=4, gpu_uuid=UUID, order=order, task=base.TASK, episodes_per_case=args.episodes,
                diagnostic=args.episodes == 4, seed=0, policy='OpenWAM', workers_per_gpu=1,
                deadline_per_case_s=base.DEADLINE, capacity_stop_mib=70 * 1024,
                node_available_stop_kib=128 * 1024 * 1024, source_sha256=hashes,
                launch_prefix=prefix, render_gpu=args.render_gpu, base_script=str(base_source),
                repo=str(repo), pause_proof=str(args.pause_proof), formal_untouched=True)
    if args.check:
        print(json.dumps({'check': 'PASS', 'plan': plan}))
        return 0
    run.mkdir(exist_ok=False)
    base.guard = base.ProcessGuard(run.name, 1003, run / 'cleanup')
    base.atomic_json(run / 'plan.json', plan)
    base.atomic_json(run / 'owner.json', dict(pid=os.getpid(), uid=os.getuid(),
                                            proc_stat=Path('/proc/self/stat').read_text()))
    cancelled = False
    reports, error, released = [], None, False

    def stop(*_):
        nonlocal cancelled
        if not cancelled:
            cancelled = True
            raise RuntimeError('Operator cancelled scoped probe')

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    try:
        for n in order:
            if cancelled:
                break
            verify_sources()
            report = base.case(n)
            reports.append(report)
            base.atomic_json(run / 'summary.json', dict(cases=reports,
                             finished=len(reports) == len(order) or report['state'] != 'COMPLETE'))
            if report['state'] != 'COMPLETE':
                break
    except Exception as caught:
        error = repr(caught)
    finally:
        # The first cancellation can arrive during base.case's cleanup. Finish
        # exact terminal cleanup here before permitting the outer owner to act.
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: None)
        try:
            base.guard.cleanup(None, 'scoped_probe_terminal_cleanup')
            if base.guard.scan():
                raise RuntimeError('Probe processes remain')
            verify_sources()
            health = base.require_idle()
            base.atomic_json(run / 'released.json', dict(time=time.time(), gpu=health,
                             owned_processes=[], source_unchanged=True, cancelled=cancelled))
            released = True
        except Exception as caught:
            error = (error + '; ' if error else '') + repr(caught)
        fatal = False
        for log in run.glob('n*/*.log'):
            text = log.read_text(errors='replace')
            fatal |= bool(base.FATAL.search(text) or 'Invalid PhysX transform' in text)
        complete = len(reports) == len(order) and all(row['state'] == 'COMPLETE' for row in reports)
        state = 'COMPLETE' if complete and released and not error and not fatal else ('INTERRUPTED' if cancelled else 'FAILED')
        base.atomic_json(run / 'summary.json', dict(cases=reports, finished=True, state=state,
                         cancelled=cancelled, released=released, fatal=fatal, error=error, time=time.time()))
    return 0 if state == 'COMPLETE' else (5 if not released else 3 if cancelled else 2)


if __name__ == '__main__':
    sys.exit(main())
