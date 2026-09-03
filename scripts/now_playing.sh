#!/bin/bash

# Priority order: prefer music apps over browsers
preferred_players="spotify mpv firefox chromium"

# Find the first actually-playing player
playing_player=""
for player in $preferred_players; do
    if playerctl -p "$player" status 2>/dev/null | grep -q "Playing"; then
        playing_player="$player"
        break
    fi
done

# Fallback: check all players if none in preferred list is playing
if [ -z "$playing_player" ]; then
    while IFS= read -r player; do
        if playerctl -p "$player" status 2>/dev/null | grep -q "Playing"; then
            playing_player="$player"
            break
        fi
    done < <(playerctl -l 2>/dev/null)
fi

# No player is playing
if [ -z "$playing_player" ]; then
    echo " "
    exit 0
fi

# Get metadata from the playing player
data=$(playerctl -p "$playing_player" metadata --format '{{playerName}}|{{artist}}|{{title}}' 2>/dev/null)
if [ -z "$data" ]; then
    echo " "
    exit 0
fi

IFS='|' read -r player artist title <<< "$data"

case "$player" in
    spotify*) icon="" ;;
    firefox*) icon="" ;;
    mpv*)     icon="" ;;
    *)        icon="" ;;
esac

if [ -n "$artist" ]; then
    output="$icon $artist - $title"
else
    output="$icon $title"
fi

echo " $(echo "$output" | cut -c 1-50) "
