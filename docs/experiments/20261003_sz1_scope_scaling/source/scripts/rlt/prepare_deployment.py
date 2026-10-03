"""Produce SZ1 deployment readiness after pinned import/install and CPU acceptance.

Does not borrow GPUs, stop RLT, initialize CUDA, or alter Ray. The owner consumes
the final manifest. Existing episode results remain byte-identical.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

P = Path('/srv/dojo')
C = Path('/home/researcher/cache/dojo-sz1-20261001')
OUT = P / 'runs/deployment-preparation-sz1-20261002-v2'
IMPORT = P / 'runs/import-sz1-20261002'
INSTALL = P / 'runs/install-sz1-20261002-v2'
RLT_PYTHON = '/home/researcher/venvs/rlinf-7d07-openpi-robotwin/bin/python'
DOJO = '6dddac88a4fb9a72cbb9d39a90a9850e2ea811a8'
XPL = '10ab2651a0b7cd5b8a948cb13f18ccdf818c6de4'
ASSET_REV = '43dacb13d3051a9ccd421f4e7e08e4e3eb29dfab'
OW_REV = '2c1302294e3ba8319bbdb2c803b7a27de9292d03'
PI_REV = '35efbc7dedfdbeeb6e95fb749bd885d73d483e41'
RUNS = {'openwam': 'sz2_openwam_official_6300_n4_dual_20260929_r2',
        'pi05': 'sz3_pi05_official_6300_n4_dual_20260929_r2'}


def read(path): return json.loads(Path(path).read_text())


def digest(path, git_size=None):
    value = hashlib.sha256() if git_size is None else hashlib.sha1(f'blob {git_size}\0'.encode())
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''): value.update(block)
    return value.hexdigest()


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    with temporary.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temporary.chmod(0o600); os.replace(temporary, path)


def log(kind, **fields):
    print(json.dumps({'time': time.time(), 'event': kind, **fields}, ensure_ascii=False), flush=True)


def checked(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink() and path.stat().st_uid == 1003, str(path)
    assert path.resolve().is_relative_to(P) or path.resolve().is_relative_to(C), str(path)
    return path


def run(argv, label, extra_env=None):
    env = os.environ.copy(); env.update(CUDA_VISIBLE_DEVICES='', JAX_PLATFORMS='cpu')
    if extra_env: env.update(extra_env)
    path = OUT / (label + '.log')
    log('cpu_step', name=label, argv=argv)
    with path.open('wb') as stream:
        result = subprocess.run(argv, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
    assert result.returncode == 0, f'{label} failed: {path}'
    return path


def wait_prerequisites():
    deadline = time.monotonic() + 36 * 3600
    while True:
        complete = True
        for directory in (IMPORT, INSTALL):
            exit_path = directory / 'exit.txt'
            if exit_path.exists():
                assert exit_path.read_text().strip() == '0', 'Prerequisite failed: ' + str(directory)
                assert read(directory / 'ready.json')['status'] == 'ready'
            else: complete = False
        if complete: return
        assert time.monotonic() < deadline, 'Import/install exceeded preparation deadline'
        time.sleep(10)


def source_assets():
    repo = P / 'RoboDojo'
    source = read(IMPORT / 'source-ready.json')
    assert source['dojo_head'] == DOJO and source['all_hashes_verified'] is True
    assert subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() == DOJO
    assert subprocess.check_output(['git', '-C', str(repo / 'XPolicyLab'), 'rev-parse', 'HEAD'], text=True).strip() == XPL
    assert set(source['submodules']) == {'XPolicyLab', 'IsaacLab', 'cuRobo'}
    expected = {'XPolicyLab': XPL, 'IsaacLab': 'afca7b09', 'cuRobo': '895c6517'}
    for name, row in source['submodules'].items():
        assert row['head'].startswith(expected[name])
        path = repo / row['path']
        assert path.resolve().is_relative_to(repo)
        assert subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip() == row['head']
    patch = P / 'imports/source/xpolicy-local.patch'
    assert digest(patch) == source['local_patch_sha256']
    subprocess.run(['git', '-C', str(repo / 'XPolicyLab'), 'apply', '--reverse', '--check', str(patch)], check=True)
    meta = read(P / 'imports/source/manifest.json')
    assert meta['dojo_head'] == DOJO
    for name, row in meta['files'].items():
        assert digest(P / 'imports/source' / name) == row['sha256']
    assets = read(IMPORT / 'assets-ready.json')
    formal = read(P / 'runs/full-assets-sz1-20261001/ready.json')
    manifest = read(P / 'runs/full-assets-sz1-20261001/manifest.json')
    for ready in (assets, formal):
        assert ready['revision'] == ASSET_REV and ready['verified'] == ready['files'] == len(manifest) == 15365
        assert ready['all_sizes_verified'] is True and ready['bytes'] == 41269513111 and not ready['errors']
    transferred = read(IMPORT / 'assets-manifest.json')
    assert len(transferred['files']) == 15365 and transferred['bytes'] == 41269513111
    paths = read(INSTALL / 'asset-paths-ready.json')
    assert paths['status'] == 'ready' and paths['source_assets_sizes_verified_before_repath'] is True
    assert len({row['path'] for row in manifest}) == len(manifest)
    for row in manifest:
        path = repo / row['path']
        assert path.resolve().is_relative_to(repo / 'Assets') and path.is_file(), str(path)
        # YAML path rewriting is intentionally after verification of the
        # immutable official objects; their original SHA is kept in the manifest.
        if path.suffix not in ('.yml', '.yaml'):
            assert path.stat().st_size == row.get('size', row['git_size']), str(path)
    atomic(OUT / 'source-assets-verified.json', {'passed': True, 'dojo_head': DOJO,
        'xpl_head': XPL, 'asset_revision': ASSET_REV, 'files': len(manifest),
        'immutable_import_hashes_verified': False, 'verification':'fixed_revision_and_sizes', 'asset_paths_updated': True})


def checkpoints():
    checked_rows = []
    for model, revision in (('openwam', OW_REV), ('pi05', PI_REV)):
        ready = read(IMPORT / (model + '-ready.json'))
        assert ready['revision'] == revision and ready['all_sizes_verified'] is True
        manifest = read(IMPORT / (model + '-manifest.json'))
        assert ready['files'] == len(manifest['files'])
        for row in manifest['files']:
            path = checked(P / row['target'])
            assert path.stat().st_size == row['size'], str(path)
            checked_rows.append({'path': str(path), 'bytes': row['size'], 'verification':'manifest_size'})
    for seed in range(3):
        checkpoint = P / f'checkpoints/Pi_05/RoboDojo-sim-arx_x5-joint-{seed}/59999'
        manifest = read(checkpoint / '.download-pi05/manifest.json')
        ready = read(checkpoint / 'pi05-inference-ready.json')
        assert ready['status'] == 'ready' and ready['revision'] == manifest['revision'] == PI_REV
        assert ready['file_count'] == len(manifest['files'])
        assert all(row['verified'] is True for row in ready['files'])
        canonical = [{key: row[key] for key in ('path', 'size', 'sha256')} for row in ready['files']]
        assert canonical == manifest['files']
        value = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert value == manifest['manifest_sha256'] == ready['manifest_sha256']
    atomic(OUT / 'checkpoints-verified.json', {'passed': True, 'files': checked_rows,
        'openwam_revision': OW_REV, 'pi05_revision': PI_REV, 'seeds': [0, 1, 2]})


def environments():
    gates = {
        'sim': (P / 'envs/RoboDojo/bin/python', {'torch': '2.7.0+cu128', 'torchvision': '0.22.0+cu128', 'isaacsim': '5.1.0.0', 'numpy': '1.26.0'}),
        'openwam': (P / 'envs/openwam/bin/python', {'torch': '2.7.1+cu128', 'torchvision': '0.22.1+cu128'}),
        'pi05': (P / 'RoboDojo/XPolicyLab/policy/Pi_05/openpi/.venv/bin/python', {'jax': '0.5.3', 'torch': '2.10.0', 'numpy': '1.26.4', 'orbax-checkpoint': '0.11.13'})}
    actual = {}
    for name, (python, expected) in gates.items():
        ready = read(INSTALL / (name + '-ready.json'))
        assert ready['status'] == 'ready' and digest(INSTALL / (name + '.sh')) == ready['script_sha256']
        assert (P / 'logs' / ('install-' + name + '.exit')).read_text().strip() == '0'
        report_path = P / 'logs' / (name + '-pip-check.txt')
        rc_path = P / 'logs' / (name + '-pip-check.exit')
        compat_path = OUT / (name + '-pip-compatibility-fresh.json')
        argv = [str(python), '-u', '-B', str(P / 'scripts/pip_compatibility.py'),
                '--environment', name, '--report', str(report_path),
                '--returncode-file', str(rc_path), '--output', str(compat_path)]
        if name == 'pi05': argv += ['--lock-file', str(P / 'RoboDojo/XPolicyLab/policy/Pi_05/openpi/uv.lock')]
        run(argv, name + '-pip-compatibility')
        compatibility = read(compat_path)
        assert compatibility['accepted'] is True and compatibility['report_sha256'] == digest(report_path)
        assert compatibility['returncode'] == int(rc_path.read_text().strip())
        script = 'import importlib.metadata as m,json; print(json.dumps({k:m.version(k) for k in ' + repr(list(expected)) + '}))'
        path = run([str(python), '-u', '-B', '-c', script], name + '-versions')
        versions = json.loads(path.read_text().splitlines()[-1])
        for package, value in expected.items():
            assert versions[package] == value or name == 'pi05' and package == 'torch' and versions[package].split('+')[0] == value
        actual[name] = versions
    ready = read(INSTALL / 'ready.json')
    assert ready['gpu_execution'] is False and ready['renderer_settings_changed'] is False and ready['driver_changed'] is False
    atomic(OUT / 'environments-verified.json', {'passed': True, 'versions': actual, 'gpu_execution': False})


def cpu_checks():
    rlt = P / 'scripts/rlt'
    for label, argv, count in (
        ('pip-compatibility-cpu', [RLT_PYTHON, '-u', '-B', str(P / 'scripts/check_pip_compatibility_cpu.py'), '--classifier', str(P / 'scripts/pip_compatibility.py')], 10),
        ('preparation-cpu', [RLT_PYTHON, '-u', '-B', str(rlt / 'check_prepare_deployment_cpu.py'), '--producer', str(rlt / 'prepare_deployment.py'), '--lane-root', str(P / 'scripts/lanes')], 16),
    ):
        path = run(argv, label)
        report = json.loads(path.read_text().splitlines()[-1])
        assert report['passed'] is True and report['tests'] == count
        atomic(OUT / (label + '.json'), report)
    path = run([RLT_PYTHON, '-u', '-B', str(rlt / 'check_rlt_cycle_sz1_cpu.py'), '--helper', str(rlt / 'rlt_cycle_sz1.py')], 'rlt-cpu')
    report = json.loads(path.read_text().splitlines()[-1]); assert report['passed'] is True and report['count'] == 9
    atomic(P / 'logs/rlt-cpu-check.json', report)
    receipt = P / 'logs/owner-cpu-check.json'
    run([RLT_PYTHON, '-u', '-B', str(rlt / 'check_owner_sz1_cpu.py'), '--owner', str(rlt / 'owner_sz1.py'), '--receipt', str(receipt)], 'owner-cpu')
    report = read(receipt); assert report['passed'] is True and report['tests'] == 8
    for model in ('openwam', 'pi05'):
        source = P / 'scripts/lanes' / model
        path = run([str(P / 'envs/RoboDojo/bin/python'), '-u', '-B', str(P / 'scripts/lanes/test_single_gpu_lane.py'), '-v'],
                   model + '-lane-cpu', {'PYTHONPATH': str(source)})
        output = path.read_text(); match = re.search(r'Ran (\d+) tests? in ', output)
        assert match and int(match.group(1)) >= 10 and re.search(r'\nOK\s*$', output), str(path)
        atomic(OUT / (model + '-lane-cpu.json'), {'passed': True, 'tests': int(match.group(1)),
            'source_sha256': {p.name: digest(p) for p in source.glob('*.py')}, 'gpu_used': False, 'log': str(path)})


def plans():
    ports = []
    result = {}
    for gpu in (4, 5, 6, 7):
        model = 'openwam' if gpu < 6 else 'pi05'
        cfg = read(P / f'scripts/lanes/configs/gpu{gpu}.json')
        assert cfg['run_id'] == RUNS[model] and cfg['lane_gpu'] == gpu and cfg['workers_per_gpu'] == 1
        path = run([str(Path(cfg['policy_env']) / 'bin/python'), '-u', '-B',
            str(P / 'scripts/lanes' / model / 'dojo_sweep.py'), '--config', str(P / f'scripts/lanes/configs/gpu{gpu}.json'), '--plan-only'], f'gpu{gpu}-plan')
        plan = read(path)
        assert len(plan['tasks']) == len(set(plan['tasks'])) == 54 and plan['seeds'] == [0, 1, 2]
        assert plan['episode_total'] == 6300 and sum(plan['budgets'].values()) == 2100 and plan['num_envs'] == 4
        assert plan['workers_per_gpu'] == 1 and len(plan['groups']) == 8
        mapping = [4, 4, 5, 5, 4, 4, 5, 5] if model == 'openwam' else [6, 6, 7, 7, 6, 6, 7, 7]
        assert [row['gpu'] for row in plan['groups']] == mapping
        lane = [row for row in plan['groups'] if row['gpu'] == gpu]; assert len(lane) == 4
        ports.extend(int(row['port']) for row in lane)
        atomic(OUT / f'gpu{gpu}-plan.json', plan); result[gpu] = plan
    assert len(ports) == len(set(ports)) == 16
    for port in ports:
        with socket.socket() as check:
            check.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); check.bind(('127.0.0.1', port))
    atomic(OUT / 'plans-verified.json', {'passed': True, 'gpus': [4, 5, 6, 7], 'ports': ports,
        'full_model_episodes': 6300, 'n_envs': 4, 'workers_per_gpu': 1})
    return result


def audit_model(model):
    sys.path.insert(0, str(P / 'scripts/lanes' / model))
    from resume_results import prepare_result
    from dojo_sweep import result_check
    plan = read(OUT / f"gpu{4 if model == 'openwam' else 6}-plan.json")
    repo = P / 'RoboDojo'; archive = OUT / 'resume-archive' / model
    policy = 'OpenWAM' if model == 'openwam' else 'Pi_05'
    info = 'ckpt_name=OpenWAM-Alpha-Sim-RoboDojo,action_type=ee' if model == 'openwam' else 'ckpt_name=sim,action_type=joint'
    old_repo = Path('/srv/research/projects/robodojo-openwam' + ('' if model == 'openwam' else '-sz3')) / 'RoboDojo'
    source_report = read(IMPORT / f"results-{'sz2' if model == 'openwam' else 'sz3'}-ready.json")
    assert source_report['all_sizes_verified'] is True and source_report['no_result_values_changed'] is True
    assert source_report['run_id'] == RUNS[model] and source_report['policy'] == policy
    rows = []
    for seed in (0, 1, 2):
        for task in plan['tasks']:
            run_id = f'{RUNS[model]}_s{seed}_{task}'
            base = repo / f'eval_result/RoboDojo/{task}/{policy}/arx_x5/{seed}_{info}'
            result = base / run_id / '_result.json'; resume = base / f'_resume_{run_id}.json'
            before = digest(result) if result.exists() else None
            if resume.exists():
                original = resume.read_bytes(); manifest = json.loads(original)
                # Native prepare_result skips the manifest after a full budget;
                # explicitly reconcile it here even for an already complete task.
                assert result.exists(), 'Resume manifest without original result'
                actual = read(result); details = actual['details']; count = actual['eval_time']
                assert manifest['run_id'] == run_id and manifest['task_name'] == task
                assert manifest['policy_name'] == policy and manifest['config_name'] == 'arx_x5'
                assert manifest['eval_seed'] == seed and manifest['details'] == details
                successes = sum(row['success'] for row in details.values())
                assert manifest['success_nums'] == successes and manifest['fail_nums'] == count - successes
                assert math.isclose(manifest['total_score'], math.fsum(row['score'] for row in details.values()), abs_tol=1e-6)
                layout_ids = sorted(row['layout_id'] for row in details.values())
                assert sorted(manifest['completed_layout_ids']) == layout_ids
                assert not set(manifest.get('abandoned_layout_ids', [])) & set(layout_ids)
                save_dir = Path(manifest['save_dir'])
                if save_dir.is_absolute() and save_dir.is_relative_to(old_repo):
                    relative = save_dir.relative_to(old_repo)
                    assert (repo / relative).resolve() == result.parent.resolve(), 'Old resume path suffix differs'
                    saved = OUT / 'resume-rebase-originals' / model / f'seed{seed}' / task / 'resume-original.json'
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    with saved.open('xb') as stream: stream.write(original)
                    changed = dict(manifest, save_dir=str(result.parent.relative_to(repo)))
                    assert {key: value for key, value in changed.items() if key != 'save_dir'} == {key: value for key, value in manifest.items() if key != 'save_dir'}
                    atomic(resume, changed)
                    manifest = changed
                assert (repo / manifest['save_dir']).resolve() == result.parent.resolve(), 'Resume save_dir differs'
            expected = plan['budgets'][task]
            prepared = prepare_result(repo, task, seed, run_id, expected, archive, apply=True)
            assert (digest(result) if result.exists() else None) == before, 'Episode results changed'
            complete = result_check(result, expected)
            if prepared['action'] == 'skip_complete': assert complete['complete'] is True
            else: assert not complete['complete']
            rows.append({**prepared, 'full_budget_complete': complete['complete'], 'result_sha256': before})
    assert len(rows) == 162
    atomic(OUT / (model + '-resume-verified.json'), {'passed': True, 'model': model,
        'run_id': RUNS[model], 'native_budget': 6300, 'tasks_seeds': len(rows),
        'completed_episodes': sum(row.get('episodes', 0) for row in rows),
        'complete_tasks': sum(row['full_budget_complete'] for row in rows), 'rows': rows,
        'result_values_changed': False, 'abandoned_layout_history_fabricated': False})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'preparation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (P / 'deployment-ready.json').exists() and not (P / 'deployment-preparation-failed.json').exists(), 'Preparation already reached a terminal state'
        wait_prerequisites(); source_assets(); checkpoints(); environments(); cpu_checks()
        model_plans = plans()
        for model in ('openwam', 'pi05'):
            run([str(P / 'envs/RoboDojo/bin/python'), '-u', '-B', str(Path(__file__).resolve()), '--audit-model', model], model + '-resume-audit')
            assert read(OUT / (model + '-resume-verified.json'))['passed'] is True
        spec = importlib.util.spec_from_file_location('owner_readiness_contract', P / 'scripts/rlt/owner_sz1.py')
        owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
        paths = set(owner.required_files(P)) | {Path(__file__).resolve(), P / 'project-env.sh', P / 'scripts/pip_compatibility.py'}
        paths.update(P / 'scripts/rlt' / name for name in ('check_owner_sz1_cpu.py', 'check_rlt_cycle_sz1_cpu.py', 'check_prepare_deployment_cpu.py'))
        paths.add(P / 'scripts/check_pip_compatibility_cpu.py')
        paths.add(P / 'scripts/lanes/test_single_gpu_lane.py')
        for directory in (IMPORT, INSTALL, OUT, P / 'runs/full-assets-sz1-20261001'):
            paths.update(directory.glob('*.json'))
        paths.update(P / 'logs' / name for name in ('rlt-cpu-check.json', 'owner-cpu-check.json', 'checkpoint-manifest.json'))
        paths.add(P / 'imports/source/manifest.json')
        paths.add(P / 'RoboDojo/XPolicyLab/policy/Pi_05/openpi/uv.lock')
        paths.add(P / 'scripts/openwam-source-constraints.txt')
        paths.add(P / 'scripts/sim-source-constraints.txt')
        for model in ('sim', 'openwam', 'pi05'):
            paths.add(P / 'logs' / (model + '-pip-check.txt')); paths.add(P / 'logs' / (model + '-pip-freeze.txt'))
            paths.add(P / 'logs' / (model + '-pip-check.exit')); paths.add(P / 'logs' / (model + '-pip-compatibility.json'))
        for plan in model_plans.values(): paths.update(Path(path) for path in plan['source_sha256'])
        for seed in range(3):
            checkpoint = P / f'checkpoints/Pi_05/RoboDojo-sim-arx_x5-joint-{seed}/59999'
            paths.add(checkpoint / '.download-pi05/manifest.json'); paths.add(checkpoint / 'pi05-inference-ready.json')
        payload = {'ready': True, 'host': 'admin', 'uid': 1003, 'created_at': time.time(),
            'checks': [{'name': name, 'passed': True} for name in sorted(owner.CHECKS)],
            'files': [{'path': str(checked(path)), 'sha256': digest(path)} for path in sorted(paths)],
            'gpu_execution': False, 'rlt_mutated': False, 'ray_mutated': False,
            'model_episodes': 6300, 'seeds': [0, 1, 2], 'gpus': [4, 5, 6, 7]}
        owner.validate_ready(P, payload)
        atomic(P / 'deployment-ready.json', payload)
        log('deployment_ready', path=str(P / 'deployment-ready.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--audit-model', choices=('openwam', 'pi05'))
    args = parser.parse_args()
    assert os.getuid() == 1003 and socket.gethostname() == 'admin', 'Wrong host/account'
    if args.audit_model:
        audit_model(args.audit_model); sys.exit(0)
    if args.launch:
        OUT.mkdir(parents=True, exist_ok=True)
        assert not (OUT / 'pid.json').exists(), 'Preparation launch already recorded'
        with (OUT / 'stdout.log').open('xb') as stream:
            child = subprocess.Popen([sys.executable, '-u', '-B', str(Path(__file__).resolve())],
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        fields = (Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        atomic(OUT / 'pid.json', {'pid': child.pid, 'uid': 1003, 'start_ticks': int(fields[19]),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'script_sha256': digest(__file__)})
        print(json.dumps({'launched': True, 'pid': child.pid, 'directory': str(OUT)})); sys.exit(0)
    try:
        main(); (OUT / 'exit.txt').write_text('0\n')
    except BaseException as error:
        atomic(P / 'deployment-preparation-failed.json', {'ready': False, 'time': time.time(),
            'error_type': type(error).__name__, 'error': str(error), 'gpu_execution': False,
            'rlt_mutated': False, 'ray_mutated': False})
        (OUT / 'exit.txt').write_text('1\n'); raise
