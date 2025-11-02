"""
🧪 Moon Dev's OpenRouter Test Script
Built with love by Moon Dev 🚀

Quick test to verify OpenRouter integration is working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_openrouter():
    """Test OpenRouter integration"""
    print("\n🌙 Moon Dev's OpenRouter Test\n")
    print("="*60)

    try:
        from models.model_factory import ModelFactory

        print("\n✅ Step 1: Importing ModelFactory... SUCCESS")

        # Initialize factory
        factory = ModelFactory()
        print("✅ Step 2: Initializing ModelFactory... SUCCESS")

        # Check if OpenRouter is available
        if not factory.is_model_available('openrouter'):
            print("\n❌ OpenRouter is not available!")
            print("   Make sure OPENROUTER_API_KEY is set in .env")
            print("   Get your key at: https://openrouter.ai/keys")
            return False

        print("✅ Step 3: OpenRouter is available... SUCCESS")

        # Get OpenRouter model
        model = factory.get_model('openrouter', 'anthropic/claude-3.5-sonnet')
        print("✅ Step 4: Getting Claude 3.5 Sonnet via OpenRouter... SUCCESS")

        # Test generation
        print("\n📝 Testing response generation...")
        response = model.generate_response(
            system_prompt="You are a helpful AI assistant.",
            user_content="Say 'Hello from OpenRouter!' if you can read this.",
            temperature=0.7,
            max_tokens=100
        )

        if response and response.content:
            print(f"✅ Step 5: Generate response... SUCCESS")
            print(f"\n🤖 Response: {response.content}\n")

            # Check usage info
            if response.usage:
                print(f"📊 Token Usage:")
                usage = response.usage
                if isinstance(usage, dict):
                    for key, value in usage.items():
                        print(f"   - {key}: {value}")
                else:
                    print(f"   - {usage}")

            print("\n" + "="*60)
            print("🎉 ALL TESTS PASSED! OpenRouter is working!")
            print("="*60)

            # Model suggestions
            print("\n💡 Suggested models for different use cases:")
            print("   - Best balance: anthropic/claude-3.5-sonnet")
            print("   - Cheapest: mistralai/mistral-small")
            print("   - Best reasoning: deepseek/deepseek-reasoner")
            print("   - Fastest: anthropic/claude-3-haiku")
            print("\n   See all models: https://openrouter.ai/models")

            return True
        else:
            print("❌ Step 5: Generate response... FAILED")
            print("   No response content received")
            return False

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Make sure you're in the project root directory")
        return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Helpful error messages
        error_str = str(e).lower()
        if "api key" in error_str or "unauthorized" in error_str:
            print("\n💡 TIP: Check your OPENROUTER_API_KEY in .env")
            print("   Get your key at: https://openrouter.ai/keys")
        elif "credits" in error_str:
            print("\n💡 TIP: Add credits at: https://openrouter.ai/credits")
        elif "rate limit" in error_str:
            print("\n💡 TIP: Rate limit hit - wait a moment and try again")

        return False

if __name__ == "__main__":
    success = test_openrouter()
    sys.exit(0 if success else 1)
