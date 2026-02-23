"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""

from flask import Flask, render_template, request, jsonify
import os
import time
import mimetypes
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from werkzeug.exceptions import HTTPException

from config import *
from llm.gemini_client import gemini_bac_tool
# from llm.groq_client import groq_bac_tool
# from llm.claude_client import claude_bac_tool
from llm.cloudflare_client import cloudflare_bac_tool
from llm.openrouter_client import openrouter_bac_tool
from llm.ollama_cloud_client import ollama_cloud_bac_tool

from memory.memory_store import save_message, save_message_and_get_memory
from memory.document_index import index_file as index_document_file, search_index, list_documents, get_documents_by_ids


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
GEMINI_NATIVE_ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}
MODEL_CATALOG = [
    # {"id": "claude-3-5-haiku-latest", "provider": "claude", "type": "remote", "key_name": "ANTHROPIC_API_KEY"},
    # {"id": "claude-3-5-sonnet-latest", "provider": "claude", "type": "remote", "key_name": "ANTHROPIC_API_KEY"},
    {"id": "@cf/meta/llama-3.1-8b-instruct", "provider": "cloudflare", "type": "remote", "key_name": "CLOUDFLARE_API_TOKEN"},
    {"id": "@cf/openai/gpt-oss-20b", "provider": "cloudflare", "type": "remote", "key_name": "CLOUDFLARE_API_TOKEN"},
    {"id": "@cf/openai/gpt-oss-120b", "provider": "cloudflare", "type": "remote", "key_name": "CLOUDFLARE_API_TOKEN"},
    {"id": "gemini-3-flash-preview", "provider": "gemini", "type": "remote", "key_name": "GEMINI_API_KEY"},
    {"id": "gemini-2.0-flash", "provider": "gemini", "type": "remote", "key_name": "GEMINI_API_KEY"},
    {"id": "gemini-2.0-flash-lite", "provider": "gemini", "type": "remote", "key_name": "GEMINI_API_KEY"},
    # {"id": "llama-3.1-8b-instant", "provider": "groq", "type": "remote", "key_name": "GROQ_API_KEY"},
    # {"id": "llama-3.3-70b-versatile", "provider": "groq", "type": "remote", "key_name": "GROQ_API_KEY"},
    # {"id": "gemma2-9b-it", "provider": "groq", "type": "remote", "key_name": "GROQ_API_KEY"},
    # {"id": "openai/gpt-oss-20b", "provider": "groq", "type": "remote", "key_name": "GROQ_API_KEY"},
    # {"id": "openai/gpt-oss-120b", "provider": "groq", "type": "remote", "key_name": "GROQ_API_KEY"},
    {"id": "openai/gpt-oss-20b:free", "provider": "openrouter", "type": "remote", "key_name": "OPENROUTER_API_KEY"},
    {"id": "gpt-oss:20b", "provider": "ollama_cloud", "type": "remote", "key_name": "OLLAMA_API_KEY"},
    {"id": "gpt-oss:120b", "provider": "ollama_cloud", "type": "remote", "key_name": "OLLAMA_API_KEY"},
]


def bac_log(message):
    if ENABLE_BAC_LOGS:
        print(message)


def with_rag_context(messages, file_ids=None):
    latest_user = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            latest_user = (msg.get("content") or "").strip()
            break

    hits = search_index(
        latest_user,
        index_file=RAG_INDEX_FILE,
        top_k=RAG_TOP_K,
        vector_dims=RAG_VECTOR_DIMS,
        file_ids=file_ids,
    )
    if not hits:
        return messages, []

    snippets = []
    for hit in hits:
        snippet = (hit.get("text") or "")[:RAG_MAX_SNIPPET_CHARS]
        snippets.append(
            f"[doc:{hit['file_name']}#{hit['chunk_index']} score={hit['score']:.3f}]\n{snippet}"
        )

    grounding = (
        "The text snippets below are REAL extracted contents from the user's uploaded files. "
        "Treat them as available context in this chat. "
        "Do NOT say you cannot access or view files when snippets are provided. "
        "Use snippets when relevant, and cite snippet tags like [doc:file#chunk]. "
        "If snippets are insufficient, say exactly what additional content is needed.\n\n"
        + "\n\n".join(snippets)
    )
    attachment_user_hint = (
        "Attached file context is already extracted below. "
        "Answer the user's latest request using this context; do not ask for re-upload when snippet(s) are present.\n\n"
        + "\n\n".join(snippets)
    )
    enhanced = (
        [{"role": "system", "content": grounding}]
        + list(messages)
        + [{"role": "user", "content": attachment_user_hint}]
    )
    return enhanced, hits


def _looks_like_missing_attachment_reply(text):
    t = (text or "").lower()
    if not t:
        return False
    patterns = (
        "don't see any file attached",
        "do not see any file attached",
        "i don't see any file",
        "i do not see any file",
        "upload the document",
        "share a link",
        "can't access files directly",
        "cannot access files directly",
        "can't open files directly",
        "cannot open files directly",
        "can't view files directly",
        "cannot view files directly",
    )
    return any(p in t for p in patterns)


def _guess_mime_type(path):
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type:
        return mime_type
    ext = os.path.splitext(path)[1].lower()
    if ext in {".md", ".txt"}:
        return "text/plain"
    if ext == ".csv":
        return "text/csv"
    if ext == ".json":
        return "application/json"
    return "application/octet-stream"


def resolve_gemini_native_attachments(file_ids):
    if not GEMINI_NATIVE_FILES_ENABLED:
        return []
    if not file_ids:
        return []

    docs = get_documents_by_ids(RAG_INDEX_FILE, file_ids)
    if not docs:
        return []

    attachments = []
    for doc in docs:
        if len(attachments) >= max(1, GEMINI_NATIVE_MAX_FILES):
            break
        path = (doc.get("path") or "").strip()
        if not path or not os.path.exists(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in GEMINI_NATIVE_ALLOWED_EXTENSIONS:
            bac_log(f"BAC: skipping native Gemini attachment (unsupported ext): {doc.get('name')}")
            continue
        size = os.path.getsize(path)
        if size > max(1024, GEMINI_NATIVE_MAX_FILE_BYTES):
            bac_log(f"BAC: skipping native Gemini attachment (too large): {doc.get('name')} ({size} bytes)")
            continue
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as exc:
            bac_log(f"BAC: failed to read attachment {path}: {exc}")
            continue
        if not data:
            continue
        attachments.append({
            "name": doc.get("name") or os.path.basename(path),
            "mime_type": _guess_mime_type(path),
            "data": data,
        })

    if attachments:
        bac_log(f"BAC: resolved {len(attachments)} Gemini native attachment(s)")
    return attachments


@app.after_request
def disable_static_cache(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.errorhandler(ValueError)
def handle_value_error(error):
    text = str(error)
    upstream_prefixes = (
        "Gemini HTTP",
        "Gemini request failed",
        "Gemini returned",
        "Claude request failed",
        "Claude returned",
        "Cloudflare HTTP",
        "Cloudflare request failed",
        "Cloudflare returned",
        "Groq HTTP",
        "Groq request failed",
        "Groq returned",
        "OpenRouter HTTP",
        "OpenRouter request failed",
        "OpenRouter returned",
        "Ollama Cloud request failed",
        "Ollama Cloud returned",
    )
    status = 502 if text.startswith(upstream_prefixes) else 400
    return jsonify({"error": text}), status


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code
    bac_log(f"BAC: unhandled exception: {error}")
    return jsonify({"error": str(error)}), 500


# -------------------------
# HOME
# -------------------------

@app.route("/")
def home():
    bac_log("BAC: GET / requested")

    return render_template("index.html")


@app.route("/models", methods=["GET"])
def models():
    enabled = available_models()
    default_model = choose_default_model(enabled)
    compare_defaults = enabled[:2] if len(enabled) >= 2 else enabled
    return jsonify({
        "bac_tool_default": default_model,
        "compare_default": compare_defaults,
        "models": [item for item in MODEL_CATALOG if item["id"] in enabled],
    })


# -------------------------
# BAC_TOOL
# -------------------------

@app.route("/bac_tool", methods=["POST"])
def bac_tool():
    bac_log("BAC: POST /bac_tool started")

    data = request.json or {}
    bac_log(f"BAC: /bac_tool payload keys = {list(data.keys())}")

    model = (data.get("model") or "").strip()
    bac_log(f"BAC: /bac_tool model = {model}")

    message = (data.get("message") or "").strip()
    bac_log(f"BAC: /bac_tool message length = {len(message)}")
    use_fallback = bool(data.get("use_fallback", True))
    bac_log(f"BAC: /bac_tool use_fallback = {use_fallback}")
    file_ids = data.get("file_ids", []) or []
    if not isinstance(file_ids, list):
        return jsonify({"error": "file_ids must be a list"}), 400
    file_ids = [str(item).strip() for item in file_ids if str(item).strip()]
    bac_log(f"BAC: /bac_tool file_ids = {len(file_ids)}")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    enabled_models = available_models()
    if not enabled_models:
        return jsonify({"error": "No remote models are configured. Set CLOUDFLARE_API_TOKEN+CLOUDFLARE_ACCOUNT_ID, GEMINI_API_KEY, OPENROUTER_API_KEY, or OLLAMA_API_KEY in .env."}), 400

    if model not in enabled_models:
        return jsonify({"error": f"Unsupported model: {model}"}), 400

    memory = save_message_and_get_memory(model, "user", message, MAX_CONTEXT_MESSAGES)
    bac_log(f"BAC: /bac_tool context size = {len(memory)} for model {model}")

    model_messages, rag_hits = with_rag_context(memory, file_ids=file_ids)
    bac_log(f"BAC: /bac_tool rag hits = {len(rag_hits)}")

    native_attachments = resolve_gemini_native_attachments(file_ids) if model.startswith("gemini") else []
    response = run_model(model, model_messages, use_fallback=use_fallback, attachments=native_attachments)
    if rag_hits and _looks_like_missing_attachment_reply(response):
        bac_log("BAC: /bac_tool retrying once with stronger attached-file instruction")
        retry_messages = list(model_messages) + [{
            "role": "user",
            "content": (
                "You already have extracted snippets from uploaded files in this chat context. "
                "Do not ask for re-upload. Answer now using those snippets and cite [doc:file#chunk]."
            ),
        }]
        response = run_model(model, retry_messages, use_fallback=use_fallback, attachments=native_attachments)
    bac_log(f"BAC: /bac_tool response length = {len(response) if response else 0}")

    save_message(model, "assistant", response)
    bac_log(f"BAC: /bac_tool saved assistant response for model {model}")
    bac_log("BAC: POST /bac_tool completed")

    return jsonify({
        "response": response,
        "rag_hits": len(rag_hits),
        "attached_files": len(file_ids),
        "native_attachments": len(native_attachments),
    })


# -------------------------
# COMPARE
# -------------------------

@app.route("/compare", methods=["POST"])
def compare():
    bac_log("BAC: POST /compare started")

    data = request.json or {}
    bac_log(f"BAC: /compare payload keys = {list(data.keys())}")

    message = data.get("message", "").strip()
    bac_log(f"BAC: /compare message length = {len(message)}")

    models = data.get("models", [])
    bac_log(f"BAC: /compare models = {models}")
    use_fallback = bool(data.get("use_fallback", True))
    bac_log(f"BAC: /compare use_fallback = {use_fallback}")
    file_ids = data.get("file_ids", []) or []
    if not isinstance(file_ids, list):
        return jsonify({"error": "file_ids must be a list"}), 400
    file_ids = [str(item).strip() for item in file_ids if str(item).strip()]
    bac_log(f"BAC: /compare file_ids = {len(file_ids)}")

    if not message:
        bac_log("BAC: /compare validation failed: empty message")
        return jsonify({"error": "Message is required"}), 400

    if not isinstance(models, list) or not models:
        bac_log("BAC: /compare validation failed: invalid models list")
        return jsonify({"error": "At least one model is required"}), 400

    valid_models = set(available_models())
    if not valid_models:
        return jsonify({"error": "No remote models are configured. Set CLOUDFLARE_API_TOKEN+CLOUDFLARE_ACCOUNT_ID, GEMINI_API_KEY, OPENROUTER_API_KEY, or OLLAMA_API_KEY in .env."}), 400
    invalid_models = [model for model in models if model not in valid_models]
    if invalid_models:
        return jsonify({"error": f"Unsupported model(s): {', '.join(invalid_models)}"}), 400

    gemini_native_attachments = resolve_gemini_native_attachments(file_ids) if any(m.startswith("gemini") for m in models) else []
    result = {}
    workers = max(1, min(len(models), COMPARE_MAX_WORKERS))

    if workers == 1:
        for model in models:
            try:
                result[model] = compare_one_model(
                    model,
                    message,
                    use_fallback=use_fallback,
                    file_ids=file_ids,
                    native_attachments=gemini_native_attachments,
                )
                bac_log(f"BAC: /compare completed model {model}")
            except Exception as exc:
                bac_log(f"BAC: /compare error for model {model}: {exc}")
                result[model] = f"Error: {exc}"
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(compare_one_model, model, message, use_fallback, file_ids, gemini_native_attachments): model
                for model in models
            }

            for future in as_completed(futures):
                model = futures[future]
                try:
                    result[model] = future.result()
                    bac_log(f"BAC: /compare completed model {model}")
                except Exception as exc:
                    bac_log(f"BAC: /compare error for model {model}: {exc}")
                    result[model] = f"Error: {exc}"

    bac_log("BAC: POST /compare completed")
    return jsonify(result)


# -------------------------
# FILE UPLOAD
# -------------------------

@app.route("/upload", methods=["POST"])
def upload():
    bac_log("BAC: POST /upload started")

    file = request.files["file"]
    bac_log(f"BAC: /upload filename = {file.filename}")

    path = os.path.join(

        app.config["UPLOAD_FOLDER"],

        file.filename

    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(path)
    bac_log(f"BAC: /upload saved file to {path}")

    doc_record = index_document_file(
        path,
        index_file=RAG_INDEX_FILE,
        vector_dims=RAG_VECTOR_DIMS,
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
    )
    bac_log(f"BAC: /upload indexed file {doc_record['name']} kind={doc_record.get('kind')} chunks={doc_record['chunk_count']}")
    bac_log("BAC: POST /upload completed")

    return jsonify({"status": "ok", "document": doc_record})


@app.route("/documents", methods=["GET"])
def documents():
    docs = list_documents(RAG_INDEX_FILE)
    return jsonify({
        "count": len(docs),
        "documents": docs
    })


# -------------------------
# MODEL ROUTER
# -------------------------

def run_model(model, messages, use_fallback=True, attachments=None):
    bac_log(f"BAC: run_model called with model = {model}, messages = {len(messages)}")
    if model.startswith("@cf/"):
        bac_log("BAC: run_model routing to Cloudflare")
        return cloudflare_bac_tool(model, messages)

    # if model.startswith("claude-"):
    #     bac_log("BAC: run_model routing to Claude")
    #     return claude_bac_tool(model, messages)

    if model.startswith("gemini"):
        bac_log("BAC: run_model routing to Gemini")
        if not use_fallback:
            return gemini_bac_tool(model, messages, attachments=attachments)
        try:
            return gemini_bac_tool(model, messages, attachments=attachments)
        except ValueError as exc:
            error_text = str(exc)
            should_fallback = (
                model == "gemini-2.0-flash"
                and "HTTP 429" in error_text
                and "RESOURCE_EXHAUSTED" in error_text
            )
            if should_fallback:
                fallback_model = "gemini-2.0-flash-lite"
                bac_log(f"BAC: fallback from {model} to {fallback_model} after quota/rate error")
                try:
                    return gemini_bac_tool(fallback_model, messages, attachments=attachments)
                except ValueError:
                    # if GROQ_API_KEY:
                    #     groq_fallback = "llama-3.1-8b-instant"
                    #     bac_log(f"BAC: fallback from Gemini to Groq model {groq_fallback}")
                    #     try:
                    #         return groq_bac_tool(groq_fallback, messages)
                    #     except ValueError:
                    #         if OPENROUTER_API_KEY:
                    #             or_fallback = "openai/gpt-oss-20b:free"
                    #             bac_log(f"BAC: fallback from Groq to OpenRouter model {or_fallback}")
                    #             return openrouter_bac_tool(or_fallback, messages)
                    #         raise
                    if OPENROUTER_API_KEY:
                        or_fallback = "openai/gpt-oss-20b:free"
                        bac_log(f"BAC: fallback from Gemini to OpenRouter model {or_fallback}")
                        return openrouter_bac_tool(or_fallback, messages)
                    raise
            # if "HTTP 429" in error_text and "RESOURCE_EXHAUSTED" in error_text and GROQ_API_KEY:
            #     groq_fallback = "llama-3.1-8b-instant"
            #     bac_log(f"BAC: fallback from Gemini to Groq model {groq_fallback}")
            #     try:
            #         return groq_bac_tool(groq_fallback, messages)
            #     except ValueError:
            #         if OPENROUTER_API_KEY:
            #             or_fallback = "openai/gpt-oss-20b:free"
            #             bac_log(f"BAC: fallback from Groq to OpenRouter model {or_fallback}")
            #             return openrouter_bac_tool(or_fallback, messages)
            #         raise
            if "HTTP 429" in error_text and "RESOURCE_EXHAUSTED" in error_text and OPENROUTER_API_KEY:
                or_fallback = "openai/gpt-oss-20b:free"
                bac_log(f"BAC: fallback from Gemini to OpenRouter model {or_fallback}")
                return openrouter_bac_tool(or_fallback, messages)
            raise

    # elif model in {
    #     "llama-3.1-8b-instant",
    #     "llama-3.3-70b-versatile",
    #     "gemma2-9b-it",
    #     "openai/gpt-oss-20b",
    #     "openai/gpt-oss-120b",
    # }:
    #     bac_log("BAC: run_model routing to Groq")
    #     if not use_fallback:
    #         return groq_bac_tool(model, messages)
    #     try:
    #         return groq_bac_tool(model, messages)
    #     except ValueError:
    #         if OPENROUTER_API_KEY:
    #             or_fallback = "openai/gpt-oss-20b:free"
    #             bac_log(f"BAC: fallback from Groq to OpenRouter model {or_fallback}")
    #             return openrouter_bac_tool(or_fallback, messages)
    #         raise

    elif model in {"openai/gpt-oss-20b:free"}:
        bac_log("BAC: run_model routing to OpenRouter")
        return openrouter_bac_tool(model, messages)

    elif model in {"gpt-oss:20b", "gpt-oss:120b"}:
        bac_log("BAC: run_model routing to Ollama Cloud")
        return ollama_cloud_bac_tool(model, messages)

    else:
        raise ValueError(f"Unsupported model: {model}.")


def compare_one_model(model, message, use_fallback=True, file_ids=None, native_attachments=None):
    bac_log(f"BAC: /compare processing model {model}")
    memory = save_message_and_get_memory(model, "user", message, MAX_CONTEXT_MESSAGES)
    bac_log(f"BAC: /compare context size = {len(memory)} for model {model}")
    model_messages, rag_hits = with_rag_context(memory, file_ids=file_ids)
    bac_log(f"BAC: /compare rag hits = {len(rag_hits)} for model {model}")
    attachments = native_attachments if model.startswith("gemini") else None
    answer = run_model(model, model_messages, use_fallback=use_fallback, attachments=attachments)
    if rag_hits and _looks_like_missing_attachment_reply(answer):
        bac_log(f"BAC: /compare retrying once for model {model} with stronger attached-file instruction")
        retry_messages = list(model_messages) + [{
            "role": "user",
            "content": (
                "You already have extracted snippets from uploaded files in this chat context. "
                "Do not ask for re-upload. Answer now using those snippets and cite [doc:file#chunk]."
            ),
        }]
        answer = run_model(model, retry_messages, use_fallback=use_fallback, attachments=attachments)
    save_message(model, "assistant", answer)
    return answer


def available_models():
    models = []
    for item in MODEL_CATALOG:
        if (
            item["key_name"] == "CLOUDFLARE_API_TOKEN"
            and CLOUDFLARE_API_TOKEN
            and CLOUDFLARE_ACCOUNT_ID
        ):
            models.append(item["id"])
        # if item["key_name"] == "ANTHROPIC_API_KEY" and ANTHROPIC_API_KEY:
        #     models.append(item["id"])
        if item["key_name"] == "GEMINI_API_KEY" and GEMINI_API_KEY:
            models.append(item["id"])
        # if item["key_name"] == "GROQ_API_KEY" and GROQ_API_KEY:
        #     models.append(item["id"])
        if item["key_name"] == "OPENROUTER_API_KEY" and OPENROUTER_API_KEY:
            models.append(item["id"])
        if item["key_name"] == "OLLAMA_API_KEY" and OLLAMA_API_KEY:
            models.append(item["id"])
    return models


def check_model_health(model):
    start = time.time()
    probe_messages = [{"role": "user", "content": "Reply with exactly: OK"}]
    try:
        output = run_model(model, probe_messages, use_fallback=False)
        text = (output or "").strip()
        if not text:
            return {
                "model": model,
                "status": "failing",
                "detail": "Empty response",
                "seconds": round(time.time() - start, 2),
            }
        return {
            "model": model,
            "status": "working",
            "detail": text[:120],
            "seconds": round(time.time() - start, 2),
        }
    except Exception as exc:
        return {
            "model": model,
            "status": "failing",
            "detail": str(exc)[:220],
            "seconds": round(time.time() - start, 2),
        }


@app.route("/health/models", methods=["GET", "POST"])
def health_models():
    models = available_models()
    if request.method == "POST":
        payload = request.json or {}
        requested = payload.get("models", [])
        if requested is not None and not isinstance(requested, list):
            return jsonify({"error": "models must be a list"}), 400
        requested = [str(item).strip() for item in (requested or []) if str(item).strip()]
        if requested:
            allowed = set(models)
            models = [m for m in requested if m in allowed]

    checked_at = datetime.now(timezone.utc).isoformat()
    if not models:
        return jsonify({
            "checked_at": checked_at,
            "count": 0,
            "results": [],
        })

    results = []
    workers = max(1, min(len(models), COMPARE_MAX_WORKERS))
    if workers == 1:
        for model in models:
            results.append(check_model_health(model))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(check_model_health, model): model for model in models}
            for future in as_completed(futures):
                results.append(future.result())

    results.sort(key=lambda item: item["model"])
    return jsonify({
        "checked_at": checked_at,
        "count": len(results),
        "results": results,
    })


def choose_default_model(enabled_models):
    if not enabled_models:
        return ""
    # if "claude-3-5-haiku-latest" in enabled_models:
    #     return "claude-3-5-haiku-latest"
    # if "llama-3.1-8b-instant" in enabled_models:
    #     return "llama-3.1-8b-instant"
    if "gpt-oss:20b" in enabled_models:
        return "gpt-oss:20b"
    if "openai/gpt-oss-20b:free" in enabled_models:
        return "openai/gpt-oss-20b:free"
    return enabled_models[0]


# -------------------------

if __name__ == "__main__":
    bac_log(f"BAC: starting Flask app on port 5050 with debug={APP_DEBUG}")

    app.run(debug=APP_DEBUG, port=5050)
