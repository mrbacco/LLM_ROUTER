# -*- coding: utf-8 -*-
"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""
# -*- coding: utf-8 -*-
"""
GEN_AI_TOOL
FINAL LLM ROUTER

Supports:

- Ollama (async)
- OpenAI
- LM Studio

Fully async streaming
"""

import json
import os
import httpx
from openai import OpenAI


# ==========================
# CONFIG
# ==========================

OLLAMA_URL = "http://localhost:11434/api/chat"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LMSTUDIO_URL = "http://localhost:1234/v1"

# app/llm.py

import ollama
import asyncio


async def generate(model: str, messages: list):

    loop = asyncio.get_running_loop()

    response = await loop.run_in_executor(

        None,

        lambda: ollama.chat(
            model=model,
            messages=messages
        )

    )

    return response["message"]["content"]
