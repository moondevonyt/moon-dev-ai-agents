"""
🌙 Moon Dev's OpenRouter Key Rotation Test Script
Built with love by Moon Dev 🚀

Test the OpenRouter API key rotation and Telegram notifications.
"""

import os
from termcolor import cprint
from src.models.model_factory import model_factory
from src.utils.telegram_notifier import get_telegram_notifier


def test_telegram():
    """Test Telegram notifications"""
    cprint("\n" + "="*80, "cyan")
    cprint("📱 TELEGRAM NOTIFICATION TEST", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    notifier = get_telegram_notifier()
    
    if not notifier.enabled:
        cprint("⚠️  Telegram not configured", "yellow")
        cprint("   Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env", "yellow")
        cprint("   See TELEGRAM_SETUP.md for instructions", "yellow")
        return False
    
    cprint("✅ Telegram configured", "green")
    cprint(f"   Bot Token: {notifier.bot_token[:10]}...", "green")
    cprint(f"   Chat ID: {notifier.chat_id}", "green")
    
    cprint("\n📤 Sending test message...", "cyan")
    success = notifier.send_message(
        "🌙 <b>Test Nachricht</b>\n\n"
        "Wenn du diese Nachricht siehst, funktioniert die Telegram-Integration! ✅\n\n"
        "<i>Moon Dev's OpenRouter Key Rotation System</i>"
    )
    
    if success:
        cprint("✅ Test message sent successfully!", "green")
        cprint("   Check your Telegram app!", "green")
        return True
    else:
        cprint("❌ Failed to send test message", "red")
        cprint("   Check your credentials in .env", "red")
        return False


def test_openrouter_keys():
    """Test OpenRouter API key configuration"""
    cprint("\n" + "="*80, "cyan")
    cprint("🔑 OPENROUTER API KEYS TEST", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    # Check for API keys in environment
    api_keys = []
    for i in range(1, 21):
        key = os.getenv(f"OPENROUTER_API_KEY_{i}")
        if key:
            api_keys.append((i, key))
    
    if not api_keys:
        cprint("❌ No OpenRouter API keys found!", "red")
        cprint("   Add OPENROUTER_API_KEY_1, _2, etc. to .env", "red")
        cprint("   See OPENROUTER_KEY_ROTATION.md for instructions", "red")
        return False
    
    cprint(f"✅ Found {len(api_keys)} API keys:", "green")
    for idx, key in api_keys:
        # Show first and last 4 chars only for security
        masked_key = f"{key[:7]}...{key[-4:]}"
        cprint(f"   Key #{idx}: {masked_key} ({len(key)} chars)", "green")
    
    return True


def test_openrouter_model():
    """Test OpenRouter model initialization and simple request"""
    cprint("\n" + "="*80, "cyan")
    cprint("🤖 OPENROUTER MODEL TEST", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    try:
        cprint("🔄 Getting OpenRouter model from factory...", "cyan")
        model = model_factory.get_model("openrouter")
        
        if not model:
            cprint("❌ Failed to get OpenRouter model", "red")
            cprint("   Make sure API keys are configured in .env", "red")
            return False
        
        cprint(f"✅ Model initialized: {model.model_name}", "green")
        cprint(f"   Total keys available: {len(model.api_keys)}", "green")
        cprint(f"   Current key: #{model.current_key_index + 1}", "green")
        
        # Test a simple request
        cprint("\n📝 Sending test request...", "cyan")
        response = model.generate_response(
            system_prompt="You are a helpful assistant. Answer in 1 short sentence.",
            user_content="What is 2+2?",
            max_tokens=50
        )
        
        if response:
            cprint(f"✅ Response received: {response.content}", "green")
            cprint(f"   Model: {response.model_name}", "green")
            if hasattr(response, 'usage'):
                cprint(f"   Tokens used: {response.usage.total_tokens}", "green")
            return True
        else:
            cprint("❌ No response received", "red")
            return False
            
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return False


def test_key_rotation_logic():
    """Test key rotation logic (without actually hitting rate limits)"""
    cprint("\n" + "="*80, "cyan")
    cprint("🔄 KEY ROTATION LOGIC TEST", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    try:
        model = model_factory.get_model("openrouter")
        
        if not model:
            cprint("❌ Model not available", "red")
            return False
        
        if len(model.api_keys) < 2:
            cprint("⚠️  Only 1 key available, can't test rotation", "yellow")
            cprint("   Add more keys to .env to test rotation", "yellow")
            return False
        
        cprint(f"✅ {len(model.api_keys)} keys available for rotation", "green")
        
        # Simulate marking first key as failed
        cprint("\n🧪 Simulating rate limit on Key #1...", "cyan")
        original_key = model.current_key_index
        model.failed_keys_today.add(0)  # Mark key 1 as failed
        
        cprint("🔄 Attempting rotation...", "cyan")
        success = model.rotate_to_next_key()
        
        if success and model.current_key_index != original_key:
            cprint(f"✅ Successfully rotated to Key #{model.current_key_index + 1}", "green")
            
            # Reset for next tests
            model.failed_keys_today.clear()
            model.current_key_index = 0
            return True
        else:
            cprint("❌ Rotation failed or stayed on same key", "red")
            return False
            
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return False


def main():
    """Run all tests"""
    cprint("\n" + "="*80, "cyan")
    cprint("🌙 MOON DEV'S OPENROUTER KEY ROTATION TEST SUITE", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    results = {}
    
    # Test 1: API Keys Configuration
    results['keys'] = test_openrouter_keys()
    
    # Test 2: Telegram Notifications
    results['telegram'] = test_telegram()
    
    # Test 3: OpenRouter Model
    results['model'] = test_openrouter_model()
    
    # Test 4: Key Rotation Logic
    results['rotation'] = test_key_rotation_logic()
    
    # Summary
    cprint("\n" + "="*80, "cyan")
    cprint("📊 TEST SUMMARY", "cyan")
    cprint("="*80 + "\n", "cyan")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        color = "green" if passed else "red"
        cprint(f"{status} - {test_name.upper()}", color)
    
    all_passed = all(results.values())
    
    cprint("\n" + "="*80, "cyan")
    if all_passed:
        cprint("🎉 ALL TESTS PASSED!", "green")
        cprint("   Your OpenRouter key rotation system is ready!", "green")
        cprint("   You can now use it in your agents!", "green")
    else:
        cprint("⚠️  SOME TESTS FAILED", "yellow")
        cprint("   Review the errors above and check:", "yellow")
        cprint("   • .env file has all required variables", "yellow")
        cprint("   • API keys are valid", "yellow")
        cprint("   • Telegram bot is configured (optional)", "yellow")
        cprint("\n   See documentation:", "yellow")
        cprint("   • OPENROUTER_KEY_ROTATION.md", "yellow")
        cprint("   • TELEGRAM_SETUP.md", "yellow")
    cprint("="*80 + "\n", "cyan")


if __name__ == "__main__":
    main()
