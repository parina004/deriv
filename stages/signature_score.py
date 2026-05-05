import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RISK_FILE = "risk_analysis.json"
OVERRIDES_FILE = "operator_overrides.json"
OUTPUT_FILE = "signature_risk_score.json"

FORMULA = {
    "critical": 25,
    "high": 12,
    "medium": 5,
    "low": 1,
}
MAX_SCORE = 100


def _effective_severity(clause: dict, overrides: dict) -> str:
    if clause["clause_number"] in overrides:
        return overrides[clause["clause_number"]]["override_severity"]
    return clause["severity"]


def _build_justification(score: int, distribution: dict, critical_titles: list) -> str:
    total = sum(distribution.values())
    parts = []
    for sev in ["critical", "high", "medium", "low"]:
        n = distribution.get(sev, 0)
        if n:
            parts.append(f"{n} {sev} clause{'s' if n > 1 else ''} ({FORMULA[sev]} pts each)")

    crit_note = ""
    if critical_titles:
        crit_note = (
            f" The most significant risks are concentrated in: {', '.join(critical_titles)}."
            " These clauses create asymmetric obligations that could cause significant financial,"
            " legal, or reputational harm to the Client."
        )

    cap_note = " The score is capped at 100." if sum(
        FORMULA[s] * n for s, n in distribution.items()
    ) > MAX_SCORE else ""

    return (
        f"This contract scores {score}/100 on the sign-as-is risk scale across {total} analysed clauses,"
        f" comprising {', '.join(parts)}."
        f"{crit_note}"
        f" Signing this contract as-is carries {'critical' if score >= 75 else 'high' if score >= 50 else 'moderate' if score >= 25 else 'low'}"
        f" risk exposure for the Client based on the weighted severity distribution."
        f"{cap_note}"
        " This assessment is AI-generated and does not constitute legal advice."
    )


def run(
    risk_path: str = RISK_FILE,
    overrides_path: str = OVERRIDES_FILE,
    output_path: str = OUTPUT_FILE,
) -> dict:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    overrides_data = json.loads(Path(overrides_path).read_text(encoding="utf-8"))
    overrides = overrides_data.get("overrides", {})

    clauses = data["clauses"]
    distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    raw_total = 0

    for clause in clauses:
        sev = _effective_severity(clause, overrides)
        distribution[sev] += 1
        raw_total += FORMULA[sev]

    score = min(MAX_SCORE, raw_total)

    critical_titles = [
        f"Clause {c['clause_number']} ({c['clause_title']})"
        for c in clauses
        if _effective_severity(c, overrides) == "critical"
    ]

    justification = _build_justification(score, distribution, critical_titles)

    output = {
        "formula": {
            "description": "sum of severity points per clause, capped at 100",
            "points_per_severity": FORMULA,
            "cap": MAX_SCORE,
        },
        "severity_distribution": distribution,
        "raw_total_before_cap": raw_total,
        "sign_as_is_risk_score": score,
        "justification": justification,
    }

    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"[signature_score] Severity distribution: {distribution}")
    print(f"[signature_score] Raw total: {raw_total} -> Score (capped at {MAX_SCORE}): {score}")
    print(f"[signature_score] Written -> {output_path}")

    return output


if __name__ == "__main__":
    run()
