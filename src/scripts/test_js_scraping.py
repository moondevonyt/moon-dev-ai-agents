#!/usr/bin/env python3
"""
🌙 Moon Dev's JS Scraping Test Script

Tests different methods to scrape JavaScript-heavy sites (Next.js, React, etc.)

Methods tested:
1. BeautifulSoup (baseline - doesn't work for JS)
2. Playwright (modern headless browser - BEST)
3. Selenium (older alternative)

Built by Moon Dev 🚀
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import requests
from bs4 import BeautifulSoup
from termcolor import cprint
import time

# Test URL
TEST_URL = "https://algotradecamp2.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def test_beautifulsoup():
    """Test BeautifulSoup (baseline - won't work for JS sites)"""
    cprint("\n" + "="*80, "cyan")
    cprint("TEST 1: BeautifulSoup (No JavaScript Support)", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(TEST_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)

        cprint(f"\n✅ Scraped {len(clean_text)} characters", "green")
        cprint(f"\n📝 Content Preview (first 500 chars):", "yellow")
        cprint(clean_text[:500], "white")

        if "Loading" in clean_text and len(clean_text) < 200:
            cprint("\n❌ RESULT: Only got loading screen (JS not executed)", "red")
        else:
            cprint("\n✅ RESULT: Got actual content!", "green")

        return clean_text

    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return None


def test_playwright():
    """Test Playwright (modern headless browser - BEST)"""
    cprint("\n" + "="*80, "cyan")
    cprint("TEST 2: Playwright (Headless Browser with JS Support)", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    try:
        from playwright.sync_api import sync_playwright

        cprint("✅ Playwright is installed!", "green")

        with sync_playwright() as p:
            # Launch browser
            cprint("\n🚀 Launching headless browser...", "yellow")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)

            # Navigate to URL
            cprint(f"🌐 Navigating to {TEST_URL}...", "yellow")
            page.goto(TEST_URL, wait_until="networkidle", timeout=60000)

            # Wait a bit for any lazy-loaded content
            cprint("⏳ Waiting for content to load...", "yellow")
            time.sleep(3)

            # Get the rendered content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Extract text
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)

            # Get metadata
            title = page.title()

            browser.close()

            cprint(f"\n✅ Scraped {len(clean_text)} characters", "green")
            cprint(f"📄 Title: {title}", "cyan")
            cprint(f"\n📝 Content Preview (first 1000 chars):", "yellow")
            cprint(clean_text[:1000], "white")

            if len(clean_text) > 500:
                cprint("\n✅ RESULT: Got full rendered content!", "green", attrs=['bold'])
            else:
                cprint("\n⚠️ RESULT: Content seems short", "yellow")

            return clean_text

    except ImportError:
        cprint("❌ Playwright not installed!", "red")
        cprint("\n💡 Install with: pip install playwright", "yellow")
        cprint("💡 Then run: playwright install chromium", "yellow")
        return None
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return None


def test_selenium():
    """Test Selenium (older alternative to Playwright)"""
    cprint("\n" + "="*80, "cyan")
    cprint("TEST 3: Selenium (Alternative Headless Browser)", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        cprint("✅ Selenium is installed!", "green")

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")

        # Launch browser
        cprint("\n🚀 Launching headless Chrome...", "yellow")
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to URL
        cprint(f"🌐 Navigating to {TEST_URL}...", "yellow")
        driver.get(TEST_URL)

        # Wait for page to load
        cprint("⏳ Waiting for content to load...", "yellow")
        time.sleep(5)

        # Get the rendered content
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        # Extract text
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)

        # Get title
        title = driver.title

        driver.quit()

        cprint(f"\n✅ Scraped {len(clean_text)} characters", "green")
        cprint(f"📄 Title: {title}", "cyan")
        cprint(f"\n📝 Content Preview (first 1000 chars):", "yellow")
        cprint(clean_text[:1000], "white")

        if len(clean_text) > 500:
            cprint("\n✅ RESULT: Got full rendered content!", "green", attrs=['bold'])
        else:
            cprint("\n⚠️ RESULT: Content seems short", "yellow")

        return clean_text

    except ImportError:
        cprint("❌ Selenium not installed!", "red")
        cprint("\n💡 Install with: pip install selenium", "yellow")
        cprint("💡 Also need ChromeDriver: brew install chromedriver (macOS)", "yellow")
        return None
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return None


def main():
    """Run all tests"""
    cprint("\n" + "="*80, "magenta")
    cprint("🌙 Moon Dev's JS Scraping Test - Testing Different Methods", "magenta", attrs=['bold'])
    cprint("="*80, "magenta")
    cprint(f"\n🎯 Target URL: {TEST_URL}", "cyan")

    # Test 1: BeautifulSoup (baseline)
    bs_result = test_beautifulsoup()

    # Test 2: Playwright (recommended)
    pw_result = test_playwright()

    # Test 3: Selenium (alternative)
    sel_result = test_selenium()

    # Summary
    cprint("\n" + "="*80, "magenta")
    cprint("📊 SUMMARY", "magenta", attrs=['bold'])
    cprint("="*80, "magenta")

    cprint("\n🏆 Recommendation:", "yellow", attrs=['bold'])
    if pw_result and len(pw_result) > 500:
        cprint("✅ Use PLAYWRIGHT - Got best results!", "green", attrs=['bold'])
        cprint("\nTo install:", "cyan")
        cprint("  pip install playwright", "white")
        cprint("  playwright install chromium", "white")
    elif sel_result and len(sel_result) > 500:
        cprint("✅ Use SELENIUM - Playwright failed but this worked!", "green", attrs=['bold'])
        cprint("\nTo install:", "cyan")
        cprint("  pip install selenium", "white")
        cprint("  brew install chromedriver  # macOS", "white")
    else:
        cprint("❌ Neither method got good results", "red")
        cprint("💡 May need to investigate site-specific issues", "yellow")

    cprint("\n✨ Test complete! 🌙\n", "cyan")


if __name__ == "__main__":
    main()
