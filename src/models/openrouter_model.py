"""
🌙 Moon Dev's OpenRouter Model Implementation
Built with love by Moon Dev 🚀

OpenRouter provides unified access to all major AI models through a single API.
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse
import time
import json
import re
from typing import List
from datetime import datetime, timezone, timedelta
from ..utils.telegram_notifier import get_telegram_notifier

class OpenRouterModel(BaseModel):
    """Implementation for OpenRouter's model routing"""

    # 🌙 OpenRouter Free Model Limits:
    # - Daily Limit: 50 requests per day per API key (shared across ALL :free models)
    # - Per-Minute Limit: ~20 requests per minute per API key
    # - Both limits apply to ALL models ending in :free (not per model!)
    # - Reset: Daily at 00:00 UTC
    # - Errors: 429 with "daily limit" → rotate to next key
    #          429 with "rate limited" / "too many requests" → wait 3 seconds, retry
    #          402 with "insufficient credits" → negative balance, rotate to next key
    
    AVAILABLE_MODELS = {
        # DeepSeek Reasoner FREE but 50 requests per Day (shared with all :free models)
        "deepseek/deepseek-r1-0528:free": {
            "description": "DeepSeek R1 - Advanced reasoning - 64k context",
            "input_price": "$0.00/1M tokens",
            "output_price": "$0.00/1M tokens"
        },

        # DeepSeek chat FREE but 50 requests per Day (shared with all :free models)
        "deepseek/deepseek-chat-v3-0324:free": {
            "description": "DeepSeek V3 - latest model - 32k context",
            "input_price": "$0.00/1M tokens",
            "output_price": "$0.00/1M tokens"
        },
    }

    def __init__(self, api_keys: List[str], model_name: str = "deepseek/deepseek-chat-v3-0324:free", **kwargs):
        try:
            cprint(f"\n🌙 Moon Dev's OpenRouter Model Initialization", "cyan")

            # Support both single key and list of keys
            if isinstance(api_keys, str):
                api_keys = [api_keys]
            
            # Validate API keys
            if not api_keys or len(api_keys) == 0:
                raise ValueError("No API keys provided")
            
            # Filter out empty keys and placeholder keys
            self.api_keys = [
                key.strip() for key in api_keys 
                if key and len(key.strip()) > 0 
                and not key.strip().startswith('your_')
                and key.strip().startswith('sk-or-')
            ]
            
            if len(self.api_keys) == 0:
                raise ValueError("All API keys are empty, None, or invalid placeholders")

            cprint(f"🔑 API Keys validation:", "cyan")
            cprint(f"  ├─ Total keys provided: {len(self.api_keys)}", "cyan")
            for i, key in enumerate(self.api_keys, 1):
                cprint(f"  ├─ Key {i}: {len(key)} chars - Starts with 'sk-or-': {'yes' if key.startswith('sk-or-') else 'no'}", "cyan")
            
            # Initialize key rotation system
            self.current_key_index = 0
            self.failed_keys_today = set()  # Track keys that hit daily limit
            self.is_paused = False  # Track if system is paused
            self.pause_until = None  # When to resume
            
            # Set default max_tokens
            self.max_tokens = kwargs.get('max_tokens', 8192)  # Default to 8k tokens
            
            # Initialize Telegram notifier
            self.telegram = get_telegram_notifier()
            
            cprint(f"  └─ ✅ Key rotation system initialized", "green")

            # Validate model name
            cprint(f"\n📝 Model validation:", "cyan")
            cprint(f"  ├─ Requested: {model_name}", "cyan")
            if model_name not in self.AVAILABLE_MODELS:
                cprint(f"  └─ ⚠️ Model not in predefined list (will still try to use it)", "yellow")
                cprint(f"  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs", "cyan")
            else:
                cprint(f"  └─ ✅ Model name recognized", "green")

            self.model_name = model_name

            # Call parent class initialization with first key
            cprint(f"\n📡 Parent class initialization...", "cyan")
            super().__init__(self.api_keys[0], **kwargs)
            cprint(f"✅ Parent class initialized", "green")

        except Exception as e:
            cprint(f"\n❌ Error in OpenRouter model initialization", "red")
            cprint(f"  ├─ Error type: {type(e).__name__}", "red")
            cprint(f"  ├─ Error message: {str(e)}", "red")
            if "api_key" in str(e).lower():
                cprint(f"  ├─ 🔑 This appears to be an API key issue", "red")
                cprint(f"  └─ Please check your OPENROUTER_API_KEY_* in .env", "red")
            elif "model" in str(e).lower():
                cprint(f"  ├─ 🤖 This appears to be a model name issue", "red")
                cprint(f"  └─ See all models at: https://openrouter.ai/docs", "red")
            raise

    def calculate_time_until_reset(self) -> int:
        """Calculate seconds until next UTC midnight (when rate limits reset)"""
        now = datetime.now(timezone.utc)
        next_midnight = datetime(
            now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc
        ) + timedelta(days=1)
        seconds_until_reset = (next_midnight - now).total_seconds()
        return int(seconds_until_reset)
    
    def pause_until_reset(self) -> None:
        """Pause system until rate limits reset at UTC midnight"""
        seconds = self.calculate_time_until_reset()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        self.is_paused = True
        self.pause_until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        
        cprint(f"\n⏸️  System PAUSED - All {len(self.api_keys)} API keys exhausted", "red")
        cprint(f"⏰ Rate limits reset in: {hours}h {minutes}m", "yellow")
        cprint(f"⏰ Resuming at: {self.pause_until.strftime('%Y-%m-%d %H:%M:%S')} UTC", "yellow")
        
        # Send Telegram notification
        if self.telegram.enabled:
            self.telegram.send_rate_limit_alert(
                total_keys=len(self.api_keys),
                model_name=self.model_name
            )
    
    def check_if_should_resume(self) -> bool:
        """Check if system should resume after pause"""
        if not self.is_paused:
            return True
        
        if self.pause_until and datetime.now(timezone.utc) >= self.pause_until:
            # Time to resume - reset failed keys
            self.is_paused = False
            self.failed_keys_today = set()
            self.current_key_index = 0
            
            cprint(f"\n✅ System RESUMED - Rate limits have been reset", "green")
            
            # Send Telegram notification
            if self.telegram.enabled:
                self.telegram.send_system_resumed_alert(model_name=self.model_name)
            
            return True
        
        return False
    
    def rotate_to_next_key(self) -> bool:
        """Rotate to the next available API key. Returns True if successful, False if all keys exhausted."""
        initial_index = self.current_key_index
        
        # Try next keys
        for _ in range(len(self.api_keys)):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            # Skip keys that already failed today
            if self.current_key_index in self.failed_keys_today:
                if self.current_key_index == initial_index:
                    break  # We've gone full circle
                continue
            
            # Update the client with new key
            try:
                new_key = self.api_keys[self.current_key_index]
                cprint(f"\n🔄 Rotating to API Key #{self.current_key_index + 1}", "yellow")
                self.api_key = new_key
                self.client = OpenAI(
                    api_key=new_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                cprint(f"✅ Successfully switched to Key #{self.current_key_index + 1}", "green")
                
                # Send Telegram notification for key rotation
                if self.telegram.enabled:
                    self.telegram.send_key_rotation_alert(
                        current_key=self.current_key_index,
                        total_keys=len(self.api_keys),
                        model_name=self.model_name
                    )
                
                return True
            except Exception as e:
                cprint(f"❌ Failed to initialize client with Key #{self.current_key_index + 1}: {str(e)}", "red")
                self.failed_keys_today.add(self.current_key_index)
                continue
        
        cprint(f"\n❌ All API keys have been exhausted or hit rate limits", "red")
        
        # Pause system until reset
        self.pause_until_reset()
        
        return False

    def initialize_client(self, **kwargs) -> None:
        """Initialize the OpenRouter client with automatic key rotation on failure"""
        max_attempts = len(self.api_keys)
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                cprint(f"\n🔌 Initializing OpenRouter client...", "cyan")
                cprint(f"  ├─ Using API Key #{self.current_key_index + 1} of {len(self.api_keys)}", "cyan")
                cprint(f"  ├─ API Key length: {len(self.api_key)} chars", "cyan")
                cprint(f"  ├─ Model name: {self.model_name}", "cyan")

                cprint(f"\n  ├─ Creating OpenRouter client (via OpenAI SDK)...", "cyan")
                # OpenRouter uses OpenAI-compatible API
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                cprint(f"  ├─ ✅ OpenRouter client created", "green")

                # Test the connection with a simple completion
                cprint(f"  ├─ Testing connection with model: {self.model_name}", "cyan")
                test_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": "Hello"}
                    ],
                    max_tokens=10
                )
                cprint(f"  ├─ ✅ Test response received", "green")
                cprint(f"  ├─ Response content: {test_response.choices[0].message.content}", "cyan")

                model_info = self.AVAILABLE_MODELS.get(self.model_name, {
                    "description": "Custom model via OpenRouter",
                    "input_price": "See openrouter.ai/docs",
                    "output_price": "See openrouter.ai/docs"
                })
                cprint(f"  ├─ ✨ OpenRouter model initialized: {self.model_name}", "green")
                cprint(f"  ├─ Model info: {model_info.get('description', '')}", "cyan")
                cprint(f"  └─ Pricing: Input {model_info.get('input_price', '')} | Output {model_info.get('output_price', '')}", "yellow")
                
                # Success! Exit the retry loop
                return

            except Exception as e:
                last_error = e
                error_str = str(e)
                
                cprint(f"\n❌ Failed to initialize OpenRouter client", "red")
                cprint(f"  ├─ Error type: {type(e).__name__}", "red")
                cprint(f"  ├─ Error message: {error_str}", "red")

                # Check for specific error types that should trigger key rotation
                should_rotate = False
                
                # Handle 402 (insufficient credits) - try next key
                if "402" in error_str or "insufficient" in error_str.lower():
                    cprint(f"  ├─ ⚠️ Key #{self.current_key_index + 1} has insufficient credits", "yellow")
                    should_rotate = True
                    self.failed_keys_today.add(self.current_key_index)
                
                # Handle 429 (rate limit) - try next key
                elif "429" in error_str or "rate_limit" in error_str.lower():
                    cprint(f"  ├─ ⚠️ Key #{self.current_key_index + 1} hit rate limit", "yellow")
                    should_rotate = True
                    self.failed_keys_today.add(self.current_key_index)
                
                # Handle 401 (invalid key) - try next key
                elif "401" in error_str or "api_key" in error_str.lower():
                    cprint(f"  ├─ ⚠️ Key #{self.current_key_index + 1} is invalid", "yellow")
                    should_rotate = True
                    self.failed_keys_today.add(self.current_key_index)
                
                # For other errors, don't rotate - probably a system issue
                else:
                    cprint(f"  ├─ 🤖 Non-key-related error, not rotating", "yellow")
                    if "model" in error_str.lower():
                        cprint(f"  ├─ 🤖 This appears to be a model name issue", "red")
                        cprint(f"  ├─ Requested model: {self.model_name}", "red")
                        cprint(f"  └─ See all models at: https://openrouter.ai/docs", "red")

                if hasattr(e, 'response'):
                    cprint(f"  ├─ Response status: {e.response.status_code}", "red")
                    cprint(f"  └─ Response body: {e.response.text}", "red")

                # Try rotating to next key if applicable
                if should_rotate and attempt < max_attempts - 1:
                    cprint(f"  └─ 💡 Trying next API key...", "cyan")
                    if self.rotate_to_next_key():
                        continue
                    else:
                        # All keys exhausted
                        break
                else:
                    # Either shouldn't rotate or no more attempts
                    break
        
        # If we get here, all attempts failed
        cprint(f"\n❌ Failed to initialize with any available API key", "red")
        if last_error:
            import traceback
            cprint(f"\n📋 Full traceback of last error:", "red")
            cprint(traceback.format_exc(), "red")
        
        self.client = None
        raise last_error if last_error else Exception("Failed to initialize OpenRouter client with any API key")

    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None, max_retries=None):
        """Generate response with no caching and automatic key rotation on rate limits"""
        # Check if system should resume from pause
        if not self.check_if_should_resume():
            # Still paused
            seconds_left = int((self.pause_until - datetime.now(timezone.utc)).total_seconds())
            hours = seconds_left // 3600
            minutes = (seconds_left % 3600) // 60
            cprint(f"⏸️  System paused - resuming in {hours}h {minutes}m", "yellow")
            return None
        
        if max_retries is None:
            max_retries = len(self.api_keys)  # Try all keys once
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Force unique request every time
                timestamp = int(time.time() * 1000)  # Millisecond precision

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{user_content}_{timestamp}"}  # Make each request unique
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens if max_tokens else self.max_tokens,
                    stream=False  # Disable streaming to prevent caching
                )

                # Extract content and filter out thinking tags
                raw_content = response.choices[0].message.content

                # Remove <think>...</think> tags and their content (for reasoning models)
                # First, try to remove complete <think>...</think> blocks
                filtered_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

                # If <think> tag exists but wasn't removed (unclosed tag due to token limit),
                # remove everything from <think> onwards
                if '<think>' in filtered_content:
                    filtered_content = filtered_content.split('<think>')[0].strip()

                # If filtering removed everything, return the original
                final_content = filtered_content if filtered_content else raw_content

                return ModelResponse(
                    content=final_content,
                    raw_response=response,
                    model_name=self.model_name,
                    usage=response.usage
                )

            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Extract error message from JSON response if available
                error_message = error_str
                try:
                    # Try to extract JSON from error string
                    json_match = re.search(r'\{.*\}', error_str, re.DOTALL)
                    if json_match:
                        error_json = json.loads(json_match.group())
                        if 'error' in error_json and 'message' in error_json['error']:
                            error_message = error_json['error']['message']
                except:
                    pass  # Use original error_str if parsing fails

                # Handle 429 Rate Limit errors
                if "429" in error_str or "rate_limit" in error_str.lower():
                    cprint(f"⚠️  OpenRouter Rate Limit for Key #{self.current_key_index + 1}", "yellow")
                    cprint(f"   Model: {self.model_name}", "yellow")
                    cprint(f"   Error: {error_message}", "yellow")
                    
                    # Check if it's daily limit or per-minute limit
                    is_daily_limit = (
                        "daily limit" in error_message.lower() or 
                        "free model" in error_message.lower() or
                        "quota exceeded" in error_message.lower()
                    )
                    
                    is_minute_limit = (
                        "too many requests" in error_message.lower() or
                        "rate limited" in error_message.lower()
                    )
                    
                    if is_daily_limit:
                        # Daily limit reached (50 req/day for :free models)
                        cprint(f"   🚫 Daily Free-Limit reached (50 requests/day shared across all :free models)", "red")
                        cprint(f"   ⏰ Reset: täglich um 00:00 UTC", "cyan")
                        
                        # Mark current key as failed for today
                        self.failed_keys_today.add(self.current_key_index)
                        
                        # Try rotating to next key
                        if attempt < max_retries - 1:
                            if self.rotate_to_next_key():
                                cprint(f"   💡 Rotating to next API key...", "cyan")
                                continue
                            else:
                                cprint(f"   ❌ All API keys exhausted", "red")
                                return None
                        else:
                            cprint(f"   ❌ Max retries reached", "red")
                            return None
                    
                    elif is_minute_limit:
                        # Per-minute limit (~20 req/min for :free models)
                        cprint(f"   ⏱️  Minute Rate-Limit reached (~20 requests/min for :free models)", "yellow")
                        if attempt < max_retries - 1:
                            cprint(f"   ⏳ Waiting 3 seconds before retry...", "cyan")
                            time.sleep(3)
                            continue  # Retry with same key
                        else:
                            cprint(f"   ❌ Max retries reached", "red")
                            return None
                    
                    else:
                        # Generic rate limit - try rotating
                        self.failed_keys_today.add(self.current_key_index)
                        if attempt < max_retries - 1:
                            if self.rotate_to_next_key():
                                cprint(f"   💡 Trying next API key...", "cyan")
                                continue
                            else:
                                return None
                        else:
                            return None

                # Handle 402 quota/credits errors
                elif "402" in error_str or "insufficient" in error_str.lower():
                    cprint(f"⚠️  OpenRouter Credits Issue for Key #{self.current_key_index + 1}", "yellow")
                    cprint(f"   Model: {self.model_name}", "yellow")
                    cprint(f"   Error: {error_message}", "yellow")
                    
                    # Check if it's negative balance
                    if "negative" in error_message.lower() or "never purchased" in error_message.lower():
                        cprint(f"   💰 Key has negative balance or no credits", "red")
                        cprint(f"   💡 Add credits at: https://openrouter.ai/credits", "cyan")
                    
                    # Mark current key as failed
                    self.failed_keys_today.add(self.current_key_index)
                    
                    # Try rotating to next key
                    if attempt < max_retries - 1:
                        if self.rotate_to_next_key():
                            cprint(f"   💡 Trying next API key...", "cyan")
                            continue
                        else:
                            cprint(f"   ❌ All API keys exhausted", "red")
                            return None
                    else:
                        cprint(f"   ❌ Max retries reached", "red")
                        return None

                # Raise 503 errors (service unavailable)
                if "503" in error_str:
                    raise e

                # Log other errors
                cprint(f"❌ OpenRouter error: {error_str}", "red")
                return None
        
        # If we exhausted all retries
        cprint(f"❌ Failed after {max_retries} attempts with all API keys", "red")
        if last_error:
            cprint(f"   Last error: {str(last_error)}", "red")
        return None

    def is_available(self) -> bool:
        """Check if OpenRouter is available"""
        return self.client is not None

    @property
    def model_type(self) -> str:
        return "openrouter"
