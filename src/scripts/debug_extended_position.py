"""
🌙 Moon Dev's Extended Position Debug Script
Shows all available fields in the position object
"""
import sys
from pathlib import Path
from termcolor import cprint

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src import nice_funcs_extended as extended

def debug_position():
    """Debug Extended position object"""
    cprint("\n🔍 Moon Dev's Extended Position Debugger\n", "white", "on_blue")

    try:
        # Get the API instance directly
        api = extended.api
        if api is None:
            cprint("❌ Extended API not initialized", "red")
            return

        # Get account info
        cprint("📊 Getting account info...", "yellow")
        account_info = api.get_account_info()

        positions = account_info['positions'].data

        if not positions:
            cprint("❌ No positions found", "red")
            return

        for pos in positions:
            cprint(f"\n{'='*70}", "cyan")
            cprint(f"🎯 Position Object Attributes:", "cyan", attrs=['bold'])
            cprint(f"{'='*70}", "cyan")

            # Show all attributes
            for attr in dir(pos):
                if not attr.startswith('_'):
                    try:
                        value = getattr(pos, attr)
                        if not callable(value):
                            cprint(f"  {attr}: {value}", "white")
                    except:
                        pass

            cprint(f"\n{'='*70}", "green")
            cprint(f"🔍 Raw Position Data:", "green", attrs=['bold'])
            cprint(f"{'='*70}", "green")
            cprint(f"{pos}", "white")

    except Exception as e:
        cprint(f"❌ Error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_position()
