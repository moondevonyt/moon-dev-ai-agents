"""
Test GLM via OpenRouter (z-ai/glm-4.6)
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')

cprint(f"\n🔑 API Key: {api_key[:20]}...{api_key[-10:]}", "cyan")
cprint(f"📏 Length: {len(api_key)}\n", "cyan")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Test z-ai/glm-4.6 via OpenRouter
cprint("🧪 Testing z-ai/glm-4.6 via OpenRouter...\n", "yellow")

try:
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
            "X-Title": "Moon Dev AI Trading",
        },
        model="z-ai/glm-4.6",
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello from GLM via OpenRouter!' in one sentence."
            }
        ],
        max_tokens=50
    )

    cprint("✅ SUCCESS!", "green")
    cprint(f"\n📨 Response: {completion.choices[0].message.content}\n", "cyan")

    if hasattr(completion, 'usage'):
        cprint(f"📊 Usage: {completion.usage}", "yellow")

except Exception as e:
    cprint(f"\n❌ ERROR: {str(e)}", "red")
    if hasattr(e, 'response'):
        cprint(f"Status: {e.response.status_code}", "red")
        cprint(f"Body: {e.response.text}", "red")

cprint("\n" + "="*80 + "\n", "cyan")
