"""
🌙 Moon Dev - PDF & YouTube Extraction Test Script
Tests PDF and YouTube transcript extraction before integrating into RBI agent
"""

import requests
from io import BytesIO
from termcolor import cprint, colored
import time

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video using youtube-transcript-api - Moon Dev"""
    try:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            cprint("⚠️ youtube-transcript-api not installed. Run: pip install youtube-transcript-api", "yellow")
            return None

        cprint(f"\n🎥 Fetching transcript for video ID: {video_id}", "cyan")

        # 🌙 Moon Dev: Using youtube-transcript-api v1.2.3+ API
        cprint("   ├─ Fetching transcript...", "cyan")
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, languages=['en'])

        cprint("   ├─ Joining transcript text...", "cyan")
        transcript_text = ' '.join([snippet.text for snippet in transcript_data])

        if not transcript_text:
            cprint("   ❌ No text could be extracted from transcript", "red")
            return None

        # Print the FULL transcript
        cprint("\n📝 YouTube Transcript (FULL):", "green", attrs=['bold'])
        cprint("=" * 80, "yellow")
        print(transcript_text)  # Print FULL transcript
        cprint("=" * 80, "yellow")
        cprint(f"📊 Transcript length: {len(transcript_text)} characters", "cyan")

        return transcript_text

    except Exception as e:
        cprint(f"\n❌ Error fetching YouTube transcript: {e}", "red", attrs=['bold'])
        cprint(f"   Video ID: {video_id}", "red")
        import traceback
        cprint(f"   Traceback: {traceback.format_exc()}", "red")
        return None

def get_pdf_text(url):
    """Extract text from PDF URL - Moon Dev"""
    try:
        try:
            import PyPDF2
        except ImportError:
            cprint("⚠️ PyPDF2 not installed. Run: pip install PyPDF2", "yellow")
            return None

        cprint(f"\n📚 Fetching PDF from: {url}", "cyan")

        # Add headers to simulate browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()

        cprint("📖 Extracting text from PDF...", "cyan")
        reader = PyPDF2.PdfReader(BytesIO(response.content))
        text = ''
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            text += page_text + '\n'
            if i == 0:
                cprint(f"   ├─ Pages found: {len(reader.pages)}", "cyan")

        # Print the FULL PDF text
        cprint("\n📄 PDF Text (FULL):", "green", attrs=['bold'])
        cprint("=" * 80, "yellow")
        print(text)  # Print FULL text
        cprint("=" * 80, "yellow")
        cprint(f"📊 Total text length: {len(text)} characters", "cyan")

        return text
    except Exception as e:
        cprint(f"\n❌ Error reading PDF: {e}", "red", attrs=['bold'])
        cprint(f"   URL: {url}", "red")
        return None

def extract_youtube_id(url):
    """Extract video ID from YouTube URL - Moon Dev"""
    try:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]
        return video_id
    except Exception as e:
        cprint(f"❌ Error extracting video ID from: {url}", "red")
        cprint(f"   Error: {e}", "red")
        return None

def test_url(url):
    """Test extraction for a single URL - Moon Dev"""
    cprint(f"\n{'='*80}", "magenta")
    cprint(f"🧪 Testing: {url}", "magenta", attrs=['bold'])
    cprint(f"{'='*80}", "magenta")

    try:
        if "youtube.com" in url or "youtu.be" in url:
            video_id = extract_youtube_id(url)
            if video_id:
                result = get_youtube_transcript(video_id)
                if result:
                    cprint(f"\n✅ SUCCESS: YouTube transcript extracted!", "green", attrs=['bold'])
                    cprint(f"\n⏸️  Sleeping for 15 seconds before next test...\n", "yellow")
                    time.sleep(15)
                    return True
                else:
                    # Red background warning
                    cprint("\n" + "="*80, "white", "on_red", attrs=['bold'])
                    cprint("⚠️  EXTRACTION FAILED - See error above", "white", "on_red", attrs=['bold'])
                    cprint("="*80 + "\n", "white", "on_red", attrs=['bold'])
                    return False
        elif url.endswith(".pdf") or "pdf" in url.lower():
            result = get_pdf_text(url)
            if result:
                cprint(f"\n✅ SUCCESS: PDF text extracted!", "green", attrs=['bold'])
                cprint(f"\n⏸️  Sleeping for 15 seconds before next test...\n", "yellow")
                time.sleep(15)
                return True
            else:
                # Red background warning
                cprint("\n" + "="*80, "white", "on_red", attrs=['bold'])
                cprint("⚠️  EXTRACTION FAILED - See error above", "white", "on_red", attrs=['bold'])
                cprint("="*80 + "\n", "white", "on_red", attrs=['bold'])
                return False
        else:
            cprint(f"⚠️ Unknown URL type: {url}", "yellow")
            return False

    except Exception as e:
        cprint(f"\n❌ Unexpected error: {e}", "red", attrs=['bold'])
        # Red background warning
        cprint("\n" + "="*80, "white", "on_red", attrs=['bold'])
        cprint("⚠️  EXTRACTION FAILED - See error above", "white", "on_red", attrs=['bold'])
        cprint("="*80 + "\n", "white", "on_red", attrs=['bold'])
        return False

def main():
    """Main test runner - Moon Dev"""
    cprint("\n" + "🌙"*40, "cyan")
    cprint("Moon Dev - PDF & YouTube Extraction Test", "cyan", attrs=['bold'])
    cprint("🌙"*40 + "\n", "cyan")

    # Test URLs provided by Moon Dev (YouTube first to get to the money fast!)
    test_urls = [
        "https://www.youtube.com/watch?v=e-QmGJU1XYc",
        "https://arxiv.org/pdf/1408.2217",
        "https://acecentre.hk/wp-content/uploads/2013/10/Mean-Reversion-across-National-Stock-Markets-and-Parametric-Contrarian-Investment-Strategies.pdf"
    ]

    results = []
    for url in test_urls:
        success = test_url(url)
        results.append((url, success))

        if not success:
            cprint(f"\n⏸️  Pausing for 30 seconds to review error...", "yellow", attrs=['bold'])
            time.sleep(30)

    # Summary
    cprint("\n" + "="*80, "cyan")
    cprint("📊 Test Summary", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")

    for url, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        color = "green" if success else "red"
        url_short = url[:70] + "..." if len(url) > 70 else url
        cprint(f"{status}: {url_short}", color)

    passed = sum(1 for _, success in results if success)
    total = len(results)
    cprint(f"\n📈 Results: {passed}/{total} tests passed", "cyan", attrs=['bold'])

    if passed == total:
        cprint("\n🎉 All tests passed! Ready to integrate into RBI agent.", "green", attrs=['bold'])
    else:
        cprint("\n⚠️ Some tests failed. Review errors above.", "yellow", attrs=['bold'])

if __name__ == "__main__":
    main()
