#!/usr/bin/env bash

set -uo pipefail

# Detect session type: Wayland if WAYLAND_DISPLAY is set, otherwise X11.
if [ -n "${WAYLAND_DISPLAY:-}" ]; then
    SESSION="wayland"
else
    SESSION="x11"
fi

# --- Toggle logic: if a recording is running, stop it and save ------------
if pgrep -f "[g]pu-screen-recorder" > /dev/null; then
    pkill -SIGINT -f "[g]pu-screen-recorder"

    if [ -f /tmp/recording_saved ]; then
        SAVED_FILE=$(cat /tmp/recording_saved)
        rm -f /tmp/recording_saved
        notify-send -t 10000 -a "Screenrecorder" \
            -A "open_video=Open Video" \
            -A "open_folder=Open Folder" \
            "Recording Stopped" "Video saved:\n$SAVED_FILE"
        case $? in
            1) xdg-open "$SAVED_FILE" ;;
            2) xdg-open "$(dirname "$SAVED_FILE")" ;;
        esac
    else
        notify-send -t 3000 -a "Screenrecorder" "Recording Stopped" "Video saved to ~/Videos"
    fi
    exit 0
fi

# --- Region selection -------------------------------------------------------
case "$SESSION" in
    wayland) GEOM=$(slurp -f '%wx%h+%x+%y') ;;
    x11)     GEOM=$(slop -f '%wx%h+%x+%y') ;;
esac

# If region selection was cancelled (Esc), exit silently.
if [ -z "$GEOM" ]; then
    exit 0
fi

# --- Start recording --------------------------------------------------------
mkdir -p "$HOME/Videos"
OUTPUT="$HOME/Videos/screenrecord_$(date +%Y%m%d_%H%M%S).mp4"
echo "$OUTPUT" > /tmp/recording_saved

gpu-screen-recorder \
    -w region \
    -region "$GEOM" \
    -k h264 -q very_high -f 60 -c mp4 \
    -a default_output \
    -o "$OUTPUT" \
    >"$HOME/Videos/gpu-screen-recorder.log" 2>&1 &

sleep 1.5
if pgrep -f "[g]pu-screen-recorder" > /dev/null; then
    notify-send -t 3000 -a "Screenrecorder" "Recording Started" "Recording region. Press the same key to stop."
else
    notify-send -u critical -t 5000 -a "Screenrecorder" "Recording Failed" "Check ~/Videos/gpu-screen-recorder.log"
fi
