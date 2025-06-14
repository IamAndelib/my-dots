#!/bin/bash
# Start Hyprland in background
Hyprland &
# Wait until Hyprland is ready
while ! pgrep -x Hyprland >/dev/null; do
    sleep 0.5
done
# Optionally wait for the XDG_SESSION_TYPE to be set properly
while [ -z "$XDG_SESSION_TYPE" ]; do
    sleep 0.5
done
# Wait a bit more to ensure the compositor is fully ready
sleep 1
# Start hyprlock
hyprlock
