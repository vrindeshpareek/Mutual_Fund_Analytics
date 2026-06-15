"""
run_pipeline.py — Bluestock Fintech MF Capstone | Master Execution Script
==========================================================================
Single entry-point that orchestrates the complete data pipeline in the
correct dependency order:

    Step 1  data_ingestion.py        — load & profile all 10 raw CSVs
    Step 2  live_nav_fetch.py        — fetch live NAV from mfapi.in
    Step 3  data_cleaning_sql.py     — clean data + build SQLite DB
    Step 4  generate_eda.py          — produce 15+ EDA charts & notebook
    Step 5  generate_performance.py  — compute risk metrics & scorecard

Each step is timed and its exit-code is checked.  The pipeline halts
immediately if any step fails so downstream scripts never run on broken
data.

Usage
-----
    python run_pipeline.py                     # run all 5 steps
    python run_pipeline.py --skip-fetch        # skip live API fetch (offline)
    python run_pipeline.py --steps 3 4 5      # run only steps 3, 4, 5
    python run_pipeline.py --dry-run           # print plan, do not execute

Options
-------
    --skip-fetch    Skip Step 2 (live_nav_fetch) — useful when offline or
                    when the mfapi.in API is temporarily unavailable.
    --steps N …     Run only the listed step numbers (1-indexed, space-separated).
    --dry-run       Print the execution plan without running anything.

Exit codes
----------
    0   All selected steps completed successfully.
    1   One or more steps failed (step number and error shown).


    ══════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent

STEPS: list[dict] = [
    {
        "number": 1,
        "label": "Data Ingestion",
        "script": PROJECT_ROOT / "data_ingestion.py",
        "description": "Load & profile all 10 raw CSV datasets",
        "skippable": False,
    },
    {
        "number": 2,
        "label": "Live NAV Fetch",
        "script": PROJECT_ROOT / "live_nav_fetch.py",
        "description": "Fetch latest NAV from mfapi.in REST API",
        "skippable": True,   # may fail if offline
    },
    {
        "number": 3,
        "label": "Clean + SQLite DB",
        "script": PROJECT_ROOT / "data_cleaning_sql.py",
        "description": "Clean all datasets and load into bluestock_mf.db",
        "skippable": False,
    },
    {
        "number": 4,
        "label": "EDA Charts",
        "script": PROJECT_ROOT / "generate_eda.py",
        "description": "Generate 15+ EDA charts and EDA_Analysis.ipynb",
        "skippable": False,
    },
    {
        "number": 5,
        "label": "Performance Analytics",
        "script": PROJECT_ROOT / "generate_performance.py",
        "description": "Compute Sharpe/VaR/Alpha/Beta and Fund Scorecard",
        "skippable": False,
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
SEP  = "═" * 56
DASH = "─" * 56


def banner(start_time: datetime) -> None:
    """Print the pipeline header banner."""
    print(SEP)
    print("  Bluestock Fintech — MF Analytics Pipeline")
    print(f"  Starting: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)


def run_step(step: dict, step_index: int, total: int) -> tuple[bool, float]:
    """
    Execute a single pipeline step as a subprocess.

    Parameters
    ----------
    step        : dict with keys number, label, script
    step_index  : 1-based position within the selected steps
    total       : total number of selected steps

    Returns
    -------
    (success: bool, elapsed_seconds: float)
    """
    label  = step["label"]
    script = step["script"]

    prefix = f"[Step {step_index}/{total}] {label:<22}"
    print(f"{prefix} ...", end="", flush=True)

    t0 = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - t0

    if result.returncode == 0:
        print(f"\r{prefix}  ✅  done  ({elapsed:.1f} s)")
        return True, elapsed
    else:
        print(f"\r{prefix}  ❌  FAILED ({elapsed:.1f} s)")
        print()
        print("  ── stdout ──────────────────────────────────────")
        for line in (result.stdout or "").strip().splitlines()[-20:]:
            print(f"    {line}")
        print("  ── stderr ──────────────────────────────────────")
        for line in (result.stderr or "").strip().splitlines()[-20:]:
            print(f"    {line}")
        print()
        return False, elapsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Bluestock MF Capstone — master pipeline runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip Step 2 (live NAV fetch from mfapi.in)",
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=range(1, len(STEPS) + 1),
        metavar="N",
        help="Run only the specified step numbers (e.g. --steps 3 4 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the execution plan without running anything",
    )
    return parser.parse_args(argv)


def select_steps(args: argparse.Namespace) -> list[dict]:
    """Return the ordered list of steps to execute based on CLI flags."""
    if args.steps:
        selected = [s for s in STEPS if s["number"] in args.steps]
    else:
        selected = list(STEPS)

    if args.skip_fetch:
        selected = [s for s in selected if s["number"] != 2]

    return selected


def dry_run(selected: list[dict]) -> None:
    """Print the execution plan and exit."""
    print(SEP)
    print("  Bluestock Fintech — MF Analytics Pipeline")
    print("  DRY RUN — no scripts will be executed")
    print(SEP)
    for i, step in enumerate(selected, 1):
        print(f"  Step {i}/{len(selected)}  [{step['number']}] {step['label']}")
        print(f"            {step['description']}")
        print(f"            Script: {step['script'].name}")
        print()
    print(DASH)
    print(f"  {len(selected)} step(s) would run.")
    print(SEP)


# ── Main ──────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    """
    Orchestrate all pipeline steps and return an exit code.

    Returns
    -------
    0 on full success, 1 if any step fails.
    """
    args = parse_args(argv)
    selected = select_steps(args)

    if not selected:
        print("No steps selected. Use --steps N … or remove conflicting flags.")
        return 1

    if args.dry_run:
        dry_run(selected)
        return 0

    start_time = datetime.now()
    banner(start_time)

    total_elapsed = 0.0
    for i, step in enumerate(selected, 1):
        success, elapsed = run_step(step, i, len(selected))
        total_elapsed += elapsed
        if not success:
            print(DASH)
            print(f"  ❌  Pipeline aborted at Step {step['number']} ({step['label']}).")
            print(f"  Fix the error above and re-run:  python run_pipeline.py --steps {step['number']}")
            print(SEP)
            return 1

    print(DASH)
    print(f"  ✅  Pipeline complete — total time: {total_elapsed:.1f} s")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
