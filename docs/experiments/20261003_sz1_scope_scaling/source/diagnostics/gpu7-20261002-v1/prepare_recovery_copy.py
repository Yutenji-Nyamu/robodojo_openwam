"""CPU-only SZ1 GPU7 replay repair, adapted from reviewed EXPO repair_latest.

Create a new checkpoint from the latest saved model/optimizer/RNG/index and
exact matching payloads in its original resume checkpoint. Never stop a
process, mutate either checkpoint, prune an index, or start training.
Large immutable files use hard links on one filesystem; cross-device files
are copied. A failed partial output is preserved and cannot be reused.
"""
import argparse
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil


REPLAY = Path('actor/sac_components/replay_buffer/rank_0')
SMALL = ('sac_components/rlt_trainer_state/complete.json',
         'sac_components/rlt_trainer_state/checkpoint_rank_0.pt',
         'dcp_checkpoint/.metadata',
         'sac_components/replay_buffer/rank_0/metadata.json',
         'sac_components/replay_buffer/rank_0/trajectory_index.json')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def anchor(path):
    stat = Path(path).stat()
    return dict(device=stat.st_dev, inode=stat.st_ino,
                bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)


def own_file(path, helper):
    path = Path(path)
    assert path.resolve().is_relative_to(helper.ROOT.resolve())
    assert not path.is_symlink() and path.is_file()
    assert path.stat().st_uid == helper.UID
    return path


def clone_file(source, dest, before, large):
    """Never alter source permissions/content; hard links require immutability."""
    if large:
        try:
            os.link(source, dest)
            assert anchor(dest) == before and anchor(source) == before
            return 'linked'
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
    shutil.copy2(source, dest)
    assert dest.stat().st_size == before['bytes'] and anchor(source) == before
    if not large:
        assert sha(dest) == sha(source)
    return 'copied'


def sample_payloads(paths):
    import torch
    def tensors(value):
        if isinstance(value, torch.Tensor):
            assert value.numel() > 0
            if value.is_floating_point():
                assert bool(torch.isfinite(value).all()), 'Nonfinite donor tensor'
            return 1
        if isinstance(value, dict):
            return sum(tensors(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return sum(tensors(item) for item in value)
        return 0
    result = []
    for path in paths:
        payload = torch.load(path, map_location='cpu', weights_only=True)
        assert isinstance(payload, dict) and tensors(payload) > 0
        result.append(dict(path=str(path), dictionary_keys=sorted(payload)))
    assert not torch.cuda.is_initialized()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'donor', 'output', 'helper', 'cfg', 'repo'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    spec = importlib.util.spec_from_file_location('frozen_sz1_rlt', args.helper)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    source, donor, output = (path.absolute() for path in
                             (args.source, args.donor, args.output))
    for path in (source, donor, output):
        helper.checked_dir(path)
    own_file(args.helper, helper)
    cfg = helper.config(own_file(args.cfg, helper))
    assert {str(value) for value in cfg['cluster']['component_placement'].values()} == {'7'}
    assert Path(cfg['runner']['resume_dir']).resolve() == donor.resolve(), 'Wrong donor lineage'
    assert source.name == output.name and re.fullmatch(r'global_step_\d+', source.name)
    assert int(source.name.rsplit('_', 1)[1]) > int(donor.name.rsplit('_', 1)[1])
    assert not output.exists() and not output.is_symlink(), 'Use a fresh output'
    for original in (source.resolve(), donor.resolve()):
        assert output.resolve() != original
        assert original not in output.resolve().parents and output.resolve() not in original.parents
    repo = args.repo.resolve()
    assert repo.is_relative_to(helper.ROOT.resolve())
    donor_checked = helper.inspect_checkpoint(donor, cfg, repo)
    metadata = read(own_file(source / REPLAY / 'metadata.json', helper))
    index = read(own_file(source / REPLAY / 'trajectory_index.json', helper))
    mapping, order = index['trajectory_index'], index['trajectory_id_list']
    assert len(order) == len(set(order)) == len(mapping) == metadata['size'] == metadata['total_samples']
    assert {str(item) for item in order} == set(mapping)
    expected = {}
    for tid, entry in mapping.items():
        assert entry['trajectory_id'] == int(tid) and entry['num_samples'] == 1
        model_id = entry['model_weights_id']
        assert isinstance(model_id, str) and re.fullmatch(r'[A-Za-z0-9-]+', model_id)
        expected['trajectory_' + tid + '_' + model_id + '.pt'] = tid
    present = {path.name: own_file(path, helper) for path in (source / REPLAY).glob('trajectory_*.pt')}
    assert set(present) <= set(expected) and all(path.stat().st_size > 0 for path in present.values())
    missing = sorted(set(expected) - set(present))
    assert missing, 'This repair supports missing replay payloads only'
    donor_index = read(donor / REPLAY / 'trajectory_index.json')['trajectory_index']
    rows, uncovered = [], []
    for name in missing:
        tid = expected[name]
        if donor_index.get(tid) != mapping[tid]:
            uncovered.append(name)
            continue
        payload = own_file(donor / REPLAY / name, helper)
        assert payload.stat().st_size > 0
        rows.append(dict(name=name, source=str(payload), source_anchor=anchor(payload),
                         trajectory_entry_sha256=hashlib.sha256(
                             json.dumps(mapping[tid], sort_keys=True).encode()).hexdigest()))
    small = {name: sha(own_file(source / 'actor' / name, helper)) for name in SMALL}
    marker = read(source / 'actor' / SMALL[0])
    assert marker['complete'] is True and marker['saved_runner_step'] == int(source.name.rsplit('_', 1)[1])
    assert marker['rlt_resume_contract_sha256'] == donor_checked['contract_sha256']
    summary = dict(original_checkpoint=str(source), donor_checkpoint=str(donor),
                   recovered_checkpoint=str(output), indexed_samples=len(order),
                   present_payloads=len(present), missing_payloads=len(missing),
                   covered_payloads=len(rows), full_coverage=len(rows) == len(missing),
                   exact_entry_matches=len(rows), uncovered_first=uncovered[:10],
                   original_small_sha256=small, helper_sha256=sha(args.helper),
                   cfg_sha256=sha(args.cfg), donor_small_sha256=donor_checked['small_sha256'])
    print(json.dumps(dict(phase='coverage_before_clone', **summary)), flush=True)
    assert summary['full_coverage'], 'No complete exact-entry donor coverage; nothing cloned'
    selected = sorted({0, len(rows) // 2, len(rows) - 1})
    samples = sample_payloads([Path(rows[i]['source']) for i in selected])
    output.mkdir(parents=True, mode=0o700)
    helper.save(output / 'repair-plan.json', dict(**summary, payload_sources=rows))
    originals, counts = [], {'linked': 0, 'copied': 0}
    for path in sorted(source.rglob('*')):
        assert not path.is_symlink(), 'Symlink in source checkpoint'
        dest = output / path.relative_to(source)
        if path.is_dir():
            dest.mkdir(exist_ok=True, mode=0o700)
            continue
        path = own_file(path, helper)
        before = anchor(path)
        originals.append((path, before))
        large = path.name.startswith('trajectory_') and path.suffix == '.pt' or before['bytes'] >= 1048576
        counts[clone_file(path, dest, before, large)] += 1
    for row in rows:
        path = Path(row['source'])
        assert anchor(path) == row['source_anchor']
        counts[clone_file(path, output / REPLAY / row['name'], row['source_anchor'], True)] += 1
    for path, before in originals:
        assert anchor(path) == before, 'Original changed during clone'
    for row in rows:
        assert anchor(row['source']) == row['source_anchor'], 'Donor changed during clone'
    for name, digest in small.items():
        assert sha(source / 'actor' / name) == sha(output / 'actor' / name) == digest
    for name, digest in donor_checked['small_sha256'].items():
        assert sha(donor / 'actor' / name) == digest, 'Frozen donor metadata changed'
    checked = helper.inspect_checkpoint(output, cfg, repo)
    import torch
    assert checked['gpu_used_for_check'] is False and not torch.cuda.is_initialized()
    manifest = dict(**summary, complete=True, validated_at=helper.now(),
                    payload_sources=rows, sampled_payloads=samples, clone_counts=counts,
                    original_file_count=len(originals), checked=checked,
                    source_unchanged=True, donor_unchanged=True, indices_pruned=False)
    helper.save(output / 'repair-manifest.json', manifest)
    print(json.dumps(dict(phase='complete', checkpoint=str(output), step=checked['step'],
                         indexed_samples=checked['replay_samples'], filled_payloads=len(rows),
                         cuda_initialized=False, source_unchanged=True, donor_unchanged=True)), flush=True)


if __name__ == '__main__':
    main()
