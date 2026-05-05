import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

RISK_FILE = "risk_analysis.json"
BASIS = "LLM general knowledge, not a sourced legal database"


def _build_prompt(clauses: list) -> str:
    clause_block = "\n\n".join(
        f"Clause {c['clause_number']} — {c['clause_title']} [{c['risk_category']}]:\n{c['clause_text']}"
        for c in clauses
    )
    numbers = [c["clause_number"] for c in clauses]

    return f"""You are a legal analyst comparing vendor contract clauses against market standards.

DISCLAIMER: This is AI-generated general knowledge comparison, not authoritative legal advice.

For each clause below, provide a one-paragraph market standard comparison describing how this clause
deviates from what is typical in commercial SaaS contracts. Be specific about what is unusual or
one-sided compared to market norms.

{clause_block}

Return a JSON array with one object per clause, in this exact order: {numbers}
Each object must have exactly:
{{
  "clause_number": "<number as string>",
  "market_standard_comparison": "<one paragraph comparing to market standard>"
}}

Return only the JSON array, no markdown fences, no explanation."""


def _extract_json(text: str) -> list:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def run(risk_path: str = RISK_FILE) -> list:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    clauses = data["clauses"]

    target_clauses = [c for c in clauses if c["severity"] in ("critical", "high")]
    print(f"[market_compare] {len(target_clauses)} critical/high clause(s) to compare: "
          f"{[c['clause_number'] for c in target_clauses]}")

    if not target_clauses:
        print("[market_compare] No critical/high clauses — skipping.")
        return clauses

    prompt = _build_prompt(target_clauses)
    raw = call_llm(
        stage="optional_market_comparison",
        prompt=prompt,
        input_artifacts=[risk_path],
        output_artifact=risk_path,
    )

    comparisons = _extract_json(raw)
    comparisons_by_clause = {str(c["clause_number"]): c for c in comparisons}

    clauses_by_number = {c["clause_number"]: c for c in clauses}
    for clause in target_clauses:
        comp = comparisons_by_clause.get(clause["clause_number"])
        if comp:
            clauses_by_number[clause["clause_number"]]["market_standard_comparison"] = (
                comp["market_standard_comparison"]
            )
            clauses_by_number[clause["clause_number"]]["basis"] = BASIS
            print(f"  Clause {clause['clause_number']}: market comparison added")
        else:
            print(f"  Clause {clause['clause_number']}: WARNING — no comparison returned")

    Path(risk_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[market_compare] Market comparisons written -> {risk_path}")
    return clauses


if __name__ == "__main__":
    run()
