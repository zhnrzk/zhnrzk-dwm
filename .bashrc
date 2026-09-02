#
# ~/.bashrc
#

# add ~/.local/bin (user scripts like theme-switch)
export PATH="$HOME/.local/bin:$PATH"

alias startw='sway'

eval "$(fzf --bash)"
eval "$(zoxide init bash)"
eval "$(starship init bash)"

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='eza -lh --icons --color=always --group-directories-first'

#alias ld='eza -lD'
#alias lf='eza -lF --color=always | grep -v /'
#alias lh='eza -dl .* --group-directories-first'
#alias ll='eza -al --group-directories-first'
#alias ls='eza -alF --color=always --sort=size | grep -v /'
#alias lt='eza -al --sort=modified'
alias cdwm="vim ~/.suckless/dwm/config.h"
alias mdwm="cd ~/.suckless/dwm; sudo make clean install; cd -";
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '
alias tsui='alacritty --class floating_window -e tsui'

eval "$(zoxide init --cmd cd bash)"

if [ -z "$XDG_DATA_DIRS" ]; then
    export XDG_DATA_DIRS="/usr/local/share:/usr/share"
fi
export XDG_DATA_DIRS="$HOME/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:$XDG_DATA_DIRS"
