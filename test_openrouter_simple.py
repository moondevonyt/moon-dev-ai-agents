"""
Simple OpenRouter API test to see exact error messages
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')

cprint(f"\n🔑 API Key: {api_key[:20]}...{api_key[-10:]}", "cyan")
cprint(f"📏 Length: {len(api_key)} chars\n", "cyan")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
        "X-Title": "Moon Dev AI Trading",
    }
)

# Try one simple request
try:
    cprint("🚀 Testing with google/gemini-2.5-flash (official upstream model ID)...\n", "yellow")
    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {"role": "user", "content": "Say hello in 5 words"}
        ],
        max_tokens=50
    )
    cprint(f"✅ SUCCESS!", "green")
    cprint(f"Response: {response.choices[0].message.content}", "cyan")
except Exception as e:
    cprint(f"\n❌ ERROR:", "red")
    cprint(f"Type: {type(e).__name__}", "red")
    cprint(f"Message: {str(e)}", "red")

    # Try to get more details
    if hasattr(e, 'response'):
        cprint(f"\n📋 Response details:", "yellow")
        cprint(f"Status code: {e.response.status_code}", "yellow")
        cprint(f"Headers: {dict(e.response.headers)}", "yellow")
        cprint(f"Body: {e.response.text}", "yellow")

    if hasattr(e, 'body'):
        cprint(f"\n📋 Body: {e.body}", "yellow")
