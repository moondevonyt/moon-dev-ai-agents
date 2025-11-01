"""
🌙 Moon Dev's Phone Agent
Built with love by Moon Dev 🚀

This agent handles real phone calls through Twilio.
Just run on your VPS and people can call your Twilio number!
"""

import sys
from pathlib import Path
import os
import time
import json
import wave
import tempfile
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import openai
from termcolor import cprint
from dotenv import load_dotenv
import asyncio
import sounddevice as sd
import numpy as np
import wave
import queue
import threading
import langdetect
import subprocess
import pandas as pd
from datetime import datetime
import random

# Testing mode flag - set to True to test in terminal without Twilio
TESTING_MODE = True

# Add project root to Python path for imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
if not TESTING_MODE:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize OpenAI client with correct env var name
    openai.api_key = os.getenv("OPENAI_KEY")
    if not openai.api_key:
        raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
else:
    # In testing mode, we can set a default model or use environment variables if available
    openai.api_key = os.getenv("OPENAI_KEY", "your-api-key-here")

# Initialize Flask app (only if not testing)
if not TESTING_MODE:
    app = Flask(__name__)
else:
    app = None

# Model settings
MODEL_NAME = "gpt-4o-mini"  # Using latest GPT-4 Turbo
VOICE_NAME = "echo"  # Options: alloy, echo, fable, onyx, nova, shimmer

# Response settings
MAX_TOKENS = 50  # Keep responses short and concise
TEMPERATURE = 0.7

# Audio timing settings
SPEECH_END_PAUSE = 1.0  # Seconds of silence to consider speech ended
BREATH_PAUSE = 0.5  # Allow short breath pauses without cutting off
MIN_PHRASE_LENGTH = 0.3  # Minimum length of a valid phrase
MAX_PHRASE_GAP = 2.0  # Maximum gap between phrases to combine them

# Audio level settings
VOLUME_THRESHOLD = 0.01  # Lowered from 0.05 to be more sensitive
SILENCE_THRESHOLD = VOLUME_THRESHOLD * 1.2  # Lowered multiplier
PEAK_THRESHOLD = VOLUME_THRESHOLD * 3.0  # Lowered multiplier
MIN_VOLUME_TIME = 0.05  # Lowered from 0.1
BACKGROUND_NOISE_FLOOR = 0.005  # Lowered from 0.02

# Audio recording settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
SILENCE_DURATION = 1.5  # Increased duration to ensure real speech
MIN_AUDIO_LENGTH = 0.5  # Minimum audio length in seconds to process

# Load knowledge base
KNOWLEDGE_BASE = """

Key points about Moon Dev:
- Passionate about AI, trading, and coding
- Streams coding sessions on YouTube
- Built github repo with 15+ AI trading agents 
- Runs a coding bootcamp called algo trade camp
- Focuses on Python and algo trading

Knowledge Base:
Frequently Asked Questions
* when do you live stream? daily at 8am est
* what is the website to join? https://algotradecamp.com
* how you get point for bootcamp? what are points used for? the person with the most points at the end of each's days stream gets the algo trade camp for free for 1 month
* what do points do? the person who gets the most points on the live stream gets the algo trade camp for free for a month
* what is 777 peace and love. i believe you can have anything in this world if you lead with love, so while i share absolutely every line of code on youtube, i get a lot of negative energy thrown at me. its the only downside of sharing. sending a 777 is an easy way to send some good vibes to not only me, but everyone reading the comments. lead with love and kindness and you can have anything in this world. imo.
* what is the best coding language to learn for algo trading?python because its the most widely used language, it isn't too hard to learn and there are so many amazing tutorials and python packages to help you with your journey. once you learn python, learning a second language, if needed is not going to be that hard. i use 100% python in my systems.
* how much is the course? how much is the bootcamp? how much is algo trade camp? we have a $69 per month subscription plan or you can get the lifetime for $420
* will i get nq or futures data from the bootcamp? no, i show all crypto algo trading but trading is trading and you can adapt to any market.
* where to learning coding for algo trading?i teach how to code in my algo trade camp here but you can also learn python on youtube
* do you prefer trading crypto vs forex or stocks? why?i personally like crypto as i am a fan of decentralization but imo, markets are markets and algo trading can be done with futures, stocks, crypto, prediction markets & any other market that gives you api access
* what is 777? peace and love. i believe you can have anything in this world if you lead with love, so while i share absolutely every line of code on youtube, i get a lot of negative energy thrown at me. its the only downside of sharing. sending a 777 is an easy way to send some good vibes to not only me, but everyone reading the comments. lead with love and kindness and you can have anything in this world. imo.
* do you run your bots on your computer? how do you run them 24/7?when getting started i used to run them on my computer but now for scaling, i use a vps provided by cherry servers. there are a ton of vps providers out there, pick your favorite. that said, i am a big believer in staying away from live trading until you have a bunch of proven backtests. i cover this in the rbi system here
* whats the bootcamps refund policy?We want to make sure that every customer is extremely happy with their decision to join the bootcamp so we offer a 90 day, no questions asked refund policy. Simply email us and we will refund your money immediately through stripe, our payment processor. We want to ensure your experience is amazing and if for any reason you don't 100% enjoy the bootcamp, we stand behind our 90 day, 100% guarantee. You can contact us and we will refund you in less than 2-24 hours. Email: moon@algotradecamp
* why don't you believe in trading by hand?while i know there is a small percentage of traders who are profitable from hand trading, it wasn't for me. emotions would always get in the way atleast one day a month and when trading size, that one day can screw up a whole months work. i believe in working things that can compound. sitting in front of the charts, guessing price direction doesnt compound. coding backtests and researching new edges, does. this is why i believe if you are going to trade, you should do it algorithmically or not do it at all.
* do you need a computer science degree for this?no you dont need a computer science degree to learn how to code. youtube is the best place on earth, you can learn anything. i didn't go to college for coding, i learned to code after 30 years old from focusing for 4 hours per day, watching youtube python tutorials. you got this.
* how do i start the algo trading journey? if i get the bootcamp for a month, will it be enough?you can start by consuming this free resource and roadmap, along with my youtube. if you want me to hold your hand in short, concise videos, you can join the bootcamp. one month will be enough to consume the whole bootcamp. dependent on your experience, one month may be enough. regardless, join and see. you can always cancel after a month.
* can you talk about the profitability of algo trading?not really, as i don't know your strategy and approach to the market. in algo trading, no one will ever share their edge. if you see someone online trying to sell you a bot that is "plug and play" its a scam. its just math, if everyone was running the same strategy, the profits would go to 0. i can teach you how to automate your trading, where to look for strategies and how to backtest them, but i can't speak on profitability since i don't know your strategy.
* whats your opinion on machine learning in trading?everyone wants to predict price with machine learning but after a bunch of tests, i don't think that is the way. instead i think it comes down to predicting other things like market regime or when to run a certain strategy. i definitely think there is room for ML in trading, just approached differently, cause if everyone is predicting price, the price wont be the price anymore.
* can you give me a rundown of what each section of your screen is showing?
* yes, during my stream you can see many data sources that i watch all day. from left to right: crypto orders up to $15k size, liquidations, massive liquidations ($300k min), bigger orders, and on far right is the top 10 tokens and their change in the last 60 mins. all of these data sources are stored and i can use them in my algos and backtesting. some of these are connected to sound as well, explained below.
* what strategy do you suggest starting with?i'm not a financial advisor, so i can't suggest anything. the one suggestion i do have, is stop trading by hand, because you will slowly lose all of your money. i understand some traders are profitable by hand, but most will have at least 1 day out of each they are on 'tilt' and will eventually lose all their money. i can't suggest any strategies as this is not financial advice but i can suggest stepping away from hand trading, even if you don't want to automate it
* what are the sounds going off on your stream?on my stream i have sounds connected to different market conditions. i am exploring the thought of connecting sounds to market actions. for example: when the market is slightly up in the last 60 mins, you may hear birds chirping. if it is down bad, it may sound like we are in the middle of the ocean getting pummeled by waves. if someone gets liquidated you may hear a dong, or a chopper coming through to pick up their body. listen closely and you will be able to know whats going on in the markets just by the sounds.
* why cant i just buy a bot from you or someone else?im very skeptical of buying bots on the internet. i think its just math that if someone is selling a bot with a specific strategy, that strategy will eventually go to 0. i dont suggest you or anyone else ever buy a bot. if you want to automate your trading, it has to be w/ your strategy that's why i prefer teaching now to automate, opposed to selling bots.
* can you share your PnL?no, i don't share pnl as i share all of my code on youtube, i don't want someone to think they can just copy my code and make a million dollars over night. this is the hardest game in the world and i don't want to attract get rich quickers. this is a long, hard game & most wont make it. you must build your own edge. if everyone runs the same algos, they mathematically will go to 0
* what do i need to download to start coding in python?visual studio code or cursor. cursor is new to me, but it is a copy of visual studio code with ai inside it.
* do you do market orders or limit orders?i try to use limit orders as much as possible, but some strategies require market orders. i use market orders more often on the close than the open of a trade as most of my bots can wait to enter, but sometimes need to get out in a hurry.
* how can i get in touch with you (moon dev)?the best way is to catch me on a live stream. if its about business you can send me a short email at moon@algotradecamp.com i can't get back to everyone, so please pitch short and concisely
* can you build a bot for me?probably not, i code live every day on youtube so i can show my code to as many people as possible to help them. if you have a project that you'd like to hire me to do & are ok with some of it being shown on youtube, feel free to email me here: moon@algotradecamp.comi would much rather teach you how to fish, opposed to just giving you a meal. that's why i teach how to automate your trading in the bootcamp
* can i have a discount?i've spent nearly 4 years testing & figuring out things. i believe code is the great equalizer so there already is a steep discount. i believe i could sell this bootcamp for 10x the price, minimum.if you really can't afford it, i would suggest checking out the #clips channel in discord so you can get the bootcamp for free, while learning. you can also earn $69 per 10,000 views instead of free bootcamp if you want. the more views you get the higher the payment per 10,000 goes. 
* how often is the bootcamp updated?the bootcamp is updated every time i find something new that helps me. the idea is to constantly share new things i figure out inside of the bootcamp members area. i stream on youtube every day and work on the hardest problems and then at the end of the week i update the bootcamp. there are usually 2-4 updates per month.
* is the bootcamp for advanced coders only?no way! i built this bootcamp because i believe code is the great equalizer. i teach you exactly how to code in python, and then teach you how to algo trade. check out the testimonials, there are students who have never coded before and others who have coded for 10+ years. the bootcamp will save everyone interested in algo trading an unbelievable amount of time.
* can i learn only from your youtube channel?yes, absolutely. i believe code is the great equalizer so every day i create "over the shoulder" type coding videos. i have over 1,369 hours of coding videos free on my youtube so you can watch them all and essentially know what i know. that was the whole point of the youtube channel. many people kept asking for a course with short and concise videos and all my code, so i launched the algo trade camp but i still want to build the youtube into the best public good about algo trading
* why do you teach algo trading?because i believe code is the great equalizer, if you learn how to code, you know a language that 99% of the population doesn't. and that language controls the current world, and the future ai world. that language is python, which is a coding language. people always talk about the threat of ai and the chances it will take over. the decision for me to learn to code was easy, i wanted to be able to control the ai in the future if that worse case scenario were to happen. but tbh, i spent 10+ years in tech, scared to learn to code. it seemed too hard, after a few failed attempts, i just gave it up until i was faced with an urgent problem several years later. i had success in tech that gave me a nice portfolio to trade, but that trading quickly led me to the realization, me a human shouldnt be dealing with these daily emotions and a robot should be trading for me. a robot had to be trading for me, or i would lose all my hard earned money. i met someone who was algo trading a big amount and i was instantly inspired to become an algo trader. problem was i didn't know how to code and had just turned 30, i was too old to learn a new skill lol. 4 hours per day and a few months later, i had learned. i also quickly discovered no one shares algo trading info as they dont want to leak their edge. since it took me 10+ years and a huge problem to get me to learn to code, and seeing the power i now have, being able to build anything i can dream of i had to fire up a mic and show this to others. i believe in abundance, finance is scarcity led. most traders fail at trading, i knew i couldnt do the same thing as others. so i learned to code, now i show every step of the way on youtube because i hope to inspire traders to not trade by hand, and everyone else to learn how to code. because if you learn to code, you have a skill to build anything and to literally build your future. i wish i would have learned to code earlier
* how did you get started with coding?i spent multiple years hiring developers to build apps & saas for me, thinking i could never code myself. once i wanted to automate my trading, i knew i had to learn how to code to iterate to success. no one has a profitable bot off the bat, and i knew it would be too costly to iterate to success with a developer. so i started learning how to code in python, 4 hours per day, using free youtube videos and documentation. the algo trading industry is super secretive though, so there wasn't much info on how to build trading bots so once i understood how, i just started to show literally every thing i do on youtube. i believe code is the great equalizer, and it took me til 30 years old to start the journey of learning to code but now i believe i can build anything in this world. thats why i believe code is the great equalizer, cause if you know how to code, you can build anything for the rest of your life.
* can i have the bootcamp for free?We have many lengthy videos on our YouTube channel that need concise clips of the key points. To earn free access to the bootcamp, check out the clips channel in our Discord. There, you can learn how to study our YouTube videos and extract the most valuable segments.
* can i pay for the bootcamp in crypto?yes, if you are looking to sign up for the lifetime package. unfortunately, there is no way to collect subscriptions in crypto so we do lifetime only. you can email moon@algotradecamp.com for the address to send crypto to set up your bootcamp account.
* what is the thing you record your voice for text? what is the voice to text software yo uuse? its called flow pro it allows me to turn my voice to text to double my words per minute
* whats your github? @moondevonyt
"""

# Create response directory
RESPONSES_DIR = Path(project_root) / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# Add after other constants
UNKNOWN_QUESTIONS_FILE = Path(project_root) / "src/data/phone_agent/unknown_questions.csv"

# Create phone agent data directory
PHONE_AGENT_DATA_DIR = Path(project_root) / "src/data/phone_agent"
PHONE_AGENT_DATA_DIR.mkdir(parents=True, exist_ok=True)

class VoiceRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.silence_start = None
        self.current_audio = []
        self.recording_start = None
        self.last_speech_end = None
        self.processing = False
        
    def start_recording(self):
        """Start recording audio"""
        try:
            # First test if we can access the microphone
            cprint("🎤 Testing microphone access...", "cyan")
            
            # List available audio devices
            devices = sd.query_devices()
            cprint(f"🎛️ Available audio devices:", "cyan")
            default_input = None
            for i, device in enumerate(devices):
                cprint(f"  {i}: {device['name']} (inputs: {device['max_input_channels']})", "cyan")
                if device['max_input_channels'] > 0:
                    if default_input is None:
                        default_input = i
                    if 'default' in device['name'].lower() or 'microphone' in device['name'].lower():
                        default_input = i
            
            if default_input is None:
                raise Exception("No input devices found!")
                
            # Try to find default input device
            try:
                default_device = sd.query_devices(kind='input')
                device_id = default_device['index'] if 'index' in default_device else default_input
                cprint(f"🎤 Using input device: {devices[device_id]['name']}", "green")
            except Exception as e:
                cprint(f"⚠️ Using fallback device {default_input}: {e}", "yellow")
                device_id = default_input
            
            # Test microphone access with explicit device
            test_stream = sd.InputStream(
                device=device_id,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=lambda *args: None,
                blocksize=CHUNK_SIZE
            )
            test_stream.start()
            test_stream.stop()
            test_stream.close()
            cprint("✅ Microphone access granted!", "green")

            # Start the actual recording stream with more sensitive settings
            self.is_recording = True
            self.stream = sd.InputStream(
                device=device_id,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=self.audio_callback,
                blocksize=CHUNK_SIZE,
                latency='low'  # Lower latency for better responsiveness
            )
            self.stream.start()
            cprint("🎙️ Recording started!", "green")
            
            # Print current audio settings
            cprint(f"🔊 Audio settings:", "cyan")
            cprint(f"  Device: {devices[device_id]['name']}", "cyan")
            cprint(f"  Sample rate: {SAMPLE_RATE} Hz", "cyan")
            cprint(f"  Channels: {CHANNELS}", "cyan")
            cprint(f"  Chunk size: {CHUNK_SIZE}", "cyan")
            cprint(f"  Volume threshold: {VOLUME_THRESHOLD}", "cyan")
            
            # Test the input stream with some initial readings
            cprint("\n📊 Testing input levels...", "cyan")
            time.sleep(0.5)  # Wait for stream to stabilize
            
        except Exception as e:
            cprint("❌ Could not access microphone. Please allow microphone access in your browser.", "red")
            cprint(f"Error: {str(e)}", "red")
            raise Exception("Microphone access denied. Please allow access and try again.")

    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            cprint(f"⚠️ {status}", "yellow")
            return
            
        if self.processing:
            return  # Don't process audio while handling a response
            
        # Get volume level with better noise handling
        volume_norm = np.linalg.norm(indata) / np.sqrt(frames)
        max_volume = np.max(np.abs(indata))
        
        # Apply noise floor
        if volume_norm < BACKGROUND_NOISE_FLOOR:
            volume_norm = 0
        
        current_time = time.currentTime
        
        # Debug volume levels more frequently during initial setup
        if not hasattr(self, 'debug_count'):
            self.debug_count = 0
        self.debug_count += 1
        
        # Print volume levels more frequently at first, then reduce frequency
        if self.debug_count < 100 or random.random() < 0.01:
            cprint(f"🎤 Volume: {volume_norm:.4f} (max: {max_volume:.4f}, threshold: {VOLUME_THRESHOLD})", "cyan")
            if volume_norm == 0:
                cprint("⚠️ No audio input detected. Please check your microphone.", "yellow")
            elif volume_norm < VOLUME_THRESHOLD:
                cprint("ℹ️ Volume too low. Please speak louder or adjust microphone.", "cyan")
        
        # Start or continue recording if volume above threshold
        if volume_norm > VOLUME_THRESHOLD or max_volume > VOLUME_THRESHOLD:
            if not self.recording_start:
                cprint(f"🎙️ Speech detected! Volume: {volume_norm:.4f} (max: {max_volume:.4f})", "green")
                self.recording_start = current_time
                self.last_speech_end = None
            self.current_audio.append(indata.copy())
            self.silence_start = None
        else:
            # If we were recording, track silence
            if self.recording_start:
                if self.silence_start is None:
                    self.silence_start = current_time
                self.current_audio.append(indata.copy())
                
                # Check if this is just a breath pause
                if (self.silence_start and 
                    current_time - self.silence_start <= BREATH_PAUSE):
                    return  # Continue recording through brief pauses
                
                # If silence long enough and we have enough audio, process it
                if (self.silence_start and 
                    current_time - self.silence_start > SPEECH_END_PAUSE and
                    current_time - self.recording_start > MIN_PHRASE_LENGTH):
                    
                    # Check if this might be part of a continuing thought
                    if (self.last_speech_end and 
                        current_time - self.last_speech_end < MAX_PHRASE_GAP):
                        return  # Wait for possible continuation
                    
                    if self.current_audio:
                        audio = np.concatenate(self.current_audio, axis=0)
                        # Extra check for minimum volume over time
                        if np.max(np.abs(audio)) > VOLUME_THRESHOLD:
                            self.audio_queue.put(audio)
                            self.processing = True  # Stop processing until response handled
                            cprint("🎙️ Speech ended, processing...", "cyan")
                    
                    # Update tracking
                    self.last_speech_end = current_time
                    self.current_audio = []
                    self.recording_start = None
                    self.silence_start = None

async def process_audio_chunk(audio_data):
    """Process an audio chunk and return transcription"""
    try:
        # Validate audio data
        if len(audio_data) < SAMPLE_RATE * MIN_AUDIO_LENGTH:
            cprint("⚠️ Audio too short, skipping...", "yellow")
            return ""
            
        # Check if audio is just silence
        if np.max(np.abs(audio_data)) < SILENCE_THRESHOLD:
            cprint("⚠️ Audio too quiet, skipping...", "yellow")
            return ""
        
        # Convert to wav file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            # Get transcription
            with open(temp_file.name, 'rb') as f:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                ).text
                
            # Cleanup
            os.unlink(temp_file.name)
            
            # Validate transcript
            if not transcript or len(transcript.strip()) < 2:
                return ""
                
            return transcript
            
    except Exception as e:
        cprint(f"❌ Error processing audio: {str(e)}", "red")
        return ""

async def play_audio_response(text):
    """Generate and play voice response for text"""
    try:
        # Clean up any extra whitespace and add final punctuation if missing
        text = text.strip()
        if not any(text.endswith(char) for char in '.!?'):
            text += '.'
            
        voice_response = openai.audio.speech.create(
            model="tts-1",
            voice=VOICE_NAME,
            speed=1.2,  # Slightly faster for more natural flow
            input=text
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            for chunk in voice_response.iter_bytes():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # Get audio duration using ffprobe
        duration = float(subprocess.check_output([
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            temp_path
        ]).decode().strip())
        
        # Calculate when to resume listening (90% through the response)
        resume_time = duration * 0.9
        
        def play_audio():
            os.system(f"afplay {temp_path}")
            os.unlink(temp_path)
            
        # Start audio playback in background thread
        play_thread = threading.Thread(target=play_audio)
        play_thread.start()
        
        # Wait until near the end to resume listening
        await asyncio.sleep(resume_time)
        
        return True
            
    except Exception as e:
        cprint(f"❌ Error playing audio: {str(e)}", "red")
        return False

def split_into_phrases(text):
    """Split text into natural phrases for smoother speech"""
    # Split on punctuation first
    chunks = []
    current = []
    
    # Split into words
    words = text.split()
    
    for word in words:
        current.append(word)
        # If word ends with punctuation or we have enough words for a natural phrase
        if (any(char in word for char in '.!?,') or 
            len(current) >= 8):  # Increased from 3 to 8 for more natural phrases
            chunks.append(' '.join(current))
            current = []
    
    # Add any remaining words
    if current:
        chunks.append(' '.join(current))
    
    return chunks

def log_unknown_question(question):
    """Log questions the AI couldn't answer"""
    try:
        # Create dataframe with new question
        new_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'question': question
        }
        
        # Load existing or create new DataFrame
        if UNKNOWN_QUESTIONS_FILE.exists():
            df = pd.read_csv(UNKNOWN_QUESTIONS_FILE)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        else:
            df = pd.DataFrame([new_data])
        
        # Save to CSV
        df.to_csv(UNKNOWN_QUESTIONS_FILE, index=False)
        cprint(f"📝 Unknown question logged: {question}", "yellow")
        
    except Exception as e:
        cprint(f"❌ Error logging unknown question: {str(e)}", "red")

def needs_knowledge_base(question):
    """Check if the question is about Moon Dev, Algo Trade Camp, or specific offerings"""
    # Convert to lowercase for matching
    question = question.lower()
    
    # Keywords that indicate we need to verify against knowledge base
    moon_dev_keywords = {
        'moon dev', 'moondev', 'moon', 'bootcamp', 'algo trade camp', 'algotradecamp',
        'course', 'discord', 'stream', 'youtube channel', 'points', 'clips',
        'refund', 'subscription', 'price', 'cost', 'payment', 'lifetime',
        '777', 'peace and love', 'trading bot', 'your bot', 'your strategy'
    }
    
    # Check if any keywords are in the question
    return any(keyword in question for keyword in moon_dev_keywords)

def is_question_in_knowledge_base(question, knowledge_base):
    """Check if the question can be confidently answered"""
    # First check if this question needs knowledge base verification
    if not needs_knowledge_base(question):
        return True  # Allow AI to use its general knowledge
        
    # Convert to lowercase for matching
    question = question.lower()
    knowledge_base = knowledge_base.lower()
    
    # Extract key terms from question (excluding common words)
    common_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'do', 'does', 
                   'can', 'could', 'would', 'will', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 
                   'for', 'of', 'with', 'by', 'about', 'your', 'you', 'i', 'we', 'they', 'he',
                   'she', 'it', 'this', 'that', 'these', 'those', 'my', 'our', 'their'}
                   
    question_terms = set(word.strip('?.,!') for word in question.split() 
                        if word.strip('?.,!').lower() not in common_words)
    
    # If no significant terms (after removing common words), allow AI to answer
    if not question_terms:
        return True
        
    # Count how many key terms are found in knowledge base
    terms_found = sum(1 for term in question_terms if term in knowledge_base)
    
    # If we find most of the key terms (>= 70%), consider it answerable
    return (terms_found / len(question_terms)) >= 0.7

async def test_conversation():
    """Run a test conversation with continuous voice interaction"""
    try:
        cprint("\n🎯 TESTING MODE ACTIVE", "yellow")
        cprint("═" * 50, "yellow")
        
        # Welcome message
        cprint("\n" + "═" * 50, "green")
        cprint("🌟 Starting Moon Dev's AI Voice Assistant! 🌙", "green")
        cprint("Press Ctrl+C to end the conversation", "yellow")
        cprint("═" * 50, "green")
        
        # Initial greeting
        greeting = "Hello! This is Moon Dev's AI Assistant. How can I help you today? 🌙"
        cprint("\n🤖 AI: " + greeting, "green")
        await play_audio_response(greeting)
        
        # Initialize recorder
        recorder = VoiceRecorder()
        recorder.start_recording()
        
        conversation_history = [
            {"role": "system", "content": f"""You are Moon Dev's friendly AI assistant. Keep responses very short and concise (1-2 sentences max). Add emojis to make responses fun and engaging.

Use this knowledge base for Moon Dev specific questions: {KNOWLEDGE_BASE}

Key guidelines:
- Use knowledge base for Moon Dev/Algo Trade Camp specific questions
- Use your general knowledge for common questions
- Keep responses under 2 sentences
- Add relevant emojis
- Never share specific trading strategies or PnL
- Emphasize learning to code over hand trading
- Promote the 777 peace and love philosophy
- Direct technical questions to the bootcamp
- Suggest watching YouTube for free learning
"""},
            {"role": "assistant", "content": greeting}
        ]
        
        cprint("\n🎤 Listening...", "cyan")
        
        while True:
            if not recorder.audio_queue.empty():
                audio_data = recorder.audio_queue.get()
                
                # Process audio
                transcript = await process_audio_chunk(audio_data)
                if transcript.strip():
                    cprint(f"\n💭 You said: {transcript}", "cyan")
                    
                    # Check if this needs knowledge base verification
                    needs_verification = needs_knowledge_base(transcript)
                    
                    # If it needs verification, check knowledge base
                    if needs_verification:
                        can_answer = is_question_in_knowledge_base(transcript, KNOWLEDGE_BASE)
                    else:
                        can_answer = True  # Let AI use its general knowledge
                    
                    if not can_answer:
                        # Log the unknown question
                        log_unknown_question(transcript)
                        
                        # Prepare "I don't know" response
                        unknown_response = "I apologize, but I'm not sure about that. Please email moon@algotradecamp.com and we'll get that answered ASAP! 🌙✉️"
                        cprint("\n🤖 AI: " + unknown_response, "yellow")
                        
                        # Play response and add to history
                        if unknown_response.strip():
                            success = await play_audio_response(unknown_response)
                            if success:
                                recorder.processing = False
                                cprint("\n🎤 Listening...", "cyan")
                        
                        conversation_history.append({"role": "assistant", "content": unknown_response})
                        continue
                    
                    # Detect language
                    try:
                        lang = langdetect.detect(transcript)
                        if lang != 'en':
                            cprint("\n⚠️ Non-English input detected. Please speak in English.", "yellow")
                            await play_audio_response("I can only understand English. Please speak in English.")
                            cprint("\n🎤 Listening...", "cyan")
                            continue
                    except:
                        pass  # Continue if language detection fails
                    
                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": transcript})
                    
                    # Get AI response
                    cprint("\n🤖 AI:", "green")
                    
                    response = openai.chat.completions.create(
                        model=MODEL_NAME,
                        messages=conversation_history,
                        temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS
                    )
                    
                    full_response = response.choices[0].message.content
                    cprint(full_response, "green")
                    
                    # Play the response and resume listening near the end
                    if full_response.strip():
                        success = await play_audio_response(full_response)
                        if success:
                            # Resume audio processing before speech finishes
                            recorder.processing = False
                            cprint("\n🎤 Listening...", "cyan")
                    
                    # Add AI response to history
                    conversation_history.append({"role": "assistant", "content": full_response})
            
            await asyncio.sleep(0.1)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        if 'recorder' in locals():
            recorder.stop_recording()
        cprint("\n\n👋 Call ended. Moon Dev's AI signing off! 🌙", "yellow")
        
    except Exception as e:
        cprint(f"\n❌ Error in conversation: {str(e)}", "red")
        if hasattr(e, '__traceback__'):
            import traceback
            cprint(f"Traceback:\n{traceback.format_exc()}", "red")

# Only define Flask routes if not in testing mode
if not TESTING_MODE:
    @app.route("/answer", methods=['POST'])
    def answer_call():
        """Handle incoming calls"""
        resp = VoiceResponse()
        
        # Welcome message
        resp.say("Welcome to Moon Dev's A.I. Assistant! 🌙", voice=VOICE_NAME)
        
        # Gather speech input
        gather = Gather(input='speech', 
                       action='/handle-input',
                       method='POST',
                       language='en-US',
                       speechTimeout='auto')
        
        gather.say("How can I help you today?", voice=VOICE_NAME)
        resp.append(gather)
        
        # If no input received
        resp.redirect('/answer')
        
        return str(resp)

    @app.route("/handle-input", methods=['POST'])
    def handle_input():
        """Handle speech input from caller"""
        try:
            # Get the speech input
            speech_result = request.values.get('SpeechResult', '')
            
            if not speech_result:
                resp = VoiceResponse()
                resp.say("I didn't catch that. Could you please try again?", voice=VOICE_NAME)
                resp.redirect('/answer')
                return str(resp)
                
            cprint(f"\n🎤 User said: {speech_result}", "cyan")
            
            # Generate AI response
            response = openai.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are Moon Dev's friendly AI assistant. Keep responses concise and clear for phone calls."},
                    {"role": "user", "content": speech_result}
                ]
            )
            
            response_text = response.choices[0].message.content
            cprint(f"\n🤖 AI response: {response_text}", "green")
            
            # Create response
            resp = VoiceResponse()
            
            # Say the response
            resp.say(response_text, voice=VOICE_NAME)
            
            # Ask if they need anything else
            gather = Gather(input='speech',
                           action='/handle-input',
                           method='POST',
                           language='en-US',
                           speechTimeout='auto')
            gather.say("Is there anything else you'd like to know?", voice=VOICE_NAME)
            resp.append(gather)
            
            # If no input received
            resp.redirect('/answer')
            
            return str(resp)
            
        except Exception as e:
            cprint(f"❌ Error handling input: {str(e)}", "red")
            resp = VoiceResponse()
            resp.say("I encountered an error. Please try again!", voice=VOICE_NAME)
            resp.redirect('/answer')
            return str(resp)

    @app.route("/status", methods=['POST'])
    def call_status():
        """Handle call status updates"""
        status = request.values.get('CallStatus', '')
        cprint(f"📞 Call Status: {status}", "cyan")
        return '', 200

async def process_message(message):
    """Process a message and return AI response - used by both web and voice interfaces"""
    try:
        # Check if this needs knowledge base verification
        needs_verification = needs_knowledge_base(message)
        
        # If it needs verification, check knowledge base
        if needs_verification:
            can_answer = is_question_in_knowledge_base(message, KNOWLEDGE_BASE)
        else:
            can_answer = True  # Let AI use its general knowledge
        
        if not can_answer:
            # Log the unknown question
            log_unknown_question(message)
            return "I apologize, but I'm not sure about that. Please email moon@algotradecamp.com and we'll get that answered ASAP! 🌙✉️"
        
        # Get AI response
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": f"""You are Moon Dev's friendly AI assistant. Keep responses very short and concise (1-2 sentences max). Add emojis to make responses fun and engaging.

Use this knowledge base for Moon Dev specific questions: {KNOWLEDGE_BASE}

Key guidelines:
- Use knowledge base for Moon Dev/Algo Trade Camp specific questions
- Use your general knowledge for common questions
- Keep responses under 2 sentences
- Add relevant emojis
- Never share specific trading strategies or PnL
- Emphasize learning to code over hand trading
- Promote the 777 peace and love philosophy
- Direct technical questions to the bootcamp
- Suggest watching YouTube for free learning
"""},
                {"role": "user", "content": message}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        cprint(f"❌ Error processing message: {str(e)}", "red")
        return "Sorry, I encountered an error. Please try again! 🙏"

def start_server():
    """Start the server based on mode"""
    try:
        cprint("\n🚀 Starting Moon Dev's Phone Agent...", "green")
        
        if TESTING_MODE:
            # Run Streamlit web interface
            cprint("🌐 Running in web mode - starting Streamlit server...", "green")
            import subprocess
            web_interface_path = Path(project_root) / "src/web/chat_interface.py"
            subprocess.run(["streamlit", "run", str(web_interface_path)])
        else:
            # Run Flask server for Twilio
            cprint("📞 Running in Twilio mode...", "green")
            cprint(f"📞 Twilio number: {TWILIO_PHONE_NUMBER}", "cyan")
            
            # Print ngrok command for testing locally
            cprint("\n🔧 To test locally:", "yellow")
            cprint("1. Install ngrok: brew install ngrok", "yellow")
            cprint("2. Run: ngrok http 5000", "yellow")
            cprint("3. Copy the ngrok URL to your Twilio phone number's webhook", "yellow")
            
            # Run the Flask app
        host = os.environ.get('PHONE_AGENT_HOST', '127.0.0.1')
        self.flask_thread = threading.Thread(target=self.app.run, kwargs={'host': host, 'port': self.port})
        
    except Exception as e:
        cprint(f"\n❌ Error starting server: {str(e)}", "red")
        raise

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        cprint("\n👋 Phone Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
