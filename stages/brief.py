import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm

RISK_FILE = "risk_analysis.json"
OVERRIDES_FILE = "operator_overrides.json"
OUTPUT_FILE = "negotiation_brief.md"


def apply_overrides(clauses: list, overrides: dict) -> list:
    for clause in clauses:
        if clause["clause_number"] in overrides:
            clause["final_severity"] = overrides[clause["clause_number"]]["override_severity"]
        else:
            clause["final_severity"] = clause["severity"]
    return clauses


def _build_prompt(clauses: list) -> str:
    def section(sev):
        return "\n".join(
            f"- Clause {c['clause_number']} ({c['clause_title']}): {c['one_sentence_risk_summary']}"
            + (f"\n  Harm: {c.get('harm_mechanism', '')}" if c.get("harm_mechanism") else "")
            + (f"\n  Precedent: {c.get('precedent_framing', '')}" if c.get("precedent_framing") else "")
            + (f"\n  Redlines: {'; '.join(c.get('redline_suggestions', []))}" if c.get("redline_suggestions") else "")
            for c in clauses if c["final_severity"] == sev
        ) or "None."

    overridden = [c for c in clauses if c.get("final_severity") != c.get("severity")]
    override_note = ""
    if overridden:
        override_note = "\nOPERATOR OVERRIDES APPLIED:\n" + "\n".join(
            f"- Clause {c['clause_number']}: {c['severity']} -> {c['final_severity']}"
            for c in overridden
        )

    return f"""You are a legal risk analyst preparing a negotiation briefing for a client.
Using the analysis below, generate a structured negotiation brief.
NOTE: This is AI-generated analysis for informational purposes only, not legal advice.
{override_note}

CRITICAL CLAUSES (final severity = critical):
{section("critical")}

HIGH CLAUSES (final severity = high):
{section("high")}

MEDIUM CLAUSES (final severity = medium):
{section("medium")}

LOW CLAUSES (final severity = low):
{section("low")}

Generate a negotiation_brief.md with EXACTLY these five sections in this order:

## Red Lines
List each critical clause with specific talking points for why it must be changed.

## Priority Negotiations
List each high severity clause with targeted negotiation talking points.

## Acceptable With Modification
List each medium severity clause with suggested modifications.

## Standard / Accept
List each low severity clause with a brief note.

## Opening Position
Write 2-3 sentences framing the overall negotiation stance for the opening call.

Use clause numbers and titles throughout. Be specific and actionable.
Begin with a disclaimer: "AI-GENERATED ANALYSIS — NOT LEGAL ADVICE" on the first line."""


def run(
    risk_path: str = RISK_FILE,
    overrides_path: str = OVERRIDES_FILE,
    output_path: str = OUTPUT_FILE,
) -> str:
    data = json.loads(Path(risk_path).read_text(encoding="utf-8"))
    overrides_data = json.loads(Path(overrides_path).read_text(encoding="utf-8"))
    overrides = overrides_data.get("overrides", {})

    clauses = apply_overrides(data["clauses"], overrides)

    severity_counts = {}
    for c in clauses:
        severity_counts[c["final_severity"]] = severity_counts.get(c["final_severity"], 0) + 1
    print(f"[brief] Final severity distribution: {severity_counts}")

    prompt = _build_prompt(clauses)

    print("[brief] Calling LLM for Stage 3 negotiation brief...")
    content = call_llm(
        stage="stage3_negotiation_brief",
        prompt=prompt,
        input_artifacts=[risk_path, overrides_path],
        output_artifact=output_path,
    )

    Path(output_path).write_text(content, encoding="utf-8")
    print(f"[brief] Negotiation brief written -> {output_path}")

    return content


if __name__ == "__main__":
    run()
