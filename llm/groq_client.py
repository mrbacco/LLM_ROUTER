"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

import json
import urllib.error
import urllib.request

from config import GROQ_API_KEY


def groq_bac_tool(model, messages):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment/.env.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Groq HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Groq request failed: {exc}") from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise ValueError(f"Groq returned no choices: {parsed}")

    text = choices[0].get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError(f"Groq returned empty text: {parsed}")

    return text
