#!/usr/bin/env python3

import subprocess
import sys
import os

def is_rofi_running():
    """Check if rofi is already running"""
    try:
        result = subprocess.run(['pgrep', '-x', 'rofi'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False

def kill_rofi():
    """Kill running rofi processes"""
    try:
        subprocess.run(['pkill', 'rofi'], check=False)
    except subprocess.SubprocessError:
        pass

def show_rofi_menu(options):
    """Display rofi menu and return selected option"""
    # Create input for rofi
    menu_input = '\n'.join(options)
    
    # Rofi command with all the original parameters plus enter key binding
    rofi_cmd = [
        'rofi', '-dmenu',
        '-theme', os.path.expanduser('~/.config/rofi/power-menu.rasi'),
        '-location', '3',
        '-yoffset', '45',
        '-xoffset', '-20',
        '-i',
        '-kb-accept-entry', 'Return,MousePrimary',  # Added Return key
        '-kb-row-select', 'MouseSecondary',
        '-me-select-entry', '',
        '-me-accept-entry', 'MousePrimary',
        '-hover-select',
        '-p', 'Power-Menu:'
    ]
    
    try:
        result = subprocess.run(rofi_cmd, 
                              input=menu_input, 
                              text=True, 
                              capture_output=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except subprocess.SubprocessError:
        return None

def execute_action(selected):
    """Execute the selected power action"""
    if not selected:
        return
    
    try:
        if 'Shutdown' in selected:
            subprocess.run(['systemctl', 'poweroff'], check=True)
        elif 'Reboot' in selected:
            subprocess.run(['systemctl', 'reboot'], check=True)
        elif 'Lock' in selected:
            subprocess.run(['hyprlock'], check=True)
        elif 'Logout' in selected:
            # Create the touch file
            with open('/tmp/hyprlock_after_login', 'w') as f:
                pass
            
            # Kill Hyprland
            subprocess.run(['killall', '-q', 'Hyprland'], check=False)
            
            # Get current TTY and kill processes
            try:
                tty_result = subprocess.run(['ps', '-o', 'tty=', '-p', str(os.getpid())], 
                                          capture_output=True, text=True)
                if tty_result.returncode == 0:
                    tty = tty_result.stdout.strip().replace('/dev/tty', '')
                    if tty:
                        subprocess.run(['pkill', '-9', '-t', tty], check=False)
            except subprocess.SubprocessError:
                pass
        else:
            sys.exit(1)
    except subprocess.SubprocessError as e:
        print(f"Error executing action: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Toggle: close Rofi if it's already open
    if is_rofi_running():
        kill_rofi()
        sys.exit(0)
    
    # Menu options with icons
    options = [
        "󰐥 Shutdown",
        "󰜉 Reboot", 
        "󰤄 Lock",
        "󰗽 Logout"
    ]
    
    # Show Rofi menu
    selected = show_rofi_menu(options)
    
    # Handle selection
    execute_action(selected)

if __name__ == "__main__":
    main()
