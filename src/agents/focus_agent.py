"""
🌙 Moon Dev's Focus Agent
Built with love by Moon Dev 🚀

This agent randomly monitors speech samples and provides focus assessments.
"""

# System prompt for focus analysis
FOCUS_PROMPT = """
You are Moon Dev's Focus AI Agent. Analyze the following transcript and:
1. Rate focus level from 1-10 (10 being completely focused on coding)
2. Provide ONE encouraging sentence to maintain/improve focus or a great quote to inspire to focus or keep pushing through hard times

Consider:
- Coding discussion = high focus
- Trading analysis = high focus
- Random chat/topics = low focus
- Non-work discussion = low focus

BE VERY STRICT WITH YOUR RATING, LIKE A DRILL SERGEANT. DONT GO EASY ON ME. I HAVE TO BE VERY FOCUSED, AND YOUR JOB IS TO MAKE ME VERY FOCUSED.

RESPOND IN THIS EXACT FORMAT:
X/10
"Quote OR motivational sentence"
"""

import os
import time as time_lib
from datetime import datetime, timedelta, time
import speech_recognition as sr  # Use SpeechRecognition for offline speech-to-text
import pyttsx3  # Import pyttsx3 for TTS
from termcolor import cprint
from pathlib import Path
from dotenv import load_dotenv
from random import uniform
import pandas as pd

# Configuration
MIN_INTERVAL_MINUTES = 4
MAX_INTERVAL_MINUTES = 11
RECORDING_DURATION = 30  # seconds
FOCUS_THRESHOLD = 8  # Minimum acceptable focus score

# Schedule settings
SCHEDULE_START = time(5, 0)  # 5:00 AM
SCHEDULE_END = time(13, 0)  # 1:00 PM

# Create directories
AUDIO_DIR = Path("src/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class FocusAgent:
    def __init__(self):
        """Initialize the Focus Agent"""
        load_dotenv()

        # Initialize SpeechRecognition recognizer
        self.recognizer = sr.Recognizer()

        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Set speech rate
        self.tts_engine.setProperty('voice', self.tts_engine.getProperty('voices')[0].id)  # Set voice

        cprint("🎯 Moon Dev's Focus Agent initialized!", "green")

        self.is_recording = False
        self.current_transcript = []

        # Add data directory path
        self.data_dir = Path("src/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.focus_log_path = self.data_dir / "focus_history.csv"

        # Initialize focus history DataFrame if file doesn't exist
        if not self.focus_log_path.exists():
            self._create_focus_log()

        cprint("📊 Focus history will be logged to: " + str(self.focus_log_path), "green")

        self._check_schedule()

    def _check_schedule(self):
        """Check if current time is within scheduled hours"""
        current_time = datetime.now().time()
        if not (SCHEDULE_START <= current_time <= SCHEDULE_END):
            cprint(f"\n🌙 Moon Dev's Focus Agent is scheduled to run between {SCHEDULE_START.strftime('%I:%M %p')} and {SCHEDULE_END.strftime('%I:%M %p')}", "yellow")
            cprint("😴 Going to sleep until next scheduled time...", "yellow")
            raise SystemExit(0)

    def _get_random_interval(self):
        """Get random interval between MIN and MAX minutes"""
        return uniform(MIN_INTERVAL_MINUTES * 60, MAX_INTERVAL_MINUTES * 60)

    def record_audio(self):
        """Record audio for specified duration using SpeechRecognition"""
        try:
            self.is_recording = True
            self.current_transcript = []

            with sr.Microphone() as source:
                cprint("\n🎤 Recording sample... (Speak now)", "cyan")
                audio = self.recognizer.listen(source, timeout=RECORDING_DURATION)

                # Recognize speech using pocketsphinx (offline)
                try:
                    transcript = self.recognizer.recognize_sphinx(audio)
                    self.current_transcript.append(transcript)
                    cprint(f"🗣️ Transcript: {transcript}", "green")
                except sr.UnknownValueError:
                    cprint("⚠️ Speech recognition could not understand audio", "yellow")
                except sr.RequestError as e:
                    cprint(f"❌ Error with speech recognition: {str(e)}", "red")

        except Exception as e:
            cprint(f"❌ Error recording audio: {str(e)}", "red")
        finally:
            self.is_recording = False

    def _announce(self, message, force_voice=False):
        """Announce message with optional voice"""
        try:
            cprint(f"\n🗣️ {message}", "cyan")

            if force_voice:
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()  # Wait for the speech to finish

        except Exception as e:
            cprint(f"❌ Error in announcement: {str(e)}", "red")

    def analyze_focus(self, transcript):
        """Analyze focus level from transcript"""
        try:
            response = self.openai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": FOCUS_PROMPT},
                    {"role": "user", "content": transcript},
                ],
                max_tokens=150,
            )

            analysis = response.choices[0].message.content.strip()

            # Split into score and message
            score_line, message = analysis.split("\n", 1)
            score = float(score_line.split("/")[0])

            return score, message.strip()

        except Exception as e:
            cprint(f"❌ Error analyzing focus: {str(e)}", "red")
            return 0, "Error analyzing focus"

    def _create_focus_log(self):
        """Create empty focus history CSV"""
        df = pd.DataFrame(columns=["timestamp", "focus_score", "quote"])
        df.to_csv(self.focus_log_path, index=False)
        cprint("🌟 Moon Dev's Focus History log created!", "green")

    def _log_focus_data(self, score, quote):
        """Log focus data to CSV"""
        try:
            # Create new row
            new_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "focus_score": score,
                "quote": quote.strip('"'),  # Remove quotation marks
            }

            # Read existing CSV
            df = pd.read_csv(self.focus_log_path)

            # Append new data
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

            # Save back to CSV
            df.to_csv(self.focus_log_path, index=False)

            cprint("📝 Focus data logged successfully!", "green")

        except Exception as e:
            cprint(f"❌ Error logging focus data: {str(e)}", "red")

    def process_transcript(self, transcript):
        """Process transcript and provide focus assessment"""
        score, message = self.analyze_focus(transcript)

        # Log the data
        self._log_focus_data(score, message)

        # Determine if voice announcement needed
        needs_voice = score < FOCUS_THRESHOLD

        # Format message
        formatted_message = f"{score}/10\n{message}"

        # Announce
        self._announce(formatted_message, force_voice=needs_voice)

        return score

    def run(self):
        """Main loop for random focus monitoring"""
        cprint("\n🎯 Moon Dev's Focus Agent starting with random monitoring...", "cyan")
        cprint(
            f"⏰ Operating hours: {SCHEDULE_START.strftime('%I:%M %p')} - {SCHEDULE_END.strftime('%I:%M %p')}",
            "cyan",
        )

        while True:
            try:
                # Check schedule before each monitoring cycle
                self._check_schedule()

                # Get random interval
                interval = self._get_random_interval()
                next_check = datetime.now() + timedelta(seconds=interval)

                # Print next check time
                cprint(
                    f"\n⏰ Next focus check will be around {next_check.strftime('%I:%M %p')}",
                    "cyan",
                )

                # Use time_lib instead of time
                time_lib.sleep(interval)

                # Start recording
                self.record_audio()

                # Process recording if we got something
                if self.current_transcript:
                    full_transcript = " ".join(self.current_transcript)
                    if full_transcript.strip():
                        self.process_transcript(full_transcript)
                    else:
                        cprint("⚠️ No speech detected in sample", "yellow")
                else:
                    cprint("⚠️ No transcript generated", "yellow")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                cprint(f"❌ Error in main loop: {str(e)}", "red")
                time_lib.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    try:
        agent = FocusAgent()
        agent.run()
    except KeyboardInterrupt:
        cprint("\n👋 Focus Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")