"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

import json
import urllib.error
import urllib.request

from config import OPENROUTER_API_KEY, OPENROUTER_SITE_URL, OPENROUTER_APP_NAME


def openrouter_bac_tool(model, messages):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set in environment/.env.")

    url = "https://openrouter.ai/api/v1/chat/completions"
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
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenRouter HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"OpenRouter request failed: {exc}") from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise ValueError(f"OpenRouter returned no choices: {parsed}")

    text = choices[0].get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError(f"OpenRouter returned empty text: {parsed}")

    return text
