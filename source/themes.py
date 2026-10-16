"""Appearance-only theme tokens, migration and custom colors (no download state)."""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Theme:
    name: str
    mood: str
    background: str
    surface: str
    accent: str
    glow: str
    text: str
    muted: str
    border: str
    light: bool = False


THEMES = {
    'ocean': Theme('Ocean', 'Deep blue · electric cyan', '#080f18', '#101c2b', '#008cff', '#36caff', '#eff5ff', '#a0b9db', '#22384e'),
    'carbon': Theme('Carbon', 'Pure monochrome', '#0c0c0c', '#202020', '#dedede', '#c6c6c6', '#f3f3f3', '#b8b8b8', '#424242'),
    'midnight': Theme('Midnight', 'Ink blue · periwinkle', '#0c1020', '#171e36', '#858bff', '#a0a5ff', '#f0f1ff', '#adb4d4', '#303b5b'),
    'aurora': Theme('Aurora', 'Indigo · mint', '#0b1420', '#142434', '#6de3c2', '#9f85ff', '#ecfff9', '#a2c5c5', '#294857'),
    'forest': Theme('Forest', 'Pine · spring green', '#091612', '#14281f', '#66db9b', '#a1e4a7', '#effbf3', '#aac9b5', '#304e3c'),
    'sunset': Theme('Sunset', 'Plum · warm coral', '#1a101c', '#302033', '#ff927f', '#dca2ff', '#fff0f2', '#d7b1c9', '#5d3a54'),
    'sakura': Theme('Sakura', 'Soft pink · rose', '#fcf2f6', '#fffafd', '#b83d75', '#f1a5cb', '#422437', '#805a72', '#e6c8d8', True),
    'lavender': Theme('Lavender', 'Lilac · violet', '#f3f0fc', '#fdfbff', '#7851c9', '#c5a0f5', '#302344', '#746583', '#dcd2ed', True),
    'frost': Theme('Frost', 'Snow · clear blue', '#eef4fa', '#ffffff', '#0879cf', '#62b8fa', '#182b41', '#5f7590', '#ccdae8', True),
    'sand': Theme('Sand', 'Warm ivory · terracotta', '#f6f0e6', '#fffbf5', '#a55830', '#dbb18a', '#392d24', '#7c6b5d', '#dfd0bc', True),
    'nord': Theme('Nord', 'Slate · arctic blue', '#232b38', '#2d3949', '#88c0d0', '#a1c8e6', '#edf1f5', '#b4c3d4', '#48596d'),
    'dracula': Theme('Dracula', 'Purple · neon pink', '#171622', '#282436', '#c59bff', '#ff79c6', '#f8f5ff', '#c0acd5', '#4d3e63'),
    'espresso': Theme('Espresso', 'Roasted brown · caramel', '#17110f', '#2b211c', '#e0b17c', '#e9c6a3', '#fff2e5', '#c9af98', '#574135'),
    'ruby': Theme('Ruby', 'Charcoal · cherry red', '#170e15', '#2a1823', '#ff6f91', '#d86caa', '#fff0f4', '#d7aabc', '#593247'),
    'lagoon': Theme('Lagoon', 'Petrol · turquoise', '#061718', '#0d2a2b', '#39d6d0', '#74efe2', '#e7fffb', '#9accc7', '#245353'),
    'contrast': Theme('Contrast', 'Black · bright gold', '#050505', '#111111', '#ffdd55', '#ffdd55', '#ffffff', '#d4d4d4', '#777777'),
}
COLOR_KEYS = ('accent', 'glow', 'bg', 'panel', 'text', 'muted', 'border')


def valid_color(value):
    return isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value) is not None


def mix(first, second, amount):
    a, b = [tuple(int(s[i:i+2], 16) for i in (1,3,5)) for s in (first, second)]
    return '#' + ''.join(f'{round(x + (y-x)*amount):02x}' for x,y in zip(a,b))


def luminance(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    channels = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return sum(c*w for c,w in zip(channels,(.2126,.7152,.0722)))


def contrast(first, second):
    a,b = sorted((luminance(first),luminance(second)))
    return (b+.05)/(a+.05)


def foreground(background):
    return '#ffffff' if luminance(background) <= .32 and contrast(background,'#ffffff') >= 3 else '#111111'


def appearance_settings(settings):
    key = {'light':'frost', 'dark':'ocean'}.get(settings.get('theme'), settings.get('theme','ocean'))
    if key not in THEMES:
        key = 'ocean'
    raw = settings.get('theme_colors', {})
    custom = {k:v.lower() for k,v in raw.items() if k in COLOR_KEYS and valid_color(v)} if isinstance(raw,dict) else {}
    return key, custom


def palette(key, custom=None):
    theme = THEMES.get(key, THEMES['ocean'])
    colors = dict(bg=theme.background, panel=theme.surface, accent=theme.accent,
                  glow=theme.glow, text=theme.text, muted=theme.muted, border=theme.border)
    colors.update({k:v.lower() for k,v in (custom or {}).items() if k in COLOR_KEYS and valid_color(v)})
    colors.update(
        sidebar=mix(colors['bg'],'#ffffff' if luminance(colors['bg'])>.4 else '#000000',.12),
        field=mix(colors['bg'],colors['panel'],.32),
        button=mix(colors['panel'],colors['accent'],.09),
        active=mix(colors['panel'],colors['accent'],.17),
        selected=mix(colors['panel'],colors['accent'],.23),
        panel_high=mix(colors['panel'],colors['glow'],.055),
        accent_hover=mix(colors['accent'],'#ffffff',.14),
        on_accent=foreground(colors['accent']),
    )
    colors['light'] = luminance(colors['bg']) > .4
    colors['icon'] = next((color for color in (colors['glow'],colors['accent'],colors['text']) if contrast(color,colors['panel'])>=3),colors['text'])
    colors['control_border'] = colors['border'] if contrast(colors['border'],colors['field'])>=2.2 else mix(colors['border'],colors['text'],.4)
    return colors
