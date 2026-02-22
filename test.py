


"""
import ollama

client = ollama.Client(host="http://127.0.0.1:11434")

response = client.chat(
    model="mistral",
    messages=[{"role":"user","content":"hello"}]
)

print(response)
"""

from app.llm import stream_chat
import asyncio

async def test():

    messages = [{"role":"user","content":"hello"}]

    async for token in stream_chat("mistral", messages):

        print(token, end="")

asyncio.run(test())