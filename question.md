## BUILD

Build a replayable pipeline that ingests vendor contract text, extracts structured clause data, scores each clause against a fixed risk framework, performs focused deep analysis on critical clauses, supports an operator review checkpoint, and produces a negotiation briefing with prioritised talking points.

This is not a one-shot contract summary task. The evaluator will run your pipeline from a clean checkout, may replace the contract and risk framework with equivalent fixtures, and will verify that clause extraction is deterministic, risk scoring follows the provided framework, critical-clause analysis is staged, and operator overrides genuinely affect downstream outputs.

The pipeline must preserve intermediate artifacts, enforce controlled risk categories and severity levels, log LLM calls, and keep legal-style outputs clearly marked as AI-generated analysis rather than legal advice.

---

## INPUT FILES

Your pipeline must read these files from disk:

- `contract.txt`
- `risk_framework.json`

The sample contract and framework below are provided for local testing. The evaluator may replace them with equivalent files. Your implementation must not depend on exact clause numbers, wording, ordering, or expected final ratings from the public fixture.

---

## SAMPLE `contract.txt`

```text
MASTER SERVICE AGREEMENT
Between: TechVendor Solutions Ltd ("Vendor") and Client ("Client")
Effective Date: 1 January 2025

1. SERVICES
Vendor shall provide software-as-a-service access to the Platform as described in Schedule A.
Vendor reserves the right to modify, suspend, or discontinue any feature of the Platform
at any time without prior notice to Client.

2. PAYMENT TERMS
Client shall pay all invoices within 14 days of issue. Late payments shall accrue interest
at 4% per month compounded daily. Vendor may suspend services immediately upon any payment
being 1 day overdue, without notice.

3. DATA OWNERSHIP AND PROCESSING
All data uploaded by Client to the Platform ("Client Data") remains the property of Client.
However, Vendor is hereby granted a perpetual, irrevocable, royalty-free licence to use,
reproduce, modify, and distribute Client Data for the purposes of product improvement,
analytics, and training of machine learning models. This licence survives termination.

4. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of the other party's Confidential
Information. Vendor's confidentiality obligations shall not apply to information that
Vendor independently develops without reference to Client's information, or that Vendor
receives from a third party.

5. LIABILITY
In no event shall Vendor be liable for any indirect, incidental, special, or consequential
damages. Vendor's total aggregate liability shall not exceed the fees paid by Client in
the one (1) month prior to the claim. This limitation applies even in cases of Vendor's
gross negligence or wilful misconduct.

6. INTELLECTUAL PROPERTY
Any customisations, integrations, or derivative works created by Vendor at Client's request
shall remain the sole property of Vendor. Client is granted a non-exclusive,
non-transferable licence to use such works solely during the term of this Agreement.

7. TERMINATION
Either party may terminate this Agreement with 90 days written notice. Upon termination,
Client shall have 7 days to export their data. After 7 days, Vendor may permanently delete
all Client Data without further notice or liability.

8. GOVERNING LAW
This Agreement shall be governed by the laws of the Cayman Islands. All disputes shall be
resolved by binding arbitration in the Cayman Islands, with arbitration costs borne equally
by both parties regardless of outcome.

9. MODIFICATIONS
Vendor may modify these terms at any time by posting updated terms on its website.
Client's continued use of the Platform constitutes acceptance of the modified terms.

10. INDEMNIFICATION
Client shall indemnify, defend, and hold harmless Vendor from any claims arising out of
Client's use of the Platform, including claims arising from Vendor's own negligence.
```

---

## SAMPLE `risk_framework.json`

```json
{
  "risk_framework": {
    "categories": [
      "data_rights",
      "financial_exposure",
      "liability_cap",
      "ip_ownership",
      "termination_rights",
      "dispute_resolution",
      "unilateral_modification"
    ],
    "severity_levels": {
      "critical": "Clause creates asymmetric obligation that could cause significant financial, legal, or reputational harm",
      "high": "Clause is non-standard in favour of the vendor with material implications",
      "medium": "Clause is aggressive but common in vendor contracts; worth negotiating",
      "low": "Standard clause; acceptable with minor modification or as-is"
    }
  }
}
```

---

## PIPELINE STAGES

Your implementation must enforce these stages in code:

```text
INIT
 -> INPUTS_LOADED
 -> CLAUSES_EXTRACTED
 -> CLAUSES_RISK_SCORED
 -> CRITICAL_CLAUSES_ANALYSED
 -> OPERATOR_REVIEW_COMPLETE
 -> NEGOTIATION_BRIEF_GENERATED
 -> OPTIONAL_OUTPUTS_GENERATED
 -> VALIDATION_COMPLETE
 -> RESULTS_FINALISED
```

The negotiation briefing must not be generated until clause extraction, Stage 1 risk scoring, Stage 2 critical-clause analysis, and operator review have completed.

---

## MUST COMPLETE

### 1. Clause Extraction

Parse `contract.txt` deterministically and split it into numbered clauses before any LLM call.

Save output to `extracted_clauses.json`.

Each clause record must include:

```json
{
  "clause_number": "string",
  "clause_title": "string",
  "clause_text": "string",
  "word_count": 0
}
```

Do not ask the LLM to perform clause splitting.

---

### 2. Clause Classification and Risk Scoring

Make one Stage 1 LLM call using:

- all extracted clauses
- the full risk framework
- allowed risk categories
- allowed severity levels and definitions

For each clause, output:

```json
{
  "clause_number": "string",
  "risk_category": "data_rights",
  "severity": "critical",
  "one_sentence_risk_summary": "string",
  "is_non_standard": true
}
```

Every clause must use one category from the provided framework.

Every severity must use one provided severity level.

The model must not invent new categories or severity labels.

Save output to `risk_analysis.json`.

---

### 3. Deep Analysis of Critical Clauses

For each clause rated `critical` after Stage 1, make one separate Stage 2 LLM call.

Do not batch critical clauses.

Each call must include:

- clause text
- clause number and title
- risk category
- severity definition
- one-sentence risk summary

Each Stage 2 output must include:

```json
{
  "clause_number": "string",
  "harm_mechanism": "string",
  "precedent_framing": "string",
  "redline_suggestions": [
    "string",
    "string",
    "string"
  ]
}
```

Append Stage 2 outputs into `risk_analysis.json` while preserving the original Stage 1 risk score.

---

### 4. Operator Review Checkpoint

Before generating the negotiation brief, display Stage 1 risk scores in the terminal.

Pause for operator review with this prompt:

```text
Are there any clauses whose severity you want to override before generating the negotiation brief?
Enter clause number and new severity, or press Enter to continue.
```

The operator must be able to override one or more clause severities.

Allowed override severities:

```text
critical
high
medium
low
```

Save overrides to `operator_overrides.json`.

Stage 3 must use the post-override severities.

The override checkpoint must affect downstream briefing inputs, not merely log a message.

---

### 5. Negotiation Briefing

Make one Stage 3 LLM call after operator review.

The call must include:

- Stage 1 risk analysis
- Stage 2 critical-clause analysis
- operator overrides
- final post-override severity per clause

Generate `negotiation_brief.md` with these sections:

- Red Lines: clauses with final severity `critical`
- Priority Negotiations: clauses with final severity `high`
- Acceptable With Modification: clauses with final severity `medium`
- Standard / Accept: clauses with final severity `low`
- Opening Position: 2-3 sentence framing statement for the negotiation call

Each section must include clause-specific talking points.

---

## SHOULD ATTEMPT

### 6. Market Standard Comparison

For each `critical` or `high` clause, add:

```json
{
  "market_standard_comparison": "string",
  "basis": "LLM general knowledge, not a sourced legal database"
}
```

This output must be clearly marked as general AI-generated comparison, not authoritative legal advice.

---

### 7. Redline Document

For each clause with Stage 2 redline suggestions, generate replacement clause text.

Output `redlined_contract.md` as the full contract with changed clauses replaced.

Changed text must be marked in bold.

The redline document must contain replacement language, not only comments or annotations.

---

## STRETCH

### 8. Clause Cross-Reference Analysis

Identify clauses that interact to compound risk.

Output to `clause_cross_references.json`:

```json
{
  "clause_a": "string",
  "clause_b": "string",
  "combined_risk_description": "string",
  "combined_severity": "critical | high | medium | low"
}
```

For the public fixture, the data licence and data deletion terms are likely to interact, but the implementation must work for replacement contracts too.

---

### 9. Signature Risk Score

Compute an overall `sign_as_is_risk_score` from 0 to 100 in deterministic code.

Do not ask the LLM to assign the score.

Define the formula explicitly, for example:

```text
critical = 25 points
high = 12 points
medium = 5 points
low = 1 point
score = min(100, sum(clause severity points))
```

Save output to `signature_risk_score.json`.

Include:

- formula
- severity distribution
- final score
- one-paragraph justification

---

## REQUIRED ARTIFACTS

Your repository must produce:

- `contract.txt`
- `risk_framework.json`
- `extracted_clauses.json`
- `risk_analysis.json`
- `operator_overrides.json`
- `negotiation_brief.md`
- `redlined_contract.md`, if attempted
- `clause_cross_references.json`, if attempted
- `signature_risk_score.json`, if attempted
- `llm_calls.jsonl`

---

## `llm_calls.jsonl` REQUIREMENTS

Log one JSON object per LLM call.

Each record must include:

```json
{
  "stage": "string",
  "clause_number": "string | null",
  "timestamp": "ISO-8601 timestamp",
  "provider": "string",
  "model": "string",
  "prompt_hash": "string",
  "input_artifacts": ["path"],
  "output_artifact": "path"
}
```

There must be separate records for:

- Stage 1 clause classification and risk scoring
- each Stage 2 critical-clause deep analysis call
- Stage 3 negotiation briefing
- optional market standard comparison or redline generation, if implemented as LLM calls

---

## VALIDATION REQUIREMENTS

The repository must include a validation command, for example:

```bash
make validate
```

or:

```bash
python validate.py
```

The validation command must check that:

- required artifacts exist
- JSON files are valid
- contract and framework were read from disk
- clause extraction happened before any LLM call
- every extracted clause has a Stage 1 risk score
- risk categories use only the framework categories
- severities use only the framework severity levels
- each critical clause has its own Stage 2 LLM call record
- critical clauses were not batched into a single Stage 2 call
- operator overrides are saved and applied to Stage 3 inputs
- negotiation brief sections reflect post-override severities
- `llm_calls.jsonl` contains separate records for required stages

---

## EXECUTION REQUIREMENTS

The evaluator will run the pipeline from a clean checkout.

Generated artifacts may be deleted before evaluation.

The evaluator may replace `contract.txt` and `risk_framework.json` with equivalent files.

Static precomputed outputs are not sufficient.

The solution must actually run the staged pipeline and regenerate the required artifacts.

---

## TOOLS

Any programming language may be used.

Any LLM provider or AI tooling may be used.

---

## TECHNICAL CONSTRAINTS

- Read `contract.txt` and `risk_framework.json` from disk.
- Do not hardcode the sample contract text into prompts.
- Clause extraction must be deterministic code.
- Stage 1 must use the provided risk framework exactly.
- Each critical clause must have its own Stage 2 LLM call.
- Critical clauses must not be batched in Stage 2.
- Operator review must be interactive and able to modify Stage 3 inputs.
- The sign-as-is risk score, if attempted, must be computed deterministically.
- Outputs must not be presented as legal advice.## BUILD

Build a replayable pipeline that ingests vendor contract text, extracts structured clause data, scores each clause against a fixed risk framework, performs focused deep analysis on critical clauses, supports an operator review checkpoint, and produces a negotiation briefing with prioritised talking points.

This is not a one-shot contract summary task. The evaluator will run your pipeline from a clean checkout, may replace the contract and risk framework with equivalent fixtures, and will verify that clause extraction is deterministic, risk scoring follows the provided framework, critical-clause analysis is staged, and operator overrides genuinely affect downstream outputs.

The pipeline must preserve intermediate artifacts, enforce controlled risk categories and severity levels, log LLM calls, and keep legal-style outputs clearly marked as AI-generated analysis rather than legal advice.

---

## INPUT FILES

Your pipeline must read these files from disk:

- `contract.txt`
- `risk_framework.json`

The sample contract and framework below are provided for local testing. The evaluator may replace them with equivalent files. Your implementation must not depend on exact clause numbers, wording, ordering, or expected final ratings from the public fixture.

---

## SAMPLE `contract.txt`

```text
MASTER SERVICE AGREEMENT
Between: TechVendor Solutions Ltd ("Vendor") and Client ("Client")
Effective Date: 1 January 2025

1. SERVICES
Vendor shall provide software-as-a-service access to the Platform as described in Schedule A.
Vendor reserves the right to modify, suspend, or discontinue any feature of the Platform
at any time without prior notice to Client.

2. PAYMENT TERMS
Client shall pay all invoices within 14 days of issue. Late payments shall accrue interest
at 4% per month compounded daily. Vendor may suspend services immediately upon any payment
being 1 day overdue, without notice.

3. DATA OWNERSHIP AND PROCESSING
All data uploaded by Client to the Platform ("Client Data") remains the property of Client.
However, Vendor is hereby granted a perpetual, irrevocable, royalty-free licence to use,
reproduce, modify, and distribute Client Data for the purposes of product improvement,
analytics, and training of machine learning models. This licence survives termination.

4. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of the other party's Confidential
Information. Vendor's confidentiality obligations shall not apply to information that
Vendor independently develops without reference to Client's information, or that Vendor
receives from a third party.

5. LIABILITY
In no event shall Vendor be liable for any indirect, incidental, special, or consequential
damages. Vendor's total aggregate liability shall not exceed the fees paid by Client in
the one (1) month prior to the claim. This limitation applies even in cases of Vendor's
gross negligence or wilful misconduct.

6. INTELLECTUAL PROPERTY
Any customisations, integrations, or derivative works created by Vendor at Client's request
shall remain the sole property of Vendor. Client is granted a non-exclusive,
non-transferable licence to use such works solely during the term of this Agreement.

7. TERMINATION
Either party may terminate this Agreement with 90 days written notice. Upon termination,
Client shall have 7 days to export their data. After 7 days, Vendor may permanently delete
all Client Data without further notice or liability.

8. GOVERNING LAW
This Agreement shall be governed by the laws of the Cayman Islands. All disputes shall be
resolved by binding arbitration in the Cayman Islands, with arbitration costs borne equally
by both parties regardless of outcome.

9. MODIFICATIONS
Vendor may modify these terms at any time by posting updated terms on its website.
Client's continued use of the Platform constitutes acceptance of the modified terms.

10. INDEMNIFICATION
Client shall indemnify, defend, and hold harmless Vendor from any claims arising out of
Client's use of the Platform, including claims arising from Vendor's own negligence.
```

---

## SAMPLE `risk_framework.json`

```json
{
  "risk_framework": {
    "categories": [
      "data_rights",
      "financial_exposure",
      "liability_cap",
      "ip_ownership",
      "termination_rights",
      "dispute_resolution",
      "unilateral_modification"
    ],
    "severity_levels": {
      "critical": "Clause creates asymmetric obligation that could cause significant financial, legal, or reputational harm",
      "high": "Clause is non-standard in favour of the vendor with material implications",
      "medium": "Clause is aggressive but common in vendor contracts; worth negotiating",
      "low": "Standard clause; acceptable with minor modification or as-is"
    }
  }
}
```

---

## PIPELINE STAGES

Your implementation must enforce these stages in code:

```text
INIT
 -> INPUTS_LOADED
 -> CLAUSES_EXTRACTED
 -> CLAUSES_RISK_SCORED
 -> CRITICAL_CLAUSES_ANALYSED
 -> OPERATOR_REVIEW_COMPLETE
 -> NEGOTIATION_BRIEF_GENERATED
 -> OPTIONAL_OUTPUTS_GENERATED
 -> VALIDATION_COMPLETE
 -> RESULTS_FINALISED
```

The negotiation briefing must not be generated until clause extraction, Stage 1 risk scoring, Stage 2 critical-clause analysis, and operator review have completed.

---

## MUST COMPLETE

### 1. Clause Extraction

Parse `contract.txt` deterministically and split it into numbered clauses before any LLM call.

Save output to `extracted_clauses.json`.

Each clause record must include:

```json
{
  "clause_number": "string",
  "clause_title": "string",
  "clause_text": "string",
  "word_count": 0
}
```

Do not ask the LLM to perform clause splitting.

---

### 2. Clause Classification and Risk Scoring

Make one Stage 1 LLM call using:

- all extracted clauses
- the full risk framework
- allowed risk categories
- allowed severity levels and definitions

For each clause, output:

```json
{
  "clause_number": "string",
  "risk_category": "data_rights",
  "severity": "critical",
  "one_sentence_risk_summary": "string",
  "is_non_standard": true
}
```

Every clause must use one category from the provided framework.

Every severity must use one provided severity level.

The model must not invent new categories or severity labels.

Save output to `risk_analysis.json`.

---

### 3. Deep Analysis of Critical Clauses

For each clause rated `critical` after Stage 1, make one separate Stage 2 LLM call.

Do not batch critical clauses.

Each call must include:

- clause text
- clause number and title
- risk category
- severity definition
- one-sentence risk summary

Each Stage 2 output must include:

```json
{
  "clause_number": "string",
  "harm_mechanism": "string",
  "precedent_framing": "string",
  "redline_suggestions": [
    "string",
    "string",
    "string"
  ]
}
```

Append Stage 2 outputs into `risk_analysis.json` while preserving the original Stage 1 risk score.

---

### 4. Operator Review Checkpoint

Before generating the negotiation brief, display Stage 1 risk scores in the terminal.

Pause for operator review with this prompt:

```text
Are there any clauses whose severity you want to override before generating the negotiation brief?
Enter clause number and new severity, or press Enter to continue.
```

The operator must be able to override one or more clause severities.

Allowed override severities:

```text
critical
high
medium
low
```

Save overrides to `operator_overrides.json`.

Stage 3 must use the post-override severities.

The override checkpoint must affect downstream briefing inputs, not merely log a message.

---

### 5. Negotiation Briefing

Make one Stage 3 LLM call after operator review.

The call must include:

- Stage 1 risk analysis
- Stage 2 critical-clause analysis
- operator overrides
- final post-override severity per clause

Generate `negotiation_brief.md` with these sections:

- Red Lines: clauses with final severity `critical`
- Priority Negotiations: clauses with final severity `high`
- Acceptable With Modification: clauses with final severity `medium`
- Standard / Accept: clauses with final severity `low`
- Opening Position: 2-3 sentence framing statement for the negotiation call

Each section must include clause-specific talking points.

---

## SHOULD ATTEMPT

### 6. Market Standard Comparison

For each `critical` or `high` clause, add:

```json
{
  "market_standard_comparison": "string",
  "basis": "LLM general knowledge, not a sourced legal database"
}
```

This output must be clearly marked as general AI-generated comparison, not authoritative legal advice.

---

### 7. Redline Document

For each clause with Stage 2 redline suggestions, generate replacement clause text.

Output `redlined_contract.md` as the full contract with changed clauses replaced.

Changed text must be marked in bold.

The redline document must contain replacement language, not only comments or annotations.

---

## STRETCH

### 8. Clause Cross-Reference Analysis

Identify clauses that interact to compound risk.

Output to `clause_cross_references.json`:

```json
{
  "clause_a": "string",
  "clause_b": "string",
  "combined_risk_description": "string",
  "combined_severity": "critical | high | medium | low"
}
```

For the public fixture, the data licence and data deletion terms are likely to interact, but the implementation must work for replacement contracts too.

---

### 9. Signature Risk Score

Compute an overall `sign_as_is_risk_score` from 0 to 100 in deterministic code.

Do not ask the LLM to assign the score.

Define the formula explicitly, for example:

```text
critical = 25 points
high = 12 points
medium = 5 points
low = 1 point
score = min(100, sum(clause severity points))
```

Save output to `signature_risk_score.json`.

Include:

- formula
- severity distribution
- final score
- one-paragraph justification

---

## REQUIRED ARTIFACTS

Your repository must produce:

- `contract.txt`
- `risk_framework.json`
- `extracted_clauses.json`
- `risk_analysis.json`
- `operator_overrides.json`
- `negotiation_brief.md`
- `redlined_contract.md`, if attempted
- `clause_cross_references.json`, if attempted
- `signature_risk_score.json`, if attempted
- `llm_calls.jsonl`

---

## `llm_calls.jsonl` REQUIREMENTS

Log one JSON object per LLM call.

Each record must include:

```json
{
  "stage": "string",
  "clause_number": "string | null",
  "timestamp": "ISO-8601 timestamp",
  "provider": "string",
  "model": "string",
  "prompt_hash": "string",
  "input_artifacts": ["path"],
  "output_artifact": "path"
}
```

There must be separate records for:

- Stage 1 clause classification and risk scoring
- each Stage 2 critical-clause deep analysis call
- Stage 3 negotiation briefing
- optional market standard comparison or redline generation, if implemented as LLM calls

---

## VALIDATION REQUIREMENTS

The repository must include a validation command, for example:

```bash
make validate
```

or:

```bash
python validate.py
```

The validation command must check that:

- required artifacts exist
- JSON files are valid
- contract and framework were read from disk
- clause extraction happened before any LLM call
- every extracted clause has a Stage 1 risk score
- risk categories use only the framework categories
- severities use only the framework severity levels
- each critical clause has its own Stage 2 LLM call record
- critical clauses were not batched into a single Stage 2 call
- operator overrides are saved and applied to Stage 3 inputs
- negotiation brief sections reflect post-override severities
- `llm_calls.jsonl` contains separate records for required stages

---

## EXECUTION REQUIREMENTS

The evaluator will run the pipeline from a clean checkout.

Generated artifacts may be deleted before evaluation.

The evaluator may replace `contract.txt` and `risk_framework.json` with equivalent files.

Static precomputed outputs are not sufficient.

The solution must actually run the staged pipeline and regenerate the required artifacts.

---

## TOOLS

Any programming language may be used.

Any LLM provider or AI tooling may be used.

---

## TECHNICAL CONSTRAINTS

- Read `contract.txt` and `risk_framework.json` from disk.
- Do not hardcode the sample contract text into prompts.
- Clause extraction must be deterministic code.
- Stage 1 must use the provided risk framework exactly.
- Each critical clause must have its own Stage 2 LLM call.
- Critical clauses must not be batched in Stage 2.
- Operator review must be interactive and able to modify Stage 3 inputs.
- The sign-as-is risk score, if attempted, must be computed deterministically.
- Outputs must not be presented as legal advice.