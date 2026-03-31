from dataclasses import dataclass, field, fields
from typing import Optional


@dataclass
class TextConfig:
    font: str = "Arial"
    size: int = 60
    color: str = "#FFFFFF"
    line_height: int = 10   # extra pixel spacing between wrapped lines


@dataclass
class SessionConfig:
    output_dir: str = ""
    frame_rate: str = "24"
    resolution_width: int = 1920
    resolution_height: int = 1080
    fade_in: float = 0.5
    fade_out: float = 0.5
    override_duration: bool = False
    global_duration: float = 3.0
    global_gap: float = 0.5
    block_x_percent: float = 50.0   # horizontal centre of the text block
    block_y_percent: float = 50.0   # vertical centre of the text block
    block_spacing: int = 20         # gap in pixels between primary and secondary text
    primary_text: TextConfig = field(
        default_factory=lambda: TextConfig(size=60)
    )
    secondary_text: TextConfig = field(
        default_factory=lambda: TextConfig(size=48)
    )


def session_config_from_dict(data: dict) -> SessionConfig:
    """
    Build a SessionConfig from a plain dict.
    Unknown or legacy keys are silently ignored so that old session files
    can still be opened without errors.
    """
    d = dict(data)
    d.pop('json_path', None)          # legacy field — no longer used
    primary_data   = d.pop('primary_text',   {})
    secondary_data = d.pop('secondary_text', {})

    known_cfg = {f.name for f in fields(SessionConfig)}
    config = SessionConfig(**{k: v for k, v in d.items() if k in known_cfg})

    known_txt = {f.name for f in fields(TextConfig)}
    if primary_data:
        config.primary_text = TextConfig(
            **{k: v for k, v in primary_data.items() if k in known_txt}
        )
    if secondary_data:
        config.secondary_text = TextConfig(
            **{k: v for k, v in secondary_data.items() if k in known_txt}
        )

    return config
