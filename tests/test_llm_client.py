"""Basic tests for the LLM client adapters."""

import pytest
from unittest.mock import Mock, patch
from src.llm import LLMClientFactory, ChatMessage, ChatResponse


def test_factory_create_openai_client():
    """Test creating an OpenAI-compatible client via factory."""
    config = {"api_key": "test-key"}
    client = LLMClientFactory.create_client("openai", config)
    assert client is not None
    assert client.provider_name == "OpenAI-Compatible"


def test_factory_create_groq_client():
    """Test creating a Groq client via factory."""
    config = {"api_key": "test-key"}
    client = LLMClientFactory.create_client("groq", config)
    assert client is not None
    assert client.provider_name == "Groq"


def test_factory_create_ollama_client():
    """Test creating an Ollama client via factory."""
    config = {}
    client = LLMClientFactory.create_client("ollama", config)
    assert client is not None
    assert client.provider_name == "Ollama"


def test_factory_unsupported_provider():
    """Test that unsupported provider raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClientFactory.create_client("unsupported", {})


def test_factory_get_supported_providers():
    """Test getting list of supported providers."""
    providers = LLMClientFactory.get_supported_providers()
    assert "openai" in providers
    assert "groq" in providers
    assert "ollama" in providers


@patch("src.llm.adapters.OpenAI")
def test_openai_chat(mock_openai_class):
    """Test chat completion with OpenAI adapter."""
    # Mock the OpenAI client
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # Mock the response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"), finish_reason="stop")]
    mock_response.model = "gpt-4"
    mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_client.chat.completions.create.return_value = mock_response
    
    # Create client and test chat
    from src.llm.adapters import OpenAICompatibleAdapter
    client = OpenAICompatibleAdapter({"api_key": "test-key"})
    
    messages = [ChatMessage(role="user", content="Hello")]
    response = client.chat(messages, "gpt-4")
    
    assert response.content == "Test response"
    assert response.model == "gpt-4"
    assert response.finish_reason == "stop"
    assert response.usage["total_tokens"] == 30


@patch("src.llm.adapters.requests.post")
def test_ollama_chat(mock_post):
    """Test chat completion with Ollama adapter."""
    # Mock the response
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Test response"},
        "model": "llama2",
        "done_reason": "stop"
    }
    mock_post.return_value = mock_response
    
    # Create client and test chat
    from src.llm.adapters import OllamaAdapter
    client = OllamaAdapter({})
    
    messages = [ChatMessage(role="user", content="Hello")]
    response = client.chat(messages, "llama2")
    
    assert response.content == "Test response"
    assert response.model == "llama2"
    assert response.finish_reason == "stop"


@patch("src.llm.adapters.OpenAI")
def test_openai_chat_error_handling(mock_openai_class):
    """Test error handling in chat completion."""
    # Mock the OpenAI client to raise an exception
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    # Create client and test error handling
    from src.llm.adapters import OpenAICompatibleAdapter
    client = OpenAICompatibleAdapter({"api_key": "test-key"})
    
    messages = [ChatMessage(role="user", content="Hello")]
    
    with pytest.raises(RuntimeError, match="Chat completion failed"):
        client.chat(messages, "gpt-4")
