"""
Font discovery for Movie Cards Generator.

Builds a lookup table by reading the metadata embedded in every font file
(the OpenType 'name' table), so font families and styles are matched by
their actual names rather than by filename heuristics.

The map is built once on first use and cached for the lifetime of the process.
"""

import os
import sys
from typing import Dict, List, Optional

from PIL import ImageFont


# { family_lower: { style_lower: absolute_file_path } }
_FontStyles = Dict[str, str]
_FontMap    = Dict[str, _FontStyles]

_font_map: Optional[_FontMap] = None


def _get_system_font_dirs() -> List[str]:
    if sys.platform == 'win32':
        windir      = os.environ.get('WINDIR', 'C:\\Windows')
        localappdata = os.environ.get('LOCALAPPDATA', '')
        dirs = [os.path.join(windir, 'Fonts')]
        if localappdata:
            dirs.append(os.path.join(localappdata, 'Microsoft', 'Windows', 'Fonts'))
        return dirs
    elif sys.platform == 'darwin':
        return [
            '/Library/Fonts',
            '/System/Library/Fonts',
            os.path.expanduser('~/Library/Fonts'),
        ]
    else:
        return [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            os.path.expanduser('~/.fonts'),
        ]


def _build_font_map() -> _FontMap:
    """
    Scan every TTF/OTF file in the system font directories and read
    (family, style) directly from the font's own metadata.

    The resulting map is: { family_lower: { style_lower: filepath } }
    If two files claim the same family+style the first one wins.
    """
    font_map: _FontMap = {}
    for fonts_dir in _get_system_font_dirs():
        if not os.path.isdir(fonts_dir):
            continue
        for fname in sorted(os.listdir(fonts_dir)):
            if os.path.splitext(fname)[1].lower() not in ('.ttf', '.otf'):
                continue
            path = os.path.join(fonts_dir, fname)
            try:
                family, style = ImageFont.truetype(path, 10).getname()
                fk = family.lower()
                sk = style.lower()
                font_map.setdefault(fk, {}).setdefault(sk, path)
            except Exception:
                continue
    return font_map


def _get_font_map() -> _FontMap:
    global _font_map
    if _font_map is None:
        _font_map = _build_font_map()
    return _font_map


def _find_style(styles: _FontStyles, bold: bool, italic: bool) -> str:
    """Pick the best file path from a family's style dict."""
    if bold and italic:
        want = ['bold italic', 'bolditalic', 'bold oblique']
    elif bold:
        want = ['bold', 'semibold', 'demibold', 'extrabold', 'black', 'heavy']
    elif italic:
        want = ['italic', 'oblique']
    else:
        want = ['regular', 'normal', '']

    for w in want:
        if w in styles:
            return styles[w]

    # No exact style match — return whatever is available and let
    # _apply_variation select the right instance (handles variable fonts).
    return next(iter(styles.values()))


def find_font_file(
    family: str,
    bold: bool = False,
    italic: bool = False,
) -> Optional[str]:
    """
    Return the path of the best-matching font file for the given family name
    and variant flags.  Matching is done against font metadata, not filenames.

    If the family name is not found directly (e.g. "Candara Light"), the name
    is progressively split so that trailing words are treated as a style
    qualifier (e.g. family "Candara", style "Light").  When such a split
    matches, the embedded style takes precedence over the bold/italic flags.

    Returns None if the family is not found at all.
    """
    font_map = _get_font_map()
    styles   = font_map.get(family.strip().lower())
    if styles:
        return _find_style(styles, bold, italic)

    # The full name was not a known family.  Progressively strip trailing
    # words and check if they name a style inside a shorter family name.
    # E.g. "Candara Light" → family "candara", target style "light".
    words = family.strip().split()
    for split in range(len(words) - 1, 0, -1):
        base_family = ' '.join(words[:split]).lower()
        styles = font_map.get(base_family)
        if not styles:
            continue
        # The trailing words become the target style.
        target_style = ' '.join(words[split:]).lower()
        if target_style in styles:
            return styles[target_style]
        # Also try without spaces (e.g. "Semi Bold" → "semibold").
        target_joined = target_style.replace(' ', '')
        if target_joined in styles:
            return styles[target_joined]
        # Try a compound style with bold/italic flags appended.
        if bold and italic:
            extras = [target_style + ' bold italic', target_style + ' bolditalic']
        elif bold:
            extras = [target_style + ' bold']
        elif italic:
            extras = [target_style + ' italic', target_style + ' oblique']
        else:
            extras = []
        for e in extras:
            if e in styles:
                return styles[e]
        # Found the family via split — pick the best partial match.
        # Try substring match (e.g. "light" matches "light italic").
        for s, p in styles.items():
            if target_style in s or target_joined in s:
                return p
        # Last resort: return any style from this family.
        return next(iter(styles.values()))


def get_available_font_names() -> List[str]:
    """Return a sorted list of font family names available on this system."""
    return sorted(_get_font_map().keys())
