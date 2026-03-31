import os
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.font_utils import find_font_file
from core.json_reader import Card
from core.session_config import SessionConfig, TextConfig
from core.utils import index_to_alpha


def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font by name, falling back to Pillow's default if not found."""
    # Try the name directly (works if it's already a valid path or system font)
    try:
        return ImageFont.truetype(font_name, size)
    except (OSError, IOError):
        pass

    # Search system fonts directory
    font_path = find_font_file(font_name)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            pass

    # Fall back to Pillow's built-in default
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex_to_rgba(hex_color: str) -> Tuple[int, int, int, int]:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, 255)


def _draw_text_centered(
    draw: ImageDraw.Draw,
    text: str,
    cfg: TextConfig,
    img_width: int,
    img_height: int,
    y_override: float = None,
) -> None:
    font = _load_font(cfg.font, cfg.size)
    color = _hex_to_rgba(cfg.color)

    x = (cfg.x_percent / 100.0) * img_width
    y = ((y_override if y_override is not None else cfg.y_percent) / 100.0) * img_height

    # Use multiline variants so \n in text is respected and line_height is honoured
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=cfg.line_height, align='center')
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw.multiline_text(
        (x - text_w / 2, y - text_h / 2), text,
        font=font, fill=color, spacing=cfg.line_height, align='center',
    )


def generate_images(cards: List[Card], config: SessionConfig, output_dir: str) -> List[str]:
    """Render each card as a transparent PNG and return a list of file paths."""
    cards_dir = os.path.join(output_dir, 'cards')
    os.makedirs(cards_dir, exist_ok=True)

    width = config.resolution_width
    height = config.resolution_height
    paths = []

    for i, card in enumerate(cards):
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        has_secondary = bool(card.secondary.strip())

        if has_secondary:
            _draw_text_centered(draw, card.primary, config.primary_text, width, height)
            _draw_text_centered(draw, card.secondary, config.secondary_text, width, height)
        else:
            # No secondary text — vertically center the primary text
            _draw_text_centered(draw, card.primary, config.primary_text, width, height,
                                 y_override=50.0)

        filepath = os.path.join(cards_dir, f"card_{index_to_alpha(i)}.png")
        img.save(filepath, 'PNG')
        paths.append(filepath)

    return paths
