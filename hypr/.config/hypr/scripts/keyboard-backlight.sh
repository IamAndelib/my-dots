#!/bin/bash

# Get current brightness value
current=$(brightnessctl -d '*::kbd_backlight' g)
max=$(brightnessctl -d '*::kbd_backlight' m)

# Calculate thresholds
mid=$((max / 2))

# Cycle: 0 → mid → max → 0
if [ "$current" -eq 0 ]; then
    brightnessctl -d '*::kbd_backlight' set "$mid"
elif [ "$current" -lt "$max" ]; then
    brightnessctl -d '*::kbd_backlight' set "$max"
else
    brightnessctl -d '*::kbd_backlight' set 0
fi

