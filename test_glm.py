"""
Test GLM (Zhipu AI) integration
"""
from src.models.model_factory import ModelFactory
from termcolor import cprint

cprint("\n" + "="*80, "cyan")
cprint("🧪 TESTING GLM (ZHIPU AI) INTEGRATION", "cyan")
cprint("="*80 + "\n", "cyan")

# Initialize ModelFactory
factory = ModelFactory()

# Check if GLM is available
if "glm" in factory._models:
    cprint("✅ GLM model initialized successfully!", "green")

    # Get GLM model
    glm_model = factory.get_model("glm")

    if glm_model:
        cprint(f"\n📝 Model: {glm_model.model_name}", "cyan")
        cprint(f"🔧 Base URL: {glm_model.base_url}", "cyan")

        # Test generation
        cprint("\n🚀 Testing response generation...\n", "yellow")

        try:
            response = glm_model.generate_response(
                system_prompt="You are a helpful AI assistant.",
                user_content="Say 'Hello from GLM!' in one sentence.",
                temperature=0.7,
                max_tokens=50
            )

            cprint("✅ SUCCESS!", "green")
            cprint(f"\n📨 Response: {response.content}\n", "cyan")

            if response.usage:
                cprint(f"📊 Usage: {response.usage}", "yellow")

        except Exception as e:
            cprint(f"\n❌ ERROR: {str(e)}", "red")
            import traceback
            traceback.print_exc()
    else:
        cprint("❌ Failed to get GLM model", "red")
else:
    cprint("❌ GLM not initialized - check GLM_API_KEY in .env", "red")
    cprint("\n📋 Available models:", "yellow")
    for model_type in factory._models.keys():
        cprint(f"  • {model_type}", "cyan")

cprint("\n" + "="*80 + "\n", "cyan")
