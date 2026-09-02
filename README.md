# .suckless

My personal suckless tool configurations: dwm, slock, slstatus, st.

## Dependencies

```bash
sudo pacman -S git base-devel xorg-xinit xorg-xrandr xorg-xsetroot alacritty rofi libx11 libxinerama libxext libxrandr fontconfig freetype2 fzf zoxide eza starship
```

## Installation

```bash
git clone git@github.com:zhnrzk/zhnrzk-dwm.git ~/.suckless
```

Then build and install each tool:

```bash
cd ~/.suckless/dwm && sudo make clean install
cd ~/.suckless/slock && sudo make clean install
cd ~/.suckless/slstatus && sudo make clean install
cd ~/.suckless/st && sudo make clean install
```

Copy the config files to your home directory:

```bash
cp ~/.suckless/.xinitrc ~/.xinitrc
cp ~/.suckless/.bashrc ~/.bashrc
```

## Usage

Start X with:

```bash
startx
```
