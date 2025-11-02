"""
🌙 Moon Dev's Telegram Notifier
Built with love by Moon Dev 🚀

Sends notifications to Telegram when important events occur.
"""

import os
import requests
from termcolor import cprint
from typing import Optional
from datetime import datetime


class TelegramNotifier:
    """Send notifications via Telegram Bot"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram Notifier
        
        Args:
            bot_token: Telegram Bot Token (or load from TELEGRAM_BOT_TOKEN env)
            chat_id: Telegram Chat ID (or load from TELEGRAM_CHAT_ID env)
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            cprint("⚠️  Telegram credentials not found", "yellow")
            cprint("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env", "yellow")
            self.enabled = False
        else:
            self.enabled = True
            cprint("✅ Telegram Notifier initialized", "green")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram
        
        Args:
            message: Message text (supports HTML or Markdown)
            parse_mode: "HTML" or "Markdown"
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            cprint("⚠️  Telegram not enabled - skipping notification", "yellow")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                cprint("✅ Telegram notification sent", "green")
                return True
            else:
                cprint(f"❌ Telegram API error: {response.status_code}", "red")
                cprint(f"   Response: {response.text}", "red")
                return False
                
        except Exception as e:
            cprint(f"❌ Failed to send Telegram notification: {str(e)}", "red")
            return False
    
    def send_rate_limit_alert(self, total_keys: int, model_name: str) -> bool:
        """
        Send alert when all API keys are exhausted
        
        Args:
            total_keys: Total number of API keys
            model_name: Name of the model being used
            
        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🚨 <b>OpenRouter Rate Limit Alert</b>\n\n"
            f"⏰ <b>Time:</b> {timestamp}\n"
            f"🔑 <b>Keys Exhausted:</b> {total_keys}/{total_keys}\n"
            f"🤖 <b>Model:</b> <code>{model_name}</code>\n\n"
            f"❌ All API keys have reached their daily limit (50 requests/key).\n\n"
            f"💡 <b>Actions:</b>\n"
            f"• System is now paused\n"
            f"• Will resume at 00:00 UTC (limit reset)\n"
            f"• Or add more API keys to .env\n\n"
            f"🌙 <i>Moon Dev's AI Trading Bot</i>"
        )
        
        return self.send_message(message)
    
    def send_key_rotation_alert(self, current_key: int, total_keys: int, model_name: str) -> bool:
        """
        Send alert when rotating to a new API key
        
        Args:
            current_key: Index of current key (0-based, will be displayed as 1-based)
            total_keys: Total number of API keys
            model_name: Name of the model being used
            
        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🔄 <b>API Key Rotation</b>\n\n"
            f"⏰ <b>Time:</b> {timestamp}\n"
            f"🔑 <b>Switched to Key:</b> #{current_key + 1}/{total_keys}\n"
            f"🤖 <b>Model:</b> <code>{model_name}</code>\n\n"
            f"ℹ️ Previous key reached rate limit.\n"
            f"✅ Continuing with next available key.\n\n"
            f"🌙 <i>Moon Dev's AI Trading Bot</i>"
        )
        
        return self.send_message(message)
    
    def send_system_resumed_alert(self, model_name: str) -> bool:
        """
        Send alert when system resumes after rate limit pause
        
        Args:
            model_name: Name of the model being used
            
        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"✅ <b>System Resumed</b>\n\n"
            f"⏰ <b>Time:</b> {timestamp}\n"
            f"🤖 <b>Model:</b> <code>{model_name}</code>\n\n"
            f"🔄 API key limits have been reset.\n"
            f"✅ System is now operational again.\n\n"
            f"🌙 <i>Moon Dev's AI Trading Bot</i>"
        )
        
        return self.send_message(message)


# Create singleton instance
_telegram_notifier = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get or create Telegram Notifier singleton"""
    global _telegram_notifier
    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier
