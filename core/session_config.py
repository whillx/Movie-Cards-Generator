from dataclasses import dataclass, field, fields
from typing import Optional


@dataclass
class TextConfig:
    font: str = "Arial"
    size: int = 60
    color: str = "#FFFFFF"
    x_percent: float = 50.0
    y_percent: float = 45.0
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
    primary_text: TextConfig = field(
        default_factory=lambda: TextConfig(size=60, y_percent=45.0)
    )
    secondary_text: TextConfig = field(
        default_factory=lambda: TextConfig(size=48, y_percent=57.0)
    )


def session_config_from_dict(data: dict) -> SessionConfig:
    """
    Build a SessionConfig from a plain dict.
    Unknown or legacy keys (e.g. 'json_path') are silently ignored so that
    old session files can still be opened without errors.
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
