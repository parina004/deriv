import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

RISK_FILE = "risk_analysis.json"
CONTRACT_FILE = "contract.txt"
OUTPUT_FILE = "redlined_contract.md"


def _build_prompt(clause: dict) -> str:
    suggestions = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(clause["redline_suggestions"]))
    return f"""You are a legal drafter rewriting a contract clause on behalf of the Client.

CLAUSE {clause["clause_number"]} — {clause["clause_title"]}

ORIGINAL TEXT:
{clause["clause_text"]}

RISK: {clause["one_sentence_risk_summary"]}
HARM MECHANISM: {clause["harm_mechanism"]}

REDLINE SUGGESTIONS:
{suggestions}

Write a complete replacement for this clause that addresses all redline suggestions.
The replacement must be full clause text (not a summary or annotation).
Start directly with the clause content — do not include the clause number or title header.
DISCLAIMER: This is AI-generated draft language, not legal advice."""


def _extract_replacement(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```(?:markdown|text)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    # Strip any "DISCLAIMER" line the model might prepend
    lines = text.splitlines()
    lines = [l for l in lines if not l.strip().upper().startswith("DISCLAIMER")]
    return "\n".join(lines).strip()


def run(
    risk_path: str = RISK_FILE,
    contract_path: str = CONTRACT_FILE,
    output_path: str = OUTPUT_FILE,
) -> str:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    contract_text = Path(contract_path).read_text(encoding="utf-8")
    clauses = data["clauses"]

    redline_clauses = [c for c in clauses if "redline_suggestions" in c]
    print(f"[redline] {len(redline_clauses)} clause(s) with redline suggestions: "
          f"{[c['clause_number'] for c in redline_clauses]}")

    replacements = {}
    for clause in redline_clauses:
        print(f"[redline] Generating replacement for clause {clause['clause_number']} — {clause['clause_title']}...")
        prompt = _build_prompt(clause)
        raw = call_llm(
            stage="optional_redline_generation",
            prompt=prompt,
            input_artifacts=[risk_path],
            output_artifact=output_path,
            clause_number=clause["clause_number"],
        )
        replacements[clause["clause_number"]] = _extract_replacement(raw)

    # Build redlined contract: replace changed clauses with bold replacement text
    output_lines = [
        "# REDLINED CONTRACT",
        "",
        "> AI-GENERATED REDLINE — NOT LEGAL ADVICE. Changes are shown in **bold**.",
        "",
    ]

    # Walk the original contract line by line, replacing clause bodies
    # We know clause headers are "N. TITLE" at start of line
    pattern = re.compile(r'^(\d+)\.\s+([A-Z][A-Z\s]*)$', re.MULTILINE)
    matches = list(pattern.finditer(contract_text))

    # Add any preamble before the first clause
    if matches:
        preamble = contract_text[:matches[0].start()].strip()
        if preamble:
            output_lines.append(preamble)
            output_lines.append("")

    for i, match in enumerate(matches):
        clause_num = match.group(1)
        clause_title = match.group(2).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(contract_text)
        original_body = contract_text[body_start:body_end].strip()

        output_lines.append(f"{clause_num}. {clause_title}")
        if clause_num in replacements:
            output_lines.append(f"**{replacements[clause_num]}**")
        else:
            output_lines.append(original_body)
        output_lines.append("")

    content = "\n".join(output_lines)
    Path(output_path).write_text(content, encoding="utf-8")
    print(f"[redline] Redlined contract written -> {output_path}")
    return content


if __name__ == "__main__":
    run()
