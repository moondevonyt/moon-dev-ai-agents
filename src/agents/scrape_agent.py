#!/usr/bin/env python3
"""
🌙 Moon Dev's Scrape Agent 🌙

Scrapes websites and analyzes them using AI swarms!

Features:
- Batch processing - enter multiple URLs at once (space-separated)
- Parallel execution - all URLs scrape + analyze simultaneously
- Selenium headless browser - handles JavaScript-rendered sites (Next.js, React, etc.)
- SwarmAgent integration - multiple AI models analyze in parallel
- Extracts text, metadata (title, description, keywords)
- Saves AI analysis to file with cleaned URL names
- Clean terminal - results shown only when all URLs complete

Requirements:
    pip install selenium
    brew install chromedriver  # macOS (or download for Windows/Linux)

Usage:
    python src/agents/scrape_agent.py

    Then enter multiple URLs separated by spaces:
    > https://site1.com https://site2.com https://site3.com

    All process in parallel, results shown when complete!
    Then ready for next batch.

Built with love by Moon Dev 🚀
"""

import os
import sys
import re
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from termcolor import colored, cprint
from bs4 import BeautifulSoup
import threading
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 🌙 Moon Dev: Dynamic path calculation
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"

# Add project root to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import Moon Dev's agents and models
from src.agents.swarm_agent import SwarmAgent
from src.models.model_factory import model_factory

# ============================================
# 🎯 CONFIGURATION - EDIT THIS SECTION
# ============================================

# Use SwarmAgent (True) or XAI model only (False)
USE_SWARM = True

# XAI model to use when swarm is disabled
XAI_MODEL = "grok-4-fast-reasoning"

# Default analysis prompt
DEFAULT_PROMPT = """Give me two sentences and ten bullet points about what this website is about."""

# Where to save results
RESULTS_DIR = DATA_DIR / "scrape_agent"

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# User agent for scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# ============================================
# END CONFIGURATION
# ============================================


class ScrapeAgent:
    """🌙 Moon Dev's Scrape Agent for website analysis"""

    def __init__(self, use_swarm: bool = USE_SWARM, prompt: Optional[str] = None):
        """
        Initialize the Scrape Agent

        Args:
            use_swarm: Use SwarmAgent (True) or XAI model only (False)
            prompt: Custom analysis prompt (uses DEFAULT_PROMPT if None)
        """
        self.use_swarm = use_swarm
        self.prompt = prompt or DEFAULT_PROMPT
        self.results_dir = RESULTS_DIR

        # Create results directory
        self.results_dir.mkdir(parents=True, exist_ok=True)

        cprint("\n" + "="*60, "cyan")
        cprint("🌙 Moon Dev's Scrape Agent Initialized 🌙", "cyan", attrs=['bold'])
        cprint("="*60, "cyan")

        # Initialize AI models
        if self.use_swarm:
            cprint("\n🤖 Initializing SwarmAgent (multi-model analysis)...", "green")
            self.swarm = SwarmAgent()
            self.ai_mode = "SWARM"
        else:
            cprint(f"\n🤖 Initializing XAI model ({XAI_MODEL})...", "green")
            self.xai_model = model_factory.get_model("xai", XAI_MODEL)
            if not self.xai_model:
                cprint("❌ Failed to initialize XAI model!", "red")
                raise Exception("XAI model not available")
            self.ai_mode = "XAI"

        cprint(f"✅ AI Mode: {self.ai_mode}", "green")
        cprint(f"📝 Analysis Prompt: {self.prompt[:60]}...", "blue")
        cprint(f"💾 Results saved to: {self.results_dir.relative_to(PROJECT_ROOT)}", "blue")

    def clean_url_for_filename(self, url: str) -> str:
        """
        Clean URL to create a valid filename

        Args:
            url: The URL to clean

        Returns:
            Cleaned filename string
        """
        # Parse the URL
        parsed = urlparse(url)

        # Get domain + path
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip("/").replace("/", "_")

        # Combine
        if path:
            filename = f"{domain}_{path}"
        else:
            filename = domain

        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)

        # Truncate if too long
        if len(filename) > 100:
            filename = filename[:100]

        return filename

    def scrape_website(self, url: str) -> Dict:
        """
        Scrape a website and extract content using Selenium (handles JS-rendered sites)

        Args:
            url: The URL to scrape

        Returns:
            Dict containing scraped data
        """
        cprint(f"\n🌐 Scraping: {url}", "cyan")

        driver = None
        try:
            # Set up Chrome options for headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={USER_AGENT}")
            chrome_options.add_argument("--window-size=1920,1080")

            # Suppress logs
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            # Launch browser
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(REQUEST_TIMEOUT)

            # Navigate to URL
            cprint(f"🚀 Loading page with headless browser...", "yellow")
            driver.get(url)

            # Wait for page to fully load (including JS)
            time.sleep(3)

            # Get the rendered HTML
            page_source = driver.page_source

            # Get title
            title_text = driver.title or "No title found"

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if not meta_desc:
                meta_desc = soup.find('meta', property='og:description')
            description = meta_desc.get('content', '') if meta_desc else "No description found"

            # Extract meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            keywords = meta_keywords.get('content', '') if meta_keywords else "No keywords found"

            # Extract main text content (remove scripts, styles, etc.)
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up text (remove extra whitespace)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)

            # Truncate if too long (keep first 10000 chars for AI)
            if len(clean_text) > 10000:
                clean_text = clean_text[:10000] + "\n\n[Content truncated...]"

            # Close browser
            driver.quit()

            cprint(f"✅ Scraped {len(clean_text)} characters", "green")

            return {
                "url": url,
                "title": title_text,
                "description": description,
                "keywords": keywords,
                "content": clean_text,
                "success": True,
                "error": None,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Make sure to close browser on error
            if driver:
                try:
                    driver.quit()
                except:
                    pass

            cprint(f"❌ Error scraping {url}: {str(e)}", "red")
            return {
                "url": url,
                "title": None,
                "description": None,
                "keywords": None,
                "content": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def analyze_content(self, scraped_data: Dict) -> Dict:
        """
        Analyze scraped content using AI

        Args:
            scraped_data: Dict containing scraped website data

        Returns:
            Dict containing AI analysis results
        """
        if not scraped_data["success"]:
            return {
                "success": False,
                "error": "Scraping failed, cannot analyze"
            }

        # Build analysis prompt with scraped data
        analysis_prompt = f"""Website: {scraped_data['url']}
Title: {scraped_data['title']}
Description: {scraped_data['description']}
Keywords: {scraped_data['keywords']}

Content:
{scraped_data['content']}

---

{self.prompt}"""

        cprint(f"\n🧠 Analyzing content with {self.ai_mode}...", "magenta")

        try:
            if self.use_swarm:
                # Use SwarmAgent
                result = self.swarm.query(analysis_prompt)

                return {
                    "success": True,
                    "ai_mode": "SWARM",
                    "consensus_summary": result.get("consensus_summary"),
                    "model_mapping": result.get("model_mapping"),
                    "responses": result.get("responses"),
                    "metadata": result.get("metadata"),
                    "error": None
                }
            else:
                # Use XAI model
                response = self.xai_model.generate_response(
                    system_prompt="You are a helpful AI assistant analyzing websites.",
                    user_content=analysis_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                # Extract response text
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)

                return {
                    "success": True,
                    "ai_mode": "XAI",
                    "response": response_text,
                    "model": XAI_MODEL,
                    "error": None
                }

        except Exception as e:
            cprint(f"❌ Error analyzing content: {str(e)}", "red")
            return {
                "success": False,
                "error": str(e)
            }

    def save_results(self, url: str, scraped_data: Dict, analysis_results: Dict):
        """
        Save results to multiple file formats

        Args:
            url: Original URL
            scraped_data: Scraped website data
            analysis_results: AI analysis results
        """
        # Create filename from URL
        filename = self.clean_url_for_filename(url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename}_{timestamp}"

        # Create subfolders
        raw_scrapes_dir = self.results_dir / "raw_scrapes"
        raw_scrapes_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Save JSON (full data) - main directory
            json_filepath = self.results_dir / f"{base_filename}.json"
            full_results = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "scraped_data": scraped_data,
                "analysis": analysis_results
            }
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, indent=2, ensure_ascii=False)

            # 2. Save human-readable TXT (metadata + AI responses) - main directory
            txt_filepath = self.results_dir / f"{base_filename}.txt"
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"URL: {url}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n\n")

                # METADATA SECTION
                f.write("METADATA:\n")
                f.write("="*80 + "\n\n")
                f.write(f"Title:\n{scraped_data.get('title', 'N/A')}\n\n")
                f.write(f"Description:\n{scraped_data.get('description', 'N/A')}\n\n")
                f.write(f"Keywords:\n{scraped_data.get('keywords', 'N/A')}\n\n")

                # AI ANALYSIS SECTION
                f.write("="*80 + "\n\n")
                f.write("AI ANALYSIS:\n")
                f.write("="*80 + "\n\n")

                if analysis_results and analysis_results["success"]:
                    if analysis_results["ai_mode"] == "SWARM":
                        # Consensus summary
                        f.write("🧠 AI CONSENSUS SUMMARY:\n")
                        f.write("-"*80 + "\n")
                        f.write(f"{analysis_results['consensus_summary']}\n\n")

                        # Model mapping
                        if analysis_results.get("model_mapping"):
                            f.write("🔢 MODEL KEY:\n")
                            f.write("-"*80 + "\n")
                            for ai_num, provider in analysis_results["model_mapping"].items():
                                f.write(f"{ai_num} = {provider}\n")
                            f.write("\n")

                        # Individual responses
                        f.write("📋 INDIVIDUAL AI RESPONSES:\n")
                        f.write("-"*80 + "\n\n")
                        for provider, data in analysis_results["responses"].items():
                            if data["success"]:
                                f.write(f"🤖 {provider.upper()}:\n")
                                f.write(f"{data['response']}\n\n")
                                f.write("-"*80 + "\n\n")
                            else:
                                f.write(f"❌ {provider.upper()}: Failed - {data.get('error', 'Unknown error')}\n\n")
                    else:
                        # XAI mode
                        f.write("🤖 XAI RESPONSE:\n")
                        f.write("-"*80 + "\n")
                        f.write(f"{analysis_results['response']}\n")
                else:
                    f.write(f"ERROR: {analysis_results.get('error', 'Analysis failed')}\n")

            # 3. Save raw scraped content (debug) - raw_scrapes/
            raw_filepath = raw_scrapes_dir / f"{base_filename}.txt"
            with open(raw_filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n\n")
                f.write("RAW SCRAPED CONTENT:\n")
                f.write("="*80 + "\n\n")
                if scraped_data["success"]:
                    f.write(scraped_data["content"])
                else:
                    f.write(f"ERROR: {scraped_data['error']}")

            cprint(f"\n💾 Results saved:", "green", attrs=['bold'])
            cprint(f"   📄 JSON: {json_filepath.name}", "white")
            cprint(f"   📝 Human Readable: {txt_filepath.name}", "white")
            cprint(f"   🔍 Raw Scrape: raw_scrapes/{raw_filepath.name}", "white")

            # Also print the analysis to console
            self._print_analysis(analysis_results, url)

        except Exception as e:
            cprint(f"❌ Error saving results: {str(e)}", "red")

    def _print_analysis(self, analysis_results: Dict, url: str):
        """Print analysis results to console"""
        cprint("\n" + "="*60, "green")
        cprint(f"🎯 ANALYSIS RESULTS: {url}", "green", attrs=['bold'])
        cprint("="*60, "green")

        if not analysis_results["success"]:
            cprint(f"❌ Analysis failed: {analysis_results['error']}", "red")
            return

        if analysis_results["ai_mode"] == "SWARM":
            # Show consensus summary
            cprint("\n🧠 AI CONSENSUS SUMMARY:", "magenta", attrs=['bold'])
            cprint(f"{analysis_results['consensus_summary']}\n", "white")

            # Show model mapping
            if analysis_results.get("model_mapping"):
                cprint("🔢 Model Key:", "blue")
                for ai_num, provider in analysis_results["model_mapping"].items():
                    cprint(f"   {ai_num} = {provider}", "white")

            # Show individual responses (truncated)
            cprint("\n📋 Individual AI Responses:", "cyan")
            for provider, data in analysis_results["responses"].items():
                if data["success"]:
                    cprint(f"\n🤖 {provider.upper()}:", "yellow", attrs=['bold'])
                    response_text = data["response"]
                    # Truncate if too long
                    if len(response_text) > 500:
                        cprint(f"{response_text[:500]}...", "white")
                    else:
                        cprint(response_text, "white")
        else:
            # XAI mode
            cprint("\n🤖 XAI RESPONSE:", "magenta", attrs=['bold'])
            cprint(f"{analysis_results['response']}", "white")

        cprint("\n" + "="*60, "green")

    def process_url(self, url: str) -> Dict:
        """
        Process a single URL (scrape + analyze + save)

        Args:
            url: The URL to process

        Returns:
            Dict containing all results for this URL
        """
        # Scrape the website
        scraped_data = self.scrape_website(url)

        if not scraped_data["success"]:
            return {
                "url": url,
                "success": False,
                "error": scraped_data["error"],
                "scraped_data": scraped_data,
                "analysis": None
            }

        # Analyze the content
        analysis_results = self.analyze_content(scraped_data)

        # Save results
        self.save_results(url, scraped_data, analysis_results)

        return {
            "url": url,
            "success": True,
            "error": None,
            "scraped_data": scraped_data,
            "analysis": analysis_results
        }

    def process_batch(self, urls: list) -> list:
        """
        Process multiple URLs in parallel

        Args:
            urls: List of URLs to process

        Returns:
            List of results for each URL
        """
        cprint(f"\n🚀 Processing {len(urls)} URLs in parallel...", "yellow", attrs=['bold'])

        results = [None] * len(urls)
        threads = []

        def process_and_store(index, url):
            """Wrapper to store results by index"""
            results[index] = self.process_url(url)

        # Start all threads
        for i, url in enumerate(urls):
            thread = threading.Thread(target=process_and_store, args=(i, url))
            thread.start()
            threads.append(thread)

        # Wait for all to complete
        for thread in threads:
            thread.join()

        return results

    def run(self):
        """
        Run the scrape agent in batch mode

        Accepts multiple space-separated URLs, processes all in parallel,
        then outputs all results together
        """
        cprint("\n" + "="*60, "cyan")
        cprint("🌐 SCRAPE AGENT - BATCH MODE", "cyan", attrs=['bold'])
        cprint("="*60, "cyan")
        cprint("\n💡 Enter multiple URLs separated by spaces", "yellow")
        cprint("💡 Example: https://site1.com https://site2.com https://site3.com", "yellow")
        cprint("💡 All URLs process in parallel, results shown when complete", "yellow")
        cprint("💡 Type 'quit' or 'exit' to stop\n", "yellow")

        while True:
            try:
                # Get URLs from user
                user_input = input(colored("🌙 Enter URLs > ", "cyan", attrs=['bold'])).strip()

                if not user_input:
                    continue

                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    cprint("\n👋 Goodbye Moon Dev! 🌙", "green", attrs=['bold'])
                    break

                # Split by spaces to get multiple URLs
                raw_urls = user_input.split()

                # Validate and clean URLs
                urls = []
                for url in raw_urls:
                    url = url.strip()
                    if not url:
                        continue
                    # Add https:// if missing
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    urls.append(url)

                if not urls:
                    cprint("❌ No valid URLs provided", "red")
                    continue

                cprint(f"\n📋 URLs to process: {len(urls)}", "cyan")
                for i, url in enumerate(urls, 1):
                    cprint(f"   {i}. {url}", "white")

                # Process all URLs in parallel
                start_time = time.time()
                results = self.process_batch(urls)
                elapsed = time.time() - start_time

                # Print all results
                cprint("\n" + "="*60, "green")
                cprint("🎯 BATCH RESULTS", "green", attrs=['bold'])
                cprint("="*60, "green")

                for i, result in enumerate(results, 1):
                    cprint(f"\n{'─'*60}", "cyan")
                    cprint(f"📄 RESULT {i}/{len(results)}: {result['url']}", "cyan", attrs=['bold'])
                    cprint(f"{'─'*60}", "cyan")

                    if not result["success"]:
                        cprint(f"❌ Failed: {result['error']}", "red")
                        continue

                    # Print analysis
                    analysis = result["analysis"]
                    if analysis and analysis["success"]:
                        if analysis["ai_mode"] == "SWARM":
                            # Show consensus summary
                            cprint("\n🧠 AI CONSENSUS:", "magenta", attrs=['bold'])
                            cprint(f"{analysis['consensus_summary']}\n", "white")

                            # Show model mapping
                            if analysis.get("model_mapping"):
                                cprint("🔢 Model Key:", "blue")
                                for ai_num, provider in analysis["model_mapping"].items():
                                    cprint(f"   {ai_num} = {provider}", "white")

                            # Show individual responses (truncated)
                            cprint("\n📋 Individual Responses:", "cyan")
                            for provider, data in analysis["responses"].items():
                                if data["success"]:
                                    cprint(f"\n🤖 {provider.upper()}:", "yellow")
                                    response_text = data["response"]
                                    # Truncate if too long
                                    if len(response_text) > 300:
                                        cprint(f"{response_text[:300]}...", "white")
                                    else:
                                        cprint(response_text, "white")
                        else:
                            # XAI mode
                            cprint("\n🤖 XAI RESPONSE:", "magenta", attrs=['bold'])
                            response_text = analysis["response"]
                            if len(response_text) > 500:
                                cprint(f"{response_text[:500]}...", "white")
                            else:
                                cprint(response_text, "white")
                    else:
                        cprint(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}", "red")

                # Summary
                cprint(f"\n{'='*60}", "green")
                successful = sum(1 for r in results if r["success"])
                cprint(f"✅ Completed: {successful}/{len(results)} URLs", "green", attrs=['bold'])
                cprint(f"⏱️  Total Time: {elapsed:.2f}s", "cyan")
                cprint(f"💾 Results saved to: src/data/scrape_agent/", "blue")
                cprint(f"{'='*60}\n", "green")

            except KeyboardInterrupt:
                cprint("\n\n⚠️ Interrupted by user", "yellow")
                cprint("👋 Goodbye Moon Dev! 🌙", "cyan", attrs=['bold'])
                break
            except Exception as e:
                cprint(f"\n❌ Error: {str(e)}", "red")


def main():
    """Main entry point"""
    # Create and run the scrape agent
    agent = ScrapeAgent(use_swarm=USE_SWARM, prompt=DEFAULT_PROMPT)
    agent.run()


if __name__ == "__main__":
    main()
