#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import urllib.parse
import shutil

ROFI_THEME = os.path.expanduser("~/.config/rofi/catppuccin-mocha.rasi")

def is_rofi_running():
    """Check if rofi is already running"""
    try:
        result = subprocess.run(['pgrep', '-x', 'rofi'], capture_output=True)
        return result.returncode == 0
    except:
        return False

def kill_rofi():
    """Kill rofi if running"""
    try:
        subprocess.run(['pkill', '-x', 'rofi'], check=False)
    except:
        pass

def rofi_dmenu(prompt, options=None, lines=None):
    """Run rofi dmenu with given prompt and options"""
    cmd = [
        'rofi', '-dmenu',
        '-p', prompt,
        '-theme', ROFI_THEME
    ]
    if lines:
        cmd.extend(['-lines', str(lines)])

    try:
        if options:
            result = subprocess.run(cmd, input=options, text=True, capture_output=True)
        else:
            result = subprocess.run(cmd, text=True, capture_output=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except:
        return None

def open_browser(url):
    """Open URL in browser"""
    try:
        subprocess.run(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def type_prompt(text):
    """Type prompt using xdotool"""
    if shutil.which('xdotool'):
        try:
            time.sleep(1)
            subprocess.run(['xdotool', 'search', '--sync', '--onlyvisible', '--class', 'browser', 'windowactivate', '--sync'], check=False)
            subprocess.run(['xdotool', 'type', '--delay', '20', text], check=False)
            subprocess.run(['xdotool', 'key', 'Return'], check=False)
        except:
            pass
    else:
        subprocess.run(['notify-send', 'AI Search', 'Install xdotool for automatic prompt insertion'], check=False)

def main():
    # Kill rofi if already running
    if is_rofi_running():
        kill_rofi()
        sys.exit(0)

    # Define main search options
    search_options = "🌐 Google\n🤖 ChatGPT"

    # Run rofi prompt with search options
    selection = rofi_dmenu("🔍 Search ", search_options)

    if not selection:
        sys.exit(0)

    # Extract command prefix and query
    parts = selection.split(' ', 1)
    prefix = parts[0]
    query = parts[1].strip() if len(parts) > 1 else ""

    if prefix == '🌐' or selection.startswith('🌐 Google'):
        if not query or query.lower() == 'google':
            query = rofi_dmenu("Google Search:")
        if not query:
            sys.exit(0)
        encoded_query = urllib.parse.quote_plus(query)
        open_browser(f"https://www.google.com/search?q={encoded_query}")

    elif prefix == '🤖' or selection.startswith('🤖 ChatGPT'):
        if not query or query.lower() == 'chatgpt' or query.isspace():
            prompt = rofi_dmenu("Ask ChatGPT:", lines=3)
            if not prompt:
                sys.exit(0)
            encoded_prompt = urllib.parse.quote_plus(prompt)
            open_browser(f"https://chat.openai.com/?q={encoded_prompt}")
        else:
            encoded_query = urllib.parse.quote_plus(query)
            open_browser(f"https://chat.openai.com/?q={encoded_query}")

    else:
        # Default to Google search
        encoded_selection = urllib.parse.quote_plus(selection)
        open_browser(f"https://www.google.com/search?q={encoded_selection}")

if __name__ == "__main__":
    main()

