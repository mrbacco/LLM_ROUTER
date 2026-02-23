"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

from config import GEMINI_API_KEY


def _to_gemini_contents(messages, types, attachments=None):
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    attachment_items = attachments or []
    if attachment_items:
        names = [item.get("name") for item in attachment_items if item.get("name")]
        names_text = ", ".join(names) if names else "attached files"
        attachment_parts = [
            types.Part.from_text(
                text=(
                    f"Use these attached files as direct context: {names_text}. "
                    "If the answer needs file content, prioritize these attachments."
                )
            )
        ]
        for item in attachment_items:
            data = item.get("data")
            mime_type = (item.get("mime_type") or "application/octet-stream").strip()
            if not isinstance(data, (bytes, bytearray)):
                continue
            attachment_parts.append(
                types.Part.from_bytes(data=bytes(data), mime_type=mime_type)
            )
        if len(attachment_parts) > 1:
            contents.append(types.Content(role="user", parts=attachment_parts))
    return contents


def _extract_text(response):
    text = (getattr(response, "text", "") or "").strip()
    if text:
        return text

    candidates = getattr(response, "candidates", None) or []
    collected = []
    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            piece = getattr(part, "text", "") or ""
            if piece:
                collected.append(piece)
    text = "".join(collected).strip()
    if text:
        return text
    raise ValueError(f"Gemini returned empty text: {response}")


def gemini_bac_tool(model, messages, attachments=None):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in environment/.env.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ValueError(
            "Gemini SDK is missing. Install it with: pip install google-genai"
        ) from exc

    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = _to_gemini_contents(messages, types, attachments=attachments)

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
    except Exception as exc:
        raise ValueError(f"Gemini request failed: {exc}") from exc

    return _extract_text(response)
