"""
🌙 Moon Dev's Sora 2 Video Generation Agent

Parallel video generation using OpenAI's Sora 2 API.
Creates multiple videos simultaneously with background processing.

Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock
from queue import Queue
from dataclasses import dataclass
from typing import Dict, List, Optional
from termcolor import cprint
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

# =============================================================================
# 🔧 CONFIGURATION 
# =============================================================================

OUTPUT_DIR = "src/data/video_agent/"
OPENAI_API_KEY = os.getenv("OPENAI_KEY")  # Moon Dev's repo uses OPENAI_KEY

# Sora 2 Configuration
MODEL = "sora-2"  # Options: "sora-2", "sora-2-pro"
DEFAULT_RESOLUTION = "720p"  # Options: "1080p", "720p"
DEFAULT_DURATION = 8  # Seconds: 4, 8, or 12
MAX_WORKERS = 9  # Number of parallel video generation threads

# Aspect Ratio Configuration
# 16:9  = Widescreen (YouTube, landscape)
# 9:16  = Vertical (TikTok, Instagram Reels, YouTube Shorts)
# 1:1   = Square (Instagram feed)
# 4:3   = Classic TV
# 21:9  = Cinematic widescreen
DEFAULT_ASPECT_RATIO = "9:16"  # Change this for different video formats!

# =============================================================================
# 📊 VIDEO JOB TRACKING
# =============================================================================

@dataclass
class VideoJob:
    """Tracks a video generation job"""
    job_id: str
    prompt: str
    status: str  # "queued", "generating", "completed", "failed"
    created_at: datetime
    completed_at: Optional[datetime] = None
    video_path: Optional[str] = None
    error: Optional[str] = None

# Global job tracker
jobs: Dict[str, VideoJob] = {}
jobs_lock = Lock()
job_queue = Queue()

# =============================================================================
# 🎥 SORA 2 VIDEO GENERATION
# =============================================================================

def create_video_job(prompt: str, resolution: str = DEFAULT_RESOLUTION, duration: int = DEFAULT_DURATION, aspect_ratio: str = DEFAULT_ASPECT_RATIO) -> Optional[VideoJob]:
    """
    Create a Sora 2 video generation job using OpenAI SDK

    Args:
        prompt: Text description of video to generate
        resolution: Video resolution ("1080p" or "720p")
        duration: Video duration in seconds (4, 8, or 12)
        aspect_ratio: Video aspect ratio ("16:9", "9:16", "1:1", etc.)

    Returns:
        VideoJob object or None if failed
    """
    if not OPENAI_API_KEY:
        cprint("❌ OPENAI_KEY not found in .env", "red")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        cprint(f"\n🎬 Creating video job...", "cyan")
        cprint(f"   Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}", "white")
        cprint(f"   Resolution: {resolution}", "white")
        cprint(f"   Duration: {duration}s", "white")
        cprint(f"   Aspect Ratio: {aspect_ratio}", "white")

        # Convert resolution and aspect ratio to size format (e.g., "1280x720")
        # Sora expects size in WIDTHxHEIGHT format
        if aspect_ratio == "16:9":
            if resolution == "1080p":
                size = "1920x1080"
            else:  # 720p
                size = "1280x720"
        elif aspect_ratio == "9:16":
            if resolution == "1080p":
                size = "1080x1920"
            else:  # 720p
                size = "720x1280"
        elif aspect_ratio == "1:1":
            if resolution == "1080p":
                size = "1080x1080"
            else:  # 720p
                size = "720x720"
        else:
            # Default to 16:9
            size = "1280x720"

        # Create video using SDK (matches GitHub example)
        video = client.videos.create(
            model=MODEL,
            prompt=prompt,
            seconds=str(duration),  # Must be string
            size=size
        )

        # Create job object
        job = VideoJob(
            job_id=video.id,
            prompt=prompt,
            status="queued",
            created_at=datetime.now()
        )

        # Store job
        with jobs_lock:
            jobs[video.id] = job

        cprint(f"✅ Job created: {video.id[:16]}...", "green")
        return job

    except Exception as e:
        cprint(f"❌ Error creating video job: {e}", "red")
        import traceback
        traceback.print_exc()
        return None

def poll_video_job(job: VideoJob) -> bool:
    """
    Poll a video job for completion using OpenAI SDK

    Returns:
        True if completed, False if still processing
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Retrieve video status
        video = client.videos.retrieve(job.job_id)

        status = video.status

        if status == "completed":
            job.status = "completed"
            job.completed_at = datetime.now()

            # Download video using SDK method
            try:
                content = client.videos.download_content(job.job_id, variant="video")
                video_bytes = content.read()

                # Save to disk
                video_path = save_video_bytes(video_bytes, job)
                job.video_path = video_path
            except Exception as e:
                cprint(f"⚠️  Error downloading video: {e}", "yellow")
                job.status = "failed"
                job.error = f"Download failed: {str(e)}"

            return True

        elif status == "failed":
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = getattr(video, 'error', 'Video generation failed')
            return True

        else:
            # Still processing (queued, in_progress)
            job.status = "generating"
            return False

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.now()
        return True

def save_video_bytes(video_bytes: bytes, job: VideoJob) -> str:
    """
    Save video bytes to disk

    Returns:
        Path to saved video file
    """
    try:
        # Create date-based folder
        today = datetime.now().strftime("%Y-%m-%d")
        output_folder = Path(OUTPUT_DIR) / today
        output_folder.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%H%M%S")
        safe_prompt = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in job.prompt[:30])
        safe_prompt = safe_prompt.replace(' ', '_')
        filename = f"{timestamp}_{safe_prompt}.mp4"
        video_path = output_folder / filename

        # Save video
        cprint(f"\n📥 Saving video: {job.job_id[:16]}...", "cyan")
        with open(video_path, 'wb') as f:
            f.write(video_bytes)

        cprint(f"✅ Video saved: {video_path}", "green")
        return str(video_path)

    except Exception as e:
        cprint(f"❌ Error saving video: {e}", "red")
        return ""

# =============================================================================
# 🔄 BACKGROUND WORKER
# =============================================================================

def video_worker(worker_id: int):
    """
    Background worker that processes video generation jobs

    Args:
        worker_id: Worker thread identifier
    """
    cprint(f"🤖 Worker {worker_id} started", "green")

    while True:
        try:
            # Get job from queue (blocks until available)
            job = job_queue.get()

            if job is None:  # Poison pill to stop worker
                break

            cprint(f"\n🎬 Worker {worker_id} processing: {job.job_id[:16]}...", "yellow")
            cprint(f"   Prompt: {job.prompt[:80]}{'...' if len(job.prompt) > 80 else ''}", "white")

            # Poll for completion
            poll_interval = 10  # seconds
            max_attempts = 120  # 20 minutes max (120 * 10s)
            attempts = 0

            while attempts < max_attempts:
                completed = poll_video_job(job)

                if completed:
                    if job.status == "completed":
                        cprint(f"✅ Worker {worker_id} completed: {job.job_id[:16]}...", "green")
                        cprint(f"   Video: {job.video_path}", "cyan")
                    else:
                        cprint(f"❌ Worker {worker_id} failed: {job.job_id[:16]}...", "red")
                        cprint(f"   Error: {job.error}", "yellow")
                    break

                time.sleep(poll_interval)
                attempts += 1

            if attempts >= max_attempts:
                job.status = "failed"
                job.error = "Timeout - took too long to generate"
                job.completed_at = datetime.now()
                cprint(f"⏱️  Worker {worker_id} timeout: {job.job_id[:16]}...", "red")

            # Mark job as done
            job_queue.task_done()

        except Exception as e:
            cprint(f"❌ Worker {worker_id} error: {e}", "red")
            job_queue.task_done()

# =============================================================================
# 📊 STATUS DISPLAY
# =============================================================================

def display_status():
    """Display status of all video jobs"""
    with jobs_lock:
        if not jobs:
            cprint("\n📊 No video jobs yet", "yellow")
            return

        cprint("\n" + "="*80, "cyan")
        cprint("📊 VIDEO GENERATION STATUS", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        # Count by status
        queued = sum(1 for j in jobs.values() if j.status == "queued")
        generating = sum(1 for j in jobs.values() if j.status == "generating")
        completed = sum(1 for j in jobs.values() if j.status == "completed")
        failed = sum(1 for j in jobs.values() if j.status == "failed")

        cprint(f"\n📈 Summary:", "white", attrs=['bold'])
        cprint(f"   ⏳ Queued: {queued}", "yellow")
        cprint(f"   🎬 Generating: {generating}", "cyan")
        cprint(f"   ✅ Completed: {completed}", "green")
        cprint(f"   ❌ Failed: {failed}", "red")

        cprint(f"\n📋 All Jobs:", "white", attrs=['bold'])

        for job in sorted(jobs.values(), key=lambda j: j.created_at, reverse=True):
            # Status emoji
            if job.status == "queued":
                status_emoji = "⏳"
                status_color = "yellow"
            elif job.status == "generating":
                status_emoji = "🎬"
                status_color = "cyan"
            elif job.status == "completed":
                status_emoji = "✅"
                status_color = "green"
            else:
                status_emoji = "❌"
                status_color = "red"

            # Time info
            created = job.created_at.strftime("%H:%M:%S")
            if job.completed_at:
                duration = (job.completed_at - job.created_at).total_seconds()
                time_info = f"({duration:.0f}s)"
            else:
                elapsed = (datetime.now() - job.created_at).total_seconds()
                time_info = f"({elapsed:.0f}s elapsed)"

            # Display job
            cprint(f"\n{status_emoji} {job.job_id[:16]}... [{job.status.upper()}] {time_info}", status_color, attrs=['bold'])
            cprint(f"   Created: {created}", "white")
            cprint(f"   Prompt: {job.prompt[:80]}{'...' if len(job.prompt) > 80 else ''}", "white")

            if job.video_path:
                cprint(f"   Video: {job.video_path}", "cyan")

            if job.error:
                cprint(f"   Error: {job.error}", "red")

        cprint("\n" + "="*80, "cyan")

# =============================================================================
# 🚀 MAIN INTERACTIVE LOOP
# =============================================================================

def main():
    """Main interactive loop for video generation"""
    cprint("""
╔══════════════════════════════════════════════════════════╗
║  🌙 Moon Dev's Sora 2 Video Generation Agent           ║
║  Parallel video generation with OpenAI Sora 2          ║
╚══════════════════════════════════════════════════════════╝
""", "cyan", attrs=['bold'])

    # Check API key
    if not OPENAI_API_KEY:
        cprint("❌ OPENAI_KEY not found in .env", "red")
        cprint("   Please add OPENAI_KEY=your_key_here to .env file", "yellow")
        return

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Show current configuration
    cprint("⚙️  Video Settings:", "cyan", attrs=['bold'])
    cprint(f"   Model: {MODEL} | Resolution: {DEFAULT_RESOLUTION} | Duration: {DEFAULT_DURATION}s", "white")
    cprint(f"   Aspect Ratio: {DEFAULT_ASPECT_RATIO}", "yellow", attrs=['bold'])
    if DEFAULT_ASPECT_RATIO == "16:9":
        cprint(f"   Format: Widescreen (YouTube, landscape)", "white")
    elif DEFAULT_ASPECT_RATIO == "9:16":
        cprint(f"   Format: Vertical (TikTok, Reels, Shorts)", "white")
    elif DEFAULT_ASPECT_RATIO == "1:1":
        cprint(f"   Format: Square (Instagram feed)", "white")

    # Workers (lazy init - start on first video)
    workers = []
    workers_started = False

    def start_workers():
        """Start worker threads on first video submission"""
        nonlocal workers_started
        if not workers_started:
            cprint("\n🚀 Starting video workers...", "cyan")
            for i in range(MAX_WORKERS):
                worker = Thread(target=video_worker, args=(i+1,), daemon=True)
                worker.start()
                workers.append(worker)
            workers_started = True
            cprint(f"✅ {MAX_WORKERS} workers ready!", "green")

    # Help text
    cprint("\n💡 Pro Tips:", "yellow", attrs=['bold'])
    cprint("   - Type '/status' to see all jobs", "white")
    cprint("   - Type '/quit' to exit", "white")
    cprint("   - Videos process in parallel - queue multiple ideas!\n", "white")

    try:
        first_video = True
        while True:
            # Add spacing and clear prompt for video idea
            print()  # Extra newline for spacing
            cprint("─"*60, "cyan")
            if first_video:
                cprint("TYPE YOUR VIDEO IDEA BELOW:", "white", "on_green", attrs=['bold'])
            else:
                cprint("TYPE YOUR NEXT VIDEO IDEA:", "white", "on_blue", attrs=['bold'])

            user_input = input("➤ ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "/status":
                display_status()
                continue

            if user_input.lower() in ["/quit", "/exit", "/q"]:
                cprint("\n👋 Shutting down...", "yellow")
                break

            # Start workers on first video
            if first_video:
                start_workers()
                first_video = False

            # Create video job
            cprint(f"\n🎬 Creating video: '{user_input[:60]}{'...' if len(user_input) > 60 else ''}'", "cyan")
            job = create_video_job(user_input)

            if job:
                # Add to queue
                job_queue.put(job)
                cprint(f"✅ Started video creation!", "green", attrs=['bold'])
                cprint(f"   Job ID: {job.job_id[:16]}...", "white")

                # Quick status
                with jobs_lock:
                    queued = sum(1 for j in jobs.values() if j.status == "queued")
                    generating = sum(1 for j in jobs.values() if j.status == "generating")
                    completed = sum(1 for j in jobs.values() if j.status == "completed")

                cprint(f"   Status: {queued} queued | {generating} generating | {completed} completed", "cyan")
                cprint(f"\n💡 Your video is processing in the background!", "yellow")

                # Small delay to let worker messages print before showing next prompt
                time.sleep(0.5)

    except KeyboardInterrupt:
        cprint("\n\n⚠️  Keyboard interrupt detected", "yellow")

    finally:
        # Cleanup
        if workers_started:
            cprint("\n🛑 Stopping workers...", "yellow")

            # Send poison pills to stop workers
            for _ in range(MAX_WORKERS):
                job_queue.put(None)

            # Wait for workers to finish
            for worker in workers:
                worker.join(timeout=5)

        # Final status
        display_status()

        cprint("\n✅ Video Agent shutdown complete", "green")
        cprint("🌙 Moon Dev says: Check your videos in src/data/video_agent/", "cyan")

if __name__ == "__main__":
    main()
