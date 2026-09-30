"""Target-server CPU checks for the candidate, with no simulator/model launch.

Copy beside the candidate controller and its reviewed runtime imports, then run
with the server's simulator Python. Do not run project tests on Windows.
"""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

import dojo_sweep


class TestGpuLanes(unittest.TestCase):
    def sweep(self):
        value = dojo_sweep.Sweep.__new__(dojo_sweep.Sweep)
        value.stop = threading.Event()
        value.gpu_slots = {gpu: threading.Lock() for gpu in (4, 5, 6, 7)}
        value.plan = {"groups": [
            {"worker": worker, "gpu": 4 + worker // 2, "port": 63080 + worker,
             "tasks": [{"task": "task" + str(worker)}]}
            for worker in range(8)]}
        value.event = lambda *args, **kwargs: None
        value.wait_checkpoint = lambda seed: None
        return value

    def test_idle_lane_crosses_seed_while_other_gpu_is_still_busy(self):
        sweep = self.sweep()
        busy = threading.Event()
        fast_started_next_seed = threading.Event()
        def body(seed, group):
            if seed == 0 and group["worker"] == 2:
                busy.set()
                if not fast_started_next_seed.wait(3):
                    raise AssertionError("idle GPU waited for another GPU's seed")
            if seed == 1 and group["worker"] == 0:
                self.assertTrue(busy.wait(3))
                fast_started_next_seed.set()
        sweep.worker_body = body
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(sweep.gpu_lane, gpu) for gpu in (4, 5)]
            for future in futures:
                future.result(timeout=5)
        self.assertTrue(fast_started_next_seed.is_set())

    def test_original_worker_gpu_ports_and_each_seed_are_retained_once(self):
        sweep = self.sweep()
        calls = []
        def body(seed, group):
            calls.append((seed, group["worker"], group["gpu"], group["port"]))
        sweep.worker_body = body
        for gpu in (4, 5, 6, 7):
            sweep.gpu_lane(gpu)
        expected = {(seed, worker, 4 + worker // 2, 63080 + worker)
                    for seed in dojo_sweep.SEEDS for worker in range(8)}
        self.assertEqual(len(calls), 24)
        self.assertEqual(set(calls), expected)
        for gpu in (4, 5, 6, 7):
            self.assertEqual([seed for seed, worker, card, port in calls if card == gpu],
                             [0, 0, 1, 1, 2, 2])

    def test_checkpoint_for_current_seed_is_verified_before_pi05_work(self):
        if not hasattr(dojo_sweep.Sweep, "wait_checkpoint"):
            self.skipTest("OpenWAM checkpoint preflight has no per-seed manifest")
        sweep = self.sweep()
        current = []
        sweep.wait_checkpoint = lambda seed: current.append(seed)
        def body(seed, group):
            self.assertTrue(current)
            self.assertEqual(current[-1], seed)
        sweep.worker_body = body
        sweep.gpu_lane(4)
        self.assertEqual(current, [0, 1, 2])

    def test_stop_after_first_group_prevents_later_groups_and_seeds(self):
        sweep = self.sweep()
        calls = []
        def body(seed, group):
            calls.append((seed, group["worker"]))
            sweep.stop.set()
        sweep.worker_body = body
        sweep.gpu_lane(4)
        self.assertEqual(calls, [(0, 0)])

    def test_missing_or_duplicate_original_group_fails_before_launch(self):
        for groups in ([{"gpu": 4, "worker": 0}],
                       [{"gpu": 4, "worker": 0}, {"gpu": 4, "worker": 0}]):
            sweep = self.sweep()
            sweep.plan = {"groups": groups}
            sweep.worker_body = lambda *args: self.fail("must not launch")
            with self.assertRaisesRegex(RuntimeError, "two distinct groups"):
                sweep.gpu_lane(4)


if __name__ == "__main__":
    unittest.main()
