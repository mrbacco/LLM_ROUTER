"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Feb 21, 2026

"""
from openai import OpenAI
from config import OPENAI_API_KEY

if not OPENAI_API_KEY:
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)


def openai_chat(model, messages):
    if client is None:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    response = client.chat.completions.create(

        model=model,

        messages=messages

    )

    return response.choices[0].message.content
