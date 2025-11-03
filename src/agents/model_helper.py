"""
🌙 Moon Dev's Agent Model Helper
Built with love by Moon Dev 🚀

Centralized helper for agents to access LLM models via OpenRouter or other providers.
This simplifies model initialization and ensures all agents use the same pattern.
"""

from src.models.model_factory import model_factory
from src import config
from termcolor import cprint

def get_agent_model(
    provider=None,
    model_name=None,
    use_config_defaults=True,
    verbose=True
):
    """
    Get an AI model for agent use with smart defaults from config.

    Args:
        provider (str): Provider type ('openrouter', 'claude', 'openai', etc.)
                       If None, uses config.AI_PROVIDER
        model_name (str): Specific model name. If None, uses config.AI_MODEL
        use_config_defaults (bool): If True, falls back to config.py settings
        verbose (bool): Print initialization messages

    Returns:
        BaseModel: Initialized model instance ready for use

    Examples:
        # Use config.py defaults (RECOMMENDED for most agents)
        model = get_agent_model()

        # Override for specific agent needs
        model = get_agent_model(provider='openrouter', model_name='deepseek/deepseek-reasoner')

        # High-stakes trading decision
        model = get_agent_model(model_name='anthropic/claude-3.5-sonnet')

        # Fast, cheap tasks
        model = get_agent_model(model_name='mistralai/mistral-small')
    """

    # Use config defaults if not specified
    if use_config_defaults:
        if provider is None and hasattr(config, 'AI_PROVIDER'):
            provider = config.AI_PROVIDER
        elif provider is None:
            provider = 'openrouter'  # Default to OpenRouter

        if model_name is None and hasattr(config, 'AI_MODEL'):
            model_name = config.AI_MODEL
        elif model_name is None:
            model_name = 'anthropic/claude-3.5-sonnet'  # Sensible default

    if verbose:
        cprint(f"\n🤖 Initializing AI model...", "cyan")
        cprint(f"  ├─ Provider: {provider}", "cyan")
        cprint(f"  └─ Model: {model_name or 'default'}", "cyan")

    # Get model from factory
    model = model_factory.get_model(provider, model_name)

    if not model:
        cprint(f"❌ Failed to initialize {provider} model!", "red")
        cprint(f"💡 Make sure API keys are set in .env", "yellow")
        if provider == 'openrouter':
            cprint(f"   OPENROUTER_API_KEY=your_key_here", "yellow")
        return None

    if verbose:
        cprint(f"✅ Model initialized successfully!", "green")

    return model


def get_model_for_task(task_type, verbose=True):
    """
    Get recommended model for specific task types.
    Uses OpenRouter with optimized model selection per task.

    Args:
        task_type (str): Type of task - 'trading', 'risk', 'chat', 'research', 'content'
        verbose (bool): Print initialization messages

    Returns:
        BaseModel: Initialized model optimized for the task

    Examples:
        # For high-stakes trading decisions
        model = get_model_for_task('trading')

        # For risk management
        model = get_model_for_task('risk')

        # For chat/tweets (cheap & fast)
        model = get_model_for_task('chat')

        # For research/strategy development (reasoning)
        model = get_model_for_task('research')
    """

    # Recommended models per task type
    task_models = {
        'trading': {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3.5-sonnet',  # Best for critical decisions
            'description': 'High-stakes trading decisions'
        },
        'risk': {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3.5-sonnet',  # Best for risk analysis
            'description': 'Risk management and portfolio analysis'
        },
        'research': {
            'provider': 'openrouter',
            'model': 'deepseek/deepseek-reasoner',  # Best value for reasoning
            'description': 'Strategy development and research'
        },
        'chat': {
            'provider': 'openrouter',
            'model': 'mistralai/mistral-small',  # Cheapest, fast enough
            'description': 'Chat, tweets, simple content'
        },
        'content': {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3-haiku',  # Fast and creative
            'description': 'Content creation (videos, clips, etc.)'
        },
        'analysis': {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3-haiku',  # Fast analysis
            'description': 'Market analysis and data interpretation'
        }
    }

    # Get recommended config for task
    task_config = task_models.get(task_type.lower())

    if not task_config:
        if verbose:
            cprint(f"⚠️ Unknown task type '{task_type}', using config defaults", "yellow")
        return get_agent_model(verbose=verbose)

    if verbose:
        cprint(f"\n🎯 Optimizing model for: {task_config['description']}", "cyan")

    return get_agent_model(
        provider=task_config['provider'],
        model_name=task_config['model'],
        use_config_defaults=False,  # Use task-specific model
        verbose=verbose
    )


# Convenience functions for common use cases
def get_trading_model(verbose=True):
    """Get optimized model for trading decisions"""
    return get_model_for_task('trading', verbose=verbose)


def get_risk_model(verbose=True):
    """Get optimized model for risk management"""
    return get_model_for_task('risk', verbose=verbose)


def get_research_model(verbose=True):
    """Get optimized model for research and strategy development"""
    return get_model_for_task('research', verbose=verbose)


def get_chat_model(verbose=True):
    """Get optimized model for chat and simple content"""
    return get_model_for_task('chat', verbose=verbose)


def get_content_model(verbose=True):
    """Get optimized model for content creation"""
    return get_model_for_task('content', verbose=verbose)
