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


def find_font_file(font_name: str) -> Optional[str]:
    """Try to find a TTF/OTF file matching the given font family name."""
    clean = font_name.lower().replace(' ', '').replace('-', '')

    for fonts_dir in _get_system_font_dirs():
        if not os.path.isdir(fonts_dir):
            continue
        for fname in os.listdir(fonts_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ('.ttf', '.otf'):
                continue
            stem = os.path.splitext(fname)[0].lower().replace(' ', '').replace('-', '')
            # Exact match or the file starts with the requested name (e.g. "arial" matches "arial.ttf")
            if stem == clean or stem.startswith(clean):
                return os.path.join(fonts_dir, fname)

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
