"""
🌙 Moon Dev's OpenAI Model Implementation
Built with love by Moon Dev 🚀
"""

from openai import OpenAI
import requests
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OpenAIModel(BaseModel):
    """Implementation for OpenAI's models"""
    
    AVAILABLE_MODELS = {
        "gpt-5": {
            "description": "Most advanced GPT-5 model with breakthrough capabilities",
            "input_price": "$0.015/1K tokens",
            "output_price": "$0.045/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-5-mini": {
            "description": "Efficient GPT-5 mini model with strong performance",
            "input_price": "$0.007/1K tokens",
            "output_price": "$0.021/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-5-nano": {
            "description": "Ultra-fast GPT-5 nano model for high-speed tasks",
            "input_price": "$0.003/1K tokens",
            "output_price": "$0.009/1K tokens",
            "supports_reasoning_effort": False
        },
        "o3": {
            "description": "Advanced reasoning model with superior problem-solving capabilities",
            "input_price": "$1.50/1m tokens",
            "output_price": "$5.00/1m tokens",
            "supports_reasoning_effort": True
        },
        "o3-mini": {
            "description": "Fast reasoning model with problem-solving capabilities",
            "input_price": "$1.10/1m tokens",
            "output_price": "$4.40/1m tokens",
            "supports_reasoning_effort": True
        },
        "o1": {
            "description": "Latest O1 model with reasoning capabilities",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens",
            "supports_reasoning_effort": False
        },
        "o1-mini": {
            "description": "Smaller O1 model with reasoning capabilities",
            "input_price": "$0.005/1K tokens",
            "output_price": "$0.015/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-4o": {
            "description": "Advanced GPT-4 Optimized model",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-4o-mini": {
            "description": "Efficient GPT-4 Optimized mini model",
            "input_price": "$0.005/1K tokens",
            "output_price": "$0.015/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-4.1": {
            "description": "Latest GPT-4.1 model with enhanced capabilities",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens",
            "supports_reasoning_effort": True
        },
        "o4-mini": {
            "description": "Efficient O4 model with balanced performance",
            "input_price": "$1.30/1m tokens",
            "output_price": "$4.70/1m tokens",
            "supports_reasoning_effort": True
        }
    }
    
    def __init__(self, api_key: str, model_name: str = "o1-mini", reasoning_effort: str = "medium", **kwargs):
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the OpenAI client"""
        try:
            self.client = OpenAI(api_key=self.api_key)
            cprint(f"✨ Moon Dev's magic initialized OpenAI model: {self.model_name} 🌟", "green")
            if self._supports_reasoning_effort():
                cprint(f"🧠 Reasoning effort set to: {self.reasoning_effort}", "cyan")
        except Exception as e:
            cprint(f"❌ Failed to initialize OpenAI model: {str(e)}", "red")
            self.client = None
    
    def _supports_reasoning_effort(self) -> bool:
        """Check if the current model supports reasoning effort"""
        model_info = self.AVAILABLE_MODELS.get(self.model_name, {})
        return isinstance(model_info, dict) and model_info.get('supports_reasoning_effort', False)

    def _prepare_model_kwargs(self, **kwargs):
        """Prepare model-specific kwargs"""
        model_kwargs = kwargs.copy()
        
        if self._supports_reasoning_effort():
            cprint("🚀 Moon Dev's O3 model powering up with reasoning capabilities! 🌙", "cyan")
            model_kwargs["reasoning_effort"] = self.reasoning_effort
            # Remove unsupported parameters for O3
            model_kwargs.pop('max_tokens', None)
            model_kwargs.pop('temperature', None)
        elif self.model_name.startswith('o1'):
            # Handle O1 specific parameters
            if 'max_tokens' in model_kwargs:
                model_kwargs['max_completion_tokens'] = model_kwargs.pop('max_tokens')
            model_kwargs.pop('temperature', None)
            model_kwargs.pop('reasoning_effort', None)
        elif self.model_name.startswith('gpt-5'):
            # Handle GPT-5 specific parameter name support
            if 'max_tokens' in model_kwargs:
                provided = model_kwargs.pop('max_tokens')
                try:
                    provided_int = int(provided)
                except Exception:
                    provided_int = 0
                model_kwargs['max_completion_tokens'] = max(provided_int, 4096)
            # Temperature not supported for GPT-5 (defaults only)
            model_kwargs.pop('temperature', None)
            model_kwargs.pop('reasoning_effort', None)
            # Sensible default if not set
            if 'max_completion_tokens' not in model_kwargs:
                model_kwargs['max_completion_tokens'] = 4096
        else:
            # Remove O3 specific parameters for other models
            model_kwargs.pop('reasoning_effort', None)
            
        return model_kwargs

    def generate_response(self, system_prompt, user_content, **kwargs):
        """Generate a response using the OpenAI model"""
        try:
            # Prefer Responses API for newer models if available (per OpenAI Text guide)
            if self.model_name.startswith(('gpt-5', 'o1')):
                try:
                    content_str = f"Instructions: {system_prompt}\n\nInput: {user_content}"
                    # Map token limit for Responses API
                    max_output_tokens = None
                    if 'max_tokens' in kwargs:
                        max_output_tokens = kwargs.get('max_tokens')
                    elif 'max_completion_tokens' in kwargs:
                        max_output_tokens = kwargs.get('max_completion_tokens')
                    if max_output_tokens is None:
                        max_output_tokens = 2048  # sensible default for RBI tasks

                    response = self.client.responses.create(
                        model=self.model_name,
                        input=content_str,
                        max_output_tokens=max_output_tokens
                    )

                    # Extract text per Responses API
                    content_text = getattr(response, 'output_text', None)
                    if not content_text and hasattr(response, 'output'):
                        try:
                            # Try to stitch text parts
                            parts = []
                            for item in response.output:
                                # item.content may be a list of parts
                                content_list = getattr(item, 'content', None)
                                if isinstance(content_list, list):
                                    for part in content_list:
                                        text_val = getattr(part, 'text', None)
                                        if isinstance(text_val, str):
                                            parts.append(text_val)
                            content_text = "".join(parts).strip() if parts else None
                        except Exception:
                            content_text = None

                    if content_text and content_text.strip():
                        return ModelResponse(
                            content=content_text.strip(),
                            raw_response=response,
                            model_name=self.model_name,
                            usage=getattr(response, 'usage', None)
                        )
                except AttributeError:
                    # Responses API not available, fall back to direct HTTP
                    try:
                        content_str = f"Instructions: {system_prompt}\n\nInput: {user_content}"
                        max_output_tokens = kwargs.get('max_tokens') or kwargs.get('max_completion_tokens') or 2048
                        http_resp = requests.post(
                            url="https://api.openai.com/v1/responses",
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": self.model_name,
                                "input": content_str,
                                "max_output_tokens": max_output_tokens
                            },
                            timeout=60
                        )
                        http_resp.raise_for_status()
                        data = http_resp.json()
                        content_text = data.get('output_text')
                        if not content_text:
                            # stitch from output items
                            output_items = data.get('output', []) or []
                            parts = []
                            for item in output_items:
                                content_list = item.get('content') if isinstance(item, dict) else None
                                if isinstance(content_list, list):
                                    for part in content_list:
                                        text_val = None
                                        if isinstance(part, dict):
                                            text_val = part.get('text') or part.get('content')
                                        if isinstance(text_val, str):
                                            parts.append(text_val)
                            content_text = "".join(parts).strip() if parts else None
                        if content_text and content_text.strip():
                            return ModelResponse(
                                content=content_text.strip(),
                                raw_response=data,
                                model_name=self.model_name,
                                usage=data.get('usage')
                            )
                    except Exception as http_e:
                        cprint(f"❌ Direct Responses HTTP fallback failed: {repr(http_e)}", "red")
                        cprint("⚠️ Falling back to Chat Completions", "yellow")

            # Special handling for O3 models via Chat Completions
            if self.model_name.startswith('o3'):
                cprint("🧠 Using Moon Dev's O3 model with reasoning capabilities...", "cyan")
                messages = [
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            # Special handling for O1 models
            elif self.model_name.startswith('o1'):
                messages = [
                    {
                        "role": "user",
                        "content": f"Instructions: {system_prompt}\n\nInput: {user_content}"
                    }
                ]
            # Standard handling for other models (including GPT-5)
            else:
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
            
            cprint(f"🤔 Moon Dev's {self.model_name} is thinking...", "yellow")
            
            # Prepare model-specific kwargs
            model_kwargs = self._prepare_model_kwargs(**kwargs)
            
            # Create completion with appropriate parameters
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **model_kwargs
            )

            # Robust content extraction to avoid empty content edge cases
            choice = response.choices[0]
            message = choice.message
            content_text = None

            # Debug: show finish_reason and meta
            try:
                finish_reason = getattr(choice, 'finish_reason', None)
                cprint(f"🧪 Moon Dev debug: finish_reason={finish_reason}", "cyan")
            except Exception:
                pass

            if hasattr(message, 'content'):
                # content may be a string or a list of typed objects
                if isinstance(message.content, str):
                    content_text = message.content.strip()
                elif isinstance(message.content, list):
                    # Join any text parts if content is structured (defensive)
                    try:
                        parts = []
                        for part in message.content:
                            if isinstance(part, dict):
                                text_val = part.get('text') or part.get('content')
                                if isinstance(text_val, str):
                                    parts.append(text_val)
                            elif isinstance(part, str):
                                parts.append(part)
                            else:
                                # Handle typed content parts like ChatCompletionContentPart with .text
                                text_val = getattr(part, 'text', None)
                                if isinstance(text_val, str):
                                    parts.append(text_val)
                        content_text = "".join(parts).strip() if parts else None
                    except Exception:
                        content_text = None

            if not content_text:
                cprint("⚠️ OpenAI returned empty content", "yellow")

            # If still empty, do a single simplified retry (matches other GPT handling)
            if not content_text:
                cprint("🔁 Retrying once with simplified prompt format (Moon Dev fallback)", "yellow")
                retry_messages = [
                    {
                        "role": "user",
                        "content": f"Instructions: {system_prompt}\n\nInput: {user_content}\n\nRespond with plain text only."
                    }
                ]
                retry_kwargs = self._prepare_model_kwargs(**kwargs)
                # Ensure no temperature for restricted models
                retry_kwargs.pop('temperature', None)
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=retry_messages,
                    **retry_kwargs
                )
                choice = response.choices[0]
                message = choice.message
                content_text = getattr(message, 'content', None)
                if isinstance(content_text, str):
                    content_text = content_text.strip()

            # If still empty and Responses API available, try Responses API once
            if not content_text and hasattr(self.client, 'responses'):
                try:
                    cprint("🛠️ Moon Dev fallback: trying Responses API for text output", "yellow")
                    content_str = f"Instructions: {system_prompt}\n\nInput: {user_content}"
                    # Map token limit to responses API
                    max_output_tokens = None
                    if 'max_tokens' in kwargs:
                        max_output_tokens = kwargs.get('max_tokens')
                    elif 'max_completion_tokens' in kwargs:
                        max_output_tokens = kwargs.get('max_completion_tokens')
                    if max_output_tokens is None:
                        max_output_tokens = 2048
                    resp2 = self.client.responses.create(
                        model=self.model_name,
                        input=content_str,
                        max_output_tokens=max_output_tokens
                    )
                    text2 = getattr(resp2, 'output_text', None)
                    if not text2 and hasattr(resp2, 'output'):
                        parts = []
                        for item in getattr(resp2, 'output', []) or []:
                            content_list = getattr(item, 'content', None)
                            if isinstance(content_list, list):
                                for part in content_list:
                                    text_val = getattr(part, 'text', None)
                                    if isinstance(text_val, str):
                                        parts.append(text_val)
                        text2 = "".join(parts).strip() if parts else None
                    if text2:
                        content_text = text2.strip()
                        response = resp2  # return this raw response for visibility
                except Exception as fallback_e:
                    cprint(f"❌ Moon Dev Responses API fallback error: {repr(fallback_e)}", "red")

            # Final safety net: fallback to a stable chat model if nothing came back
            if (not content_text) and self.model_name == 'gpt-5':
                try:
                    cprint("🛟 Moon Dev fallback: retrying with gpt-4o to avoid empty content", "yellow")
                    fallback_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                    fb_kwargs = kwargs.copy()
                    # Map tokens for non-O1/O3 models
                    if 'max_tokens' not in fb_kwargs and 'max_completion_tokens' in fb_kwargs:
                        fb_kwargs['max_tokens'] = fb_kwargs.pop('max_completion_tokens')
                    fb_kwargs.pop('temperature', None)  # keep defaults safe
                    fb_response = self.client.chat.completions.create(
                        model='gpt-4o',
                        messages=fallback_messages,
                        **fb_kwargs
                    )
                    fb_choice = fb_response.choices[0]
                    fb_message = fb_choice.message
                    fb_text = getattr(fb_message, 'content', None)
                    if isinstance(fb_text, str) and fb_text.strip():
                        return ModelResponse(
                            content=fb_text.strip(),
                            raw_response=fb_response,
                            model_name='gpt-4o',
                            usage=fb_response.usage.model_dump() if hasattr(fb_response, 'usage') else None
                        )
                except Exception as fb_e:
                    cprint(f"❌ Fallback to gpt-4o failed: {repr(fb_e)}", "red")

            return ModelResponse(
                content=content_text or "",
                raw_response=response,
                model_name=self.model_name,
                usage=response.usage.model_dump() if hasattr(response, 'usage') else None
            )

        except Exception as e:
            # Print detailed error info per Moon Dev style
            cprint(f"❌ OpenAI generation error (Moon Dev full dump) 🚨: {repr(e)}", "red")
            try:
                cprint(f"🔎 type={type(e).__name__}", "yellow")
                if hasattr(e, 'status_code'):
                    cprint(f"🔎 status_code={getattr(e, 'status_code', None)}", "yellow")
                if hasattr(e, 'request_id'):
                    cprint(f"🔎 request_id={getattr(e, 'request_id', None)}", "yellow")
                if hasattr(e, 'code'):
                    cprint(f"🔎 code={getattr(e, 'code', None)}", "yellow")
                if hasattr(e, 'param'):
                    cprint(f"🔎 param={getattr(e, 'param', None)}", "yellow")
                resp = getattr(e, 'response', None)
                if resp is not None:
                    cprint(f"🔎 response={resp}", "yellow")
                    try:
                        cprint(f"🔎 response.body={getattr(e, 'body', None)}", "yellow")
                    except Exception:
                        pass
            except Exception:
                pass
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "openai" 