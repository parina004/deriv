import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

RISK_FILE = "risk_analysis.json"
OUTPUT_FILE = "clause_cross_references.json"


def _build_prompt(clauses: list) -> str:
    clause_block = "\n\n".join(
        f"Clause {c['clause_number']} — {c['clause_title']} [{c['risk_category']}, {c['severity']}]:\n"
        f"{c['clause_text']}\nRisk: {c['one_sentence_risk_summary']}"
        for c in clauses
    )

    return f"""You are a legal risk analyst identifying clause interactions in a vendor contract.

Some clauses individually carry risk, but when read together they can compound that risk significantly.

CONTRACT CLAUSES:
{clause_block}

Identify pairs of clauses whose combined effect creates greater risk than each clause alone.
Focus on interactions where one clause enables, amplifies, or locks in the harm described by another.

For each interacting pair, return a JSON object. Return a JSON array of all such pairs.
Each object must have exactly these fields:
{{
  "clause_a": "<clause number as string>",
  "clause_b": "<clause number as string>",
  "combined_risk_description": "<one paragraph explaining how these two clauses interact to compound risk>",
  "combined_severity": "<critical | high | medium | low>"
}}

Rules:
- Only include pairs where the interaction genuinely compounds risk (not just thematic similarity)
- combined_severity must be one of: critical, high, medium, low
- clause_a number must be lower than clause_b number
- Return only the JSON array, no markdown fences, no explanation
- Minimum 2 pairs, maximum 6 pairs"""


def _extract_json(text: str) -> list:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def _validate(pairs: list, valid_clause_numbers: set) -> None:
    allowed_severities = {"critical", "high", "medium", "low"}
    for pair in pairs:
        for field in ["clause_a", "clause_b", "combined_risk_description", "combined_severity"]:
            if field not in pair:
                raise ValueError(f"Cross-reference pair missing field '{field}': {pair}")
        if pair["clause_a"] not in valid_clause_numbers:
            raise ValueError(f"clause_a '{pair['clause_a']}' not a valid clause number")
        if pair["clause_b"] not in valid_clause_numbers:
            raise ValueError(f"clause_b '{pair['clause_b']}' not a valid clause number")
        if pair["combined_severity"] not in allowed_severities:
            raise ValueError(f"Invalid combined_severity '{pair['combined_severity']}'")


def run(risk_path: str = RISK_FILE, output_path: str = OUTPUT_FILE) -> list:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    clauses = data["clauses"]
    valid_numbers = {c["clause_number"] for c in clauses}

    prompt = _build_prompt(clauses)

    print("[cross_reference] Calling LLM to identify interacting clause pairs...")
    raw = call_llm(
        stage="stretch_cross_reference",
        prompt=prompt,
        input_artifacts=[risk_path],
        output_artifact=output_path,
    )

    pairs = _extract_json(raw)
    _validate(pairs, valid_numbers)

    output = {"cross_references": pairs}
    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"[cross_reference] {len(pairs)} interacting pair(s) identified -> {output_path}")
    for p in pairs:
        print(f"  Clause {p['clause_a']} x Clause {p['clause_b']} [{p['combined_severity']}]: "
              f"{p['combined_risk_description'][:70]}...")

    return pairs


if __name__ == "__main__":
    run()
