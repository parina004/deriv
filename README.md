# Contract Risk Analysis Pipeline

A replayable, staged pipeline that ingests a vendor contract, extracts and scores every clause against a fixed risk framework, performs deep analysis on critical clauses, supports an operator review checkpoint, and produces a negotiation briefing with prioritised talking points.

---

## Features

| Stage | What it does |
|---|---|
| **Clause Extraction** | Deterministically splits `contract.txt` into numbered clauses using regex — no LLM involved |
| **Risk Scoring** | One LLM call scores every clause against the provided risk framework (category + severity) |
| **Deep Analysis** | One separate LLM call per critical clause — harm mechanism, precedent framing, redline suggestions |
| **Operator Review** | Interactive terminal checkpoint to override severities before the brief is generated |
| **Negotiation Brief** | One LLM call produces a structured `negotiation_brief.md` with Red Lines, Priority Negotiations, and Opening Position |
| **Market Comparison** | Adds market-standard deviation notes to every critical/high clause |
| **Redline Document** | Generates `redlined_contract.md` — the full contract with AI-drafted replacement clauses in **bold** |
| **Cross-Reference Analysis** | Identifies clause pairs whose combined effect compounds risk |
| **Signature Risk Score** | Deterministic 0–100 score computed from severity distribution (no LLM) |

All LLM calls are logged to `llm_calls.jsonl`. All intermediate artifacts are preserved between runs. A built-in validator checks every requirement.

---

## Project Structure

```
├── pipeline.py                  # Main entry point — orchestrates all stages
├── validate.py                  # Validation script — checks all artifacts
├── llm_client.py                # OpenRouter wrapper + llm_calls.jsonl logger
├── contract.txt                 # Input: vendor contract (replaceable)
├── risk_framework.json          # Input: risk categories and severity definitions (replaceable)
├── requirements.txt
├── stages/
│   ├── extract.py               # Stage 0: deterministic clause extraction
│   ├── score.py                 # Stage 1: risk scoring (1 LLM call)
│   ├── analyse.py               # Stage 2: deep analysis per critical clause
│   ├── review.py                # Stage 3: operator review checkpoint
│   ├── brief.py                 # Stage 4: negotiation brief (1 LLM call)
│   ├── market_compare.py        # Optional: market standard comparison
│   ├── redline.py               # Optional: redlined contract generation
│   ├── cross_reference.py       # Stretch: clause cross-reference analysis
│   └── signature_score.py       # Stretch: deterministic signature risk score
```

---

## Output Artifacts

| File | Description |
|---|---|
| `extracted_clauses.json` | All clauses with number, title, text, word count |
| `risk_analysis.json` | Risk scores, deep analysis, and market comparisons per clause |
| `operator_overrides.json` | Any severity overrides entered during review |
| `negotiation_brief.md` | Final negotiation briefing (5 sections) |
| `redlined_contract.md` | Full contract with replacement clause language in bold |
| `clause_cross_references.json` | Interacting clause pairs that compound risk |
| `signature_risk_score.json` | Deterministic 0–100 risk score with formula and justification |
| `llm_calls.jsonl` | Log of every LLM call (stage, model, timestamp, prompt hash, artifacts) |
| `pipeline_state.json` | Current pipeline stage — used for resume-on-rerun |

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd <repo-directory>
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
#api key
OPENROUTER_API_KEY=your-key

# LLM Model Name
LLM_MODEL=anthropic/claude-3.7-sonnet
```

Get an API key at [openrouter.ai](https://openrouter.ai). The pipeline works with any model available on OpenRouter.

### 4. Add your contract (optional)

Replace `contract.txt` and `risk_framework.json` with your own files. The pipeline does not depend on specific clause numbers, wording, or ordering — it works with any contract that uses numbered clause headings (e.g. `1. SERVICES`).

`risk_framework.json` must follow this structure:

```json
{
  "risk_framework": {
    "categories": ["data_rights", "financial_exposure", ...],
    "severity_levels": {
      "critical": "...",
      "high": "...",
      "medium": "...",
      "low": "..."
    }
  }
}
```

---

## Running the Pipeline

### Full run (from scratch)

```bash
python pipeline.py --fresh
```

This clears all previously generated artifacts and runs every stage in order.

### Resume from last completed stage

```bash
python pipeline.py
```

Skips stages whose output artifacts already exist. Operator review always prompts interactively.

### Operator Review

When the pipeline reaches the review stage, it displays all clause risk scores and pauses:

```
Are there any clauses whose severity you want to override before generating the negotiation brief?
Enter clause number and new severity, or press Enter to continue.

Override> 3 high
Override> 5 critical
Override>
```

Valid severities: `critical`, `high`, `medium`, `low`. Press Enter with no input to continue.

### Validate outputs

```bash
python validate.py
```

Runs 47 checks covering artifact existence, JSON validity, schema correctness, stage ordering, no LLM batching, override application, and brief section structure.

---

## Pipeline Stage Order

```
INIT
 -> INPUTS_LOADED
 -> CLAUSES_EXTRACTED            (no LLM)
 -> CLAUSES_RISK_SCORED          (1 LLM call)
 -> CRITICAL_CLAUSES_ANALYSED    (1 LLM call per critical clause)
 -> OPERATOR_REVIEW_COMPLETE     (interactive)
 -> NEGOTIATION_BRIEF_GENERATED  (1 LLM call)
 -> OPTIONAL_OUTPUTS_GENERATED   (market comparison + redline + cross-ref + signature score)
 -> VALIDATION_COMPLETE
 -> RESULTS_FINALISED
```

The negotiation brief is never generated until clause extraction, risk scoring, deep analysis, and operator review have all completed. Stage order is enforced in code via `pipeline_state.json`.

---

## Disclaimer

All outputs are AI-generated analysis for informational purposes only. Nothing produced by this pipeline constitutes legal advice. Consult a qualified legal professional before making contract decisions.
