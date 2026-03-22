"""
GEN_AI_TOOL project
Router and AI responses comparison tool done with flask

mrbacco04@gmail.com
Q2, 2026

"""

import ollama


def ollama_chat(model, messages):

    response = ollama.chat(

        model=model,

        messages=messages

    )

    return response["message"]["content"]