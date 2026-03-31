"""
Image renderer for Movie Cards Generator.

BBCode supported in primary and secondary text fields:
  [b]...[/b]            bold
  [i]...[/i]            italic
  [bi]...[/bi]          bold + italic  (also [b][i]...[/i][/b])
  [color=#rrggbb]...[/color]   colour override (hex, e.g. #FF8800)

The two-character sequence \\n (backslash + n) is treated as a newline
wherever it appears, with or without BBCode.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.font_utils import find_font_file
from core.json_reader import Card
from core.session_config import SessionConfig, TextConfig
from core.utils import index_to_alpha


# ── Font loading ──────────────────────────────────────────────────────────────

def _load_font(
    font_name: str,
    size: int,
    bold: bool = False,
    italic: bool = False,
) -> ImageFont.FreeTypeFont:
    """Load a font by name and variant, falling back to Pillow's default."""
    # 1. Try direct path (already a file path)
    try:
        return ImageFont.truetype(font_name, size)
    except (OSError, IOError):
        pass

    # 2. Search system fonts with variant hints
    font_path = find_font_file(font_name, bold=bold, italic=italic)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            pass

    # 3. Pillow built-in default (no variant support)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex_to_rgba(hex_color: str) -> Tuple[int, int, int, int]:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, 255)


# ── BBCode parser ─────────────────────────────────────────────────────────────

@dataclass
class Segment:
    """A run of text with uniform styling."""
    text:  str
    bold:  bool  = False
    italic: bool = False
    color: Optional[str] = None   # hex string or None → use layer default


_TAG_RE = re.compile(
    r'\[b\]|\[/b\]'
    r'|\[i\]|\[/i\]'
    r'|\[bi\]|\[/bi\]'
    r'|\[color=(#[0-9A-Fa-f]{6})\]|\[/color\]',
    re.IGNORECASE,
)


def _preprocess(text: str) -> str:
    """Replace the literal two-char sequence \\n with a real newline."""
    return text.replace('\\n', '\n')


def _parse_bbcode(raw: str) -> List[Segment]:
    """
    Parse BBCode tags and return a flat list of Segments.
    Unrecognised tags are passed through as literal text.
    """
    text = _preprocess(raw)
    segments: List[Segment] = []
    bold_depth   = 0
    italic_depth = 0
    color_stack: List[str] = []
    pos = 0

    for m in _TAG_RE.finditer(text):
        # Emit plain text before this tag
        if m.start() > pos:
            chunk = text[pos:m.start()]
            if chunk:
                segments.append(Segment(
                    chunk,
                    bold=bold_depth > 0,
                    italic=italic_depth > 0,
                    color=color_stack[-1] if color_stack else None,
                ))

        tag = m.group(0).lower()
        if tag == '[b]':
            bold_depth += 1
        elif tag == '[/b]':
            bold_depth = max(0, bold_depth - 1)
        elif tag == '[i]':
            italic_depth += 1
        elif tag == '[/i]':
            italic_depth = max(0, italic_depth - 1)
        elif tag == '[bi]':
            bold_depth   += 1
            italic_depth += 1
        elif tag == '[/bi]':
            bold_depth   = max(0, bold_depth   - 1)
            italic_depth = max(0, italic_depth - 1)
        elif tag.startswith('[color='):
            color_stack.append(m.group(1))   # captured hex value
        elif tag == '[/color]':
            if color_stack:
                color_stack.pop()

        pos = m.end()

    # Remaining text after last tag
    if pos < len(text):
        chunk = text[pos:]
        if chunk:
            segments.append(Segment(
                chunk,
                bold=bold_depth > 0,
                italic=italic_depth > 0,
                color=color_stack[-1] if color_stack else None,
            ))

    return segments if segments else [Segment(text)]


# ── Inline renderer ───────────────────────────────────────────────────────────

@dataclass
class _Run:
    """A single-line, single-style text run ready to draw."""
    text:   str
    font:   ImageFont.FreeTypeFont
    color:  Tuple[int, int, int, int]
    width:  int
    height: int


def _make_run(
    seg_text: str,
    seg: Segment,
    cfg: TextConfig,
    default_color: Tuple[int, int, int, int],
) -> _Run:
    font  = _load_font(cfg.font, cfg.size, bold=seg.bold, italic=seg.italic)
    color = _hex_to_rgba(seg.color) if seg.color else default_color
    # Use a temporary draw surface to measure
    tmp   = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox  = tmp.textbbox((0, 0), seg_text, font=font)
    return _Run(seg_text, font, color, bbox[2] - bbox[0], bbox[3] - bbox[1])


def _render_segments(
    draw: ImageDraw.Draw,
    raw: str,
    cfg: TextConfig,
    x_center: float,
    y_top: float,
) -> float:
    """
    Render BBCode text starting at y_top, centred on x_center.
    Returns the total rendered height (sum of all line heights + line_height spacing).
    """
    default_color = _hex_to_rgba(cfg.color)
    segments = _parse_bbcode(raw)

    # Split segments on newlines to get logical lines
    # Each logical line is a list of (text, Segment) pairs
    logical_lines: List[List[Tuple[str, Segment]]] = [[]]
    for seg in segments:
        parts = seg.text.split('\n')
        for k, part in enumerate(parts):
            if k > 0:
                logical_lines.append([])
            if part:
                logical_lines[-1].append((part, seg))

    total_height = 0
    y = y_top

    for line_idx, line_parts in enumerate(logical_lines):
        if not line_parts:
            # Empty line — advance by the font's line height
            sample_font = _load_font(cfg.font, cfg.size)
            tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
            _, _, _, lh = tmp.textbbox((0, 0), 'Ay', font=sample_font)
            advance = lh + cfg.line_height
            if line_idx > 0:
                total_height += advance
            y += advance
            continue

        # Build runs for this line
        runs: List[_Run] = [
            _make_run(t, seg, cfg, default_color)
            for t, seg in line_parts
        ]

        line_w    = sum(r.width  for r in runs)
        line_h    = max(r.height for r in runs)
        x         = x_center - line_w / 2
        baseline  = y

        for run in runs:
            # Vertically align each run to the bottom of the tallest run
            draw.text(
                (x, baseline + (line_h - run.height)),
                run.text,
                font=run.font,
                fill=run.color,
            )
            x += run.width

        spacing = cfg.line_height if line_idx < len(logical_lines) - 1 else 0
        if line_idx > 0 or line_idx == 0:
            total_height += line_h
        if spacing:
            total_height += spacing

        y += line_h + (cfg.line_height if line_idx < len(logical_lines) - 1 else 0)

    return total_height


def _measure_segments(raw: str, cfg: TextConfig) -> Tuple[int, int]:
    """Return (width, height) of the full rendered text without drawing."""
    segments = _parse_bbcode(raw)

    logical_lines: List[List[Tuple[str, Segment]]] = [[]]
    for seg in segments:
        parts = seg.text.split('\n')
        for k, part in enumerate(parts):
            if k > 0:
                logical_lines.append([])
            if part:
                logical_lines[-1].append((part, seg))

    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    max_w      = 0
    total_h    = 0

    for line_idx, line_parts in enumerate(logical_lines):
        if not line_parts:
            sample_font = _load_font(cfg.font, cfg.size)
            _, _, _, lh = tmp.textbbox((0, 0), 'Ay', font=sample_font)
            total_h += lh + cfg.line_height
            continue

        line_w = 0
        line_h = 0
        for t, seg in line_parts:
            font = _load_font(cfg.font, cfg.size, bold=seg.bold, italic=seg.italic)
            bbox = tmp.textbbox((0, 0), t, font=font)
            line_w += bbox[2] - bbox[0]
            line_h  = max(line_h, bbox[3] - bbox[1])

        max_w    = max(max_w, line_w)
        total_h += line_h
        if line_idx < len(logical_lines) - 1:
            total_h += cfg.line_height

    return max_w, total_h


# ── Block layout ──────────────────────────────────────────────────────────────

def _draw_block(
    draw: ImageDraw.Draw,
    card: Card,
    config: SessionConfig,
    img_width: int,
    img_height: int,
) -> None:
    """
    Render primary and secondary text as a single centred block.

    The centre of the combined block is placed at
    (block_x_percent%, block_y_percent%) of the image.
    When secondary is absent, only the primary is drawn.
    """
    primary_raw   = card.primary
    secondary_raw = card.secondary
    has_secondary = bool(_preprocess(secondary_raw).strip())

    cx = (config.block_x_percent / 100.0) * img_width
    cy = (config.block_y_percent / 100.0) * img_height

    p_w, p_h = _measure_segments(primary_raw,   config.primary_text)

    if has_secondary:
        s_w, s_h = _measure_segments(secondary_raw, config.secondary_text)
        spacing   = config.block_spacing
        block_h   = p_h + spacing + s_h
        block_top = cy - block_h / 2

        _render_segments(draw, primary_raw,   config.primary_text,   cx, block_top)
        _render_segments(draw, secondary_raw, config.secondary_text, cx, block_top + p_h + spacing)
    else:
        _render_segments(draw, primary_raw, config.primary_text, cx, cy - p_h / 2)


# ── Public API ────────────────────────────────────────────────────────────────

def render_card(card: Card, config: SessionConfig) -> Image.Image:
    """Render a single card on a solid black background and return the PIL Image."""
    width  = config.resolution_width
    height = config.resolution_height
    img    = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw   = ImageDraw.Draw(img)
    _draw_block(draw, card, config, width, height)
    return img


def generate_images(
    cards: List[Card],
    config: SessionConfig,
    output_dir: str,
    name_prefix: str = "card",
) -> List[str]:
    """Render each card as a transparent PNG and return a list of file paths.

    Images are named <name_prefix>_aaa.png, <name_prefix>_aab.png, etc.
    """
    cards_dir = os.path.join(output_dir, 'cards')
    os.makedirs(cards_dir, exist_ok=True)

    width  = config.resolution_width
    height = config.resolution_height
    paths  = []

    for i, card in enumerate(cards):
        img  = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _draw_block(draw, card, config, width, height)

        filepath = os.path.join(cards_dir, f"{name_prefix}_{index_to_alpha(i)}.png")
        img.save(filepath, 'PNG')
        paths.append(filepath)

    return paths
