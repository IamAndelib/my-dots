#!/usr/bin/env python3

import subprocess
import sys
import shutil

NOTIFY_ID = 2


def run_command(command):
    try:
        return subprocess.check_output(command, text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def get_brightness():
    output = run_command(["brightnessctl"])
    for part in output.split():
        if part.startswith("(") and part.endswith("%)"):
            try:
                return int(part.strip("()%"))
            except ValueError:
                pass
    return 0


def get_raw_brightness():
    current = run_command(["brightnessctl", "get"])
    maximum = run_command(["brightnessctl", "max"])
    try:
        return int(current), int(maximum)
    except ValueError:
        return 0, 100


def set_brightness(value):
    subprocess.run(["brightnessctl", "set", value])


def send_notification(percent):
    if percent <= 15:
        icon = "󰃞"
    elif percent <= 50:
        icon = "󰃟"
    else:
        icon = "󰃠"

    subprocess.run([
        "notify-send", "-r", str(NOTIFY_ID), "-u", "normal",
        "-h", "string:x-canonical-private-synchronous:brightness",
        "-h", f"int:value:{percent}",
        "Brightness", f"{icon} {percent}%"
    ])


def main():
    if not shutil.which("brightnessctl") or not shutil.which("notify-send"):
        print("Error: 'brightnessctl' and/or 'notify-send' not found.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: brightness_control.py [+ | - | <value>%]")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "+":
        set_brightness("+5%")
    elif arg == "-":
        current, maximum = get_raw_brightness()
        percent = int((current * 100) / maximum) if maximum else 0
        if percent <= 10:
            set_brightness("5%")
        else:
            set_brightness("5%-")
    else:
        set_brightness(arg)

    brightness = get_brightness()
    send_notification(brightness)


if __name__ == "__main__":
    main()

