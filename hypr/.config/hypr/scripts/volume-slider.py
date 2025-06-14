#!/usr/bin/env python3

import subprocess
import os
import sys
import shutil

VOLUME_FILE = "/tmp/volume_pre_mute"
NOTIFY_ID = 12345  # Unique ID for replacing notifications


def run_command(command):
    try:
        return subprocess.check_output(command, text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def get_default_sink():
    output = run_command(["pactl", "info"])
    for line in output.splitlines():
        if "Default Sink:" in line:
            return line.split(":")[1].strip()
    return None


def get_volume(sink):
    output = run_command(["pactl", "get-sink-volume", sink])
    if output:
        for line in output.splitlines():
            if "/" in line:
                try:
                    return int(line.split("/")[1].strip().replace("%", ""))
                except ValueError:
                    pass
    return 0


def get_mute(sink):
    output = run_command(["pactl", "get-sink-mute", sink])
    return output.split()[-1] == "yes" if output else False


def cap_volume(sink):
    current_vol = get_volume(sink)
    if current_vol > 100:
        subprocess.run(["pactl", "set-sink-volume", sink, "100%"])


def send_notification(vol):
    icon = "󰝟" if vol == 0 else "󰖀" if vol < 50 else "󰕾"
    subprocess.run([
        "notify-send", "-r", str(NOTIFY_ID), "-u", "normal", "-t", "2000",
        "-h", "string:x-canonical-private-synchronous:volume",
        "-h", f"int:value:{min(vol, 100)}", "Volume", f"{icon} {min(vol, 100)}%"
    ])


def adjust_volume(sink, direction):
    if get_mute(sink):
        if direction == "down":
            send_notification(0)
            return
        subprocess.run(["pactl", "set-sink-mute", sink, "0"])
        prev_vol = 5
        if os.path.exists(VOLUME_FILE):
            with open(VOLUME_FILE) as f:
                try:
                    prev_vol = max(int(f.read().strip()), 5)
                except ValueError:
                    pass
        subprocess.run(["pactl", "set-sink-volume", sink, f"{prev_vol}%"])
        cap_volume(sink)
        send_notification(prev_vol)
        return

    if direction == "up":
        subprocess.run(["pactl", "set-sink-volume", sink, "+5%"])
    else:
        subprocess.run(["pactl", "set-sink-volume", sink, "-5%"])

    cap_volume(sink)
    new_vol = get_volume(sink)
    if new_vol == 0:
        with open(VOLUME_FILE, "w") as f:
            f.write("0")
        subprocess.run(["pactl", "set-sink-mute", sink, "1"])
        send_notification(0)
    else:
        send_notification(new_vol)


def toggle_mute(sink):
    if not get_mute(sink):
        current_vol = get_volume(sink)
        with open(VOLUME_FILE, "w") as f:
            f.write(str(current_vol))
        subprocess.run(["pactl", "set-sink-mute", sink, "1"])
        send_notification(0)
    else:
        subprocess.run(["pactl", "set-sink-mute", sink, "0"])
        prev_vol = 50
        if os.path.exists(VOLUME_FILE):
            with open(VOLUME_FILE) as f:
                try:
                    prev_vol = int(f.read().strip())
                except ValueError:
                    pass
        cap_volume(sink)
        send_notification(prev_vol)


def main():
    if not shutil.which("pactl") or not shutil.which("notify-send"):
        print("Error: 'pactl' and/or 'notify-send' not found in PATH.")
        sys.exit(1)

    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    sink = get_default_sink()

    if not sink:
        subprocess.run(["notify-send", "Volume Control", "No active audio sink found!", "-u", "critical"])
        sys.exit(1)

    if action in ["up", "down"]:
        adjust_volume(sink, action)
    elif action == "mute":
        toggle_mute(sink)
    else:  # status
        current_vol = get_volume(sink)
        send_notification(current_vol)


if __name__ == "__main__":
    main()

