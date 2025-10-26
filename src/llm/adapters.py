"""Concrete LLM client adapters for different providers."""

import os
from typing import List, Optional, Dict, Any
from openai import OpenAI
from groq import Groq as GroqClient
import requests

from .client import (
    LLMClient, 
    ChatMessage, 
    ChatResponse, 
    EmbeddingResponse, 
    TTSResponse
)


class OpenAICompatibleAdapter(LLMClient):
    """Adapter for OpenAI-compatible APIs (OpenAI, DeepSeek, xAI, etc.)."""

    def _validate_config(self) -> None:
        """Validate the configuration."""
        if "api_key" not in self.config:
            raise ValueError("OpenAI-compatible adapter requires 'api_key' in config")
        
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config.get("base_url")  # Optional custom endpoint
        )

    def chat(self, 
             messages: List[ChatMessage], 
             model: str,
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             **kwargs) -> ChatResponse:
        """Generate a chat completion using OpenAI-compatible API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            )
        except Exception as e:
            raise RuntimeError(f"Chat completion failed: {str(e)}")

    def embed(self, 
              text: str, 
              model: str,
              **kwargs) -> EmbeddingResponse:
        """Generate an embedding using OpenAI-compatible API."""
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text,
                **kwargs
            )
            
            return EmbeddingResponse(
                embedding=response.data[0].embedding,
                model=response.model
            )
        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    def tts(self, 
            text: str, 
            voice: str = "alloy",
            **kwargs) -> TTSResponse:
        """Generate text-to-speech audio (OpenAI only)."""
        try:
            response = self.client.audio.speech.create(
                model=kwargs.get("model", "tts-1"),
                voice=voice,
                input=text
            )
            
            return TTSResponse(
                audio_data=response.content,
                format=kwargs.get("response_format", "mp3")
            )
        except Exception as e:
            raise RuntimeError(f"TTS generation failed: {str(e)}")

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return self.config.get("provider_name", "OpenAI-Compatible")


class GroqAdapter(LLMClient):
    """Adapter for Groq API."""

    def _validate_config(self) -> None:
        """Validate the configuration."""
        if "api_key" not in self.config:
            raise ValueError("Groq adapter requires 'api_key' in config")

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = GroqClient(api_key=self.config["api_key"])

    def chat(self, 
             messages: List[ChatMessage], 
             model: str,
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             **kwargs) -> ChatResponse:
        """Generate a chat completion using Groq API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            )
        except Exception as e:
            raise RuntimeError(f"Chat completion failed: {str(e)}")

    def embed(self, 
              text: str, 
              model: str,
              **kwargs) -> EmbeddingResponse:
        """Groq doesn't currently support embeddings."""
        raise NotImplementedError("Groq adapter does not support embeddings")

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "Groq"


class OllamaAdapter(LLMClient):
    """Adapter for Ollama local API."""

    def _validate_config(self) -> None:
        """Validate the configuration."""
        # Ollama doesn't require an API key
        pass

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = self.config.get("base_url", "http://localhost:11434")

    def chat(self, 
             messages: List[ChatMessage], 
             model: str,
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             **kwargs) -> ChatResponse:
        """Generate a chat completion using Ollama API."""
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return ChatResponse(
                content=data["message"]["content"],
                model=data["model"],
                finish_reason=data.get("done_reason", "stop")
            )
        except Exception as e:
            raise RuntimeError(f"Chat completion failed: {str(e)}")

    def embed(self, 
              text: str, 
              model: str,
              **kwargs) -> EmbeddingResponse:
        """Generate an embedding using Ollama API."""
        try:
            url = f"{self.base_url}/api/embeddings"
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return EmbeddingResponse(
                embedding=data["embedding"],
                model=model
            )
        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "Ollama"
