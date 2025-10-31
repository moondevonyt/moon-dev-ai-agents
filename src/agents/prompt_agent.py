'''
🌙 Moon Dev's Prompt Enhancement Agent 🌙

This agent takes your basic prompts and transforms them into professional,
high-quality prompts using best practices from top prompt design resources.

## What It Does
- Takes your raw prompt as input
- Applies prompt design best practices from Parahelp & Cursor
- Returns an enhanced, production-ready prompt
- Runs continuously in interactive mode

## Design Principles Applied

### From Cursor Blog:
- Clarity over complexity (communicate like with a busy person)
- Composable components (modular, reusable sections)
- Declarative structure (clear organization)
- Context window awareness (efficient space usage)
- Pixel-perfect formatting (no extraneous whitespace)

### From Parahelp:
- Role-based prompting (assign clear identity/purpose)
- Structured formatting (markdown & XML tags)
- Explicit thinking order (guide model's reasoning)
- Important/ALWAYS keywords (highlight critical instructions)
- No else branches (enumerate all valid paths)
- Evaluation-driven (design for measurable outcomes)

## Usage
```bash
python src/agents/prompt_agent.py
```

Then paste your basic prompt and get back an enhanced version!

Created with ❤️ by Moon Dev
'''

import os
import time
import json
from datetime import datetime
from pathlib import Path
from termcolor import cprint, colored
import sys
import shutil
import textwrap
from typing import Optional
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# 🌙 Moon Dev Configuration 🌙
GLM_MODEL = "z-ai/glm-4.6"  # Zhipu AI GLM - Moon Dev's choice!
# Alternative models:
# GLM_MODEL = "meta-llama/llama-3.3-70b-instruct:free"  # Llama 3.3 70B (reliable English)
# GLM_MODEL = "deepseek/deepseek-chat"  # DeepSeek Chat

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Get terminal width for better formatting
TERM_WIDTH = shutil.get_terminal_size().columns

# Comprehensive prompt design guidelines from Parahelp & Cursor
PROMPT_DESIGN_GUIDELINES = """
# 🎯 EXPERT PROMPT DESIGN GUIDELINES

You are Moon Dev's Prompt Enhancement Expert. Your job is to take a basic user prompt
and transform it into a professional, production-ready prompt following industry best practices.

## Core Principles (Cursor Blog)

1. **Clarity Over Complexity**
   - Write like you're communicating with a busy, intelligent person
   - High-quality, extremely clear instructions beat complex LLM tricks
   - Avoid unnecessary jargon or over-engineering

2. **Structured & Composable**
   - Break prompts into modular, reusable sections
   - Use clear headers and organization
   - Make each section have a single, clear purpose

3. **Context Window Awareness**
   - Be efficient with token usage
   - Front-load the most important information
   - Remove redundant or unnecessary content

4. **Pixel-Perfect Formatting**
   - Eliminate extraneous newlines
   - Consistent indentation and spacing
   - Clean, professional appearance

## Advanced Techniques (Parahelp)

1. **Role-Based Prompting**
   - Assign a clear role/identity (e.g., "You are an expert...")
   - Define the model's purpose and expertise
   - Set expectations for behavior and output

2. **Structured Formatting**
   - Use markdown headers (##, ###) for sections
   - Use XML-like tags for special content (<instructions>, <examples>)
   - Use bullet points and numbered lists for clarity

3. **Explicit Thinking Order**
   - Tell the model HOW to think through the problem
   - Break down reasoning into steps
   - Guide the analysis process

4. **Emphasis Keywords**
   - Use "IMPORTANT:", "CRITICAL:", "ALWAYS:", "NEVER:" for key points
   - Bold (**text**) important concepts
   - Use ⚠️ emoji for warnings/critical info

5. **No Else Branches**
   - Enumerate ALL valid paths explicitly
   - Avoid vague "handle other cases" instructions
   - Be exhaustive in covering scenarios

6. **Evaluation-Driven Design**
   - Design prompts that produce measurable outputs
   - Include success criteria when relevant
   - Make outputs easy to validate

## Enhancement Process

When enhancing a prompt:

1. **Analyze the Intent**: What is the user really trying to achieve?
2. **Add Structure**: Organize into clear sections with headers
3. **Assign Role**: Give the AI a clear identity and expertise
4. **Specify Behavior**: Define exact expectations for output
5. **Add Examples**: Include examples when they clarify intent
6. **Emphasize Critical Points**: Use formatting to highlight key requirements
7. **Define Success**: What makes a good response?
8. **Remove Ambiguity**: Make every instruction explicit and clear

## Output Format

Return the enhanced prompt with:
- Clear role assignment at the top
- Structured sections with markdown headers
- Key points emphasized with bold/caps
- Examples if helpful
- Success criteria if applicable
- Professional, clean formatting

ALWAYS AT THE END OF THIS PERFECT PROMPT HAVE IT SAY "ASK ANY QUESTIONS YOU HAVE IN ORDER TO BE MORE CLEAR ABOUT THE TASK, IF YOU DONT HAVE ANY, START NOW"

⚠️ IMPORTANT: Return ONLY the enhanced prompt. Do NOT add explanations,
commentary, or meta-text. The user wants a ready-to-use prompt.
"""

def clear_line():
    """Clear the current line in the terminal"""
    print("\r" + " " * TERM_WIDTH, end="\r", flush=True)

def animate_text(text, color="yellow", bg_color="on_blue", delay=0.03):
    """Animate text with a typewriter effect"""
    clear_line()
    text = ' '.join(text.split())
    result = ""
    for char in text:
        result += char
        print("\r" + " " * len(result), end="\r", flush=True)
        print(f"\r{colored(result, color, bg_color)}", end='', flush=True)
        time.sleep(delay)
    print()

def animate_loading(duration=2, message="Processing", emoji="🌙"):
    """Show a fun loading animation"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    colors = ["cyan", "magenta", "blue", "green", "yellow"]

    end_time = time.time() + duration
    i = 0

    while time.time() < end_time:
        frame = frames[i % len(frames)]
        color = colors[(i // 3) % len(colors)]

        clear_line()
        print(f"\r{colored(f' {frame} {message} {emoji} ', color, 'on_blue')}", end="", flush=True)

        time.sleep(0.2)
        i += 1

    clear_line()

def print_banner():
    """Print the Moon Dev banner"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║  🌙 Moon Dev's Prompt Enhancement Agent 🌙                ║
║                                                            ║
║  Transform basic prompts into professional masterpieces   ║
║  Using best practices from Parahelp & Cursor              ║
╚════════════════════════════════════════════════════════════╝
"""
    cprint(banner, "cyan", attrs=['bold'])

def enhance_prompt_with_glm(user_prompt: str) -> Optional[str]:
    """
    Enhance a user's prompt using GLM with prompt design best practices

    Args:
        user_prompt: The basic prompt from the user

    Returns:
        Enhanced prompt string or None if failed
    """
    try:
        print("\n" + "=" * min(70, TERM_WIDTH))
        cprint(" 🔮 ENHANCING YOUR PROMPT 🔮 ", "white", "on_magenta")
        print("=" * min(70, TERM_WIDTH))

        cprint("\n📝 Your Original Prompt:", "yellow")
        print("─" * min(70, TERM_WIDTH))
        wrapped_prompt = textwrap.fill(user_prompt, width=min(70, TERM_WIDTH))
        cprint(wrapped_prompt, "cyan")
        print("─" * min(70, TERM_WIDTH))

        if not OPENROUTER_API_KEY:
            cprint("\n❌ OPENROUTER_API_KEY not found in .env!", "white", "on_red")
            cprint("Please add OPENROUTER_API_KEY to your .env file", "yellow")
            return None

        animate_loading(2, "Applying prompt design principles", "🧠")

        # Prepare the API request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/moon-dev-ai",
            "X-Title": "Moon Dev Prompt Enhancement Agent"
        }

        payload = {
            "model": GLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": PROMPT_DESIGN_GUIDELINES
                },
                {
                    "role": "user",
                    "content": f"Enhance this prompt following all best practices:\n\n{user_prompt}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        cprint("\n⏳ Calling AI to enhance your prompt...", "cyan")
        animate_loading(2, "AI is thinking", "🤖")

        # Make the API request
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            cprint(f"\n❌ API Error: {response.status_code}", "white", "on_red")
            cprint(f"Response: {response.text}", "red")
            return None

        # Parse the response
        response_json = response.json()
        enhanced_prompt = response_json['choices'][0]['message']['content'].strip()

        # Fallback to reasoning field if content is empty (GLM models do this)
        if not enhanced_prompt or len(enhanced_prompt) < 20:
            reasoning = response_json['choices'][0]['message'].get('reasoning', '').strip()
            if reasoning:
                cprint("\n🔄 Content field empty, extracting from reasoning...", "yellow")
                enhanced_prompt = reasoning

        # Clean up any thinking tags or markdown code blocks
        if "<think>" in enhanced_prompt and "</think>" in enhanced_prompt:
            import re
            match = re.search(r'</think>\s*(.+)', enhanced_prompt, re.DOTALL)
            if match:
                enhanced_prompt = match.group(1).strip()

        # Remove markdown code block wrappers if present
        if enhanced_prompt.startswith("```") and enhanced_prompt.endswith("```"):
            lines = enhanced_prompt.split("\n")
            enhanced_prompt = "\n".join(lines[1:-1])

        if not enhanced_prompt or len(enhanced_prompt) < 20:
            cprint("\n⚠️ AI returned empty or invalid response!", "white", "on_red")
            return None

        return enhanced_prompt

    except requests.exceptions.Timeout:
        cprint("\n❌ Request timed out after 60 seconds", "white", "on_red")
        return None
    except requests.exceptions.RequestException as e:
        cprint(f"\n❌ Request error: {str(e)}", "white", "on_red")
        return None
    except Exception as e:
        cprint(f"\n❌ Error enhancing prompt: {str(e)}", "white", "on_red")
        import traceback
        cprint(traceback.format_exc(), "red")
        return None

def display_enhanced_prompt(enhanced_prompt: str):
    """Display the enhanced prompt in a nice format"""
    print("\n" + "=" * min(70, TERM_WIDTH))
    cprint(" ✨ ENHANCED PROMPT ✨ ", "white", "on_green")
    print("=" * min(70, TERM_WIDTH))
    print()

    # Display with syntax highlighting
    for line in enhanced_prompt.split("\n"):
        if line.startswith("##"):
            cprint(line, "yellow", attrs=['bold'])
        elif line.startswith("#"):
            cprint(line, "cyan", attrs=['bold'])
        elif line.startswith("**") or "IMPORTANT" in line or "CRITICAL" in line:
            cprint(line, "white", attrs=['bold'])
        elif line.startswith("-") or line.startswith("*"):
            cprint(line, "green")
        elif line.strip().startswith("⚠️"):
            cprint(line, "red", attrs=['bold'])
        else:
            print(line)

    print("\n" + "=" * min(70, TERM_WIDTH))

def copy_to_clipboard(text: str):
    """Try to copy text to clipboard"""
    try:
        import pyperclip
        pyperclip.copy(text)
        cprint("\n📋 Enhanced prompt copied to clipboard!", "white", "on_green")
        return True
    except ImportError:
        cprint("\n💡 Tip: Install pyperclip to auto-copy enhanced prompts", "yellow")
        cprint("   pip install pyperclip", "cyan")
        return False
    except Exception:
        return False

def save_prompt_to_file(original: str, enhanced: str):
    """Save prompts to a markdown file"""
    try:
        # Create output directory
        output_dir = Path("src/data/prompt_agent")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_prompt_{timestamp}.md"
        filepath = output_dir / filename

        # Create markdown content
        content = f"""# Enhanced Prompt - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🌙 Generated by Moon Dev's Prompt Enhancement Agent 🌙

---

## Original Prompt

{original}

---

## Enhanced Prompt

{enhanced}

---

*Enhanced using best practices from Parahelp & Cursor*
"""

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        cprint(f"\n💾 Saved to: {filepath}", "cyan")
        return filepath

    except Exception as e:
        cprint(f"\n⚠️ Could not save to file: {str(e)}", "yellow")
        return None

def interactive_mode():
    """Run the agent in continuous interactive mode"""
    print_banner()

    cprint("\n💡 How it works:", "yellow", attrs=['bold'])
    cprint("   1. Type your basic prompt (blank lines are fine!)", "white")
    cprint("   2. Press Enter twice to submit", "white")
    cprint("   3. Get back a professional, enhanced prompt", "white")
    cprint("   4. Repeat!\n", "white")

    cprint("⚙️  Configuration:", "cyan", attrs=['bold'])
    cprint(f"   Model: {GLM_MODEL}", "white")
    cprint(f"   API Key: {'✓ Configured' if OPENROUTER_API_KEY else '✗ Missing'}",
           "green" if OPENROUTER_API_KEY else "red")

    if not OPENROUTER_API_KEY:
        cprint("\n❌ OPENROUTER_API_KEY not found!", "white", "on_red")
        cprint("   Add it to your .env file to continue", "yellow")
        return

    cprint("\n📝 Commands:", "magenta", attrs=['bold'])
    cprint("   Press Enter twice - Submit your prompt", "white")
    cprint("   /quit or /exit - Exit the agent", "white")
    cprint("   /help - Show this help message\n", "white")

    prompt_count = 0

    try:
        while True:
            # Prompt for input
            print("=" * min(70, TERM_WIDTH))
            cprint("PASTE YOUR PROMPT (press Enter twice when done):", "white", "on_blue", attrs=['bold'])
            print("=" * min(70, TERM_WIDTH))

            # Collect multi-line input
            lines = []
            empty_count = 0
            while True:
                try:
                    line = input()

                    # Handle commands first
                    if line.strip().lower() in ['/quit', '/exit', '/q']:
                        raise KeyboardInterrupt
                    elif line.strip().lower() == '/help':
                        cprint("\n💡 How to use:", "yellow")
                        cprint("   1. Type or paste your prompt", "white")
                        cprint("   2. Press Enter twice to submit", "white")
                        cprint("   3. Wait for enhanced version", "white")
                        cprint("   Commands: /quit, /exit, /help\n", "cyan")
                        lines = []
                        empty_count = 0
                        break

                    # Check for empty line
                    if line.strip() == "":
                        empty_count += 1
                        if empty_count >= 2 and lines:
                            # Two consecutive empty lines - submit
                            break
                        # Store empty line in prompt
                        if lines:
                            lines.append(line)
                    else:
                        # Reset empty counter on non-empty line
                        empty_count = 0
                        lines.append(line)

                except EOFError:
                    break

            if not lines:
                continue

            user_prompt = "\n".join(lines).strip()

            if not user_prompt:
                cprint("\n⚠️ Empty prompt. Please enter something to enhance.\n", "yellow")
                continue

            # Enhance the prompt
            enhanced_prompt = enhance_prompt_with_glm(user_prompt)

            if enhanced_prompt:
                prompt_count += 1

                # Try to copy to clipboard
                copy_to_clipboard(enhanced_prompt)

                # Save to file
                save_prompt_to_file(user_prompt, enhanced_prompt)

                cprint(f"\n✅ Prompt #{prompt_count} enhanced successfully!", "white", "on_green")
                cprint("Ready for your next prompt!\n", "cyan")

                # Display the enhanced prompt LAST so it's at the bottom
                display_enhanced_prompt(enhanced_prompt)
            else:
                cprint("\n❌ Failed to enhance prompt. Please try again.\n", "red")

    except KeyboardInterrupt:
        print("\n")
        cprint("=" * min(70, TERM_WIDTH), "cyan")
        cprint(" 👋 SHUTTING DOWN ", "white", "on_yellow")
        cprint("=" * min(70, TERM_WIDTH), "cyan")
        cprint(f"\n📊 Session Stats:", "yellow")
        cprint(f"   Prompts Enhanced: {prompt_count}", "white")
        cprint(f"   Saved to: src/data/prompt_agent/", "cyan")
        cprint("\n🌙 Thanks for using Moon Dev's Prompt Enhancement Agent!", "white", "on_magenta")
        cprint("🚀 May your prompts be forever clear and effective!\n", "cyan")

def main():
    """Main function"""
    interactive_mode()

if __name__ == "__main__":
    main()
