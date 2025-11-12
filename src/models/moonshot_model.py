"""
🌙 Moon Dev's Moonshot Model Integration
Built with love by Moon Dev 🚀

This module provides integration with Moonshot AI's API.
Moonshot is a powerful reasoning model optimized for complex analysis.

Docs: https://platform.moonshot.ai/docs/overview
"""

import requests
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class MoonshotModel(BaseModel):
    """Implementation for Moonshot API models"""
    
    # Available Moonshot models
    AVAILABLE_MODELS = [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",  # Recommended for complex reasoning
    ]
    
    def __init__(self, api_key=None, model_name="moonshot-v1-128k"):
        """Initialize Moonshot model
        
        Args:
            api_key: Moonshot API key (if not provided, loads from env)
            model_name: Name of the Moonshot model to use
        """
        self.base_url = "https://api.moonshot.ai/v1"
        self.model_name = model_name
        super().__init__(api_key=api_key)
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize the Moonshot client connection"""
        if not self.api_key:
            cprint("❌ Moonshot API key not found!", "white", "on_red")
            cprint("   Please set MOONSHOT_API_KEY in your .env file", "yellow")
            raise ValueError("MOONSHOT_API_KEY not configured")
        
        try:
            # Test the connection with a simple request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make a test request
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 401:
                cprint("❌ Moonshot authentication failed!", "white", "on_red")
                cprint("   Invalid or expired API key", "yellow")
                raise ValueError("Invalid Moonshot API key")
            elif response.status_code != 200:
                cprint(f"❌ Moonshot API error: {response.status_code}", "white", "on_red")
                raise Exception(f"Moonshot API returned {response.status_code}")
            
            cprint(f"✨ Successfully connected to Moonshot API", "green")
            cprint(f"   Model: {self.model_name}", "cyan")
            
        except requests.exceptions.ConnectionError:
            cprint("❌ Failed to connect to Moonshot API", "white", "on_red")
            cprint("   Check your internet connection", "yellow")
            raise
        except Exception as e:
            cprint(f"❌ Error initializing Moonshot: {str(e)}", "white", "on_red")
            raise
    
    @property
    def model_type(self):
        """Return the model type identifier"""
        return "moonshot"
    
    def is_available(self):
        """Check if the model is available"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None, **kwargs):
        """Generate a response using Moonshot API
        
        Args:
            system_prompt: System prompt/instructions
            user_content: User's query/content
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse object with the generated content
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                "temperature": temperature,
            }
            
            # Add optional parameters
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Handle response
            if response.status_code == 401:
                raise Exception("Moonshot API error: 401 - Unauthorized (invalid API key)")
            elif response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"Status {response.status_code}")
                raise Exception(f"Moonshot API error: {error_msg}")
            
            # Parse response
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise Exception("No response from Moonshot API")
            
            content = data["choices"][0]["message"]["content"]
            
            # Return as ModelResponse
            return ModelResponse(
                content=content,
                model=self.model_name,
                tokens_used=data.get("usage", {}).get("total_tokens", 0)
            )
            
        except requests.exceptions.Timeout:
            raise Exception("Moonshot API request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to Moonshot API")
        except Exception as e:
            raise Exception(f"Moonshot API error: {str(e)}")
    
    def __str__(self):
        """String representation"""
        return f"MoonshotModel({self.model_name})"
    
    def get_model_parameters(self, model_name=None):
        """Get parameters for a specific Moonshot model"""
        model = model_name or self.model_name
        
        params = {
            "moonshot-v1-8k": {
                "context_window": 8000,
                "max_output_tokens": 4096,
            },
            "moonshot-v1-32k": {
                "context_window": 32000,
                "max_output_tokens": 8000,
            },
            "moonshot-v1-128k": {
                "context_window": 128000,
                "max_output_tokens": 8000,
            },
        }
        
        return params.get(model, {})