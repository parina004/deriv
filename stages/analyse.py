import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

RISK_FILE = "risk_analysis.json"
FRAMEWORK_FILE = "risk_framework.json"


def _build_prompt(clause: dict, severity_definition: str) -> str:
    return f"""You are a legal risk analyst performing a deep analysis of a single high-risk contract clause.

CLAUSE NUMBER: {clause["clause_number"]}
CLAUSE TITLE: {clause["clause_title"]}
RISK CATEGORY: {clause["risk_category"]}
SEVERITY: {clause["severity"]}
SEVERITY DEFINITION: {severity_definition}
RISK SUMMARY: {clause["one_sentence_risk_summary"]}

CLAUSE TEXT:
{clause["clause_text"]}

Perform a deep analysis and return a JSON object with exactly these fields:
{{
  "clause_number": "{clause["clause_number"]}",
  "harm_mechanism": "<how this clause causes harm to the Client in practice>",
  "precedent_framing": "<how to frame this clause in negotiation — what precedent or standard to reference>",
  "redline_suggestions": [
    "<suggested redline change 1>",
    "<suggested redline change 2>",
    "<suggested redline change 3>"
  ]
}}

Return only the JSON object, no markdown fences, no explanation.
NOTE: This is AI-generated legal analysis, not legal advice."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def run(risk_path: str = RISK_FILE, framework_path: str = FRAMEWORK_FILE) -> list:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    framework = json.loads(Path(framework_path).read_text(encoding="utf-8"))
    severity_definitions = framework["risk_framework"]["severity_levels"]

    critical_clauses = [c for c in data["clauses"] if c["severity"] == "critical"]
    print(f"[analyse] {len(critical_clauses)} critical clause(s) to analyse: "
          f"{[c['clause_number'] for c in critical_clauses]}")

    clauses_by_number = {c["clause_number"]: c for c in data["clauses"]}

    for clause in critical_clauses:
        print(f"[analyse] Calling LLM for clause {clause['clause_number']} — {clause['clause_title']}...")
        severity_def = severity_definitions[clause["severity"]]
        prompt = _build_prompt(clause, severity_def)

        raw = call_llm(
            stage="stage2_deep_analysis",
            prompt=prompt,
            input_artifacts=[risk_path, framework_path],
            output_artifact=risk_path,
            clause_number=clause["clause_number"],
        )

        analysis = _extract_json(raw)

        # Append Stage 2 fields into the existing clause record
        clauses_by_number[clause["clause_number"]].update({
            "harm_mechanism": analysis["harm_mechanism"],
            "precedent_framing": analysis["precedent_framing"],
            "redline_suggestions": analysis["redline_suggestions"],
        })

        print(f"  harm_mechanism: {analysis['harm_mechanism'][:80]}...")

    # Write updated data back — Stage 1 fields preserved, Stage 2 fields added
    Path(risk_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[analyse] Stage 2 analysis appended -> {risk_path}")

    return data["clauses"]


if __name__ == "__main__":
    run()
