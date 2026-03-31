import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

from core.session_config import SessionConfig, session_config_from_dict


@dataclass
class Card:
    primary: str
    secondary: str
    duration: float
    gap: float = 0.0        # blank gap (seconds) inserted after this card in the timeline


def load_session(path: str) -> Tuple[List[Card], Optional[SessionConfig]]:
    """
    Load a session file and return (cards, config).
    `config` is None if the file contains no 'config' section (legacy cards-only file).
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cards = [
        Card(
            primary=item.get('primary', ''),
            secondary=item.get('secondary', ''),
            duration=float(item.get('duration', 3.0)),
            gap=float(item.get('gap', 0.0)),
        )
        for item in data.get('cards', [])
    ]

    config_data = data.get('config')
    config = session_config_from_dict(config_data) if config_data else None
    return cards, config


def save_session(cards: List[Card], config: SessionConfig, path: str) -> None:
    """Write cards and config together into a single session JSON file."""
    data = {
        'config': asdict(config),
        'cards': [
            {
                'primary':  c.primary,
                'secondary': c.secondary,
                'duration': c.duration,
                'gap':      c.gap,
            }
            for c in cards
        ],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
