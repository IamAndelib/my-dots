#!/bin/bash
TEMP=$(sensors | awk '/Tdie|Package|Composite/ {print $2}' | head -n1 | tr -d '+°C')
COLOR="#b4befe" # Default @lavender

if [ "$TEMP" -ge 50 ]; then COLOR="#fab387" # @peach
elif [ "$TEMP" -ge 65 ]; then COLOR="#f38ba8" # @red
fi

echo "{\"text\":\" $TEMP°C\", \"class\":\"temp\", \"alt\":\"$COLOR\"}"
