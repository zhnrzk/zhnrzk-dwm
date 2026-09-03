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
    notify-send -a Screenshot "Saved" "$dest"
fi
