"""Use the original Dojo CLI with an independent first-batch trace.

Run from the existing RoboDojo repository, using the original client Python,
environment, CLI options and policy server. This file never starts a server,
owns a GPU, retries a client, or edits production code.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import sys
import traceback

from trace_hook import wrap_factory


def validate_entry():
    parser = argparse.ArgumentParser(add_help=False)
    for name in ("task_name", "policy_name", "env_cfg_type", "additional_info"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--num_envs", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    args, _ = parser.parse_known_args()
    if (args.task_name != "store_laptop_and_headphones_random"
            or args.policy_name != "Pi_05" or args.env_cfg_type != "arx_x5"
            or args.num_envs != 4 or args.seed != 0
            or args.additional_info != "ckpt_name=sim,action_type=joint"):
        raise ValueError("Requires independent Pi_05/arx_x5/N4/seed0 laptop diagnostic")
    run_id = os.environ.get("ROBODOJO_RUN_ID", "")
    if not re.fullmatch(r"diag-gpu7-[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", run_id):
        raise ValueError("A fresh diag-gpu7- run ID is required")
    output = Path(os.environ["DOJO_DIAGNOSTIC_TRACE"])
    if not output.is_absolute() or output.exists():
        raise ValueError("DOJO_DIAGNOSTIC_TRACE must be a new absolute directory")
    repository = Path.cwd()
    if not (repository / "src/eval_client/main.py").is_file():
        raise ValueError("Run from the existing RoboDojo repository root")
    # Only this independent diagnostic process receives the four-layout cap.
    os.environ["EVAL_NUM"] = "4"
    os.environ["ROBODOJO_MAX_BASH_RETRIES"] = "1"
    return repository


def main():
    repository = validate_entry()
    sys.path.insert(0, str(repository))
    # Import initializes the original CLI/AppLauncher once, without calling
    # its __main__ block. It is not safe to import this module in CPU tests.
    client = importlib.import_module("src.eval_client.main")
    os.environ["ROBODOJO_FATAL_RESTART_COUNT"] = str(client.MAX_INPROC_RESTARTS)
    traced_factory = wrap_factory(client.create_eval_env)

    def create_first_batch(*args, **kwargs):
        if kwargs.get("resume_state") is not None:
            raise ValueError("Diagnostic cannot resume or reuse existing results")
        env = traced_factory(*args, **kwargs)
        reset = env.reset

        def reset_once(*reset_args, **reset_kwargs):
            try:
                return reset(*reset_args, **reset_kwargs)
            except Exception as exc:
                # Keep sampling disabled during normal offscreen reset, but
                # prevent main's exception handlers from advancing any seed.
                env._dojo_diagnostic_trace.failed("reset", exc)

        env.reset = reset_once
        return env

    client.create_eval_env = create_first_batch
    client.main()
    # A healthy diagnostic exits 85 inside its first run_eval. A normal return
    # here means it never completed the expected observed first batch.
    raise RuntimeError("Original main returned without a diagnostic terminal")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        # Startup/import failures can occur before Trace creates its directory.
        # Keep their receipt separate, so they never look like physics evidence.
        output = os.environ.get("DOJO_DIAGNOSTIC_TRACE")
        if output:
            receipt = Path(output + ".entrypoint-failure.json")
            try:
                receipt.parent.mkdir(parents=True, exist_ok=True)
                with receipt.open("x", encoding="utf-8") as stream:
                    json.dump({"kind": "entrypoint_failed", "exit_code": 86,
                               "exception_type": type(exc).__name__,
                               "exception": str(exc)}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
            except Exception:
                traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(86)
