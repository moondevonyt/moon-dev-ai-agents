"""
🌙 Test Script for Groq Qwen3-32B Model
Tests the qwen/qwen3-32b model via Groq API
Built with love by Moon Dev 🚀
"""

import os
import sys
from pathlib import Path
from termcolor import cprint
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import base_model first
import importlib.util
spec_base = importlib.util.spec_from_file_location(
    "base_model",
    os.path.join(project_root, "src/models/base_model.py")
)
base_module = importlib.util.module_from_spec(spec_base)
sys.modules['src.models.base_model'] = base_module
spec_base.loader.exec_module(base_module)

# Make base_model classes available for groq_model's relative import
sys.modules['models.base_model'] = base_module

# Import groq_model
spec = importlib.util.spec_from_file_location(
    "groq_model",
    os.path.join(project_root, "src/models/groq_model.py")
)
groq_module = importlib.util.module_from_spec(spec)

# Inject base model classes before executing
groq_module.BaseModel = base_module.BaseModel
groq_module.ModelResponse = base_module.ModelResponse

# Now execute the module
import groq as groq_client  # Import the groq package
groq_module.Groq = groq_client.Groq

# Read and exec the file manually to avoid import issues
with open(os.path.join(project_root, "src/models/groq_model.py"), 'r') as f:
    code = f.read()
    # Replace relative imports
    code = code.replace('from .base_model import BaseModel, ModelResponse', '# BaseModel and ModelResponse injected')
    code = code.replace('from groq import Groq', '# Groq injected')
    exec(code, groq_module.__dict__)

GroqModel = groq_module.GroqModel

# Load environment variables
load_dotenv()

def test_qwen_model():
    """Test the Qwen3-32B model"""
    cprint("\n" + "="*60, "cyan")
    cprint("🌙 Moon Dev's Groq Qwen3-32B Test Script", "cyan", attrs=['bold'])
    cprint("="*60 + "\n", "cyan")

    # Get API key
    api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        cprint("❌ GROQ_API_KEY not found in .env file!", "red")
        cprint("Please add your Groq API key to .env", "yellow")
        return False

    cprint(f"✅ API Key found: {api_key[:10]}...{api_key[-10:]}", "green")

    try:
        # Initialize the model
        cprint("\n📡 Initializing Qwen3-32B model...", "yellow")
        model = GroqModel(api_key=api_key, model_name="qwen/qwen3-32b")

        cprint("\n✅ Model initialized successfully!", "green")

        # Test prompt
        test_system_prompt = "You are a helpful AI assistant. Provide direct, concise answers without showing your internal thinking process."
        test_user_prompt = """Analyze Bitcoin's current market sentiment in 2-3 sentences. Be concise and actionable."""

        cprint("\n" + "="*60, "cyan")
        cprint("📝 Test Prompt:", "yellow", attrs=['bold'])
        cprint("="*60, "cyan")
        cprint(test_user_prompt, "white")

        cprint("\n⏳ Generating response...", "yellow")

        # Generate response (increased max_tokens to allow model to finish thinking + provide actual response)
        response = model.generate_response(
            system_prompt=test_system_prompt,
            user_content=test_user_prompt,
            temperature=0.7,
            max_tokens=2000
        )

        if response and response.content:
            cprint("\n" + "="*60, "green")
            cprint("✅ Response Received!", "green", attrs=['bold'])
            cprint("="*60, "green")
            cprint(response.content, "white")

            # Show usage stats
            if response.usage:
                cprint("\n" + "="*60, "cyan")
                cprint("📊 Usage Statistics:", "cyan", attrs=['bold'])
                cprint("="*60, "cyan")
                cprint(f"  📥 Input tokens: {response.usage.prompt_tokens}", "white")
                cprint(f"  📤 Output tokens: {response.usage.completion_tokens}", "white")
                cprint(f"  💰 Total tokens: {response.usage.total_tokens}", "white")

            cprint("\n" + "="*60, "green")
            cprint("✨ TEST PASSED! Qwen3-32B is working! ✨", "green", attrs=['bold'])
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
    success = test_qwen_model()

    if success:
        cprint("\n🚀 Ready to integrate into trading agent!", "green", attrs=['bold'])
        sys.exit(0)
    else:
        cprint("\n⚠️  Fix issues before integrating", "yellow", attrs=['bold'])
        sys.exit(1)
