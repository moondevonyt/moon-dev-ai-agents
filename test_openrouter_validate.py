"""
Validate OpenRouter API key with a free model
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

# Try multiple models to see which works
test_models = [
    "google/gemini-2.0-flash-thinking-exp:free",  # Free model
    "meta-llama/llama-3.2-3b-instruct:free",  # Free Llama
    "qwen/qwen-2-7b-instruct:free",  # Free Qwen
    "google/gemini-2.5-flash",  # Paid Gemini
    "anthropic/claude-sonnet-4.5",  # Paid Claude
]

for model_id in test_models:
    cprint(f"\n🧪 Testing: {model_id}", "yellow")
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "Hi"}
            ],
            max_tokens=10
        )
        cprint(f"   ✅ SUCCESS: {response.choices[0].message.content}", "green")
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response'):
            try:
                error_details = e.response.json()
                if 'error' in error_details:
                    error_msg = error_details['error'].get('message', error_msg)
            except:
                pass
        cprint(f"   ❌ FAILED: {error_msg}", "red")

cprint("\n" + "="*80 + "\n", "cyan")
