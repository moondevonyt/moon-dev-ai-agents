"""
Test OpenRouter API integratie
"""

import os
from openai import OpenAI

# OpenRouter configuratie
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

print("=" * 80)
print("🌙 OPENROUTER API INTEGRATIE TEST")
print("=" * 80)

print(f"\n🔑 API Key: {OPENROUTER_API_KEY[:20]}...{OPENROUTER_API_KEY[-10:]}")

# Test verschillende modellen
test_models = [
    "google/gemini-2.0-flash-thinking-exp:free",  # Gratis model
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "moonshot/kimi-k2",
    "deepseek/deepseek-chat",
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
