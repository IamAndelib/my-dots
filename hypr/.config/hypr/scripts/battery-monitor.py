#!/usr/bin/env python3

import time
import subprocess
from pathlib import Path
import sys
from typing import Optional

# === CONFIG ===
BATTERY_PATH = Path("/sys/class/power_supply/BAT0")
LOW = 20
CRITICAL = 10
SUFFICIENT = 90
NOTIFY_SOUND = "/usr/share/sounds/freedesktop/stereo"

# === STATE ===
last_state = {
    "plugged": None,
    "notified_low": False,
    "notified_critical": False,
    "notified_sufficient": False,
    "notified_plugged": False,
    "notified_unplugged": False
}

DEBUG_MODE = False
DEBUG_CAPACITY = 0
DEBUG_STATUS = "Discharging"
DEBUG_PREV_STATUS = "Discharging"

# === UTILS ===
def notify(title: str, msg: str, urgency: str = "normal", sound: Optional[str] = None):
    print(f"[NOTIFY] {title}: {msg}")
    try:
        subprocess.run(["notify-send", "-u", urgency, "-t", "2000", title, msg], check=True)
        if sound:
            subprocess.Popen(["paplay", sound], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ERROR: notify] {e}")

def read_battery_file(filename: str) -> str:
    try:
        return (BATTERY_PATH / filename).read_text().strip()
    except Exception:
        return ""

def get_battery_info() -> tuple[int, str]:
    if DEBUG_MODE:
        return DEBUG_CAPACITY, DEBUG_STATUS
    try:
        capacity = int(read_battery_file("capacity"))
        status = read_battery_file("status")
        return capacity, status
    except Exception:
        return 0, ""

def is_plugged(status: str) -> bool:
    return status in ("Charging", "Full")

# === MAIN LOOP ===
def main():
    if DEBUG_MODE:
        last_state["plugged"] = is_plugged(DEBUG_PREV_STATUS)

    while True:
        try:
            capacity, status = get_battery_info()
            if not status:
                time.sleep(5)
                continue

            plugged_now = is_plugged(status)
            plugged_last = last_state["plugged"]

            # === Detect Plug/Unplug Transitions ===
            if plugged_last is not None and plugged_now != plugged_last:
                if plugged_now:
                    # Plugged in
                    if not last_state["notified_plugged"]:
                        notify("⚡ Charger Connected", f"Charging started at {capacity}%", "normal", f"{NOTIFY_SOUND}/bell.oga")
                        last_state["notified_plugged"] = True
                        last_state["notified_unplugged"] = False
                        last_state["notified_low"] = False
                        last_state["notified_critical"] = False
                else:
                    # Unplugged
                    if not last_state["notified_unplugged"]:
                        notify("🔌 Charger Disconnected", f"Unplugged at {capacity}%", "normal", f"{NOTIFY_SOUND}/message.oga")
                        last_state["notified_unplugged"] = True
                        last_state["notified_plugged"] = False
                        last_state["notified_sufficient"] = False

            # === Notification Logic ===
            if plugged_now:
                # When charging, notify once if battery is sufficient
                if capacity >= SUFFICIENT and not last_state["notified_sufficient"]:
                    notify("🔋 Battery Sufficient", f"Battery at {capacity}%. Consider unplugging.", "normal", f"{NOTIFY_SOUND}/complete.oga")
                    last_state["notified_sufficient"] = True
            else:
                # When discharging, notify once if battery is low or critical
                if capacity <= CRITICAL and not last_state["notified_critical"]:
                    notify("🔴 Battery Critical", f"Battery at {capacity}%. Plug in now!", "critical", f"{NOTIFY_SOUND}/alarm-clock-elapsed.oga")
                    last_state["notified_critical"] = True
                elif CRITICAL < capacity <= LOW and not last_state["notified_low"]:
                    notify("⚠️ Battery Low", f"Battery at {capacity}%. Please charge.", "normal", f"{NOTIFY_SOUND}/message.oga")
                    last_state["notified_low"] = True

            # Update last plugged status
            last_state["plugged"] = plugged_now
            time.sleep(5 if not DEBUG_MODE else 1)

        except KeyboardInterrupt:
            print("Battery monitor stopped.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(5)

# === ENTRY POINT ===
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--debug":
        DEBUG_MODE = True
        try:
            DEBUG_CAPACITY = int(sys.argv[2])
            DEBUG_STATUS = sys.argv[3] if len(sys.argv) > 3 else "Discharging"
            DEBUG_PREV_STATUS = sys.argv[4] if len(sys.argv) > 4 else "Discharging"
            print(f"[DEBUG] Starting with capacity={DEBUG_CAPACITY}, status={DEBUG_STATUS}, prev_status={DEBUG_PREV_STATUS}")
        except Exception:
            print("Usage: ./battery_monitor.py --debug <capacity> <status> <prev_status>")
            sys.exit(1)
    main()

