import os
import json
import urllib.request
from pathlib import Path
from typing import Optional

def _load_env_files():
    """Load .env files from both project root and backend directory."""
    cur = Path(__file__).resolve()
    candidates = [
        cur.parent.parent.parent.parent / ".env",  # InsightX/.env
        cur.parent.parent.parent / ".env",         # InsightX/backend/.env
    ]
    for env_file in candidates:
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if v and not v.startswith("your_"):
                            os.environ[k] = v

_load_env_files()

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 InsightX/1.0"

# Groq models tried in sequence for highest compatibility
_GROQ_MODELS = [
    "groq/compound-mini",
    "groq/compound",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def query_free_llm(prompt: str, system_context: str = "") -> Optional[str]:
    """
    Calls available free LLM APIs in priority order:
    1. Groq (Active high-speed inference models)
    2. Google Gemini 1.5 Flash  (GEMINI_API_KEY)
    3. Local Ollama              (OLLAMA_URL)
    """
    _load_env_files()

    # ── 1. Groq Cloud ────────────────────────────────────────────────────────
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.startswith("your_"):
        for model_name in _GROQ_MODELS:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_context},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {groq_key}",
                        "User-Agent": _USER_AGENT,
                    },
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    content = result["choices"][0]["message"]["content"]
                    if content:
                        return content.strip()
            except Exception:
                continue

    # ── 2. Google Gemini 1.5 Flash ───────────────────────────────────────────
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key and not gemini_key.startswith("your_"):
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-1.5-flash:generateContent?key={gemini_key}"
            )
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_context}\n\nQuestion: {prompt}"}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                    "topP": 0.8,
                },
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": _USER_AGENT,
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[LLM] Gemini API call failed: {e}")

    # ── 3. Local Ollama ──────────────────────────────────────────────────────
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    try:
        url = f"{ollama_url}/api/generate"
        payload = {
            "model": os.environ.get("OLLAMA_MODEL", "llama3"),
            "prompt": f"{system_context}\n\n{prompt}",
            "stream": False,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": _USER_AGENT,
            },
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "response" in result:
                return result["response"].strip()
    except Exception:
        pass

    return None
