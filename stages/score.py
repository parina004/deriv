import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

CLAUSES_FILE = "extracted_clauses.json"
FRAMEWORK_FILE = "risk_framework.json"
OUTPUT_FILE = "risk_analysis.json"


def _build_prompt(clauses: list, framework: dict) -> str:
    categories = framework["risk_framework"]["categories"]
    severity_levels = framework["risk_framework"]["severity_levels"]

    severity_block = "\n".join(
        f'  "{k}": "{v}"' for k, v in severity_levels.items()
    )
    categories_block = ", ".join(f'"{c}"' for c in categories)

    clauses_block = "\n\n".join(
        f'Clause {c["clause_number"]} — {c["clause_title"]}:\n{c["clause_text"]}'
        for c in clauses
    )

    return f"""You are a legal risk analyst reviewing a vendor contract on behalf of the Client.

Analyse each clause below and classify it using ONLY the categories and severity levels provided.
Do not invent new categories or severity labels.

ALLOWED RISK CATEGORIES (use exactly as written):
{categories_block}

ALLOWED SEVERITY LEVELS (use exactly as written):
{{
{severity_block}
}}

CONTRACT CLAUSES:
{clauses_block}

Return a JSON array with one object per clause. Each object must have exactly these fields:
{{
  "clause_number": "<number as string>",
  "risk_category": "<one of the allowed categories>",
  "severity": "<one of: critical, high, medium, low>",
  "one_sentence_risk_summary": "<one sentence>",
  "is_non_standard": <true or false>
}}

Return only the JSON array, no markdown fences, no explanation."""


def _extract_json(text: str) -> list:
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def _validate(scores: list, framework: dict) -> None:
    allowed_categories = set(framework["risk_framework"]["categories"])
    allowed_severities = set(framework["risk_framework"]["severity_levels"].keys())

    for item in scores:
        cat = item.get("risk_category")
        sev = item.get("severity")
        if cat not in allowed_categories:
            raise ValueError(
                f"Clause {item['clause_number']}: invalid category '{cat}'. "
                f"Allowed: {allowed_categories}"
            )
        if sev not in allowed_severities:
            raise ValueError(
                f"Clause {item['clause_number']}: invalid severity '{sev}'. "
                f"Allowed: {allowed_severities}"
            )


def run(
    clauses_path: str = CLAUSES_FILE,
    framework_path: str = FRAMEWORK_FILE,
    output_path: str = OUTPUT_FILE,
) -> list:
    clauses = json.loads(Path(clauses_path).read_text(encoding="utf-8"))["clauses"]
    framework = json.loads(Path(framework_path).read_text(encoding="utf-8"))

    prompt = _build_prompt(clauses, framework)

    print("[score] Calling LLM for Stage 1 risk scoring (1 call for all clauses)...")
    raw = call_llm(
        stage="stage1_risk_scoring",
        prompt=prompt,
        input_artifacts=[clauses_path, framework_path],
        output_artifact=output_path,
    )

    scores = _extract_json(raw)
    _validate(scores, framework)

    # Merge scores into clause records
    scores_by_clause = {s["clause_number"]: s for s in scores}
    for clause in clauses:
        score = scores_by_clause.get(clause["clause_number"])
        if not score:
            raise ValueError(f"No score returned for clause {clause['clause_number']}")
        clause.update(score)

    output = {"clauses": clauses}
    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"[score] Risk scores written -> {output_path}")
    print(f"\n{'Clause':<8} {'Category':<25} {'Severity':<10} Summary")
    print("-" * 90)
    for c in clauses:
        print(f"  {c['clause_number']:<6} {c['risk_category']:<25} {c['severity']:<10} {c['one_sentence_risk_summary'][:55]}")

    critical = [c for c in clauses if c["severity"] == "critical"]
    print(f"\n[score] {len(critical)} critical clause(s): {[c['clause_number'] for c in critical]}")

    return clauses


if __name__ == "__main__":
    run()
