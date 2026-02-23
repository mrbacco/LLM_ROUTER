


"""
import ollama

client = ollama.Client(host="http://127.0.0.1:11434")

response = client.chat(
    model="mistral",
    messages=[{"role":"user","content":"hello"}]
)

print(response)
"""

"""
from app.llm import stream_chat
import asyncio

async def test():

    messages = [{"role":"user","content":"hello"}]

    async for token in stream_chat("mistral", messages):

        print(token, end="")

asyncio.run(test())

"""

from google import genai
from config import GEMINI_API_KEY

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)