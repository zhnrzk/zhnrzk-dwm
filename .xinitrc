#startupapps

# 1. Start core environment and D-Bus first
# Force-remove Sway/Wayland remnants from D-Bus/Systemd memory
systemctl --user unset-environment WAYLAND_DISPLAY
dbus-update-activation-environment --systemd --remove-variable WAYLAND_DISPLAY

# Define and export the clean X11/dwm environment
export XDG_CURRENT_DESKTOP=dwm
export XDG_SESSION_TYPE=x11
dbus-update-activation-environment --systemd DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE
systemctl --user import-environment DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE

# Kill lingering Wayland portals so they don't intercept screenshot/screencast calls
systemctl --user stop xdg-desktop-portal-wlr 2>/dev/null

# 2. Settings and displays (Synchronous commands - NO ampersands)
xrandr --output HDMI-1 --mode 1920x1080 --rate 90 --pos 0x520 --output DP-2 --mode 1600x1200 --rate 60 --rotate left --pos 1920x0
xset r rate 200 50
xset s 300
feh --randomize --bg-fill /home/zhnrzk/Pictures/wallz/*

# 3. Background Services and Daemons (Persistent commands - WITH ampersands)
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
dunst &
picom -b
slstatus &
xss-lock -- slock &
gpu-screen-recorder &

# Start Flameshot LAST, and explicitly bypass the GTK portal restriction
export GTK_USE_PORTAL=1
GTK_USE_PORTAL=0 flameshot &
caffeine &

# 4. Start Window Manager (with error logging enabled)
exec dwm > ~/.dwm.log 2>&1
