"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

import json
import urllib.error
import urllib.parse
import urllib.request

from config import GEMINI_API_KEY


def _to_gemini_contents(messages):
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        text = (msg.get("content") or "").strip()
        if not text:
            continue

        gemini_role = "model" if role == "assistant" else "user"
        contents.append({
            "role": gemini_role,
            "parts": [{"text": text}]
        })

    return contents


def gemini_bac_tool(model, messages):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in environment/.env.")

    safe_model = urllib.parse.quote(model, safe="")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{safe_model}:generateContent"
        f"?key={urllib.parse.quote(GEMINI_API_KEY, safe='')}"
    )

    payload = {
        "contents": _to_gemini_contents(messages)
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
            parsed = json.loads(response_body)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Gemini HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Gemini request failed: {exc}") from exc

    candidates = parsed.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini returned no candidates: {parsed}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join((part.get("text") or "") for part in parts).strip()
    if not text:
        raise ValueError(f"Gemini returned empty text: {parsed}")

    return text
