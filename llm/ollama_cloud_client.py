"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

from config import OLLAMA_API_KEY, OLLAMA_CLOUD_BASE_URL


def ollama_cloud_bac_tool(model, messages):
    if not OLLAMA_API_KEY:
        raise ValueError("OLLAMA_API_KEY is not set in environment/.env.")

    try:
        from ollama import Client
    except ImportError as exc:
        raise ValueError(
            "Ollama Python package is missing. Install it with: pip install ollama"
        ) from exc

    client = Client(
        host=OLLAMA_CLOUD_BASE_URL,
        headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
    )

    try:
        response = client.chat(
            model=model,
            messages=messages,
            stream=False,
        )
    except Exception as exc:
        raise ValueError(f"Ollama Cloud request failed: {exc}") from exc

    text = ""
    if isinstance(response, dict):
        text = ((response.get("message") or {}).get("content") or "").strip()
    else:
        message = getattr(response, "message", None)
        text = (getattr(message, "content", "") or "").strip()

    if not text:
        raise ValueError(f"Ollama Cloud returned empty text: {response}")

    return text
