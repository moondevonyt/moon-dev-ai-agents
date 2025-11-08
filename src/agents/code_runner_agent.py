"""
building an agent to run code

Essentially, this agent can run code inside of cursor, and then get the error and send it 
to composer and then apply the air and go on an infinite loop of working on and fixing code. 
Everybody will have different places, different x y coordinates for things. So you'll need to 
change your x y coordinates by using the script in the scripts folder called find coordinates. 
 
"""

"""
🚀 Moon Dev's Code Executor Agent
Moves to position, executes code, and captures screenshot

1 - move mouse to code editor and hit command + return to run the code
2 - move mouse to terminal output & hit command + a to select all then command + i to paste the error into composer
3 - move mouse to composer and hit command + return to send the error to the ai
4 - analyze composer screenshot for completion
5 - if not complete, wait for AI fix and continue loop

"""

import pyautogui
import time
from pathlib import Path
from termcolor import cprint
from datetime import datetime
import Quartz
import sys
import os
from Quartz import CoreGraphics as CG
import AppKit
import subprocess
import base64
from src.models import model_factory  # Import Moon Dev's model factory
import traceback
from Cocoa import NSURL
import time

# Configuration - Moon Dev's target coordinates (DO NOT ADJUST THESE)
CODE_EDITOR_X = -2686
CODE_EDITOR_Y = -1144

# command 

# Terminal coordinates
TERMINAL_X = -2593
TERMINAL_Y = -556

# Composer coordinates and settings
AI_CHAT_X = -1683  # Adjust as needed
AI_CHAT_Y = -414   # Adjust as needed
AI_CHAT_WIDTH = 200
AI_CHAT_HEIGHT = 1500

# Screenshot area coordinates (top half of screen)
SCREENSHOT_X = -1933  # Same X as AI chat
SCREENSHOT_Y = -1614  # Higher up (600 pixels up from AI_CHAT_Y)
SCREENSHOT_WIDTH = 600  # Wider capture area
SCREENSHOT_HEIGHT = 1200  # Shorter but captures top area

# Composer screenshot prompt
AI_CHAT_SCREENSHOT_PROMPT = "Does this image have more than 5 emojis in it? Return ONLY true or false."

# AI Model settings
MODEL_TYPE = "gemini"  # Using OpenAI for image analysis
MODEL_NAME = "gemini-2.5-pro"  # GPT-4 Vision model

# Easily configurable settings
CLICK_PAUSE = 2.0         # Pause after movement before clicking
ACTIVATION_PAUSE = 1.0    # Pause after click to ensure window activation
EXECUTE_PAUSE = 8       # Pause after cmd+return before screenshot
MOVEMENT_SPEED = 1.0      # Speed of cursor movement (seconds)

# New configuration constants added by Moon Dev 💫
WAIT_AI_FIX_SECONDS = 30  # Wait time in seconds for AI to fix the code 💫
CODE_FIX_PROMPT = "please fix my code - if it looks like it is done and running successfully, just output 100 emoojis in a block. done is considered when the backtesting.py stats are in the output and i can clearly see Return, drawdown and all other things"  # Code fix prompt for AI debug 🛠️
TYPING_SPEED = 0.0001  # Delay between keystrokes in seconds (lower = faster)

# Key command configurations 🎹
APPLY_FIX_COMMAND = {
    'key': 0x27,          # Apostrophe key code
    'name': "cmd + '"     # Command description for logging
}

# Maximum retries for screenshot capture
MAX_SCREENSHOT_RETRIES = 5
SCREENSHOT_RETRY_DELAY = 3  # seconds

def get_display_bounds():
    """Get all display bounds including negative coordinates"""
    try:
        # Create array for display IDs
        max_displays = 32
        display_count = CG.CGGetActiveDisplayList(max_displays, None, None)[1]
        active_displays = CG.CGGetActiveDisplayList(display_count, None, None)[0]
        
        displays = []
        for display in active_displays:
            bounds = CG.CGDisplayBounds(display)
            displays.append({
                'id': display,
                'x': bounds.origin.x,
                'y': bounds.origin.y,
                'width': bounds.size.width,
                'height': bounds.size.height
            })
            
        return displays
    except Exception as e:
        cprint(f"❌ Error getting displays: {e}", "red")
        return []

def move_mouse_cg(x, y, debug=True):
    """Move mouse using CoreGraphics with display bounds checking"""
    try:
        if debug:
            displays = get_display_bounds()
            cprint("\n🖥️ Display Information:", "cyan")
            for i, display in enumerate(displays, 1):
                cprint(f"  ├─ Display {i}: Origin({display['x']}, {display['y']}) Size({display['width']}x{display['height']})", "cyan")
        
        # Get current position for verification
        current = CG.CGEventGetLocation(CG.CGEventCreate(None))
        cprint(f"\n📍 Starting position: ({int(current.x)}, {int(current.y)})", "yellow")
        
         # Create smooth movement
        steps = 20
        start_x, start_y = current.x, current.y
        
        for i in range(steps + 1):
            # Calculate intermediate position
            current_x = start_x + (x - start_x) * i / steps
            current_y = start_y + (y - start_y) * i / steps
            
            # Create point for movement
            point = CG.CGPoint(current_x, current_y)
            
            # Move cursor
            CG.CGWarpMouseCursorPosition(point)
            
            # Small pause between movements
            time.sleep(MOVEMENT_SPEED / steps)
            
            if debug and i % 5 == 0:
                pos = CG.CGEventGetLocation(CG.CGEventCreate(None))
                cprint(f"  ├─ Step {i}: Moving to ({int(current_x)}, {int(current_y)}) At: ({int(pos.x)}, {int(pos.y)})", "cyan")
        
        # Final position check
        final_pos = CG.CGEventGetLocation(CG.CGEventCreate(None))
        cprint(f"📍 Final position: ({int(final_pos.x)}, {int(final_pos.y)})", "yellow")
        
        # Create and post a mouse moved event
        point = CG.CGPoint(x, y)
        event = CG.CGEventCreateMouseEvent(None, CG.kCGEventMouseMoved, point, CG.kCGMouseButtonLeft)
        CG.CGEventPost(CG.kCGHIDEventTap, event)
        
        success = abs(final_pos.x - x) <= 10 and abs(final_pos.y - y) <= 10
        if not success:
            cprint(f"⚠️ Warning: Expected ({x}, {y}) but got ({int(final_pos.x)}, {int(final_pos.y)})", "yellow")
        
        return success
        
    except Exception as e:
        cprint(f"❌ Error moving mouse: {e}", "red")
        return False

def activate_vscode():
    """Activate VSCode application"""
    try:
        # Get VSCode app
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        
        # Find VSCode
        vscode_app = None
        for app in apps:
            if 'Code' in app.localizedName():
                vscode_app = app
                break
        
        if vscode_app:
            cprint("\n🎯 Found VSCode, activating...", "cyan")
            vscode_app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
            time.sleep(0.5)  # Wait for activation
            return True
        else:
            cprint("❌ VSCode not found running!", "red")
            return False
            
    except Exception as e:
        cprint(f"❌ Error activating VSCode: {e}", "red")
        return False

def simple_click(double_click=True):
    """Simple click at current position with optional double-click using pyautogui"""
    try:
        # Get current position for logging
        pos = CG.CGEventGetLocation(CG.CGEventCreate(None))
        cprint(f"🖱️ {'Double' if double_click else 'Single'} clicking at: ({int(pos.x)}, {int(pos.y)})", "cyan")
        
        # Use pyautogui for clicking
        time.sleep(0.8)  # Pause before clicking
        
        if double_click:
            pyautogui.click(clicks=2, interval=0.3)  # Double click with 0.3s between clicks
        else:
            pyautogui.click()
            
        time.sleep(0.8)  # Pause after clicking
        
        return True
        
    except Exception as e:
        cprint(f"❌ Error clicking: {e}", "red")
        return False

def setup_directories():
    """Setup necessary directories"""
    data_dir = Path("src/data/code_runner")
    screenshot_dir = data_dir / "screenshots"
    data_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir

def click_with_applescript():
    """Use AppleScript to click and activate window"""
    try:
        # AppleScript to click and activate
        script = '''
        tell application "System Events"
            set currentPosition to {%d, %d}
            click at currentPosition
            delay 0.3
            click at currentPosition
            delay 0.3
            click at currentPosition
        end tell
        ''' % (CODE_EDITOR_X, CODE_EDITOR_Y)
        
        cprint("🍎 Using AppleScript for clicking...", "cyan")
        subprocess.run(['osascript', '-e', script], capture_output=True)
        return True
    except Exception as e:
        cprint(f"❌ Error with AppleScript click: {e}", "red")
        return False

def quick_click():
    """Quick and direct click using CoreGraphics"""
    try:
        # First try CoreGraphics click
        cprint("🖱️ Attempting click...", "cyan")
        
        # Get current position
        pos = CG.CGEventGetLocation(CG.CGEventCreate(None))
        
        # Create and post mouse events
        mouse_down = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseDown, pos, CG.kCGMouseButtonLeft)
        mouse_up = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseUp, pos, CG.kCGMouseButtonLeft)
        
        # Click with proper timing
        time.sleep(0.3)  # Small pause before
        CG.CGEventPost(CG.kCGHIDEventTap, mouse_down)
        time.sleep(0.2)  # Hold the click
        CG.CGEventPost(CG.kCGHIDEventTap, mouse_up)
        time.sleep(0.3)  # Pause after
        
        return True
    except Exception as e:
        cprint(f"❌ Error clicking: {e}", "red")
        return False

def send_command_return():
    """Send Command+Return using CoreGraphics events"""
    try:
        # Create Command key down event
        cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)  # 0x37 is Command
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
        time.sleep(0.1)
        
        # Create Return key down/up events
        return_down = CG.CGEventCreateKeyboardEvent(None, 0x24, True)  # 0x24 is Return
        return_up = CG.CGEventCreateKeyboardEvent(None, 0x24, False)
        
        CG.CGEventSetFlags(return_down, CG.kCGEventFlagMaskCommand)
        CG.CGEventSetFlags(return_up, CG.kCGEventFlagMaskCommand)
        
        CG.CGEventPost(CG.kCGHIDEventTap, return_down)
        time.sleep(0.1)
        CG.CGEventPost(CG.kCGHIDEventTap, return_up)
        time.sleep(0.1)
        
        # Release Command key
        cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)
        
        return True
    except Exception as e:
        cprint(f"❌ Error sending cmd+return: {e}", "red")
        return False

def send_command_apostrophe():
    """Send Command+apostrophe (') using CoreGraphics events"""
    try:
        # Create Command key down event
        cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)  # 0x37 is Command key
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
        time.sleep(0.1)

        # Apostrophe key down/up events using constant
        apostrophe_down = CG.CGEventCreateKeyboardEvent(None, APPLY_FIX_COMMAND['key'], True)
        apostrophe_up = CG.CGEventCreateKeyboardEvent(None, APPLY_FIX_COMMAND['key'], False)

        CG.CGEventSetFlags(apostrophe_down, CG.kCGEventFlagMaskCommand)
        CG.CGEventSetFlags(apostrophe_up, CG.kCGEventFlagMaskCommand)

        CG.CGEventPost(CG.kCGHIDEventTap, apostrophe_down)
        time.sleep(0.1)
        CG.CGEventPost(CG.kCGHIDEventTap, apostrophe_up)
        time.sleep(0.1)

        # Release Command key
        cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)

        cprint(f"⌨️ {APPLY_FIX_COMMAND['name']} sent successfully! 🚀 Moon Dev 🙏", "cyan")
        return True
    except Exception as e:
        cprint(f"❌ Error sending {APPLY_FIX_COMMAND['name']}: {e}", "red")
        return False

def send_keys(text):
    """Send keyboard input using pyautogui"""
    try:
        # Type the text character by character
        for char in text:
            if char == '@':
                # On Mac, @ is Shift+2
                pyautogui.keyDown('shift')
                pyautogui.press('2')
                pyautogui.keyUp('shift')
            else:
                pyautogui.write(char)
            time.sleep(TYPING_SPEED)  # Reduced delay between characters
            
        return True
    except Exception as e:
        cprint(f"❌ Error sending keys: {e}", "red")
        return False

def send_enter():
    """Send Enter key press"""
    try:
        # Create Return key events
        return_down = CG.CGEventCreateKeyboardEvent(None, 0x24, True)  # 0x24 is Return
        return_up = CG.CGEventCreateKeyboardEvent(None, 0x24, False)
        
        # Post events
        CG.CGEventPost(CG.kCGHIDEventTap, return_down)
        time.sleep(0.1)
        CG.CGEventPost(CG.kCGHIDEventTap, return_up)
        
        return True
    except Exception as e:
        cprint(f"❌ Error sending enter: {e}", "red")
        return False

def set_clipboard_content(text):
    """Set clipboard content using pbcopy"""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return True
    except Exception as e:
        cprint(f"❌ Error setting clipboard content: {e}", "red")
        return False

def paste_from_clipboard():
    """Paste content from clipboard using Command+V"""
    try:
        # Command key down
        cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
        time.sleep(0.1)
        
        # 'V' key with command flag
        v_down = CG.CGEventCreateKeyboardEvent(None, 0x09, True)  # 0x09 is 'v'
        v_up = CG.CGEventCreateKeyboardEvent(None, 0x09, False)
        CG.CGEventSetFlags(v_down, CG.kCGEventFlagMaskCommand)
        CG.CGEventSetFlags(v_up, CG.kCGEventFlagMaskCommand)
        
        CG.CGEventPost(CG.kCGHIDEventTap, v_down)
        time.sleep(0.1)
        CG.CGEventPost(CG.kCGHIDEventTap, v_up)
        
        # Command key up
        cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
        CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)
        
        return True
    except Exception as e:
        cprint(f"❌ Error pasting from clipboard: {e}", "red")
        return False

def submit_to_ai_debug(number):
    """Submit to AI debug with new process and handle code fix loop"""
    try:
        cprint("\n🤖 Starting AI Debug Submission...", "cyan")
        
        # Copy prompt to clipboard first
        cprint("\n📋 Copying prompt to clipboard...", "cyan")
        if not set_clipboard_content(CODE_FIX_PROMPT):
            cprint("❌ Failed to copy prompt to clipboard!", "red")
            return False
        
        # Move to terminal coordinates
        cprint(f"\n🖱️ Moving to terminal position ({TERMINAL_X}, {TERMINAL_Y})", "cyan")
        if not move_mouse_cg(TERMINAL_X, TERMINAL_Y):
            cprint("❌ Failed to move to terminal position!", "red")
            return False
            
        # Click to activate
        cprint("\n🖱️ Clicking to activate debug input...", "cyan")
        time.sleep(0.5)
        if not quick_click():
            cprint("❌ Failed to click debug input!", "red")
            return False
        
        time.sleep(0.5)
        
        # Send Command+A to select all
        cprint("\n⌨️ Selecting all text (cmd+a)...", "cyan")
        try:
            # Command key down
            cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)
            CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
            time.sleep(0.1)
            
            # 'A' key with command flag
            a_down = CG.CGEventCreateKeyboardEvent(None, 0x00, True)  # 0x00 is 'a'
            a_up = CG.CGEventCreateKeyboardEvent(None, 0x00, False)
            CG.CGEventSetFlags(a_down, CG.kCGEventFlagMaskCommand)
            CG.CGEventSetFlags(a_up, CG.kCGEventFlagMaskCommand)
            
            CG.CGEventPost(CG.kCGHIDEventTap, a_down)
            time.sleep(0.1)
            CG.CGEventPost(CG.kCGHIDEventTap, a_up)
            
            # Command key up
            cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
            CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)
        except Exception as e:
            cprint(f"❌ Error sending cmd+a: {e}", "red")
            return False
            
        time.sleep(0.5)
        
        # Send Command+I
        cprint("\n⌨️ Inserting (cmd+i)...", "cyan")
        try:
            # Command key down
            cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)
            CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
            time.sleep(0.1)
            
            i_down = CG.CGEventCreateKeyboardEvent(None, 0x22, True)
            i_up = CG.CGEventCreateKeyboardEvent(None, 0x22, False)
            CG.CGEventSetFlags(i_down, CG.kCGEventFlagMaskCommand)
            CG.CGEventSetFlags(i_up, CG.kCGEventFlagMaskCommand)
            
            CG.CGEventPost(CG.kCGHIDEventTap, i_down)
            time.sleep(0.1)
            CG.CGEventPost(CG.kCGHIDEventTap, i_up)
            
            cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
            CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)

            # Add pause to ensure cmd+i completes
            time.sleep(1.0)
            
            # Move back to cursor position
            cprint("\n🖱️ Moving back to cursor position...", "cyan")
            if not move_mouse_cg(AI_CHAT_X, AI_CHAT_Y):
                cprint("❌ Failed to move to cursor position!", "red")
                return False
                
            time.sleep(0.5)
            if not quick_click():
                cprint("❌ Failed to click cursor position!", "red")
                return False
                
            time.sleep(0.5)
            
        except Exception as e:
            cprint(f"❌ Error sending keyboard commands: {e}", "red")
            return False
        
        # Paste the prompt instead of typing it
        cprint("\n📋 Pasting fix prompt...", "cyan")
        if not paste_from_clipboard():
            cprint("❌ Failed to paste fix prompt!", "red")
            return False
        
        # Send enter
        time.sleep(0.3)
        if not send_enter():
            cprint("❌ Failed to submit message!", "red")
            return False
        
        # Step 4: Wait for AI to process, then apply fix
        cprint(f"\n⏳ Waiting {WAIT_AI_FIX_SECONDS} seconds for AI to process...", "yellow")
        time.sleep(WAIT_AI_FIX_SECONDS)
        
        # Move back to code editor
        cprint(f"\n🖱️ Moving back to code editor ({CODE_EDITOR_X}, {CODE_EDITOR_Y})", "cyan")
        if not move_mouse_cg(CODE_EDITOR_X, CODE_EDITOR_Y):
            cprint("❌ Failed to move to code editor!", "red")
            return False
            
        # Click to activate window
        time.sleep(0.5)
        if not quick_click():
            cprint("❌ Failed to activate code editor!", "red")
            return False
            
        time.sleep(0.5)
        
        # Send Command+Apostrophe to apply fix
        cprint("\n⌨️ Applying code fix (cmd+')...", "cyan")
        if not send_command_apostrophe():
            cprint("❌ Failed to apply code fix!", "red")
            return False
            
        cprint("\n✨ AI Debug cycle completed! Starting next iteration... 🔄", "green")
        return True
        
    except Exception as e:
        cprint(f"\n❌ Error in AI debug submission: {str(e)}", "red")
        return False

def capture_composer_screenshot():
    """Capture screenshot of AI chat area and return file path"""
    for attempt in range(MAX_SCREENSHOT_RETRIES):
        try:
            cprint(f"\n📸 Screenshot attempt {attempt + 1}/{MAX_SCREENSHOT_RETRIES}...", "cyan")
            
            # Use the correct screenshots directory path
            screenshot_dir = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/code_runner/screenshots")
            cprint(f"\n📁 Using screenshot directory: {screenshot_dir}", "cyan")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename with timestamp and random ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import uuid
            unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
            screenshot_path = screenshot_dir / f"ai_chat_screenshot_{timestamp}_{unique_id}.png"
            cprint(f"📝 Screenshot will be saved to: {screenshot_path}", "cyan")
            
            # Debug display bounds
            displays = get_display_bounds()
            cprint("\n🖥️ Available Displays:", "cyan")
            for i, display in enumerate(displays, 1):
                cprint(f"  ├─ Display {i}: Origin({display['x']}, {display['y']}) Size({display['width']}x{display['height']})", "cyan")
            
            # Create CGImage of specified region
            cprint(f"\n📸 Capturing AI chat screenshot...", "cyan")
            cprint(f"🎯 Capture region: x={SCREENSHOT_X}, y={SCREENSHOT_Y}, width={SCREENSHOT_WIDTH}, height={SCREENSHOT_HEIGHT}", "cyan")
            
            # Ensure we have valid coordinates
            if not all(isinstance(x, (int, float)) for x in [SCREENSHOT_X, SCREENSHOT_Y, SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT]):
                raise ValueError("Invalid screenshot coordinates")
            
            region = CG.CGRectMake(
                float(SCREENSHOT_X),
                float(SCREENSHOT_Y),
                float(SCREENSHOT_WIDTH),
                float(SCREENSHOT_HEIGHT)
            )
            
            # Get screenshot
            cprint("📷 Attempting to capture window...", "cyan")
            screenshot = CG.CGWindowListCreateImage(
                region,
                CG.kCGWindowListOptionOnScreenOnly,
                CG.kCGNullWindowID,
                CG.kCGWindowImageDefault
            )
            
            if screenshot is None:
                raise Exception("Failed to capture screenshot - CGWindowListCreateImage returned None")
                
            cprint("✅ Screenshot captured successfully", "green")
            
            # Get dimensions
            width = int(CG.CGImageGetWidth(screenshot))
            height = int(CG.CGImageGetHeight(screenshot))
            
            if width == 0 or height == 0:
                raise ValueError(f"Invalid screenshot dimensions: {width}x{height}")
            
            cprint(f"📏 Screenshot dimensions: {width}x{height}", "cyan")
            
            # Create bitmap context
            colorspace = CG.CGColorSpaceCreateDeviceRGB()
            context = CG.CGBitmapContextCreate(
                None,
                width,
                height,
                8,  # bits per component
                0,  # bytes per row (0 = automatically calculated)
                colorspace,
                CG.kCGImageAlphaPremultipliedFirst | CG.kCGBitmapByteOrder32Little
            )
            
            if context is None:
                raise Exception("Failed to create bitmap context")
            
            # Draw the image to the context
            CG.CGContextDrawImage(context, CG.CGRectMake(0, 0, width, height), screenshot)
            
            # Get the image from the context
            final_image = CG.CGBitmapContextCreateImage(context)
            
            if final_image is None:
                raise Exception("Failed to create final image from context")
            
            # Create NSData from the image
            image_data = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(final_image)
            png_data = image_data.representationUsingType_properties_(AppKit.NSPNGFileType, None)
            
            if png_data is None:
                raise Exception("Failed to create PNG data")
            
            # Write to file
            success = png_data.writeToFile_atomically_(str(screenshot_path), True)
            
            if not success:
                raise Exception("Failed to write PNG data to file")
            
            if not screenshot_path.exists():
                raise Exception("Screenshot file was not created")
                
            file_size = screenshot_path.stat().st_size
            if file_size == 0:
                raise Exception("Screenshot file is empty")
                
            cprint(f"✨ Screenshot saved successfully: {screenshot_path}", "green")
            cprint(f"📊 File size: {file_size} bytes", "cyan")
            
            # Verify the file can be read back
            try:
                with open(screenshot_path, 'rb') as f:
                    test_read = f.read(1024)
                    if not test_read:
                        raise Exception("Screenshot file is unreadable")
            except Exception as e:
                raise Exception(f"Failed to verify screenshot file: {str(e)}")
            
            return str(screenshot_path)
            
        except Exception as e:
            cprint(f"❌ Error capturing screenshot (attempt {attempt + 1}): {str(e)}", "red")
            cprint("📋 Full error details:", "red")
            cprint(traceback.format_exc(), "red")
            
            if attempt < MAX_SCREENSHOT_RETRIES - 1:
                cprint(f"😴 Waiting {SCREENSHOT_RETRY_DELAY} seconds before retry...", "yellow")
                time.sleep(SCREENSHOT_RETRY_DELAY)
            else:
                cprint("❌ All screenshot attempts failed!", "red")
                return None
    
    return None

def analyze_composer_screenshot(screenshot_path: str) -> bool:
    """Analyze AI chat screenshot using GPT-4 Vision"""
    try:
        cprint("\n🔍 Analyzing AI chat screenshot...", "cyan")
        
        # Get model instance from factory
        model = model_factory.get_model(MODEL_TYPE, MODEL_NAME)
        if not model:
            cprint("❌ Failed to get GPT-4 Vision model!", "red")
            return False
            
        # Read image file as base64
        with open(screenshot_path, "rb") as image_file:
            import base64
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Create message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": AI_CHAT_SCREENSHOT_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        cprint("📤 Sending image to OpenAI for analysis...", "cyan")
        
        # Get response
        response = model.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=10
        )
        
        # Parse response
        result = response.choices[0].message.content.strip().lower()
        cprint(f"🤖 GPT-4 Analysis Result: {result}", "cyan")
        
        return result == "true"
        
    except Exception as e:
        cprint(f"❌ Error analyzing screenshot: {str(e)}", "red")
        import traceback
        cprint("📋 Full error details:", "red")
        cprint(traceback.format_exc(), "red")
        return False

def execute_and_capture():
    """Move to position, execute code, and capture screenshot"""
    try:
        cprint("\n🎯 Moon Dev's Code Executor Starting...", "cyan")
        
        # Store initial position
        initial_pos = CG.CGEventGetLocation(CG.CGEventCreate(None))
        
        # Add first run flag
        first_run = True
        
        # Main execution loop
        while True:
            try:
                # 1. Move to code editor & run code
                cprint(f"\n🖱️ Moving to code editor ({CODE_EDITOR_X}, {CODE_EDITOR_Y})", "cyan")
                if not move_mouse_cg(CODE_EDITOR_X, CODE_EDITOR_Y):
                    cprint("❌ Failed to move to code editor!", "red")
                    continue
                    
                time.sleep(0.5)
                if not quick_click():
                    cprint("❌ Failed to click code editor!", "red")
                    continue
                
                # Only apply fix (cmd+') if not first run
                if not first_run:
                    time.sleep(0.5)
                    cprint("\n⌨️ Applying fix (cmd+')...", "cyan")
                    if not send_command_apostrophe():
                        cprint("❌ Failed to apply fix!", "red")
                        continue
                    time.sleep(1.0)
                
                # Send cmd+return to run code
                cprint("\n⌨️ Running code (cmd+return)...", "cyan")
                if not send_command_return():
                    cprint("❌ Failed to run code!", "red")
                    continue
                
                # Set first_run to false after first iteration
                first_run = False
                
                # Wait for code execution
                time.sleep(EXECUTE_PAUSE)
                
                # 2. Move to terminal & select all error
                cprint("\n🖱️ Moving to terminal output...", "cyan")
                if not move_mouse_cg(TERMINAL_X, TERMINAL_Y):
                    cprint("❌ Failed to move to terminal!", "red")
                    continue
                    
                time.sleep(0.5)
                if not quick_click():
                    cprint("❌ Failed to click terminal!", "red")
                    continue
                
                # Select all (cmd+a) and paste to composer (cmd+i)
                time.sleep(0.5)
                try:
                    # Send cmd+a
                    cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)
                    CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
                    time.sleep(0.1)
                    
                    a_down = CG.CGEventCreateKeyboardEvent(None, 0x00, True)
                    a_up = CG.CGEventCreateKeyboardEvent(None, 0x00, False)
                    CG.CGEventSetFlags(a_down, CG.kCGEventFlagMaskCommand)
                    CG.CGEventSetFlags(a_up, CG.kCGEventFlagMaskCommand)
                    
                    CG.CGEventPost(CG.kCGHIDEventTap, a_down)
                    time.sleep(0.1)
                    CG.CGEventPost(CG.kCGHIDEventTap, a_up)
                    
                    cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
                    CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)
                    
                    time.sleep(0.5)
                    
                    # Send cmd+i
                    cmd_down = CG.CGEventCreateKeyboardEvent(None, 0x37, True)
                    CG.CGEventPost(CG.kCGHIDEventTap, cmd_down)
                    time.sleep(0.1)
                    
                    i_down = CG.CGEventCreateKeyboardEvent(None, 0x22, True)
                    i_up = CG.CGEventCreateKeyboardEvent(None, 0x22, False)
                    CG.CGEventSetFlags(i_down, CG.kCGEventFlagMaskCommand)
                    CG.CGEventSetFlags(i_up, CG.kCGEventFlagMaskCommand)
                    
                    CG.CGEventPost(CG.kCGHIDEventTap, i_down)
                    time.sleep(0.1)
                    CG.CGEventPost(CG.kCGHIDEventTap, i_up)
                    
                    cmd_up = CG.CGEventCreateKeyboardEvent(None, 0x37, False)
                    CG.CGEventPost(CG.kCGHIDEventTap, cmd_up)

                    # Add pause to ensure cmd+i completes
                    time.sleep(1.0)
                    
                    # Move back to cursor position
                    cprint("\n🖱️ Moving back to AI chat position...", "cyan")
                    if not move_mouse_cg(AI_CHAT_X, AI_CHAT_Y):
                        cprint("❌ Failed to move to AI chat position!", "red")
                        return False
                        
                    time.sleep(0.5)
                    if not quick_click():
                        cprint("❌ Failed to click AI chat position!", "red")
                        return False
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    cprint(f"❌ Error sending keyboard commands: {e}", "red")
                    return False
                
                # Type fix prompt
                cprint("\n⌨️ Typing fix prompt...", "cyan")
                if not send_keys(CODE_FIX_PROMPT):
                    cprint("❌ Failed to type fix prompt!", "red")
                    return False
                
                # Send enter
                time.sleep(0.3)
                if not send_enter():
                    cprint("❌ Failed to send fix prompt!", "red")
                    return False
                
                # 4. Wait for AI response
                cprint(f"\n⏳ Waiting {WAIT_AI_FIX_SECONDS} seconds for AI response...", "yellow")
                time.sleep(WAIT_AI_FIX_SECONDS)
                
                # Take and analyze screenshot of AI chat area
                screenshot_path = capture_composer_screenshot()
                if not screenshot_path:
                    cprint("❌ Failed to capture AI chat screenshot!", "red")
                    continue
                
                # Check for completion
                if analyze_composer_screenshot(screenshot_path):
                    cprint("\n✨ Task completed! Found 20+ emojis!", "green")
                    cprint("👋 Moon Dev's Code Executor shutting down...", "yellow")
                    return
                
                # Not complete - move to code editor & apply fix
                cprint("\n🔄 No completion emojis found, applying fix...", "cyan")
                
                # Move to code editor
                if not move_mouse_cg(CODE_EDITOR_X, CODE_EDITOR_Y):
                    cprint("❌ Failed to move to code editor!", "red")
                    continue
                
                # Click to activate window
                time.sleep(0.5)
                if not quick_click():
                    cprint("❌ Failed to activate code editor!", "red")
                    continue
                
                # Apply fix with cmd+'
                time.sleep(0.5)
                cprint("\n⌨️ Applying fix (cmd+')...", "cyan")
                if not send_command_apostrophe():
                    cprint("❌ Failed to apply fix!", "red")
                    continue
                
                # Run the code with cmd+return
                time.sleep(1.0)
                cprint("\n⌨️ Running updated code (cmd+return)...", "cyan")
                if not send_command_return():
                    cprint("❌ Failed to run updated code!", "red")
                    continue
                
                cprint("\n✨ Fix applied and code running! Starting next iteration... 🔄", "green")
                time.sleep(EXECUTE_PAUSE)  # Wait for code execution
                
                continue  # Start next iteration
                
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                cprint(f"\n❌ Loop iteration error: {str(e)}", "red")
                time.sleep(2.0)
                continue
        
    except KeyboardInterrupt:
        cprint("\n👋 Execution cancelled by user", "yellow")
        try:
            move_mouse_cg(int(initial_pos.x), int(initial_pos.y))
        except:
            pass
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
        try:
            move_mouse_cg(int(initial_pos.x), int(initial_pos.y))
        except:
            pass

if __name__ == "__main__":
    try:
        # Check if pyobjc-framework-Quartz is installed
        try:
            import Quartz
        except ImportError:
            cprint("\n❌ Quartz framework not found. Installing required package...", "yellow")
            os.system("pip install pyobjc-framework-Quartz")
            cprint("✅ Installation complete. Please run the script again.", "green")
            sys.exit(1)
            
        execute_and_capture()
    except KeyboardInterrupt:
        cprint("\n👋 Execution cancelled by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
