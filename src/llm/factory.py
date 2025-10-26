"""Factory for creating LLM clients based on configuration."""

import os
from typing import Dict, Any
from .client import LLMClient
from .adapters import OpenAICompatibleAdapter, GroqAdapter, OllamaAdapter


class LLMClientFactory:
    """Factory for creating provider-specific LLM clients."""

    # Map provider names to adapter classes
    PROVIDERS = {
        "openai": OpenAICompatibleAdapter,
        "openai-compatible": OpenAICompatibleAdapter,
        "groq": GroqAdapter,
        "ollama": OllamaAdapter,
    }

    @staticmethod
    def create_client(provider: str, config: Dict[str, Any]) -> LLMClient:
        """Create an LLM client for the specified provider.
        
        Args:
            provider: Provider name (openai, groq, ollama, etc.)
            config: Provider-specific configuration
            
        Returns:
            LLMClient instance for the provider
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()
        
        if provider_lower not in LLMClientFactory.PROVIDERS:
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {supported}"
            )
        
        adapter_class = LLMClientFactory.PROVIDERS[provider_lower]
        return adapter_class(config)

    @staticmethod
    def create_from_env(provider: str = None) -> LLMClient:
        """Create an LLM client from environment variables.
        
        Args:
            provider: Provider name. If None, uses LLM_PROVIDER env var
            
        Returns:
            LLM client configured from environment
            
        Environment Variables:
            LLM_PROVIDER: Provider name (openai, groq, ollama)
            LLM_API_KEY: API key for the provider
            LLM_BASE_URL: Custom base URL (optional, for OpenAI-compatible APIs)
            LLM_MODEL: Default model to use
        """
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "openai")
        
        config = {}
        
        # Get API key from environment (required for most providers except Ollama)
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            config["api_key"] = api_key
        
        # Get custom base URL if provided
        base_url = os.getenv("LLM_BASE_URL")
        if base_url:
            config["base_url"] = base_url
        
        # Get default model
        model = os.getenv("LLM_MODEL")
        if model:
            config["default_model"] = model
        
        return LLMClientFactory.create_client(provider, config)

    @staticmethod
    def get_supported_providers() -> list:
        """Return list of supported provider names."""
        return list(LLMClientFactory.PROVIDERS.keys())
