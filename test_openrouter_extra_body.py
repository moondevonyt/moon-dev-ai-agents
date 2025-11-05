"""
Test OpenRouter with extra_body parameter (from official docs)
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print(f"Length: {len(api_key)}")

openai_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

print("\n🧪 Testing with extra_body (models fallback)...")

try:
    completion = openai_client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
            "X-Title": "Moon Dev AI Trading",
        },
        model="openai/gpt-4o",
        extra_body={
            "models": ["anthropic/claude-3.5-sonnet", "google/gemini-pro-1.5"],
        },
        messages=[
            {
                "role": "user",
                "content": "Say hello in one word"
            }
        ]
    )

    print(f"\n✅ SUCCESS!")
    print(f"Response: {completion.choices[0].message.content}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    if hasattr(e, 'response'):
        print(f"Status: {e.response.status_code}")
        print(f"Body: {e.response.text}")
