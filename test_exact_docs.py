"""
EXACTLY as shown in OpenRouter documentation
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print(f"Length: {len(api_key)}")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
    "X-Title": "Moon Dev AI Trading",
  },
  model="openai/gpt-4o",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)

print(completion.choices[0].message.content)
