"""
Test all model IDs found in the codebase to see which ones work
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from termcolor import cprint
import time

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')

if not api_key:
    cprint("❌ No API key found!", "red")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
        "X-Title": "Moon Dev AI Trading",
    }
)

# All model IDs from codebase
MODEL_IDS = [
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-opus-4.1",
    "openai/gpt-5-mini",
    "openai/gpt-5",
    "openai/gpt-5-nano",
    "openai/gpt-4.5-preview",
    "qwen/qwen3-max",
    "qwen/qwen3-32b",
    "qwen/qwen3-vl-32b-instruct",
    "deepseek/deepseek-r1-0528",
    "deepseek/deepseek-chat",
    "moonshot/kimi-k2",
    "moonshot/kimi-v1",
]

# Also try some known free models
FREE_MODELS = [
    "google/gemini-2.0-flash-thinking-exp:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
]

print("=" * 100)
cprint("🧪 TESTING ALL MODEL IDS FROM CODEBASE", "cyan")
print("=" * 100)
cprint(f"\n🔑 API Key: {api_key[:20]}...{api_key[-10:]}\n", "yellow")

working_models = []
failed_models = []

def test_model(model_id):
    """Test a single model"""
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return True, response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response'):
            try:
                error_details = e.response.json()
                if 'error' in error_details:
                    error_msg = error_details['error'].get('message', error_msg)
            except:
                pass
        return False, error_msg

# Test paid models
cprint("\n📋 TESTING PAID MODELS (from upstream codebase):", "cyan")
print("-" * 100)

for model_id in MODEL_IDS:
    cprint(f"\n🧪 {model_id}", "yellow")
    success, result = test_model(model_id)

    if success:
        cprint(f"   ✅ SUCCESS: {result}", "green")
        working_models.append(model_id)
    else:
        cprint(f"   ❌ FAILED: {result[:80]}", "red")
        failed_models.append((model_id, result))

    time.sleep(0.5)  # Rate limiting

# Test free models
cprint("\n\n📋 TESTING FREE MODELS:", "cyan")
print("-" * 100)

for model_id in FREE_MODELS:
    cprint(f"\n🧪 {model_id}", "yellow")
    success, result = test_model(model_id)

    if success:
        cprint(f"   ✅ SUCCESS: {result}", "green")
        working_models.append(model_id)
    else:
        cprint(f"   ❌ FAILED: {result[:80]}", "red")
        failed_models.append((model_id, result))

    time.sleep(0.5)

# Summary
print("\n" + "=" * 100)
cprint("📊 SUMMARY", "cyan")
print("=" * 100)

cprint(f"\n✅ Working models: {len(working_models)}/{len(MODEL_IDS) + len(FREE_MODELS)}", "green")
if working_models:
    for model in working_models:
        cprint(f"   • {model}", "green")

cprint(f"\n❌ Failed models: {len(failed_models)}/{len(MODEL_IDS) + len(FREE_MODELS)}", "red")
if failed_models:
    # Group by error
    errors = {}
    for model, error in failed_models:
        error_short = error[:50]
        if error_short not in errors:
            errors[error_short] = []
        errors[error_short].append(model)

    for error, models in errors.items():
        cprint(f"\n   Error: {error}", "yellow")
        for model in models:
            cprint(f"     • {model}", "red")

if working_models:
    print("\n" + "=" * 100)
    cprint("🎯 RECOMMENDED SWARM CONFIGURATION:", "green")
    print("=" * 100)
    print("\nSWARM_MODELS = [")
    for model in working_models[:6]:  # Top 6 for swarm
        print(f'    ("{model}", "{model.split("/")[1]}"),')
    print("]")

print("\n" + "=" * 100 + "\n")
