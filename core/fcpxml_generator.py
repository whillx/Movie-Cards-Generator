"""
FCPXML generator using Cross Dissolve transitions for fade-in / fade-out,
matching the structure used by Final Cut Pro.

Spine layout for each card (fi=fade_in, fo=fade_out, D=duration, G=gap):
  Given T = start offset of this card's fade-in transition:

  1. <transition offset=T          dur=fi>      ← fade in  (skipped when fi=0)
  2. <video      offset=T+fi/2     dur=D  start=fi/2>
  3. <transition offset=T+fi/2+D-fo/2 dur=fo>  ← fade out (skipped when fo=0)
  4. <gap        offset=T+fi/2+D   dur=fo/2>    ← structural tail of fade-out
  5. <gap        offset=T+fi/2+D+fo/2 dur=G>    ← actual blank gap (skipped when G=0)

  block_end  = T + fi/2 + D + fo/2 + G
  T_next     = block_end - fi_next/2   (transitions overlap with adjacent elements)

  Total sequence duration = fi/2 + Σ(D_i + fo/2 + G_i)
"""

import os
from fractions import Fraction
from typing import List

from core.json_reader import Card
from core.session_config import SessionConfig
from core.utils import index_to_alpha


# ── Constants ─────────────────────────────────────────────────────────────────

CROSS_DISSOLVE_UID = "FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265"

TIMELINE_FORMAT_ID = "r0"
EFFECT_ID          = "r1"   # Cross Dissolve effect
ASSET_FORMAT_ID    = "r2"   # FFVideoFormatRateUndefined (used for still images)
FIRST_ASSET_NUM    = 3      # assets start at r3

FRAME_DURATIONS: dict = {
    "23.976": Fraction(1001, 24000),
    "24":     Fraction(1, 24),
    "25":     Fraction(1, 25),
    "29.97":  Fraction(1001, 30000),
    "30":     Fraction(1, 30),
    "50":     Fraction(1, 50),
    "59.94":  Fraction(1001, 60000),
    "60":     Fraction(1, 60),
}

FORMAT_NAMES: dict = {
    "23.976": "FFVideoFormat1080p2398",
    "24":     "FFVideoFormat1080p24",
    "25":     "FFVideoFormat1080p25",
    "29.97":  "FFVideoFormat1080p2997",
    "30":     "FFVideoFormat1080p30",
    "50":     "FFVideoFormat1080p50",
    "59.94":  "FFVideoFormat1080p5994",
    "60":     "FFVideoFormat1080p60",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snap(seconds: float, fd: Fraction) -> Fraction:
    """Round a float duration to the nearest frame boundary, returned as Fraction."""
    frames = round(seconds / float(fd))
    return Fraction(frames) * fd


def _fmt(frac: Fraction) -> str:
    """Format a Fraction as an FCPXML rational time string (e.g. '12/24s')."""
    if frac == 0:
        return "0/1s"
    if frac.denominator == 1:
        return f"{frac.numerator}/1s"
    return f"{frac.numerator}/{frac.denominator}s"


def _file_url(path: str) -> str:
    """Convert an absolute file path to an FCPXML-compatible file:// URL."""
    abs_path = os.path.abspath(path).replace('\\', '/')
    if not abs_path.startswith('/'):
        abs_path = '/' + abs_path          # Windows: /C:/...
    return f"file://localhost{abs_path}"


def _transition(offset: Fraction, dur: Fraction) -> List[str]:
    return [
        f'                        <transition duration="{_fmt(dur)}" name="Cross Dissolve" offset="{_fmt(offset)}">',
        f'                            <filter-video name="Cross Dissolve" ref="{EFFECT_ID}">',
        f'                                <param value="-1" key="50" name="ease"/>',
        f'                            </filter-video>',
        f'                        </transition>',
    ]


def _video(offset: Fraction, dur: Fraction, start: Fraction, name: str, ref: str) -> List[str]:
    return [
        f'                        <video enabled="1" duration="{_fmt(dur)}" start="{_fmt(start)}" name="{name}" ref="{ref}" offset="{_fmt(offset)}">',
        f'                            <adjust-conform type="fit"/>',
        f'                            <adjust-transform scale="1 1" anchor="0 0" position="0 0"/>',
        f'                        </video>',
    ]


def _gap(offset: Fraction, dur: Fraction) -> str:
    return f'                        <gap duration="{_fmt(dur)}" start="3600/1s" name="Gap" offset="{_fmt(offset)}"/>'


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_fcpxml(
    cards: List[Card],
    image_paths: List[str],
    config: SessionConfig,
    output_dir: str,
) -> str:
    fr  = config.frame_rate
    fd  = FRAME_DURATIONS.get(fr, Fraction(1, 24))
    fmt = FORMAT_NAMES.get(fr, "FFVideoFormat1080p24")
    w, h = config.resolution_width, config.resolution_height

    # Snap all time values to frame boundaries
    fi = _snap(config.fade_in,  fd)
    fo = _snap(config.fade_out, fd)

    durations = [
        _snap(config.global_duration if config.override_duration else c.duration, fd)
        for c in cards
    ]
    gaps = [
        _snap(config.global_gap if config.override_duration else c.gap, fd)
        for c in cards
    ]

    # Total sequence duration = fi/2 + Σ(D_i + fo/2 + G_i)
    total_dur = fi / 2 + sum(d + fo / 2 + g for d, g in zip(durations, gaps))

    fd_str = f"{fd.numerator}/{fd.denominator}s"

    # ── Resources ──────────────────────────────────────────────────────────────
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE fcpxml>',
        '<fcpxml version="1.10">',
        '    <resources>',
        f'        <format frameDuration="{fd_str}" width="{w}" id="{TIMELINE_FORMAT_ID}" name="{fmt}" height="{h}"/>',
        f'        <format width="{w}" id="{ASSET_FORMAT_ID}" name="FFVideoFormatRateUndefined" height="{h}"/>',
        f'        <effect id="{EFFECT_ID}" name="Cross Dissolve" uid="{CROSS_DISSOLVE_UID}"/>',
    ]

    asset_ids = []
    for i, (card, img_path) in enumerate(zip(cards, image_paths)):
        aid  = f"r{FIRST_ASSET_NUM + i}"
        name = f"card_{index_to_alpha(i)}.png"
        src  = _file_url(img_path)
        asset_ids.append(aid)
        lines += [
            f'        <asset duration="0/1s" start="0/1s" id="{aid}" name="{name}" format="{ASSET_FORMAT_ID}" hasVideo="1">',
            f'            <media-rep src="{src}" kind="original-media"/>',
            f'        </asset>',
        ]

    # ── Sequence ───────────────────────────────────────────────────────────────
    lines += [
        '    </resources>',
        '    <library>',
        '        <event name="Movie Cards">',
        '            <project name="Movie Cards">',
        f'                <sequence tcStart="0/1s" tcFormat="NDF" duration="{_fmt(total_dur)}" format="{TIMELINE_FORMAT_ID}">',
        '                    <spine>',
    ]

    block_end = Fraction(0)

    for i, (card, img_path) in enumerate(zip(cards, image_paths)):
        d   = durations[i]
        g   = gaps[i]
        aid = asset_ids[i]
        name = f"card_{index_to_alpha(i)}.png"

        # Transition offset for this card:
        # First card always starts at 0; subsequent cards overlap the previous block_end by fi/2.
        T = Fraction(0) if i == 0 else block_end - fi / 2

        video_offset = T + fi / 2        # where the video clip sits on the timeline
        video_end    = video_offset + d  # where the video clip ends

        # ── Fade-in transition ──────────────────────────────────────────────
        if fi > 0:
            lines += _transition(T, fi)

        # ── Video clip ─────────────────────────────────────────────────────
        # start=fi/2 gives the transition handle (media offset borrowed by fade-in)
        lines += _video(video_offset, d, fi / 2, name, aid)

        # ── Fade-out transition ─────────────────────────────────────────────
        if fo > 0:
            fo_trans_offset = video_end - fo / 2
            lines += _transition(fo_trans_offset, fo)
            # Structural gap: fills the tail of the fade-out after the video ends
            lines.append(_gap(video_end, fo / 2))

        # ── Actual blank gap after the card ────────────────────────────────
        if g > 0:
            lines.append(_gap(video_end + fo / 2, g))

        block_end = video_end + fo / 2 + g

    lines += [
        '                    </spine>',
        '                </sequence>',
        '            </project>',
        '        </event>',
        '    </library>',
        '</fcpxml>',
    ]

    output_path = os.path.join(output_dir, 'timeline.fcpxml')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_path
