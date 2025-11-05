"""
🌙 Moon Dev - OpenRouter Integration Test
Test script to verify OpenRouter configuration
"""

import sys
from pathlib import Path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.models.model_factory import model_factory
from termcolor import cprint

def test_openrouter():
    """Test OpenRouter integration"""

    cprint("\n" + "=" * 60, "cyan")
    cprint("🌙 TESTING OPENROUTER INTEGRATION", "cyan")
    cprint("=" * 60, "cyan")

    # Test models to try
    test_models = [
        "google/gemini-2.5-flash",
        "moonshot/kimi-k2",
        "anthropic/claude-haiku-4.5",
        "qwen/qwen3-max",
    ]

    print("\n📋 Testing models:")
    for model_name in test_models:
        print(f"  • {model_name}")

    results = {}

    for model_name in test_models:
        cprint(f"\n{'='*60}", "yellow")
        cprint(f"🧪 Testing: {model_name}", "yellow")
        cprint(f"{'='*60}", "yellow")

        try:
            # Get model from factory
            model = model_factory.get_model("openrouter", model_name)

            if not model:
                results[model_name] = "❌ Failed to initialize"
                cprint(f"❌ Failed to get model", "red")
                continue

            # Test simple query
            system_prompt = "You are a helpful assistant."
            user_prompt = "Say 'Hello from OpenRouter!' and nothing else."

            cprint(f"📤 Sending test query...", "cyan")
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_prompt,
                temperature=0.7,
                max_tokens=50
            )

            if response and response.content:
                results[model_name] = "✅ Success"
                cprint(f"✅ Response received: {response.content[:100]}", "green")
            else:
                results[model_name] = "❌ No response"
                cprint(f"❌ No response received", "red")

        except Exception as e:
            results[model_name] = f"❌ Error: {str(e)[:50]}"
            cprint(f"❌ Error: {str(e)}", "red")

    # Summary
    cprint(f"\n{'='*60}", "cyan")
    cprint("📊 TEST SUMMARY", "cyan")
    cprint(f"{'='*60}", "cyan")

    for model_name, result in results.items():
        status_color = "green" if "✅" in result else "red"
        cprint(f"{model_name:40} {result}", status_color)

    success_count = sum(1 for r in results.values() if "✅" in r)
    total_count = len(results)

    cprint(f"\n{'='*60}", "cyan")
    cprint(f"Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)", "cyan")
    cprint(f"{'='*60}\n", "cyan")

    if success_count == total_count:
        cprint("🎉 ALL TESTS PASSED! OpenRouter is working perfectly!", "green")
        return True
    elif success_count > 0:
        cprint("⚠️  Some tests passed. Check API key and credits.", "yellow")
        return True
    else:
        cprint("❌ All tests failed. Check OPENROUTER_API_KEY in .env", "red")
        return False

if __name__ == "__main__":
    test_openrouter()
