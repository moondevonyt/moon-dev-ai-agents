"""
Test with REAL, currently available OpenRouter models
Based on official documentation examples
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')

if not api_key:
    cprint("❌ No API key found!", "red")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Test with REAL models that actually exist (not future models)
REAL_MODELS = [
    "openai/gpt-4o",                    # GPT-4o (current, not future gpt-5)
    "openai/gpt-4o-mini",               # GPT-4o mini
    "anthropic/claude-3.5-sonnet",      # Claude 3.5 (not 4.5)
    "anthropic/claude-3-haiku",         # Claude 3 Haiku
    "google/gemini-pro-1.5",            # Gemini Pro 1.5
    "google/gemini-flash-1.5",          # Gemini Flash 1.5
    "qwen/qwen-2.5-72b-instruct",       # Qwen 2.5 (not qwen3)
    "deepseek/deepseek-chat",           # DeepSeek Chat
    "meta-llama/llama-3.1-70b-instruct", # Llama 3.1
]

print("=" * 100)
cprint("🧪 TESTING REAL, CURRENTLY AVAILABLE MODELS", "cyan")
print("=" * 100)
cprint(f"\n🔑 API Key: {api_key[:20]}...{api_key[-10:]}\n", "yellow")

working = []
failed = []

for model_id in REAL_MODELS:
    cprint(f"\n🧪 {model_id}", "yellow")

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
                "X-Title": "Moon Dev AI Trading",
            },
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello' in one word"
                }
            ],
            max_tokens=10
        )

        response = completion.choices[0].message.content
        cprint(f"   ✅ SUCCESS: {response}", "green")
        working.append(model_id)

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response'):
            try:
                error_details = e.response.json()
                if 'error' in error_details:
                    error_msg = error_details['error'].get('message', error_msg)
            except:
                pass
        cprint(f"   ❌ FAILED: {error_msg[:80]}", "red")
        failed.append((model_id, error_msg))

# Summary
print("\n" + "=" * 100)
cprint("📊 SUMMARY", "cyan")
print("=" * 100)

cprint(f"\n✅ Working models: {len(working)}/{len(REAL_MODELS)}", "green")
if working:
    for model in working:
        cprint(f"   • {model}", "green")

cprint(f"\n❌ Failed models: {len(failed)}/{len(REAL_MODELS)}", "red")
if failed:
    for model, error in failed:
        cprint(f"   • {model}: {error[:60]}", "red")

if working:
    print("\n" + "=" * 100)
    cprint("🎯 UPDATE SWARM AGENT WITH THESE WORKING MODELS:", "green")
    print("=" * 100)
    print("\nSWARM_MODELS = {")
    for i, model in enumerate(working[:6], 1):
        model_name = model.split('/')[-1].replace('-', '_')
        print(f'    "model_{i}": (True, "openrouter", "{model}"),')
    print("}")

print("\n" + "=" * 100 + "\n")
