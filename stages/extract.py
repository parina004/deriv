import json
import re
from pathlib import Path

CONTRACT_FILE = "contract.txt"
OUTPUT_FILE = "extracted_clauses.json"


def extract_clauses(contract_path: str = CONTRACT_FILE) -> list:
    text = Path(contract_path).read_text(encoding="utf-8")

    # Match numbered clause headings at the start of a line, e.g. "1. SERVICES"
    # Titles are expected to be uppercase words; works with equivalent replacement contracts
    pattern = re.compile(r'^(\d+)\.\s+([A-Z][A-Z\s]*)$', re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        raise ValueError(f"No numbered clauses found in {contract_path}. "
                         "Expected format: '1. CLAUSE TITLE' at the start of a line.")

    clauses = []
    for i, match in enumerate(matches):
        clause_number = match.group(1)
        clause_title = match.group(2).strip()

        # Body starts after the heading line; ends at the next heading or EOF
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        clause_text = text[body_start:body_end].strip()

        clauses.append({
            "clause_number": clause_number,
            "clause_title": clause_title,
            "clause_text": clause_text,
            "word_count": len(clause_text.split()),
        })

    return clauses


def run(contract_path: str = CONTRACT_FILE, output_path: str = OUTPUT_FILE) -> list:
    clauses = extract_clauses(contract_path)

    output = {"clauses": clauses}
    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"[extract] {len(clauses)} clauses extracted -> {output_path}")
    for c in clauses:
        print(f"  Clause {c['clause_number']}: {c['clause_title']} ({c['word_count']} words)")

    return clauses


if __name__ == "__main__":
    run()
