"""
Test OpenRouter API integratie
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter configuratie
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env file!")
    print("Please add your OpenRouter API key to .env")
    exit(1)

print("=" * 80)
print("🌙 OPENROUTER API INTEGRATIE TEST")
print("=" * 80)

print(f"\n🔑 API Key: {OPENROUTER_API_KEY[:20]}...{OPENROUTER_API_KEY[-10:]}")

# Test verschillende modellen - using official upstream model IDs
test_models = [
    "google/gemini-2.5-flash",  # Gemini 2.5 Flash
    "anthropic/claude-sonnet-4.5",  # Claude 4.5 Sonnet
    "openai/gpt-5-mini",  # GPT-5 Mini
    "moonshot/kimi-k2",  # Kimi K2
    "qwen/qwen3-max",  # Qwen 3 Max
]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

print(f"\n📊 Testing {len(test_models)} models:\n")

for i, model in enumerate(test_models, 1):
    print(f"{i}. Testing {model}...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello from Moon Dev!' and nothing else."}
            ],
            max_tokens=20,
        )

        content = response.choices[0].message.content
        print(f"   ✅ SUCCESS: {content}")

    except Exception as e:
        error_msg = str(e)
        if "Access denied" in error_msg or "401" in error_msg:
            print(f"   ❌ ACCESS DENIED - API key heeft geen credits of permissies")
        elif "404" in error_msg:
            print(f"   ❌ MODEL NOT FOUND - Model bestaat niet")
        elif "429" in error_msg:
            print(f"   ❌ RATE LIMITED - Te veel requests")
        else:
            print(f"   ❌ ERROR: {error_msg[:100]}")

print(f"\n{'='*80}")
print("CONCLUSIE")
print(f"{'='*80}\n")

print("Als alle modellen 'Access denied' geven:")
print("1. OpenRouter account heeft geen credits")
print("2. Voeg credits toe op https://openrouter.ai/credits")
print("3. Of genereer nieuwe API key")
print("")
print("Alternatief: gebruik rbi_systematic_generator.py (geen API nodig)")
print(f"\n{'='*80}\n")
