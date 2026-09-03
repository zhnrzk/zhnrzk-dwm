#!/bin/sh
python3 ~/.suckless/scripts/dwm-cheatsheet.py --list | \
	fzf --prompt="dwm keybind> " \
	    --layout=reverse \
	    --border \
	    --height=100% \
	    --info=inline \
	    --no-preview \
	    --footer=" esc: quit | j/k: scroll | Enter: select"
