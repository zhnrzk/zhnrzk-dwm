#!/bin/sh

FLAG_FILE="$HOME/.config/slock-disabled"

if [ -f "$FLAG_FILE" ]; then
    rm "$FLAG_FILE"
    xset s 300     # Restore your 5-minute timeout
    notify-send "Screen Lock" "Enabled (5m)"
else
    touch "$FLAG_FILE"
    xset s off     # Disable the X screensaver timer completely
    notify-send "Screen Lock" "Suspended"
fi
