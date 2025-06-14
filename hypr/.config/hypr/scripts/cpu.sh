#!/bin/bash

TERMINAL="kitty"          # Or use alacritty / foot / wezterm
WORKSPACE_ID=10           # Change this to your preferred workspace

# Launch terminal with btop on a new workspace
hyprctl dispatch workspace "$WORKSPACE_ID"
hyprctl dispatch exec "$TERMINAL -e btop"

