#!/usr/bin/env python3

import subprocess
import time
import os
import shutil
import sys
from pathlib import Path

TMP_FILE = Path("/tmp/bluetooth_devices.tmp")

def notify(message):
    subprocess.run(["notify-send", "-i", "bluetooth", "Bluetooth", message, "-t", "3000"])

def bluetoothctl(*args):
    try:
        output = subprocess.check_output(["bluetoothctl"] + list(args), text=True)
        return output
    except subprocess.CalledProcessError:
        return ""

def is_bluetooth_on():
    return "Powered: yes" in bluetoothctl("show")

def power_on_bluetooth():
    if not is_bluetooth_on():
        notify("Turning Bluetooth ON...")
        bluetoothctl("power", "on")
        time.sleep(2)
        if is_bluetooth_on():
            notify("Bluetooth is ON")
            return True
        else:
            notify("Failed to turn on Bluetooth")
            return False
    return True

def power_off_bluetooth():
    if is_bluetooth_on():
        notify("Turning Bluetooth OFF...")
        bluetoothctl("power", "off")
        notify("Bluetooth is OFF")
        return True
    return False

def smart_connect():
    notify("Connecting to nearby devices...")

    subprocess.run(["timeout", "5", "bluetoothctl", "scan", "on"])
    time.sleep(3)
    bluetoothctl("scan", "off")

    paired = bluetoothctl("devices", "Paired")
    if not paired.strip():
        notify("No paired devices found")
        return

    TMP_FILE.write_text(paired)

    connected = 0
    with TMP_FILE.open() as file:
        for line in file:
            parts = line.split()
            if len(parts) < 3:
                continue
            mac = parts[1]
            name = " ".join(parts[2:])
            info = bluetoothctl("info", mac)

            if "Connected: yes" in info:
                connected += 1
                continue

            result = subprocess.run(["timeout", "8", "bluetoothctl", "connect", mac],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                notify(f"✓ Connected: {name}")
                connected += 1

    TMP_FILE.unlink(missing_ok=True)

    if connected == 0:
        notify("No devices connected")
    else:
        notify(f"Connected to {connected} device(s)")

def launch_bluetuith():
    if not power_on_bluetooth():
        return

    terminals = ["kitty", "alacritty", "foot", "wezterm"]
    term = next((t for t in terminals if shutil.which(t)), None)

    if term:
        notify("Launched Bluetuith interface")
        cmd = {
            "kitty":      [term, "--class=floating", "--title=Bluetuith", "-e", "bluetuith"],
            "alacritty":  [term, "--class=floating", "--title=Bluetuith", "-e", "bluetuith"],
            "foot":       [term, "--app-id=floating", "--title=Bluetuith", "bluetuith"],
            "wezterm":    [term, "start", "--class=floating", "bluetuith"]
        }.get(term, [term, "-e", "bluetuith"])

        subprocess.Popen(cmd)
    else:
        notify("No supported terminal found.")

def show_status():
    if is_bluetooth_on():
        connected_output = bluetoothctl("devices", "Connected")
        count = len(connected_output.strip().splitlines())
        notify(f"Bluetooth ON - {count} device(s) connected")
        if count > 0:
            print("Connected devices:")
            for line in connected_output.strip().splitlines():
                name = " ".join(line.split()[2:])
                print(f"  → {name}")
    else:
        notify("Bluetooth OFF")

def check_deps():
    for dep in ["bluetoothctl", "bluetuith"]:
        if not shutil.which(dep):
            notify(f"Missing dependency: {dep}")
            print(f"Error: '{dep}' not found. Please install it.")
            sys.exit(1)

def print_help():
    print("""Usage: bluetooth_control.py [command]
Commands:
  toggle    - Toggle Bluetooth and auto-connect (default)
  on        - Turn on and connect to devices
  off       - Turn off Bluetooth
  connect   - Connect to nearby paired devices
  gui       - Launch bluetuith interface
  status    - Show current status
  help      - Show this help message
""")

def main():
    check_deps()
    command = sys.argv[1] if len(sys.argv) > 1 else "toggle"

    match command:
        case "on":
            if power_on_bluetooth():
                smart_connect()
        case "off":
            power_off_bluetooth()
        case "toggle":
            if is_bluetooth_on():
                power_off_bluetooth()
            elif power_on_bluetooth():
                smart_connect()
        case "connect":
            if power_on_bluetooth():
                smart_connect()
        case "gui" | "ui" | "interface":
            launch_bluetuith()
        case "status":
            show_status()
        case "help" | "-h" | "--help":
            print_help()
        case _:
            print(f"Unknown command: {command}")
            print_help()
            sys.exit(1)

if __name__ == "__main__":
    main()
