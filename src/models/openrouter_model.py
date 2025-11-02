"""
🌙 Moon Dev's OpenRouter Model Implementation
Built with love by Moon Dev 🚀

OpenRouter provides unified access to 100+ AI models through a single API.
Perfect for production: automatic failover, load balancing, and unified billing.
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OpenRouterModel(BaseModel):
    """Implementation for OpenRouter's unified API"""

    # Most popular production models across providers
    AVAILABLE_MODELS = {
        # Anthropic Claude (Best for complex reasoning)
        "anthropic/claude-3.5-sonnet": {
            "description": "Claude 3.5 Sonnet - Best balance of intelligence and speed",
            "input_price": "$3.00/1M tokens",
            "output_price": "$15.00/1M tokens",
            "context": "200K tokens"
        },
        "anthropic/claude-3-opus": {
            "description": "Claude 3 Opus - Most powerful for complex tasks",
            "input_price": "$15.00/1M tokens",
            "output_price": "$75.00/1M tokens",
            "context": "200K tokens"
        },
        "anthropic/claude-3-haiku": {
            "description": "Claude 3 Haiku - Fast and efficient",
            "input_price": "$0.25/1M tokens",
            "output_price": "$1.25/1M tokens",
            "context": "200K tokens"
        },

        # OpenAI GPT Models (Best for general tasks)
        "openai/gpt-4o": {
            "description": "GPT-4 Optimized - Latest OpenAI flagship",
            "input_price": "$2.50/1M tokens",
            "output_price": "$10.00/1M tokens",
            "context": "128K tokens"
        },
        "openai/gpt-4o-mini": {
            "description": "GPT-4o Mini - Fast and cost-effective",
            "input_price": "$0.15/1M tokens",
            "output_price": "$0.60/1M tokens",
            "context": "128K tokens"
        },
        "openai/o1": {
            "description": "O1 - Advanced reasoning capabilities",
            "input_price": "$15.00/1M tokens",
            "output_price": "$60.00/1M tokens",
            "context": "200K tokens"
        },

        # Google Gemini (Best for multimodal)
        "google/gemini-2.0-flash-exp": {
            "description": "Gemini 2.0 Flash - Fast multimodal model",
            "input_price": "$0.30/1M tokens",
            "output_price": "$1.20/1M tokens",
            "context": "1M tokens"
        },
        "google/gemini-pro-1.5": {
            "description": "Gemini Pro 1.5 - Complex reasoning with huge context",
            "input_price": "$1.25/1M tokens",
            "output_price": "$5.00/1M tokens",
            "context": "2M tokens"
        },

        # DeepSeek (Best for reasoning at low cost)
        "deepseek/deepseek-chat": {
            "description": "DeepSeek Chat - Fast conversational model",
            "input_price": "$0.14/1M tokens",
            "output_price": "$0.28/1M tokens",
            "context": "64K tokens"
        },
        "deepseek/deepseek-reasoner": {
            "description": "DeepSeek R1 - Advanced reasoning at low cost",
            "input_price": "$0.55/1M tokens",
            "output_price": "$2.19/1M tokens",
            "context": "64K tokens"
        },

        # Meta Llama (Open source via OpenRouter)
        "meta-llama/llama-3.3-70b-instruct": {
            "description": "Llama 3.3 70B - High-performance open model",
            "input_price": "$0.50/1M tokens",
            "output_price": "$0.70/1M tokens",
            "context": "128K tokens"
        },

        # xAI Grok (Latest from X/Twitter)
        "x-ai/grok-beta": {
            "description": "Grok - Real-time knowledge and humor",
            "input_price": "$5.00/1M tokens",
            "output_price": "$15.00/1M tokens",
            "context": "131K tokens"
        },

        # Mistral (European AI, cost-effective)
        "mistralai/mistral-large": {
            "description": "Mistral Large - Top-tier European model",
            "input_price": "$2.00/1M tokens",
            "output_price": "$6.00/1M tokens",
            "context": "128K tokens"
        },
        "mistralai/mistral-small": {
            "description": "Mistral Small - Fast and efficient",
            "input_price": "$0.20/1M tokens",
            "output_price": "$0.60/1M tokens",
            "context": "32K tokens"
        },

        # Qwen (Alibaba's powerful models)
        "qwen/qwen-2.5-72b-instruct": {
            "description": "Qwen 2.5 72B - Strong multilingual capabilities",
            "input_price": "$0.40/1M tokens",
            "output_price": "$0.40/1M tokens",
            "context": "32K tokens"
        }
    }

    def __init__(self, api_key: str, model_name: str = "anthropic/claude-3.5-sonnet", **kwargs):
        """
        Initialize OpenRouter model

        Args:
            api_key: OpenRouter API key (from https://openrouter.ai/keys)
            model_name: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
        """
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1"
        super().__init__(api_key, **kwargs)

    def initialize_client(self, **kwargs) -> None:
        """Initialize the OpenRouter client using OpenAI SDK"""
        try:
            # OpenRouter is OpenAI-compatible, so we use the OpenAI SDK
            # with a custom base_url
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/moon-dev-ai-agents-for-trading",  # Optional, for rankings
                    "X-Title": "Moon Dev AI Trading Agents",  # Optional, for user display
                }
            )
            cprint(f"✨ Moon Dev's magic initialized OpenRouter: {self.model_name} 🌟", "green")
            cprint(f"🌐 Using unified API for multi-provider access", "cyan")

            # Show cost info if available
            if self.model_name in self.AVAILABLE_MODELS:
                model_info = self.AVAILABLE_MODELS[self.model_name]
                cprint(f"💰 Cost: {model_info['input_price']} input / {model_info['output_price']} output", "yellow")
                cprint(f"📝 Context: {model_info['context']}", "cyan")

        except Exception as e:
            cprint(f"❌ Failed to initialize OpenRouter: {str(e)}", "red")
            self.client = None

    def generate_response(self, system_prompt, user_content, **kwargs):
        """Generate a response using OpenRouter"""
        try:
            # Standard OpenAI-compatible message format
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]

            cprint(f"🤔 {self.model_name} is thinking via OpenRouter...", "yellow")

            # Extract parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 4096)

            # Create completion
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content
            content = response.choices[0].message.content

            # OpenRouter provides additional metadata in the response
            if hasattr(response, 'model'):
                cprint(f"✅ Response from: {response.model}", "green")

            return ModelResponse(
                content=content,
                raw_response=response,
                model_name=self.model_name,
                usage=response.usage.model_dump() if hasattr(response, 'usage') else None
            )

        except Exception as e:
            cprint(f"❌ OpenRouter generation error: {str(e)}", "red")

            # Check for common OpenRouter errors
            error_str = str(e)
            if "insufficient credits" in error_str.lower():
                cprint("💳 OpenRouter credits exhausted - add credits at https://openrouter.ai/credits", "yellow")
            elif "rate limit" in error_str.lower():
                cprint("⏱️ Rate limit hit - OpenRouter will retry automatically", "yellow")
            elif "model not found" in error_str.lower():
                cprint(f"❌ Model '{self.model_name}' not available on OpenRouter", "red")
                cprint("📋 Check available models: https://openrouter.ai/models", "yellow")

            raise

    def is_available(self) -> bool:
        """Check if OpenRouter is available"""
        return self.client is not None

    @property
    def model_type(self) -> str:
        return "openrouter"

    @staticmethod
    def get_recommended_models():
        """Get recommended models for different use cases"""
        return {
            "best_value": "anthropic/claude-3-haiku",  # Fast, cheap, smart
            "best_reasoning": "deepseek/deepseek-reasoner",  # Best reasoning per dollar
            "best_overall": "anthropic/claude-3.5-sonnet",  # Best balance
            "fastest": "openai/gpt-4o-mini",  # Fastest responses
            "cheapest": "mistralai/mistral-small",  # Cheapest option
            "largest_context": "google/gemini-pro-1.5",  # 2M tokens
        }
