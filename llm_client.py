import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

LLM_LOG_FILE = "llm_calls.jsonl"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(
    stage: str,
    prompt: str,
    input_artifacts: list,
    output_artifact: str,
    clause_number: str = None,
) -> str:
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY is not set in .env")
    if not LLM_MODEL:
        raise EnvironmentError("LLM_MODEL is not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    if not response.ok:
        raise RuntimeError(
            f"OpenRouter API error {response.status_code}: {response.text}"
        )

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    _log_call(
        stage=stage,
        clause_number=clause_number,
        model=LLM_MODEL,
        prompt=prompt,
        input_artifacts=input_artifacts,
        output_artifact=output_artifact,
    )

    return content


def _log_call(stage, clause_number, model, prompt, input_artifacts, output_artifact):
    record = {
        "stage": stage,
        "clause_number": clause_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": "openrouter",
        "model": model,
        "prompt_hash": hashlib.md5(prompt.encode("utf-8")).hexdigest(),
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
    }
    with open(LLM_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
