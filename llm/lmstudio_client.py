"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""
from openai import OpenAI
from config import LMSTUDIO_URL

client = OpenAI(

    base_url=LMSTUDIO_URL,

    api_key="lmstudio"

)


def lmstudio_chat(model, messages):

    response = client.chat.completions.create(

        model=model,

        messages=messages

    )

    return response.choices[0].message.content