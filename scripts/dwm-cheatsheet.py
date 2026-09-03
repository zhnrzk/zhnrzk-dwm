#!/usr/bin/env python3
"""dwm keybind cheatsheet TUI.

Parses dwm's config.h keys[] array and shows the keybindings in a
scrollable, searchable curses interface.
"""
import argparse
import curses
import os
import re
import sys

MODKEY_NAME = "Super"

KEY_ALIASES = {
    "XK_space": "Space",
    "XK_Return": "Enter",
    "XK_Tab": "Tab",
    "XK_comma": ",",
    "XK_period": ".",
    "XK_slash": "/",
    "XK_backslash": "\\",
    "XK_Escape": "Esc",
    "XK_BackSpace": "Backspace",
    "XK_Delete": "Delete",
    "XK_Insert": "Insert",
    "XK_Home": "Home",
    "XK_End": "End",
    "XK_Prior": "PageUp",
    "XK_Next": "PageDown",
    "XK_Up": "Up",
    "XK_Down": "Down",
    "XK_Left": "Left",
    "XK_Right": "Right",
}

MEDIA_KEYS = {
    "XF86XK_AudioRaiseVolume": "AudioRaiseVolume",
    "XF86XK_AudioLowerVolume": "AudioLowerVolume",
    "XF86XK_AudioMute": "AudioMute",
    "XF86XK_AudioPlay": "AudioPlay",
    "XF86XK_AudioNext": "AudioNext",
    "XF86XK_AudioPrev": "AudioPrev",
    "XF86XK_MonBrightnessUp": "BrightnessUp",
    "XF86XK_MonBrightnessDown": "BrightnessDown",
    "XF86XK_AudioStop": "AudioStop",
    "XF86XK_XF86_ScreenSaver": "Lock",
}

LAYOUTS = {0: "tatami (|+|)", 1: "tile ([]=)", 2: "monocle ([M])", 3: "floating (><>)"}

# Human-friendly labels for spawn command arrays (keyed by the config.h
# variable name). Overrides the auto-detected first binary.
COMMAND_DESCRIPTIONS = {
    "gemini": "Gemini (chromium app)",
    "downvol": "pamixer --decrease 5",
    "upvol": "pamixer --increase 5",
    "mutevol": "pamixer --toggle-mute",
}

# Human descriptions for dwm core functions.
FUNC_LABEL = {
    "view": "view tag",
    "toggleview": "toggle view tag",
    "tag": "send to tag",
    "toggletag": "toggle tag",
    "focusstack": "focus next client",
    "incnmaster": "change number of masters",
    "setmfact": "master factor",
    "zoom": "zoom / toggle focus layout",
    "killclient": "close window",
    "quit": "quit dwm",
    "setlayout": "set layout",
    "cyclelayout": "cycle layout",
    "togglefloating": "toggle floating",
    "togglebar": "toggle bar",
    "focusmon": "focus monitor",
    "tagmon": "send to monitor",
    "spawn": None,  # handled specially
}


def decode_key(token):
    token = token.strip()
    if token in MEDIA_KEYS:
        return MEDIA_KEYS[token]
    token = token.lstrip("XK_")
    if token in KEY_ALIASES.values():
        if token == ",":
            return ","
        if token == ".":
            return "."
    alias = KEY_ALIASES.get("XK_" + token)
    if alias:
        return alias
    if len(token) == 1:
        return token.upper()
    if len(token) == 1 and token.isalnum():
        return token.upper()
    # Camel-case split e.g. F1, AudioLowerVolume
    return token


def decode_mods(modtoken):
    mods = []
    if not modtoken:
        return []
    modtoken = modtoken.strip()
    if modtoken == "0":
        return []
    order = []
    for m in re.split(r"\|", modtoken):
        m = m.strip()
        if m in ("MODKEY", "Mod4Mask"):
            order.append("Super")
        elif m == "ControlMask":
            order.append("Ctrl")
        elif m == "ShiftMask":
            order.append("Shift")
        elif m == "Mod1Mask":
            order.append("Alt")
    # canonical order: Super, Alt, Ctrl, Shift
    for pref in ("Super", "Alt", "Ctrl", "Shift"):
        if pref in order:
            mods.append(pref)
    return mods


def fmt_keys(mods, key):
    if not mods:
        return key
    return "+".join(mods + [key])


class Entry:
    def __init__(self, keycombo, desc):
        self.keycombo = keycombo
        self.desc = desc


def clean_cmd(cmd):
    """Turn a shell command string into something readable."""
    cmd = cmd.strip()
    # Replace $HOME / literal home with ~
    home = os.path.expanduser("~")
    cmd = cmd.replace(home + "/", "~/")
    return cmd


def describe_spawn(arg, var_map):
    """arg is the {.v = ...} value for a spawn binding."""
    a = arg.strip()
    # SHCMD("...") with /bin/sh -c
    m = re.search(r'SHCMD\(\s*"(.*?)"\s*\)', a)
    if m:
        return "run: " + clean_cmd(m.group(1))
    # full command array with strings
    cmds = re.findall(r'"((?:[^"\\]|\\.)*)"', a)
    if cmds:
        for c in cmds:
            if c in ("/bin/sh", "sh", "-c"):
                continue
            return "run: " + clean_cmd(c)
        return "run: " + clean_cmd(" ".join(cmds))
    # plain variable/identifier -> resolve via var_map
    name = a.strip()
    # args arrive like ".v = rofi" or ".v =termcmd"
    m2 = re.search(r"\.v\s*=\s*(\w+)", name)
    if m2:
        name = m2.group(1)
    if name in var_map:
        return "run: " + var_map[name]
    if name and name not in ("0", ".v"):
        return "run: " + name.rstrip(",{}")
    return "run"


def describe_func(fname, arg, var_map):
    if fname == "spawn":
        return describe_spawn(arg, var_map)
    if fname == "setlayout":
        arg_clean = arg.strip()
        if arg_clean in ("0", "NULL", ".v = 0", ".v = NULL"):
            return "toggle floating layout"
        m = re.search(r"layouts\[(\d+)\]", arg_clean)
        if m:
            idx = int(m.group(1))
            return "set layout: " + LAYOUTS.get(idx, str(idx))
        if arg_clean and arg_clean not in (".v", ".v ="):
            return "set layout: " + arg_clean.rstrip(",{}")
        return "set layout"
    if fname == "cyclelayout":
        return "cycle layout" + (" backward" if ".i = -1" in arg else " forward")
    if fname in ("focusstack", "incnmaster", "setmfact", "focusmon", "tagmon"):
        if ".i = +1" in arg or ".f = +" in arg:
            direction = "+"
        elif ".i = -1" in arg or ".f = -" in arg:
            direction = "-"
        else:
            direction = ""
        base = FUNC_LABEL[fname]
        return base + ((" (" + direction + ")") if direction else "")
    if fname in FUNC_LABEL and FUNC_LABEL[fname]:
        return FUNC_LABEL[fname]
    return fname


def parse_config(config_path):
    """Parse config.h and return a list of Entry objects."""
    with open(config_path) as f:
        text = f.read()

    # Extract layouts for mapping
    # (not strictly needed since we hardcode LAYOUTS by index in config)

    # Extract the keys[] array block
    keys_block = re.search(r"static\s+const\s+Key\s+keys\[\]\s*=\s*\{(.*?)\n\};",
                           text, re.DOTALL)
    if not keys_block:
        return []

    keys_src = keys_block.group(1)

    # Handle TAGKEYS macro expansion: replace TAGKEYS(KEY, TAG) with four bindings
    # We process each line; for TAGKEYS lines we synthesize entries.
    entries = []

    # Expand TAGKEYS manually.
    def expand_tagkeys(src):
        result = src
        tagdefs = {
            "XK_1": 0, "XK_2": 1, "XK_3": 2, "XK_4": 3,
            "XK_5": 4, "XK_6": 5, "XK_7": 6, "XK_8": 7, "XK_9": 8,
        }
        for key, tag in tagdefs.items():
            expansions = [
                "{{MODKEY, {k}, view, {{.ui = 1 << {t}}}}},".format(k=key, t=tag),
                "{{MODKEY|ControlMask, {k}, toggleview, {{.ui = 1 << {t}}}}},".format(k=key, t=tag),
                "{{MODKEY|ShiftMask, {k}, tag, {{.ui = 1 << {t}}}}},".format(k=key, t=tag),
                "{{MODKEY|ControlMask|ShiftMask, {k}, toggletag, {{.ui = 1 << {t}}}}},".format(k=key, t=tag),
            ]
            pat = re.compile(r"TAGKEYS\(\s*" + re.escape(key) + r"\s*,\s*" + str(tag) + r"\s*\)")
            result = pat.sub("\n".join(expansions) + "\n", result)
        return result

    keys_src = expand_tagkeys(keys_src)

    # Build map of command variable name -> readable command.
    # e.g. static const char *termcmd[] = { "alacritty", NULL };
    var_map = {}
    for m in re.finditer(
            r'static\s+const\s+char\s*\*\s*(\w+)\s*\[\]\s*=\s*\{([^}]*)\}',
            text):
        name = m.group(1)
        body = m.group(2)
        cmds = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
        if not cmds:
            continue
        if name in COMMAND_DESCRIPTIONS:
            var_map[name] = COMMAND_DESCRIPTIONS[name]
            continue
        # skip shell shim elements, use first real program
        real = None
        for c in cmds:
            if c in ("/bin/sh", "sh", "-c"):
                continue
            real = c
            break
        if real:
            var_map[name] = clean_cmd(real)
        else:
            var_map[name] = clean_cmd(cmds[0] if cmds else name)

    # Now parse each { ... } struct literal within keys[]
    # Each binding: { MOD, KEY, func, {arg} }
    # We split on '},' boundaries that are at brace depth 1.
    bindings = split_bindings(keys_src)

    for b in bindings:
        # A binding: { MOD, KEY, func, {arg} }  OR  { MOD, KEY, func, SHCMD("...") }
        m = re.match(
            r"\s*\{\s*(.*?)\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*"
            r"(?:\{(.*?)\}|SHCMD\(\s*\"(.*?)\"\s*\))\s*\}",
            b, re.DOTALL)
        if not m:
            continue
        mods_s, key_s, fn_s = m.group(1), m.group(2), m.group(3)
        arg_s = m.group(4)
        shcmd = m.group(5)
        if shcmd is not None:
            arg_s = 'SHCMD("' + shcmd + '")'
        mods = decode_mods(mods_s)
        key = decode_key(key_s)
        fn = fn_s.strip()
        combo = fmt_keys(mods, key)
        desc = describe_func(fn, arg_s, var_map)
        entries.append(Entry(combo, desc))

    return collapse_tag_entries(entries)


def collapse_tag_entries(entries):
    """Group the per-tag 1..9 bindings (view/toggleview/tag/toggletag) into
    four compact rows using a key range. Each binding is MODKEY+[Ctrl]+[Shift]
    plus a numeric key 1..9; we merge the numeric key into '1..9'."""
    tag_keys = [str(n) for n in range(1, 10)]
    kept = []
    groups = {}
    order = []
    for e in entries:
        parts = e.keycombo.split("+")
        mods, key = parts[:-1], parts[-1]
        if key in tag_keys:
            sig = tuple(mods)
            if sig not in groups:
                groups[sig] = {}
                order.append(sig)
            if e.desc in groups[sig]:
                groups[sig][e.desc].append(key)
            else:
                groups[sig][e.desc] = [key]
        else:
            kept.append(e)
    for sig in order:
        for desc, keys in groups[sig].items():
            kept.append(Entry(fmt_keys(list(sig), "1..9"), desc))
    return kept


def split_bindings(src):
    """Split a keys[] body into top-level struct literal strings."""
    result = []
    depth = 0
    start = None
    i = 0
    while i < len(src):
        c = src[i]
        if c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                result.append(src[start:i + 1])
                start = None
        i += 1
    return result


# -------------------- TUI --------------------

BG = 0
FG = 7

def init_colors(pair, fg, bg):
    try:
        curses.init_pair(pair, fg, bg)
    except curses.error:
        pass


class App:
    def __init__(self, entries):
        self.entries = entries
        self.filtered = list(entries)
        self.pos = 0
        self.search = ""
        self.help = False

    def refresh_filter(self):
        if not self.search:
            self.filtered = list(self.entries)
        else:
            s = self.search.lower()
            self.filtered = [e for e in self.entries
                             if s in e.keycombo.lower() or s in e.desc.lower()]
        if self.pos >= len(self.filtered):
            self.pos = max(0, len(self.filtered) - 1)
        if self.pos < 0:
            self.pos = 0

    def run(self, stdscr):
        curses.curs_set(1)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        bg = -1
        fg = -1
        init_colors(1, curses.COLOR_CYAN, bg)    # header / search
        init_colors(2, fg, bg)                    # normal
        init_colors(3, bg, curses.COLOR_CYAN)     # selected
        init_colors(4, curses.COLOR_YELLOW, bg)   # keycombo
        init_colors(5, curses.COLOR_CYAN, bg)     # help title

        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()

            # header
            stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
            header = " dwm keybinds  "
            stdscr.addnstr(0, 0, header, w)
            stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

            # search bar
            search_prompt = "/ " if self.search else "/ (search)  "
            stdscr.attron(curses.color_pair(1))
            stdscr.addnstr(h - 1, 0, search_prompt + self.search, w)
            stdscr.attroff(curses.color_pair(1))

            self.refresh_filter()

            if self.help:
                self.draw_help(stdscr, h, w)
            else:
                self.draw_list(stdscr, h, w)

            stdscr.refresh()

            key = stdscr.get_wch()
            if isinstance(key, int):
                ch = key
                if ch in (curses.KEY_RESIZE,):
                    continue
                if ch == curses.KEY_DOWN or ch == ord('j'):
                    if self.pos < len(self.filtered) - 1:
                        self.pos += 1
                elif ch == curses.KEY_UP or ch == ord('k'):
                    if self.pos > 0:
                        self.pos -= 1
                elif ch == curses.KEY_NPAGE:
                    self.pos = min(len(self.filtered) - 1, self.pos + h - 3)
                elif ch == curses.KEY_PPAGE:
                    self.pos = max(0, self.pos - (h - 3))
                elif ch == curses.KEY_HOME:
                    self.pos = 0
                elif ch == curses.KEY_END:
                    self.pos = len(self.filtered) - 1
                elif ch == curses.KEY_BACKSPACE or ch == 127:
                    self.search = self.search[:-1]
                elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
                    pass
                elif ch == ord('/'):
                    self.search = ""
                elif ch == ord('?'):
                    self.help = not self.help
                elif ch == ord('q') or ch == 27:  # q or ESC
                    break
                else:
                    # treat as search char
                    if 32 <= ch < 127:
                        self.search += chr(ch)
                        self.pos = 0
            else:
                # wide char / string key
                pass

    def draw_help(self, stdscr, h, w):
        lines = [
            (" dwm-cheatsheet help", True),
            ("", False),
            ("j / K_DOWN   scroll down", False),
            ("k / K_UP     scroll up", False),
            ("PageUp/Down  page scroll", False),
            ("Home/End     jump top/bottom", False),
            ("/            start a search", False),
            ("<any key>    filter results (fuzzy sub-string)", False),
            ("Backspace    edit search", False),
            ("q / ESC      quit", False),
            ("?            toggle help", False),
        ]
        y = 1
        for text, bold in lines:
            if y >= h - 1:
                break
            attr = curses.A_BOLD if bold else curses.color_pair(2)
            stdscr.attron(attr)
            stdscr.addnstr(y, 2, text, w - 4)
            stdscr.attroff(attr)
            y += 1

    def draw_list(self, stdscr, h, w):
        page_h = h - 2
        start_line = 1
        for i in range(page_h):
            idx = self.pos + i
            if idx >= len(self.filtered):
                break
            e = self.filtered[idx]
            y = start_line + i
            combo = e.keycombo
            desc = e.desc

            if idx == self.pos and not self.help:
                stdscr.attron(curses.color_pair(3))
                stdscr.addnstr(y, 0, " " * min(w, 20), w)
                stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                stdscr.addnstr(y, 2, combo, w - 2)
                stdscr.attrset(0)
                # desc on same line
                stdscr.attron(curses.color_pair(3))
                stdscr.addnstr(y, 22, " " + desc, w - 24)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.attron(curses.color_pair(4))
                stdscr.addnstr(y, 2, combo, 20)
                stdscr.attroff(curses.color_pair(4))
                stdscr.attron(curses.color_pair(2))
                stdscr.addnstr(y, 22, " " + desc, w - 24)
                stdscr.attroff(curses.color_pair(2))

        # footer count
        if 0:
            pass


def default_config_path():
    # script lives in ~/.suckless/scripts/ -> dwm at ~/.suckless/dwm/config.h
    scripts_dir = os.path.dirname(os.path.realpath(__file__))
    cand = os.path.normpath(os.path.join(scripts_dir, "..", "dwm", "config.h"))
    return cand


def main():
    ap = argparse.ArgumentParser(description="dwm keybind cheatsheet TUI")
    ap.add_argument("config", nargs="?", default=default_config_path(),
                    help="path to dwm config.h (default: auto-detect)")
    ap.add_argument("--list", action="store_true",
                    help="print parsed keybindings as plain text (for fzf) and exit")
    args = ap.parse_args()

    if not os.path.exists(args.config):
        print(f"error: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    entries = parse_config(args.config)
    if not entries:
        print("error: no keybindings parsed from config.h", file=sys.stderr)
        sys.exit(1)

    if args.list:
        width = max(len(e.keycombo) for e in entries) + 2
        for e in entries:
            print(f"{e.keycombo.ljust(width)}{e.desc}")
        return

    app = App(entries)
    try:
        curses.wrapper(app.run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
