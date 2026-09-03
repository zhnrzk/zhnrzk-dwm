#!/usr/bin/env bash
case "$1" in
  status)
    if pgrep -x swayidle >/dev/null; then
      echo '{"text": "Zero Caffeine", "tooltip": "Zero-Caffeine (Idle Active)"}'
    else
      echo '{"text": "Caffeinated <span style='"'"'italic'"'"' weight='"'"'900'"'"' color='"'"'#df6124'"'"'>active</span>", "tooltip": "Caffeinated (Idle Inhibited)"}'
    fi
    ;;
  toggle)
    if pgrep -x swayidle >/dev/null; then
      pkill -x swayidle
    else
      swayidle -w timeout 300 'swaylock -f' timeout 600 'swaymsg "output * dpms off"' resume 'swaymsg "output * dpms on"' &
    fi
    pkill -RTMIN+10 waybar
    ;;
esac
