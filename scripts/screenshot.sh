#!/usr/bin/env bash
set -euo pipefail

tmp="$(mktemp --suffix=.png)"
trap 'rm -f "$tmp"' EXIT

grim -g "$(slurp)" "$tmp" || exit 1

wl-copy < "$tmp"

action="$(notify-send -A default="Save" -a "Screenshot" \
    "Copied to clipboard" "Click to save, or ignore (copied to clipboard)")"

if [ "$action" = "default" ]; then
    mkdir -p "$HOME/Pictures/Screenshots"
    dest="$HOME/Pictures/Screenshots/screenshot-$(date +%Y%m%d-%H%M%S).png"
    mv "$tmp" "$dest"
    ACTION="$(notify-send -t 10000 -a "Screenshot" \
        -A "default=Open Folder" \
        "Saved" "$dest")"
    if [ "$ACTION" = "default" ]; then
        xdg-open "$(dirname "$dest")"
    fi
fi
