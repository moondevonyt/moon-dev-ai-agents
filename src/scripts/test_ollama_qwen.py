"""
🌙 Test Script for Ollama Qwen3:8b Model
Tests the qwen3:8b model via local Ollama
Built with love by Moon Dev 🚀
"""

import os
import sys
from pathlib import Path
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.ollama_model import OllamaModel

def test_ollama_qwen():
    """Test the Ollama Qwen3:8b model"""
    cprint("\n" + "="*60, "cyan")
    cprint("🌙 Moon Dev's Ollama Qwen3:8b Test Script", "cyan", attrs=['bold'])
    cprint("="*60 + "\n", "cyan")

    try:
        # Initialize the model
        cprint("📡 Initializing Ollama Qwen3:8b model...", "yellow")
        model = OllamaModel(model_name="qwen3:8b")

        cprint("\n✅ Model initialized successfully!", "green")

        # Test prompt
        test_system_prompt = "You are a helpful AI assistant. Provide direct, concise answers without showing your internal thinking process."
        test_user_prompt = """Analyze Bitcoin's current market sentiment in 2-3 sentences. Be concise and actionable."""

        cprint("\n" + "="*60, "cyan")
        cprint("📝 Test Prompt:", "yellow", attrs=['bold'])
        cprint("="*60, "cyan")
        cprint(test_user_prompt, "white")

        cprint("\n⏳ Generating response...", "yellow")

        # Generate response
        response = model.generate_response(
            system_prompt=test_system_prompt,
            user_content=test_user_prompt,
            temperature=0.7
        )

        if response and response.content:
            cprint("\n" + "="*60, "green")
            cprint("✅ Response Received!", "green", attrs=['bold'])
            cprint("="*60, "green")
            cprint(response.content, "white")

            cprint("\n" + "="*60, "green")
            cprint("✨ TEST PASSED! Ollama Qwen3:8b is working! ✨", "green", attrs=['bold'])
            cprint("="*60 + "\n", "green")
            return True
        else:
            cprint("\n❌ No response received from model", "red")
            return False

    except Exception as e:
        cprint("\n" + "="*60, "red")
        cprint("❌ TEST FAILED!", "red", attrs=['bold'])
        cprint("="*60, "red")
        cprint(f"Error: {str(e)}", "red")

        import traceback
        cprint("\n📋 Full traceback:", "red")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ollama_qwen()

    if success:
        cprint("\n🚀 Ready to integrate into trading agent!", "green", attrs=['bold'])
        sys.exit(0)
    else:
        cprint("\n⚠️  Fix issues before integrating", "yellow", attrs=['bold'])
        sys.exit(1)
