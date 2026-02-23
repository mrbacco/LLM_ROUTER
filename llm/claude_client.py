"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

from config import ANTHROPIC_API_KEY


def _to_claude_payload(messages):
    system_parts = []
    converted = []
    for msg in messages:
        role = (msg.get("role") or "user").strip()
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        if role == "system":
            system_parts.append(text)
            continue
        if role not in {"user", "assistant"}:
            role = "user"
        converted.append({
            "role": role,
            "content": text,
        })
    return ("\n\n".join(system_parts)).strip(), converted


def claude_bac_tool(model, messages):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not set in environment/.env.")

    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise ValueError(
            "Anthropic SDK is missing. Install it with: pip install anthropic"
        ) from exc

    system_prompt, claude_messages = _to_claude_payload(messages)
    if not claude_messages:
        claude_messages = [{"role": "user", "content": "Hello"}]

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt if system_prompt else None,
            messages=claude_messages,
        )
    except Exception as exc:
        raise ValueError(f"Claude request failed: {exc}") from exc

    blocks = getattr(response, "content", None) or []
    text = "".join(
        getattr(block, "text", "") or ""
        for block in blocks
        if getattr(block, "type", "") == "text"
    ).strip()
    if not text:
        raise ValueError(f"Claude returned empty text: {response}")
    return text
