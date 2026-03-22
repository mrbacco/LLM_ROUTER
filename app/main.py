# -*- coding: utf-8 -*-
"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select

from app.database import engine, SessionLocal, Base
from app.models import ChatMessage

from app.llm import generate
from app.file_parser import parse_file

# app/main.py

import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.llm import generate


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home():

    return FileResponse("static/index.html")


# ------------------------
# CHAT ENDPOINT
# ------------------------

@app.post("/chat")
async def chat(request: Request):

    try:

        data = await request.json()

        prompt = data.get("message")

        model = data.get("model", "phi3")

        messages = [

            {"role": "user", "content": prompt}

        ]

        from app.llm import generate

        reply = await generate(model, messages)

        return {"response": reply}

    except Exception as e:

        print("CHAT ERROR:", e)

        return {"error": str(e)}
# ------------------------
# COMPARE ENDPOINT
# ------------------------

@app.post("/compare")
async def compare(request: Request):

    try:

        data = await request.json()

        prompt = data["message"]

        models = data["models"]


        async def run(model):

            messages = [

                {"role": "user", "content": prompt}

            ]

            result = await generate(model, messages)

            return model, result


        results = await asyncio.gather(

            *[run(m) for m in models]

        )


        return {

            model: text

            for model, text in results

        }


    except Exception as e:

        print("COMPARE ERROR:", str(e))

        return {"error": str(e)}