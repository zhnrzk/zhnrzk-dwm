
if [ "$(dunstctl is-paused)" = "true" ]; then
    # Unpause first, then send the notification
    dunstctl set-paused false
    notify-send "Notifications" "Enabled (Normal Mode)" -i dialog-information
else
    # Send the notification first (so it's seen), then pause
    notify-send "Notifications" "Suspended (Do Not Disturb)" -i dialog-warning
    # Give dunst a split second to display it before freezing
    dunstctl set-paused true
fi
