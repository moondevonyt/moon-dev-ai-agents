#!/usr/bin/env python3
"""
🌙 Moon Dev's Swarm Agent 🌙

Queries multiple AI models in parallel and returns:
- Clean individual responses from each model
- AI-generated consensus summary (Claude 4.5 synthesizes all responses)

Perfect for getting diverse AI perspectives on trading decisions,
validating strategies, or any decision that benefits from multiple viewpoints.

Usage:
    # Run directly (asks for prompt interactively)
    python src/agents/swarm_agent.py

    # Import and use in other agents
    from src.agents.swarm_agent import SwarmAgent

    swarm = SwarmAgent()
    result = swarm.query("Should I buy Bitcoin now?")

    # Access consensus summary
    print(result["consensus_summary"])  # 3-sentence synthesis by Claude 4.5

    # Access individual responses
    for provider, data in result["responses"].items():
        if data["success"]:
            print(f"{provider}: {data['response']}")

    # Check model mapping (AI #1 = CLAUDE, AI #2 = OPENAI, etc.)
    print(result["model_mapping"])

Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from termcolor import colored, cprint
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import Moon Dev's model factory
from src.models.model_factory import model_factory

# ============================================
# 🎯 SWARM CONFIGURATION - EDIT THIS SECTION
# ============================================

# Configure which models to use in the swarm (set to True to enable)
SWARM_MODELS = {
    # 🌙 Moon Dev's Active Swarm Models - 3 Model Configuration
    "deepseek": (True, "deepseek", "deepseek-chat"),  # DeepSeek Chat - Fast chat model (API)
    "xai": (True, "xai", "grok-4-fast-reasoning"),  # Grok-4 fast reasoning ($0.20-$0.50/1M tokens)
    "openrouter_qwen": (True, "openrouter", "qwen/qwen3-max"),  # Qwen 3 Max - Powerful reasoning ($1.00/$1.00 per 1M tokens)

    # 🔇 Disabled Models (uncomment to enable)
    "claude": (True, "claude", "claude-sonnet-4-5"),  # Claude 4.5 Sonnet - Latest & Greatest!
    #"openai": (True, "openai", "gpt-5"),  # GPT-5 - Most advanced model!
    #"ollama_qwen": (True, "ollama", "qwen3:8b"),  # Qwen3 8B via Ollama - Fast local reasoning!
    #"ollama": (True, "ollama", "DeepSeek-R1:latest"),  # DeepSeek-R1 local model via Ollama
    #"openrouter_qwen": (True, "openrouter", "qwen/qwen3-max"),  # Qwen 3 Max - Powerful reasoning ($1.00/$1.00 per 1M tokens)

    # 🌙 OpenRouter Models - Access 200+ models through one API!
    # Uncomment any of these to add them to your swarm:
    #"openrouter_gemini": (True, "openrouter", "google/gemini-2.5-flash"),  # Gemini 2.5 Flash - Fast & cheap! ($0.10/$0.40 per 1M tokens)
    "openrouter_glm": (True, "openrouter", "z-ai/glm-4.6"),  # GLM 4.6 - Zhipu AI reasoning ($0.50/$0.50 per 1M tokens)
    #"openrouter_deepseek_r1": (True, "openrouter", "deepseek/deepseek-r1-0528"),  # DeepSeek R1 - Advanced reasoning ($0.55/$2.19 per 1M tokens)
    #"openrouter_claude_opus": (True, "openrouter", "anthropic/claude-opus-4.1"),  # Claude Opus 4.1 via OpenRouter
    "openrouter_gpt5_mini": (True, "openrouter", "openai/gpt-5-mini"),  # GPT-5 Mini via OpenRouter

    # 💡 See all 200+ models at: https://openrouter.ai/docs
    # 💡 Any model from openrouter_model.py can be used here!
}

# Default parameters for model queries
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048  # Increased for model compatibility (Gemini/Groq/Qwen need 2048+ minimum)

# Timeout for each model (seconds)
MODEL_TIMEOUT = 120  # 🌙 Moon Dev - Increased to 120s for more reliability

# Consensus Reviewer - Synthesizes all responses into a clean summary
CONSENSUS_REVIEWER_MODEL = ("deepseek", "deepseek-chat")  # Using DeepSeek Chat API (fast)
CONSENSUS_REVIEWER_PROMPT = """You are a consensus analyzer reviewing multiple AI responses.

Below are responses from {num_models} different AI models to the same question.

{responses}

Your task: Provide a clear, concise 3-sentence maximum consensus response that:
1. Synthesizes the common themes across all responses
2. Highlights any notable agreements or disagreements
3. Gives a balanced, actionable summary

Keep it under 3 sentences. Be direct and clear."""

# Save results to file
SAVE_RESULTS = True
RESULTS_DIR = Path(project_root) / "src" / "data" / "swarm_agent"

# ============================================
# END CONFIGURATION
# ============================================

class SwarmAgent:
    """Moon Dev's Swarm Agent for multi-model consensus"""

    def __init__(self, custom_models: Optional[Dict] = None):
        """
        Initialize the Swarm Agent

        Args:
            custom_models: Optional dict to override SWARM_MODELS configuration
        """
        self.models_config = custom_models or SWARM_MODELS
        self.active_models = {}
        self.results_dir = RESULTS_DIR

        # Create results directory if saving is enabled
        if SAVE_RESULTS:
            self.results_dir.mkdir(parents=True, exist_ok=True)

        # Initialize models
        self._initialize_models()

        cprint("\n" + "="*60, "cyan")
        cprint("🌙 Moon Dev's Swarm Agent Initialized 🌙", "cyan", attrs=['bold'])
        cprint("="*60, "cyan")
        cprint(f"\n🤖 Active Models in Swarm: {len(self.active_models)}", "green")
        for name in self.active_models.keys():
            cprint(f"   ✅ {name}", "green")

    def _initialize_models(self):
        """Initialize all enabled models"""
        for provider, (enabled, model_type, model_name) in self.models_config.items():
            if not enabled:
                continue

            try:
                # Get model from factory
                model = model_factory.get_model(model_type, model_name)
                if model:
                    self.active_models[provider] = {
                        "model": model,
                        "type": model_type,
                        "name": model_name
                    }
                    cprint(f"✅ Initialized {provider}: {model_name}", "green")
                else:
                    cprint(f"⚠️ Could not initialize {provider}: {model_name}", "yellow")
            except Exception as e:
                cprint(f"❌ Error initializing {provider}: {e}", "red")

    def _query_single_model(self, provider: str, model_info: Dict, prompt: str,
                          system_prompt: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Query a single model

        Returns:
            Tuple of (provider_name, response_dict)
        """
        start_time = time.time()

        try:
            # Default system prompt if none provided
            if system_prompt is None:
                system_prompt = "You are a helpful AI assistant providing thoughtful analysis."

            # Query the model
            response = model_info["model"].generate_response(
                system_prompt=system_prompt,
                user_content=prompt,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )

            elapsed = time.time() - start_time

            return provider, {
                "provider": provider,
                "model": model_info["name"],
                "response": response,
                "success": True,
                "error": None,
                "response_time": round(elapsed, 2)
            }

        except Exception as e:
            elapsed = time.time() - start_time
            cprint(f"❌ Error querying {provider}: {e}", "red")

            return provider, {
                "provider": provider,
                "model": model_info["name"],
                "response": None,
                "success": False,
                "error": str(e),
                "response_time": round(elapsed, 2)
            }

    def query(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Query all models in the swarm in parallel

        Args:
            prompt: The prompt to send to all models
            system_prompt: Optional system prompt (uses default if None)

        Returns:
            Dict containing individual responses and metadata
        """
        cprint(f"\n🌊 Initiating Swarm Query with {len(self.active_models)} models...", "cyan", attrs=['bold'])
        cprint(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}", "blue")

        # Show which models are being called in parallel
        cprint(f"\n🚀 Calling models in parallel:", "yellow", attrs=['bold'])
        for provider, model_info in self.active_models.items():
            cprint(f"   → {provider.upper()}: {model_info['name']}", "cyan")

        start_time = time.time()
        all_responses = {}

        # Use ThreadPoolExecutor for parallel queries
        with ThreadPoolExecutor(max_workers=len(self.active_models)) as executor:
            # Submit all queries
            futures = {
                executor.submit(
                    self._query_single_model,
                    provider,
                    model_info,
                    prompt,
                    system_prompt
                ): provider
                for provider, model_info in self.active_models.items()
            }

            # Track which models are still pending
            completed_count = 0
            total_models = len(futures)

            # Collect results as they complete (with timeout handling)
            try:
                for future in as_completed(futures, timeout=MODEL_TIMEOUT + 10):
                    provider = futures[future]
                    completed_count += 1

                    cprint(f"\n⏳ Waiting for responses... ({completed_count}/{total_models} completed)", "yellow")
                    cprint(f"🔄 Processing: {provider}...", "cyan")

                    try:
                        provider, response = future.result(timeout=5)  # 5 second timeout per result
                        all_responses[provider] = response

                        if response["success"]:
                            cprint(f"   ✅ {provider} responded ({response['response_time']}s)", "green")
                        else:
                            cprint(f"   ❌ {provider} failed: {response['error']}", "red")

                    except TimeoutError:
                        cprint(f"   ⏰ {provider} timed out (>{MODEL_TIMEOUT}s) - skipping", "yellow")
                        all_responses[provider] = {
                            "provider": provider,
                            "model": "timeout",
                            "response": None,
                            "success": False,
                            "error": f"Timeout after {MODEL_TIMEOUT}s",
                            "response_time": MODEL_TIMEOUT
                        }
                    except Exception as e:
                        cprint(f"   💥 {provider} error: {str(e)}", "red")
                        all_responses[provider] = {
                            "provider": provider,
                            "model": "error",
                            "response": None,
                            "success": False,
                            "error": str(e),
                            "response_time": 0
                        }

            except TimeoutError as timeout_error:
                # as_completed timed out waiting for all futures
                cprint(f"\n⏰ Overall timeout reached - some models didn't respond", "yellow")
                cprint(f"⚠️ {str(timeout_error)}", "yellow")
                # Mark any remaining futures as timed out
                for future, provider in futures.items():
                    if provider not in all_responses:
                        cprint(f"   ⏰ {provider} never responded - marking as timeout", "red")
                        all_responses[provider] = {
                            "provider": provider,
                            "model": "timeout",
                            "response": None,
                            "success": False,
                            "error": f"Global timeout - no response received",
                            "response_time": MODEL_TIMEOUT
                        }
                # 🌙 Moon Dev - Don't raise, continue with partial results
                cprint(f"✅ Continuing with {len([r for r in all_responses.values() if r['success']])} successful responses", "green")

        # Generate consensus review summary (with model mapping)
        consensus_summary, model_mapping = self._generate_consensus_review(all_responses, prompt)

        # Clean up responses for easy parsing (extract just the text content)
        clean_responses = {}
        for provider, data in all_responses.items():
            if data["success"]:
                # Extract clean text from ModelResponse
                if hasattr(data['response'], 'content'):
                    response_text = data['response'].content
                else:
                    response_text = str(data['response'])

                # Strip out <think> tags from Ollama responses
                response_text = self._strip_think_tags(response_text)

                clean_responses[provider] = {
                    "response": response_text,
                    "response_time": data["response_time"],
                    "success": True
                }
            else:
                clean_responses[provider] = {
                    "response": None,
                    "error": data["error"],
                    "response_time": data["response_time"],
                    "success": False
                }

        # Prepare results
        total_time = round(time.time() - start_time, 2)

        result = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "system_prompt": system_prompt,
            "consensus_summary": consensus_summary,  # Clean 3-sentence AI review
            "model_mapping": model_mapping,  # Which AI # corresponds to which provider
            "responses": clean_responses,  # Clean, easy-to-parse responses
            "metadata": {
                "total_models": len(self.active_models),
                "successful_responses": sum(1 for r in all_responses.values() if r["success"]),
                "failed_responses": sum(1 for r in all_responses.values() if not r["success"]),
                "total_time": total_time
            }
        }

        # Save results if enabled
        if SAVE_RESULTS:
            self._save_results(result)

        return result

    def _strip_think_tags(self, text: str) -> str:
        """Remove <think>...</think> tags from response text"""
        # Remove <think>...</think> blocks (multiline)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _generate_consensus_review(self, responses: Dict[str, Dict], original_prompt: str) -> Tuple[str, Dict]:
        """
        Generate a consensus review summary using the consensus reviewer AI

        Args:
            responses: All responses from the swarm
            original_prompt: The original user prompt

        Returns:
            Tuple of (consensus_summary, model_mapping)
            - consensus_summary: Clean 3-sentence consensus summary
            - model_mapping: Dict mapping AI numbers to provider names
        """
        try:
            # Get successful responses only
            successful_responses = [
                (provider, r["response"]) for provider, r in responses.items()
                if r["success"] and r["response"]
            ]

            if not successful_responses:
                return "No successful responses to analyze.", {}

            # Build model mapping (AI #1 = claude, AI #2 = openai, etc.)
            model_mapping = {}
            formatted_responses = []
            for i, (provider, response) in enumerate(successful_responses, 1):
                model_mapping[f"AI #{i}"] = provider.upper()

                # Extract clean text
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)

                # Strip <think> tags before sending to consensus reviewer
                response_text = self._strip_think_tags(response_text)

                # Truncate long responses for the reviewer
                if len(response_text) > 1000:
                    response_text = response_text[:1000] + "..."

                # Don't include provider name in prompt to avoid bias - just use numbers
                formatted_responses.append(f"AI #{i}:\n{response_text}\n")

            # Build the full prompt for consensus reviewer
            responses_text = "\n".join(formatted_responses)
            full_prompt = CONSENSUS_REVIEWER_PROMPT.format(
                num_models=len(successful_responses),
                responses=responses_text
            )

            # Get consensus reviewer model
            model_type, model_name = CONSENSUS_REVIEWER_MODEL
            reviewer_model = model_factory.get_model(model_type, model_name)

            if not reviewer_model:
                return "Consensus reviewer model not available.", model_mapping

            cprint(f"\n🧠 Generating consensus summary with {model_name}...", "magenta")

            # Generate consensus review
            review_response = reviewer_model.generate_response(
                system_prompt="You are a consensus analyzer. Provide clear, concise 3-sentence summaries.",
                user_content=f"Original Question: {original_prompt}\n\n{full_prompt}",
                temperature=0.3,  # Lower temperature for more focused summary
                max_tokens=200  # Short and concise
            )

            # Extract clean text
            if hasattr(review_response, 'content'):
                consensus_summary = review_response.content.strip()
            else:
                consensus_summary = str(review_response).strip()

            cprint(f"✅ Consensus summary generated!", "green")

            return consensus_summary, model_mapping

        except Exception as e:
            cprint(f"❌ Error generating consensus review: {e}", "red")
            return f"Error generating consensus summary: {str(e)}", {}

    def _save_results(self, result: Dict):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.results_dir / f"swarm_result_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        cprint(f"\n💾 Results saved to: {filename.relative_to(Path(project_root))}", "blue")

    def _print_summary(self, result: Dict):
        """Print a summary of the swarm results"""
        metadata = result["metadata"]

        cprint("\n" + "="*60, "green")
        cprint("🎯 SWARM CONSENSUS", "green", attrs=['bold'])
        cprint("="*60, "green")

        # Show model mapping first
        if "model_mapping" in result and result["model_mapping"]:
            cprint("\n🔢 Model Key:", "blue")
            for ai_num, provider in result["model_mapping"].items():
                cprint(f"   {ai_num} = {provider}", "white")

        # Show AI-generated consensus summary
        if "consensus_summary" in result:
            cprint("\n🧠 AI CONSENSUS SUMMARY:", "magenta", attrs=['bold'])
            cprint(f"{result['consensus_summary']}\n", "white")

        cprint(f"⚡ Performance:", "cyan")
        cprint(f"   Total Time: {metadata['total_time']}s", "white")
        cprint(f"   Success Rate: {metadata['successful_responses']}/{metadata['total_models']}", "white")

    def query_dataframe(self, prompt: str, system_prompt: Optional[str] = None) -> pd.DataFrame:
        """
        Query swarm and return results as a DataFrame

        Returns:
            DataFrame with columns: provider, response, success, error, response_time
        """
        result = self.query(prompt, system_prompt)

        # Convert responses to DataFrame
        data = []
        for provider, response_data in result["responses"].items():
            data.append({
                "provider": provider,
                "response": response_data["response"][:500] if response_data["response"] else None,
                "success": response_data["success"],
                "error": response_data.get("error"),
                "response_time": response_data["response_time"]
            })

        return pd.DataFrame(data)


def main():
    """Simple interactive swarm query"""
    cprint("\n" + "="*60, "cyan")
    cprint("🌙 Moon Dev's Swarm Agent 🌙", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    # Initialize swarm
    swarm = SwarmAgent()

    # Ask for prompt
    cprint("\n💭 What would you like to ask the AI swarm?", "yellow")
    prompt = input("🌙 Prompt > ").strip()

    if not prompt:
        cprint("❌ No prompt provided. Exiting.", "red")
        return

    # Query the swarm
    result = swarm.query(prompt)

    # Show individual responses
    cprint("\n" + "="*60, "cyan")
    cprint("📋 AI RESPONSES", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    # Create reverse mapping to show AI numbers
    reverse_mapping = {}
    if "model_mapping" in result:
        for ai_num, provider in result["model_mapping"].items():
            reverse_mapping[provider.lower()] = ai_num

    for provider, data in result["responses"].items():
        if data["success"]:
            # Get AI number if available
            ai_label = reverse_mapping.get(provider, "")
            if ai_label:
                cprint(f"\n🤖 {ai_label} ({provider.upper()}):", "yellow", attrs=['bold'])
            else:
                cprint(f"\n🤖 {provider.upper()}:", "yellow", attrs=['bold'])

            response_text = data['response']

            # Truncate if too long (show first 800 chars)
            if len(response_text) > 800:
                cprint(f"{response_text[:800]}...\n", "white")
                cprint("[Response truncated - see full output in saved JSON]", "cyan")
            else:
                cprint(f"{response_text}", "white")

            cprint(f"⏱️  Response time: {data['response_time']}s", "cyan")
        else:
            cprint(f"\n❌ {provider.upper()}: Failed - {data['error']}", "red")

    # Show summary
    swarm._print_summary(result)

    cprint("\n✨ Swarm query complete! 🌙", "cyan", attrs=['bold'])


if __name__ == "__main__":
    main()