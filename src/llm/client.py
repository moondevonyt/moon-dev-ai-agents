"""Provider-agnostic LLM client interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str
    content: str


@dataclass
class ChatResponse:
    """Represents a chat completion response."""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class EmbeddingResponse:
    """Represents an embedding response."""
    embedding: List[float]
    model: str


@dataclass
class TTSResponse:
    """Represents a text-to-speech response."""
    audio_data: bytes
    format: str = "mp3"


class LLMClient(ABC):
    """Abstract base class for LLM provider clients."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the client with configuration.
        
        Args:
            config: Provider-specific configuration (api_key, base_url, etc.)
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the configuration for this provider."""
        pass

    @abstractmethod
    def chat(self, 
             messages: List[ChatMessage], 
             model: str,
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             **kwargs) -> ChatResponse:
        """Generate a chat completion.
        
        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ChatResponse with the generated content
        """
        pass

    @abstractmethod
    def embed(self, 
              text: str, 
              model: str,
              **kwargs) -> EmbeddingResponse:
        """Generate an embedding for the given text.
        
        Args:
            text: Text to embed
            model: Model identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            EmbeddingResponse with the embedding vector
        """
        pass

    def tts(self, 
            text: str, 
            voice: str = "alloy",
            **kwargs) -> TTSResponse:
        """Generate text-to-speech audio (optional method).
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            TTSResponse with audio data
            
        Raises:
            NotImplementedError: If TTS is not supported by this provider
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support TTS")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
