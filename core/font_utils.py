import os
import sys
from typing import List, Optional


def _get_system_font_dirs() -> List[str]:
    if sys.platform == 'win32':
        windir = os.environ.get('WINDIR', 'C:\\Windows')
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


def find_font_file(
    font_name: str,
    bold: bool = False,
    italic: bool = False,
) -> Optional[str]:
    """
    Try to find a TTF/OTF file matching the given font family name.

    When bold and/or italic are requested the search prefers files whose stem
    contains the relevant keyword(s) (e.g. 'arialbd.ttf', 'ariali.ttf',
    'arialbi.ttf').  Falls back to the regular face if no variant is found.
    """
    clean = font_name.lower().replace(' ', '').replace('-', '')

    # Keywords that indicate each variant in a font filename stem
    BOLD_KEYWORDS   = ('bold', 'bd', 'b')
    ITALIC_KEYWORDS = ('italic', 'oblique', 'it', 'i')

    best_regular: Optional[str] = None
    best_variant: Optional[str] = None

    for fonts_dir in _get_system_font_dirs():
        if not os.path.isdir(fonts_dir):
            continue
        for fname in os.listdir(fonts_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ('.ttf', '.otf'):
                continue
            stem = os.path.splitext(fname)[0].lower().replace(' ', '').replace('-', '')
            if not (stem == clean or stem.startswith(clean)):
                continue

            full_path = os.path.join(fonts_dir, fname)
            suffix = stem[len(clean):]  # the part after the family name

            has_bold   = any(kw in suffix for kw in BOLD_KEYWORDS)
            has_italic = any(kw in suffix for kw in ITALIC_KEYWORDS)

            if bold and italic:
                if has_bold and has_italic:
                    best_variant = full_path
                    break
            elif bold:
                if has_bold and not has_italic:
                    best_variant = full_path
                    break
            elif italic:
                if has_italic and not has_bold:
                    best_variant = full_path
                    break
            else:
                # Regular: prefer the shortest stem (closest exact match)
                if best_regular is None or len(stem) < len(
                    os.path.splitext(os.path.basename(best_regular))[0]
                ):
                    best_regular = full_path

    if (bold or italic) and best_variant:
        return best_variant
    if best_regular:
        return best_regular
    return None


def get_available_font_names() -> List[str]:
    """Return font filenames (without extension) from the system fonts directory."""
    names = []
    for fonts_dir in _get_system_font_dirs():
        if not os.path.isdir(fonts_dir):
            continue
        for fname in sorted(os.listdir(fonts_dir)):
            if os.path.splitext(fname)[1].lower() in ('.ttf', '.otf'):
                names.append(os.path.splitext(fname)[0])
    return names
