"""
🌙 Moon Dev's Ollama Model Integration
Built with love by Moon Dev 🚀

This module provides integration with locally running Ollama models.
"""

import requests
import json
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OllamaModel(BaseModel):
    """Implementation for local Ollama models"""
    
    # Available Ollama models - can be expanded based on what's installed locally
    AVAILABLE_MODELS = [
        "deepseek-r1",      # DeepSeek R1 through Ollama (7B by default)
        "qwen3:8b",         # Qwen 3 8B model - fast reasoning model
        "gemma:2b",         # Google's Gemma 2B model
        "llama3.2",         # Meta's Llama 3.2 model - fast and efficient
        # implement your own local models through hugging face/ollama here
    ]
    
    def __init__(self, api_key=None, model_name="llama3.2"):
        """Initialize Ollama model
        
        Args:
            api_key: Not used for Ollama but kept for compatibility
            model_name: Name of the Ollama model to use
        """
        self.base_url = "http://localhost:11434/api"  # Default Ollama API endpoint
        self.model_name = model_name
        # Pass a dummy API key to satisfy BaseModel
        super().__init__(api_key="LOCAL_OLLAMA")
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize the Ollama client connection"""
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code == 200:
                cprint(f"✨ Successfully connected to Ollama API", "green")
                # Print available models
                models = response.json().get("models", [])
                if models:
                    model_names = [model["name"] for model in models]
                    cprint(f"📚 Available Ollama models: {model_names}", "cyan")
                    if self.model_name not in model_names:
                        cprint(f"⚠️ Model {self.model_name} not found! Please run:", "yellow")
                        cprint(f"   ollama pull {self.model_name}", "yellow")
                else:
                    cprint("⚠️ No models found! Please pull the model:", "yellow")
                    cprint(f"   ollama pull {self.model_name}", "yellow")
            else:
                cprint(f"⚠️ Ollama API returned status code: {response.status_code}", "yellow")
                raise ConnectionError(f"Ollama API returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            cprint("❌ Could not connect to Ollama API - is the server running?", "red")
            cprint("💡 Start the server with: ollama serve", "yellow")
            raise
        except Exception as e:
            cprint(f"❌ Could not connect to Ollama API: {str(e)}", "red")
            cprint("💡 Make sure Ollama is running locally (ollama serve)", "yellow")
            raise

    @property
    def model_type(self):
        """Return the type of model"""
        return "ollama"
    
    def is_available(self):
        """Check if the model is available"""
        try:
            response = requests.get(f"{self.base_url}/tags")
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None, **kwargs):
        """Generate a response using the Ollama model

        Args:
            system_prompt: System prompt to guide the model
            user_content: User's input content
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (ignored by Ollama, kept for compatibility)
            **kwargs: Additional arguments (ignored, kept for compatibility)

        Returns:
            Generated response text or None if failed
        """
        try:
            # Format the prompt with system and user content
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Prepare the request
            data = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            # Make the request with 90 second timeout
            response = requests.post(
                f"{self.base_url}/chat",
                json=data,
                timeout=90  # Match swarm timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                raw_content = response_data.get("message", {}).get("content", "")

                # Remove <think>...</think> tags and their content (Qwen reasoning)
                import re

                # First, try to remove complete <think>...</think> blocks
                filtered_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

                # If <think> tag exists but wasn't removed (unclosed tag due to token limit),
                # remove everything from <think> onwards
                if '<think>' in filtered_content:
                    filtered_content = filtered_content.split('<think>')[0].strip()

                # If filtering removed everything, return the original (in case it's not a Qwen model)
                final_content = filtered_content if filtered_content else raw_content

                return ModelResponse(
                    content=final_content,
                    raw_response=response_data,
                    model_name=self.model_name,
                    usage=None  # Ollama doesn't provide token usage info
                )
            else:
                cprint(f"❌ Ollama API error: {response.status_code}", "red")
                cprint(f"Response: {response.text}", "red")
                raise Exception(f"Ollama API error: {response.status_code}")

        except Exception as e:
            cprint(f"❌ Error generating response: {str(e)}", "red")
            # Don't re-raise - let swarm agent handle failed responses gracefully
            return ModelResponse(
                content="",
                raw_response={"error": str(e)},
                model_name=self.model_name,
                usage=None
            )
    
    def __str__(self):
        return f"OllamaModel(model={self.model_name})"

    def get_model_parameters(self, model_name=None):
        """Get the parameter count for a specific model
        
        Args:
            model_name: Name of the model to check (defaults to self.model_name)
            
        Returns:
            String with parameter count (e.g., "7B", "13B") or None if not available
        """
        if model_name is None:
            model_name = self.model_name
            
        try:
            # For specific known models
            known_models = {
                "deepseek-r1": "7B",
                "qwen3:8b": "8B",
                "gemma:2b": "2B",
                "llama3.2": "70B"
            }
            
            if model_name in known_models:
                return known_models[model_name]
                
            return "Unknown"
        except Exception as e:
            cprint(f"❌ Error getting model parameters: {str(e)}", "red")
            return None 