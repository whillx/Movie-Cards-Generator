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


def find_font_file(
    family: str,
    bold: bool = False,
    italic: bool = False,
) -> Optional[str]:
    """
    Return the path of the best-matching font file for the given family name
    and variant flags.  Matching is done against font metadata, not filenames.

    If no exact style is found but the family exists, the first available
    style is returned so that _apply_variation() can select the correct
    weight/style on variable fonts.

    Returns None if the family is not found at all.
    """
    font_map = _get_font_map()
    styles   = font_map.get(family.strip().lower())
    if not styles:
        return None

    # Preferred style names in priority order
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


def get_available_font_names() -> List[str]:
    """Return a sorted list of font family names available on this system."""
    return sorted(_get_font_map().keys())
