"""
🌙 Moon Dev's GLM (Zhipu AI) Model Implementation
Built with love by Moon Dev 🚀
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class GLMModel(BaseModel):
    """Implementation for Zhipu AI's GLM models"""

    AVAILABLE_MODELS = {
        "glm-4-plus": "GLM-4-Plus - Most powerful model",
        "glm-4-0520": "GLM-4-0520 - Flagship model",
        "glm-4": "GLM-4 - Fast chat model",
        "glm-4-air": "GLM-4-Air - Lightweight model",
        "glm-4-airx": "GLM-4-AirX - Ultra-fast model",
        "glm-4-flash": "GLM-4-Flash - Fastest model",
    }

    def __init__(self, api_key: str, model_name: str = "glm-4-flash", base_url: str = "https://open.bigmodel.cn/api/paas/v4/", **kwargs):
        self.model_name = model_name
        self.base_url = base_url
        super().__init__(api_key, **kwargs)

    def initialize_client(self, **kwargs) -> None:
        """Initialize the GLM client"""
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            cprint(f"✨ Initialized GLM model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize GLM model: {str(e)}", "red")
            self.client = None

    def generate_response(self,
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using GLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )

            return ModelResponse(
                content=response.choices[0].message.content.strip(),
                raw_response=response,
                model_name=self.model_name,
                usage=response.usage.model_dump() if hasattr(response, 'usage') else None
            )

        except Exception as e:
            cprint(f"❌ GLM generation error: {str(e)}", "red")
            raise

    def is_available(self) -> bool:
        """Check if GLM is available"""
        return self.client is not None

    @property
    def model_type(self) -> str:
        return "glm"
