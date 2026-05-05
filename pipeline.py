import argparse
import json
import sys
from pathlib import Path

STAGES = [
    "INIT",
    "INPUTS_LOADED",
    "CLAUSES_EXTRACTED",
    "CLAUSES_RISK_SCORED",
    "CRITICAL_CLAUSES_ANALYSED",
    "OPERATOR_REVIEW_COMPLETE",
    "NEGOTIATION_BRIEF_GENERATED",
    "OPTIONAL_OUTPUTS_GENERATED",
    "VALIDATION_COMPLETE",
    "RESULTS_FINALISED",
]

STATE_FILE = "pipeline_state.json"
ARTIFACTS = [
    "extracted_clauses.json",
    "risk_analysis.json",
    "operator_overrides.json",
    "negotiation_brief.md",
    "redlined_contract.md",
    "llm_calls.jsonl",
]


def read_state() -> str:
    if Path(STATE_FILE).exists():
        return json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))["state"]
    return "INIT"


def write_state(state: str):
    Path(STATE_FILE).write_text(
        json.dumps({"state": state}, indent=2), encoding="utf-8"
    )
    print(f"[pipeline] State -> {state}")


def assert_state(required: str):
    current = read_state()
    if STAGES.index(current) < STAGES.index(required):
        print(f"[pipeline] ERROR: Expected state '{required}' but current is '{current}'.")
        sys.exit(1)


def clear_artifacts():
    for path in ARTIFACTS + [STATE_FILE]:
        if Path(path).exists():
            Path(path).unlink()
            print(f"[pipeline] Cleared {path}")


def run(fresh: bool = False):
    if fresh:
        print("[pipeline] --fresh: clearing all artifacts and restarting.")
        clear_artifacts()

    state = read_state()
    print(f"[pipeline] Resuming from state: {state}")

    # ── INPUTS_LOADED ────────────────────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("INPUTS_LOADED"):
        for f in ["contract.txt", "risk_framework.json"]:
            if not Path(f).exists():
                print(f"[pipeline] ERROR: Required input file '{f}' not found.")
                sys.exit(1)
        write_state("INPUTS_LOADED")
        state = "INPUTS_LOADED"

    # ── CLAUSES_EXTRACTED ────────────────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("CLAUSES_EXTRACTED"):
        from stages.extract import run as extract
        extract()
        write_state("CLAUSES_EXTRACTED")
        state = "CLAUSES_EXTRACTED"
    else:
        print("[pipeline] Skipping extraction (already done).")

    # ── CLAUSES_RISK_SCORED ──────────────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("CLAUSES_RISK_SCORED"):
        from stages.score import run as score
        score()
        write_state("CLAUSES_RISK_SCORED")
        state = "CLAUSES_RISK_SCORED"
    else:
        print("[pipeline] Skipping risk scoring (already done).")

    # ── CRITICAL_CLAUSES_ANALYSED ────────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("CRITICAL_CLAUSES_ANALYSED"):
        from stages.analyse import run as analyse
        analyse()
        write_state("CRITICAL_CLAUSES_ANALYSED")
        state = "CRITICAL_CLAUSES_ANALYSED"
    else:
        print("[pipeline] Skipping critical analysis (already done).")

    # ── OPERATOR_REVIEW_COMPLETE ─────────────────────────────────────────────
    # Always prompt — operator review is interactive and must not be skipped
    from stages.review import run as review
    review()
    write_state("OPERATOR_REVIEW_COMPLETE")
    state = "OPERATOR_REVIEW_COMPLETE"

    # ── NEGOTIATION_BRIEF_GENERATED ──────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("NEGOTIATION_BRIEF_GENERATED"):
        from stages.brief import run as brief
        brief()
        write_state("NEGOTIATION_BRIEF_GENERATED")
        state = "NEGOTIATION_BRIEF_GENERATED"
    else:
        print("[pipeline] Skipping brief generation (already done).")

    # ── OPTIONAL_OUTPUTS_GENERATED ──────────────────────────────────────────
    if STAGES.index(state) < STAGES.index("OPTIONAL_OUTPUTS_GENERATED"):
        from stages.market_compare import run as market_compare
        market_compare()
        from stages.redline import run as redline
        redline()
        write_state("OPTIONAL_OUTPUTS_GENERATED")
        state = "OPTIONAL_OUTPUTS_GENERATED"
    else:
        print("[pipeline] Skipping optional outputs (already done).")

    # ── VALIDATION_COMPLETE ──────────────────────────────────────────────────
    import subprocess
    print("\n[pipeline] Running validation...")
    result = subprocess.run(
        [sys.executable, "validate.py"], capture_output=False
    )
    if result.returncode != 0:
        print("[pipeline] Validation failed. Fix issues above before finalising.")
        sys.exit(1)
    write_state("VALIDATION_COMPLETE")

    # ── RESULTS_FINALISED ────────────────────────────────────────────────────
    write_state("RESULTS_FINALISED")
    print("\n[pipeline] Pipeline complete. Artifacts produced:")
    for path in ARTIFACTS:
        exists = "OK" if Path(path).exists() else "MISSING"
        print(f"  [{exists}] {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contract risk analysis pipeline")
    parser.add_argument("--fresh", action="store_true", help="Clear all artifacts and restart")
    args = parser.parse_args()
    run(fresh=args.fresh)
