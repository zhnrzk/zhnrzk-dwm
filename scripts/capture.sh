
CHOICE=$(printf 'Region Screenshot\nRegion Screen Record\nFullscreen Screenshot\nFullscreen Screen Record\n' | rofi -dmenu -p "Capture")

case "$CHOICE" in
    "Region Screenshot")
        grim -g "$(slurp)" - | wl-copy
        ;;
    "Region Screen Record")
        exec "$HOME/.local/bin/screenrecord.sh"
        ;;
    "Fullscreen Screenshot")
        grim -g "$(slurp -o)" - | wl-copy
        ;;
    "Fullscreen Screen Record")
        exec "$HOME/.local/bin/fullscreen-record.sh"
        ;;
    *)
        exit 0
        ;;
esac
