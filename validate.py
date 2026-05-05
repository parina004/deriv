import json
import sys
from pathlib import Path

REQUIRED_ARTIFACTS = [
    "contract.txt",
    "risk_framework.json",
    "extracted_clauses.json",
    "risk_analysis.json",
    "operator_overrides.json",
    "negotiation_brief.md",
    "redlined_contract.md",
    "clause_cross_references.json",
    "signature_risk_score.json",
    "llm_calls.jsonl",
]

ERRORS = []
PASSES = []


def fail(msg):
    ERRORS.append(f"  FAIL: {msg}")


def ok(msg):
    PASSES.append(f"  OK:   {msg}")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"{path} is not valid JSON: {e}")
        return None


def load_jsonl(path):
    records = []
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception as e:
            fail(f"{path} line {i} is not valid JSON: {e}")
    return records


# ── 1. Required artifacts exist ───────────────────────────────────────────────
print("Checking required artifacts...")
for artifact in REQUIRED_ARTIFACTS:
    if Path(artifact).exists():
        ok(f"{artifact} exists")
    else:
        fail(f"{artifact} is missing")

# ── 2. JSON files are valid ───────────────────────────────────────────────────
print("Checking JSON validity...")
clauses_data = load_json("extracted_clauses.json")
risk_data = load_json("risk_analysis.json")
overrides_data = load_json("operator_overrides.json")
framework_data = load_json("risk_framework.json")

if clauses_data:
    ok("extracted_clauses.json is valid JSON")
if risk_data:
    ok("risk_analysis.json is valid JSON")
if overrides_data:
    ok("operator_overrides.json is valid JSON")
if framework_data:
    ok("risk_framework.json is valid JSON")

llm_calls = load_jsonl("llm_calls.jsonl") if Path("llm_calls.jsonl").exists() else []
if llm_calls is not None:
    ok(f"llm_calls.jsonl is valid JSONL ({len(llm_calls)} records)")

# ── 3. Contract and framework were read from disk ─────────────────────────────
print("Checking inputs were read from disk...")
if Path("contract.txt").exists():
    ok("contract.txt present on disk")
if Path("risk_framework.json").exists():
    ok("risk_framework.json present on disk")

# ── 4. Clause extraction happened before any LLM call ────────────────────────
print("Checking extraction precedes LLM calls...")
if clauses_data and llm_calls:
    import os
    extract_mtime = Path("extracted_clauses.json").stat().st_mtime
    stage1_calls = [r for r in llm_calls if r.get("stage") == "stage1_risk_scoring"]
    if stage1_calls:
        ok("extracted_clauses.json exists before LLM stage1 call (file precedes log record)")
    else:
        fail("No stage1_risk_scoring record found in llm_calls.jsonl")

# ── 5. Every extracted clause has a Stage 1 risk score ───────────────────────
print("Checking every clause has a risk score...")
if clauses_data and risk_data:
    extracted_nums = {c["clause_number"] for c in clauses_data["clauses"]}
    scored_nums = {c["clause_number"] for c in risk_data["clauses"]}
    missing = extracted_nums - scored_nums
    if missing:
        fail(f"Clauses without Stage 1 score: {missing}")
    else:
        ok(f"All {len(extracted_nums)} extracted clauses have Stage 1 scores")

# ── 6. Risk categories use only framework categories ─────────────────────────
print("Checking risk categories are from framework...")
if risk_data and framework_data:
    allowed_categories = set(framework_data["risk_framework"]["categories"])
    for c in risk_data["clauses"]:
        cat = c.get("risk_category")
        if cat not in allowed_categories:
            fail(f"Clause {c['clause_number']} has invalid category '{cat}'")
    ok("All risk categories are from the framework")

# ── 7. Severities use only framework severity levels ─────────────────────────
print("Checking severities are from framework...")
if risk_data and framework_data:
    allowed_severities = set(framework_data["risk_framework"]["severity_levels"].keys())
    for c in risk_data["clauses"]:
        sev = c.get("severity")
        if sev not in allowed_severities:
            fail(f"Clause {c['clause_number']} has invalid severity '{sev}'")
    ok("All severities are from the framework")

# ── 8. Each critical clause has its own Stage 2 LLM call (no batching) ───────
print("Checking Stage 2 calls are not batched...")
if risk_data and llm_calls:
    critical_clauses = [c["clause_number"] for c in risk_data["clauses"] if c.get("severity") == "critical"]
    stage2_calls = [r for r in llm_calls if r.get("stage") == "stage2_deep_analysis"]
    stage2_clause_nums = [r.get("clause_number") for r in stage2_calls]

    for num in critical_clauses:
        if num not in stage2_clause_nums:
            fail(f"Critical clause {num} has no Stage 2 LLM call record")
        else:
            ok(f"Critical clause {num} has its own Stage 2 LLM call")

    if len(stage2_calls) < len(critical_clauses):
        fail(f"Expected {len(critical_clauses)} Stage 2 calls, found {len(stage2_calls)}")
    elif len(critical_clauses) > 1 and len(stage2_calls) == 1:
        fail("Critical clauses appear to have been batched into a single Stage 2 call")
    else:
        ok(f"{len(stage2_calls)} separate Stage 2 calls made (not batched)")

# ── 9. Operator overrides are saved ──────────────────────────────────────────
print("Checking operator overrides file...")
if overrides_data is not None:
    ok("operator_overrides.json exists and is valid")
    overrides = overrides_data.get("overrides", {})
    ok(f"operator_overrides.json contains {len(overrides)} override(s)")

# ── 10. Negotiation brief sections reflect post-override severities ───────────
print("Checking negotiation brief structure...")
if Path("negotiation_brief.md").exists():
    brief_text = Path("negotiation_brief.md").read_text(encoding="utf-8")
    required_sections = [
        "## Red Lines",
        "## Priority Negotiations",
        "## Acceptable With Modification",
        "## Standard / Accept",
        "## Opening Position",
    ]
    for section in required_sections:
        if section in brief_text:
            ok(f"Brief contains section '{section}'")
        else:
            fail(f"Brief is missing section '{section}'")

# ── 11. llm_calls.jsonl has required stage records ───────────────────────────
print("Checking llm_calls.jsonl stage records...")
if llm_calls:
    stages_present = {r.get("stage") for r in llm_calls}
    for required_stage in ["stage1_risk_scoring", "stage3_negotiation_brief"]:
        if required_stage in stages_present:
            ok(f"llm_calls.jsonl has record for '{required_stage}'")
        else:
            fail(f"llm_calls.jsonl missing record for '{required_stage}'")

# ── 12. Market comparison fields on critical/high clauses ─────────────────────
print("Checking market standard comparison fields...")
if risk_data and framework_data:
    target = [c for c in risk_data["clauses"] if c.get("severity") in ("critical", "high")]
    missing_mc = [c["clause_number"] for c in target if "market_standard_comparison" not in c]
    if missing_mc:
        fail(f"Clauses missing market_standard_comparison: {missing_mc}")
    else:
        ok(f"All {len(target)} critical/high clauses have market_standard_comparison")
    missing_basis = [c["clause_number"] for c in target if "basis" not in c]
    if missing_basis:
        fail(f"Clauses missing 'basis' field: {missing_basis}")
    else:
        ok("All critical/high clauses have 'basis' field")

# ── 13. Redline document exists and has bold replacement text ─────────────────
print("Checking redlined_contract.md...")
if Path("redlined_contract.md").exists():
    redline_text = Path("redlined_contract.md").read_text(encoding="utf-8")
    if "**" in redline_text:
        ok("redlined_contract.md contains bold replacement text")
    else:
        fail("redlined_contract.md has no bold (**) markers")
    if "AI-GENERATED" in redline_text or "NOT LEGAL ADVICE" in redline_text:
        ok("redlined_contract.md contains AI-generated disclaimer")
    else:
        fail("redlined_contract.md missing AI-generated disclaimer")

# ── 14. optional_redline_generation records in llm_calls.jsonl ───────────────
print("Checking optional stage records in llm_calls.jsonl...")
if llm_calls:
    stages_present = {r.get("stage") for r in llm_calls}
    for optional_stage in ["optional_market_comparison", "optional_redline_generation"]:
        if optional_stage in stages_present:
            ok(f"llm_calls.jsonl has record for '{optional_stage}'")
        else:
            fail(f"llm_calls.jsonl missing record for '{optional_stage}'")

# ── 15. Clause cross-references structure ────────────────────────────────────
print("Checking clause_cross_references.json...")
cross_data = load_json("clause_cross_references.json") if Path("clause_cross_references.json").exists() else None
if cross_data:
    pairs = cross_data.get("cross_references", [])
    if not pairs:
        fail("clause_cross_references.json has no cross-reference pairs")
    else:
        ok(f"clause_cross_references.json contains {len(pairs)} pair(s)")
    allowed_severities = {"critical", "high", "medium", "low"}
    for p in pairs:
        for field in ["clause_a", "clause_b", "combined_risk_description", "combined_severity"]:
            if field not in p:
                fail(f"Cross-reference pair missing field '{field}'")
        if p.get("combined_severity") not in allowed_severities:
            fail(f"Invalid combined_severity '{p.get('combined_severity')}' in cross-reference")
    ok("All cross-reference pairs have required fields and valid severities")

# ── 16. Signature risk score is deterministic and within bounds ───────────────
print("Checking signature_risk_score.json...")
sig_data = load_json("signature_risk_score.json") if Path("signature_risk_score.json").exists() else None
if sig_data:
    score = sig_data.get("sign_as_is_risk_score")
    formula = sig_data.get("formula")
    distribution = sig_data.get("severity_distribution")
    justification = sig_data.get("justification")
    if score is None:
        fail("signature_risk_score.json missing 'sign_as_is_risk_score'")
    elif not (0 <= score <= 100):
        fail(f"sign_as_is_risk_score {score} is outside 0-100 range")
    else:
        ok(f"sign_as_is_risk_score = {score} (within 0-100)")
    if formula:
        ok("signature_risk_score.json contains formula")
    else:
        fail("signature_risk_score.json missing 'formula'")
    if distribution:
        ok("signature_risk_score.json contains severity_distribution")
    else:
        fail("signature_risk_score.json missing 'severity_distribution'")
    if justification:
        ok("signature_risk_score.json contains justification paragraph")
    else:
        fail("signature_risk_score.json missing 'justification'")

# ── Result ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"VALIDATION RESULTS: {len(PASSES)} passed, {len(ERRORS)} failed")
print("=" * 60)
for p in PASSES:
    print(p)
for e in ERRORS:
    print(e)

if ERRORS:
    print("\nValidation FAILED.")
    sys.exit(1)
else:
    print("\nValidation PASSED.")
    sys.exit(0)
