if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
  ~/.config/hypr/scripts/start-hypr.sh
fi



