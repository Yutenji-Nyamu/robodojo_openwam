"""Check the curated public evidence, without simulator/model dependencies."""
from pathlib import Path
import csv
import json
import math


def main():
    root = Path(__file__).resolve().parent.parent
    evidence = root / 'evidence'
    runs = {}
    for path in sorted((evidence / 'runs').glob('*/summary.json')):
        run = json.loads(path.read_text(encoding='utf-8'))
        runs[run['run_id']] = run
        if run['status'] == 'complete':
            result = json.loads((path.parent / 'result.json').read_text(encoding='utf-8'))
            assert len(result['details']) == run['episodes'] == result['eval_time']
            assert sum(bool(row['success']) for row in result['details'].values()) == run['successes']
        else:
            assert run['episodes'] is None and run['successes'] is None
            assert not (path.parent / 'result.json').exists()
        counts = run['steps']['episode_step_counts_by_env']
        assert sum(sum(v) for v in counts.values()) == run['steps']['total_control_steps']
        with (path.parent / 'resources.csv').open(encoding='utf-8', newline='') as handle:
            samples = list(csv.DictReader(handle))
        for role, stats in run['gpu'].items():
            assert max(int(x['memory_mib']) for x in samples if x['gpu_role'] == role) == stats['whole_run']['peak_memory_mib']
        assert math.isclose(max(float(x['tree_rss_kib']) for x in samples) / 1024**2,
                            run['process_tree_rss_peak_gib'], rel_tol=1e-9)
    groups = json.loads((evidence / 'groups.json').read_text(encoding='utf-8'))
    for group in groups:
        members = [runs[name] for name in group['run_ids']]
        assert all(x['status'] == 'complete' for x in members)
        assert sum(x['episodes'] for x in members) == group['total_episodes']
        steps = sum(x['steps']['total_control_steps'] for x in members)
        assert steps == group['total_control_steps']
        window = group.get('observed_action_window_seconds')
        if window:
            rebuilt_window = max(x['action_window']['last_observed_group_elapsed_s'] for x in members) - min(
                x['action_window']['first_observed_group_elapsed_s'] for x in members)
            assert math.isclose(rebuilt_window, window)
            rate = steps / window / group['physical_gpu_count']
            assert math.isclose(rate, group['control_steps_per_second_per_physical_gpu'])
            for average, hours in group['scenario_eta_four_gpus_hours'].items():
                assert math.isclose(float(average) * 6300 / (4 * rate) / 3600, hours)
    print(json.dumps({'runs_checked': len(runs), 'groups_checked': len(groups),
                      'complete_runs': sum(x['status'] == 'complete' for x in runs.values()),
                      'completed_probe_episodes': sum(x['episodes'] or 0 for x in runs.values()),
                      'note': 'Probe episodes include repeated layouts; not a benchmark success rate.'}))


if __name__ == '__main__':
    main()
