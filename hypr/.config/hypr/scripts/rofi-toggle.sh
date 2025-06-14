#!/bin/bash

MODE="$1"

# Function to check if any rofi instance is currently running
is_rofi_running() {
    pgrep -xu "$USER" rofi > /dev/null
}

if [ "$MODE" = "drun" ]; then
    if is_rofi_running; then
        pkill -xu "$USER" rofi
    else
        rofi -show drun -theme ~/.config/rofi/catppuccin-mocha.rasi &
    fi

elif [ "$MODE" = "clipboard" ]; then
    if is_rofi_running; then
        pkill -xu "$USER" rofi
    else
        cliphist list | rofi -dmenu -p "📋 Clipboard " -theme ~/.config/rofi/catppuccin-mocha.rasi | cliphist decode | wl-copy
    fi

else
    echo "Usage: $0 [drun|clipboard]"
    exit 1
fi
