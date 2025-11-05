"""
Fetch all available models from OpenRouter API
"""
import requests
import json
import os
from termcolor import cprint
from dotenv import load_dotenv

load_dotenv()

# OpenRouter models endpoint
url = "https://openrouter.ai/api/v1/models"

# Add API key authentication
api_key = os.getenv('OPENROUTER_API_KEY')
headers = {}
if api_key:
    headers['Authorization'] = f'Bearer {api_key}'

cprint("\n🌙 Fetching OpenRouter Models List...\n", "cyan")
if api_key:
    cprint(f"🔑 Using API key: {api_key[:20]}...\n", "cyan")

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    models = data.get('data', [])

    cprint(f"✅ Found {len(models)} models\n", "green")

    # Filter for popular providers
    providers = {
        'google': [],
        'anthropic': [],
        'openai': [],
        'qwen': [],
        'deepseek': [],
        'moonshot': [],
        'meta-llama': [],
    }

    for model in models:
        model_id = model.get('id', '')
        name = model.get('name', '')
        pricing = model.get('pricing', {})

        for provider in providers.keys():
            if model_id.startswith(provider + '/'):
                providers[provider].append({
                    'id': model_id,
                    'name': name,
                    'prompt_price': pricing.get('prompt', '0'),
                    'completion_price': pricing.get('completion', '0'),
                })
                break

    # Display models by provider
    print("=" * 100)
    print("📋 OPENROUTER AVAILABLE MODELS BY PROVIDER")
    print("=" * 100)

    for provider, model_list in providers.items():
        if model_list:
            cprint(f"\n{'='*100}", "cyan")
            cprint(f"{provider.upper()} ({len(model_list)} models)", "yellow")
            cprint(f"{'='*100}", "cyan")

            for m in model_list[:10]:  # Show first 10
                is_free = m['prompt_price'] == '0' and m['completion_price'] == '0'
                free_tag = " [FREE]" if is_free else ""
                cprint(f"  • {m['id']}{free_tag}", "green" if not is_free else "blue")
                print(f"    Name: {m['name']}")
                if not is_free:
                    print(f"    Price: ${m['prompt_price']}/prompt, ${m['completion_price']}/completion")

            if len(model_list) > 10:
                cprint(f"\n  ... and {len(model_list) - 10} more", "yellow")

    # Save full list to JSON
    output_file = 'openrouter_models.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_models': len(models),
            'by_provider': providers,
            'all_models': models
        }, f, indent=2)

    cprint(f"\n✅ Full model list saved to: {output_file}", "green")

    # Recommend models for swarm
    print("\n" + "=" * 100)
    cprint("🎯 RECOMMENDED MODELS FOR SWARM AGENT", "yellow")
    print("=" * 100)

    recommended = []

    # Find best models from each provider
    for provider, model_list in providers.items():
        if model_list:
            # Prefer non-free models (better quality)
            paid_models = [m for m in model_list if m['prompt_price'] != '0']
            if paid_models:
                recommended.append(paid_models[0])

    for m in recommended:
        cprint(f"  • {m['id']}", "green")
        print(f"    {m['name']}")
        print(f"    ${m['prompt_price']}/prompt, ${m['completion_price']}/completion")

    print("\n" + "=" * 100 + "\n")

except Exception as e:
    cprint(f"❌ Error: {e}", "red")
    import traceback
    traceback.print_exc()
