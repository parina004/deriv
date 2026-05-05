import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RISK_FILE = "risk_analysis.json"
OUTPUT_FILE = "operator_overrides.json"
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}


def run(risk_path: str = RISK_FILE, output_path: str = OUTPUT_FILE) -> dict:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    clauses = data["clauses"]

    print("\n" + "=" * 70)
    print("OPERATOR REVIEW — Stage 1 Risk Scores")
    print("=" * 70)
    print(f"  {'#':<6} {'Title':<30} {'Category':<25} {'Severity'}")
    print("-" * 70)
    for c in clauses:
        print(f"  {c['clause_number']:<6} {c['clause_title']:<30} {c['risk_category']:<25} {c['severity'].upper()}")
    print("=" * 70)

    overrides = {}

    print("\nAre there any clauses whose severity you want to override before")
    print("generating the negotiation brief?")
    print("Enter clause number and new severity (e.g. '2 high'), or press Enter to continue.\n")

    while True:
        try:
            entry = input("Override> ").strip()
        except EOFError:
            break

        if not entry:
            break

        parts = entry.split()
        if len(parts) != 2:
            print("  Format: <clause_number> <severity>  e.g. '3 high'")
            continue

        clause_num, new_severity = parts[0], parts[1].lower()

        clause_numbers = {c["clause_number"] for c in clauses}
        if clause_num not in clause_numbers:
            print(f"  Clause '{clause_num}' not found. Valid numbers: {sorted(clause_numbers)}")
            continue

        if new_severity not in ALLOWED_SEVERITIES:
            print(f"  Invalid severity '{new_severity}'. Allowed: {sorted(ALLOWED_SEVERITIES)}")
            continue

        old_severity = next(c["severity"] for c in clauses if c["clause_number"] == clause_num)
        overrides[clause_num] = {
            "original_severity": old_severity,
            "override_severity": new_severity,
        }
        print(f"  Clause {clause_num}: {old_severity} -> {new_severity}")

    Path(output_path).write_text(json.dumps({"overrides": overrides}, indent=2), encoding="utf-8")

    if overrides:
        print(f"\n[review] {len(overrides)} override(s) saved -> {output_path}")
    else:
        print(f"\n[review] No overrides. Continuing with original scores -> {output_path}")

    return overrides


if __name__ == "__main__":
    run()
