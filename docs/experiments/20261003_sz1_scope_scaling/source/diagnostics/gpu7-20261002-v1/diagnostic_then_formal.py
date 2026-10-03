"""One independent GPU7 diagnostic, then exec the unchanged formal lane.

The existing owner must already have protected/stopped its GPU7 RLT. This
adapter reuses Sweep launch/process guards and the owner's read-only health
function; it neither stops/restores RLT nor resets a GPU.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import socket
import sys
import time

TASK = "store_laptop_and_headphones_random"
INFO = "ckpt_name=sim,action_type=joint"
DEADLINE_SECONDS = 1200


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def diagnostic_shell(source, repo, entry):
    """Keep the current eval shell verbatim except its two relocated paths."""
    changes = {
        'PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"':
            "PROJECT_ROOT=" + shlex.quote(str(repo)),
        "sim_cmd=(python -u src/eval_client/main.py)":
            "sim_cmd=(python -u " + shlex.quote(str(entry)) + ")",
    }
    for before, after in changes.items():
        if source.count(before) != 1:
            raise ValueError("Current eval_policy.sh anchor differs: " + before)
        source = source.replace(before, after)
    return source


def require_completed_batch(exit_code, terminal, check):
    if (exit_code != 85 or terminal.get("exit_code") != 85
            or terminal.get("kind") != "diagnostic_complete"
            or terminal.get("reason") != "first_batch_returned_normally"
            or terminal.get("action", 0) < 1 or terminal.get("tick", 0) < 1
            or check.get("complete") is not True
            or sorted(check.get("layout_ids", [])) != [0, 1, 2, 3]):
        raise RuntimeError("Diagnostic did not prove normal first batch with actions/layouts0-3")


def drain(monitor, log, result):
    end = log.stat().st_size if log.is_file() else 0
    while monitor.offset < end:
        monitor.poll(log, result, time.monotonic())
    monitor.observe(monitor.carry, None, time.monotonic())


def diagnose(sweep, api, health, diag_id, entry):
    from eval_recovery import Progress
    work = sweep.run / "diagnostics" / diag_id
    work.mkdir(parents=True, exist_ok=False)
    trace = work / "trace"
    client_id, server_id = diag_id, diag_id + "-server"
    result = (sweep.repo / "eval_result/RoboDojo" / TASK / "Pi_05/arx_x5"
              / ("0_" + INFO) / diag_id / "_result.json")
    if result.parent.exists():
        raise RuntimeError("Diagnostic result identity already exists")
    groups = [g for g in sweep.plan["groups"] if g["gpu"] == 7
              and any(t["task"] == TASK for t in g["tasks"])]
    if len(groups) != 1:
        raise RuntimeError("Expected the original GPU7 laptop partition")
    port = int(groups[0]["port"])
    copied_shell = work / "eval_policy-trace.sh"
    copied_shell.write_text(diagnostic_shell(
        (sweep.repo / "scripts/eval_policy.sh").read_text(), sweep.repo, entry))
    server_command = [
        "bash", "scripts/robodojo.sh", "server", "--policy-dir", "XPolicyLab/policy/Pi_05",
        "--task", TASK, "--ckpt", "sim", "--env-cfg", "arx_x5", "--action-type", "joint",
        "--seed", "0", "--policy-env", "uv", "--policy-gpu", "7",
        "--policy-port", str(port), "--bind-host", "127.0.0.1"]
    client_command = [
        "env", "DOJO_DIAGNOSTIC_TRACE=" + str(trace),
        "DOJO_DIAGNOSTIC_MAX_BYTES=1073741824", "DOJO_DIAGNOSTIC_MAX_SECONDS=1200",
        "bash", str(copied_shell), "--root_dir", str(sweep.repo), "--task_name", TASK,
        "--env_cfg_type", "arx_x5", "--device_id", "7", "--policy_name", "Pi_05",
        "--port", str(port), "--host", "127.0.0.1", "--protocol", "ws",
        "--additional_info", INFO, "--seed", "0"]
    receipt = {"diagnostic_id": diag_id, "gpu": 7, "formal_run_id": sweep.cfg["run_id"],
               "additional_info": INFO, "result": str(result), "trace": str(trace),
               "server_command": server_command, "client_command": client_command,
               "state": "DIAGNOSTIC_FAILED", "exit_code": 86}
    status_path = work / "transition.json"
    api.atomic_json(status_path, receipt)
    server = client = None
    passed = False
    try:
        sweep.verify_sources()
        if sweep.guard.scan():
            raise RuntimeError("Formal lane still has owned processes")
        receipt["gpu_before"] = health(7, sweep.cfg.get("idle_gpu_memory_mib", 512))
        with socket.socket() as check_port:
            check_port.bind(("127.0.0.1", port))
        sweep.wait_checkpoint(0)
        deadline = time.monotonic() + DEADLINE_SECONDS
        server = sweep.launch(server_command, server_id, "server", 7,
                              sweep.cfg["sim_env"], work / "server")
        sweep.wait_server(server, port)
        if sweep.stop.is_set() or time.monotonic() >= deadline:
            raise RuntimeError("Diagnostic interrupted or exceeded external deadline")
        client = sweep.launch(client_command, client_id, "client", 7,
                              sweep.cfg["sim_env"], work / "client")
        client_log, server_log = Path(client.dojo_log_path), Path(server.dojo_log_path)
        monitors = [(Progress(time.monotonic()), client_log),
                    (Progress(time.monotonic()), server_log)]
        while client.poll() is None:
            if sweep.stop.wait(1) or time.monotonic() >= deadline:
                raise RuntimeError("Diagnostic interrupted or exceeded external 1200s deadline")
            if server.poll() is not None:
                raise RuntimeError("Diagnostic policy server exited")
            for monitor, log in monitors:
                monitor.poll(log, result, time.monotonic())
                if monitor.fatal:
                    raise RuntimeError("GPU fatal in diagnostic; no formal launch")
        if server.poll() is not None:
            raise RuntimeError("Policy server exited before diagnostic acceptance")
        for monitor, log in monitors:
            drain(monitor, log, result)
        if any(monitor.fatal for monitor, _ in monitors):
            raise RuntimeError("GPU fatal in final log bytes; no formal launch")
        terminal = json.loads((trace / "terminal.json").read_text())
        checked = api.result_check(result, 4)
        receipt.update(client_exit_code=client.returncode, terminal=terminal, result_check=checked)
        require_completed_batch(client.returncode, terminal, checked)
        passed = True
    except Exception as exc:
        receipt["error"] = repr(exc)
    finally:
        receipt["cleanup"] = []
        for run_id, process in ((client_id, client), (server_id, server)):
            try:
                receipt["cleanup"].append(sweep.guard.cleanup(run_id, "diagnostic_finished"))
                if process is not None:
                    process.wait(timeout=10)
            except Exception as exc:
                passed = False
                receipt.setdefault("cleanup_errors", []).append(repr(exc))
        try:
            clear, released, snapshot, error = sweep.release_status()
            receipt.update(processes_clear=clear, gpu_released=released,
                           gpu_snapshot=snapshot, release_error=error)
            if not clear or not released or error:
                raise RuntimeError("Diagnostic GPU/process release not confirmed")
            if passed:
                receipt["gpu_after"] = health(7, sweep.cfg.get("idle_gpu_memory_mib", 512))
                sweep.verify_sources()
        except Exception as exc:
            passed = False
            receipt["release_or_health_error"] = repr(exc)
        if sweep.stop.is_set():
            passed = False
            receipt["interrupted"] = True
        receipt.update(state="READY_FOR_FORMAL" if passed else "DIAGNOSTIC_FAILED",
                       exit_code=0 if passed else 86, finished_at=time.time())
        api.atomic_json(status_path, receipt)
    return passed, status_path, receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sweep-script", required=True, type=Path)
    parser.add_argument("--owner-source", required=True, type=Path)
    parser.add_argument("--diagnostic-id", required=True)
    parser.add_argument("--run-trace", type=Path, default=Path(__file__).with_name("run_trace.py"))
    args = parser.parse_args(argv)
    if not re.fullmatch(r"diag-gpu7-[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", args.diagnostic_id):
        raise ValueError("A fresh diag-gpu7- identifier is required")
    args.config, args.sweep_script = args.config.resolve(), args.sweep_script.resolve()
    args.owner_source, args.run_trace = args.owner_source.resolve(), args.run_trace.resolve()
    original_config = args.config.read_bytes()
    cfg = json.loads(original_config)
    if cfg["lane_gpu"] != 7 or not args.run_trace.is_file():
        raise ValueError("Only the existing GPU7 formal lane is permitted")
    sys.path.insert(0, str(args.sweep_script.parent))
    api = load_module(args.sweep_script, "dojo_sweep")
    health = load_module(args.owner_source, "dojo_diagnostic_health").gpu_health
    plan = api.build_plan(cfg)
    sweep = api.Sweep(cfg, plan)
    with (sweep.run / "controller.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, lambda _s, _f: sweep.stop.set())
        passed, status, receipt = diagnose(sweep, api, health, args.diagnostic_id, args.run_trace)
        if not passed:
            return 86
        if args.config.read_bytes() != original_config or sweep.stop.is_set():
            receipt.update(state="DIAGNOSTIC_FAILED", exit_code=86,
                           error="Formal configuration changed or adapter interrupted")
            api.atomic_json(status, receipt)
            return 86
    formal = [sys.executable, str(args.sweep_script), "--config", str(args.config)]
    receipt.update(state="EXECUTING_FORMAL", formal_command=formal)
    api.atomic_json(status, receipt)
    # Replacement preserves the outer owner's controller PID/ownership.
    try:
        os.execv(sys.executable, formal)
    except Exception as exc:
        receipt.update(state="FORMAL_EXEC_FAILED", exit_code=86, error=repr(exc))
        api.atomic_json(status, receipt)
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"state": "DIAGNOSTIC_ADAPTER_ERROR", "exit_code": 86,
                          "error": repr(exc)}), file=sys.stderr, flush=True)
        sys.exit(86)
