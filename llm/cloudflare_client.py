"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

import json
import urllib.error
import urllib.parse
import urllib.request

from config import CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID


def _to_cf_messages(messages):
    formatted = []
    for msg in messages:
        role = (msg.get("role") or "user").strip()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        formatted.append({"role": role, "content": text})
    return formatted


def _extract_choice_text(choice):
    message = (choice or {}).get("message") or {}

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict):
                txt = (part.get("text") or "").strip()
                if txt:
                    chunks.append(txt)
        joined = "\n".join(chunks).strip()
        if joined:
            return joined

    # Cloudflare/OpenAI-compatible responses may return reasoning text here.
    reasoning = (message.get("reasoning_content") or "").strip()
    if reasoning:
        return reasoning

    function_call = message.get("function_call")
    if isinstance(function_call, dict):
        args = (function_call.get("arguments") or "").strip()
        if args:
            return args

    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        return json.dumps(tool_calls, ensure_ascii=False)

    return ""


def cloudflare_bac_tool(model, messages):
    if not CLOUDFLARE_API_TOKEN:
        raise ValueError("CLOUDFLARE_API_TOKEN is not set in environment/.env.")
    if not CLOUDFLARE_ACCOUNT_ID:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID is not set in environment/.env.")

    safe_model = urllib.parse.quote(model, safe="@/_-:.")
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{safe_model}"
    payload = {
        "messages": _to_cf_messages(messages),
        "max_tokens": 1024,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Cloudflare HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Cloudflare request failed: {exc}") from exc

    if not parsed.get("success", True):
        raise ValueError(f"Cloudflare returned error: {parsed}")

    result = parsed.get("result") or {}
    text = (result.get("response") or "").strip()
    if not text:
        # fallback parser for OpenAI-compatible shaped responses
        choices = result.get("choices") or []
        if choices:
            text = _extract_choice_text(choices[0])
    if not text:
        raise ValueError(f"Cloudflare returned empty text: {parsed}")
    return text
