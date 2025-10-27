"""
🌙 Moon Dev's Gemini Model Implementation
Built with love by Moon Dev 🚀
"""

import google.generativeai as genai
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class GeminiModel(BaseModel):
    """Implementation for Google's Gemini models"""
    
    AVAILABLE_MODELS = {
        "gemini-2.5-pro": "Most advanced Gemini 2.5 model with superior capabilities",
        "gemini-2.5-flash": "Fast Gemini 2.5 model for quick responses",
        "gemini-2.5-flash-lite": "Ultra-fast lightweight Gemini 2.5 model"
    }
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", **kwargs):
        self.model_name = model_name
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            cprint(f"✨ Initialized Gemini model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize Gemini model: {str(e)}", "red")
            self.client = None
    
    def generate_response(self,
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,  # Gemini 2.5 needs 2048+ tokens minimum
        **kwargs
    ) -> ModelResponse:
        """Generate a response using Gemini"""
        try:
            # Combine system prompt and user content since Gemini doesn't have system messages
            combined_prompt = f"{system_prompt}\n\n{user_content}"

            # Configure safety settings - use BLOCK_ONLY_HIGH instead of BLOCK_NONE
            # BLOCK_NONE requires special billing access in 2025
            safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            response = self.client.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
                safety_settings=safety_settings
            )

            # Check if response was blocked or empty
            if not response.candidates or not response.candidates[0].content.parts:
                # Get detailed block reason
                block_reason = "UNSPECIFIED"
                blocked_categories = []

                if hasattr(response, 'prompt_feedback'):
                    block_reason_value = getattr(response.prompt_feedback, 'block_reason', 0)
                    # 0=UNSPECIFIED, 1=SAFETY, 2=OTHER, 3=BLOCKLIST, 4=PROHIBITED_CONTENT
                    block_reason_map = {
                        0: "UNSPECIFIED",
                        1: "SAFETY",
                        2: "OTHER",
                        3: "BLOCKLIST",
                        4: "PROHIBITED_CONTENT",
                        5: "IMAGE_SAFETY"
                    }
                    block_reason = block_reason_map.get(block_reason_value, f"UNKNOWN({block_reason_value})")

                    if hasattr(response.prompt_feedback, 'safety_ratings'):
                        for rating in response.prompt_feedback.safety_ratings:
                            prob = getattr(rating, 'probability', None)
                            if prob and str(prob) in ['MEDIUM', 'HIGH', '2', '3']:
                                blocked_categories.append(f"{rating.category.name}:{prob}")

                finish_reason = None
                if response.candidates and len(response.candidates) > 0:
                    finish_reason = getattr(response.candidates[0], 'finish_reason', None)

                error_msg = f"Empty response - block_reason={block_reason}"
                if blocked_categories:
                    error_msg += f", triggered: {', '.join(blocked_categories)}"
                if finish_reason:
                    error_msg += f", finish_reason={finish_reason}"

                raise Exception(error_msg)

            return ModelResponse(
                content=response.text.strip(),
                raw_response=response,
                model_name=self.model_name,
                usage=None  # Gemini doesn't provide token usage info
            )

        except Exception as e:
            cprint(f"❌ Gemini generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if Gemini is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "gemini" 