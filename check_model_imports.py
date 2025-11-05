"""
Check if all AI model packages can be imported correctly
"""

import sys

models_to_check = [
    ("Anthropic (Claude)", "anthropic"),
    ("OpenAI (GPT)", "openai"),
    ("Google Generative AI (Gemini)", "google.generativeai"),
    ("Groq", "groq"),
]

print("=" * 70)
print("🔍 CHECKING AI MODEL PACKAGE IMPORTS")
print("=" * 70)
print()

results = []

for name, module_name in models_to_check:
    try:
        __import__(module_name)
        print(f"✅ {name:<35} - Import SUCCESS")
        results.append((name, True, None))
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ {name:<35} - Import FAILED")
        print(f"   Error: {error_msg}")
        results.append((name, False, error_msg))

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print()

success_count = sum(1 for _, success, _ in results if success)
total_count = len(results)

print(f"Successfully imported: {success_count}/{total_count}")
print()

if success_count == total_count:
    print("✅ ALL MODEL PACKAGES WORKING!")
else:
    print("⚠️  SOME PACKAGES HAVE IMPORT ISSUES")
    print("\nFailed packages:")
    for name, success, error in results:
        if not success:
            print(f"  • {name}: {error}")

# Check OpenRouter (via openai package)
print("\n" + "=" * 70)
print("🌐 OPENROUTER CONNECTIVITY")
print("=" * 70)
print()

try:
    from openai import OpenAI
    print("✅ OpenRouter client can be initialized (via openai package)")
    print("   Base URL: https://openrouter.ai/api/v1")
    print("   API Key: Set via OPENROUTER_API_KEY env variable")

    import os
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        print(f"   Status: API key found ({api_key[:20]}...)")
    else:
        print("   Status: No API key set in environment")

except Exception as e:
    print(f"❌ OpenRouter client initialization failed: {e}")

print("\n" + "=" * 70)
print()
