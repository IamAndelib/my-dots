#!/bin/bash

# Usage: launch-network-tool.sh bluetooth
#        launch-network-tool.sh wifi

TERMINAL="kitty --class floating -e"

case "$1" in
  bluetooth)
    $TERMINAL bluetuith
    ;;
  wifi)
    $TERMINAL nmtui
    ;;
  *)
    echo "Usage: $0 {bluetooth|wifi}"
    exit 1
    ;;
esac
