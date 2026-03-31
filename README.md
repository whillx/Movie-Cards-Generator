# Movie Cards Generator

A desktop tool for creating professional title cards for film productions — credits, opening titles, and more. Generates transparent PNG images and an FCPXML timeline ready for import into Final Cut Pro or compatible editors.

## Features

- **Card editor** — Add, edit, and delete cards with primary text (e.g. job title) and secondary text (e.g. name), with live preview updates
- **PNG export** — Renders transparent RGBA images at your target resolution with full font and color control
- **FCPXML timeline** — Exports a Final Cut Pro-compatible timeline with Cross Dissolve transitions and frame-accurate timing
- **Session files** — Save and restore your full project (cards + settings) as a single JSON file
- **Flexible settings** — Frame rates from 23.976 to 60fps, resolution presets (720p to 4K), per-card duration and gap control, independent font settings for each text layer

## Requirements

- Python 3
- [Pillow](https://python-pillow.org/) >= 10.0.0

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. Load an existing session or start fresh
2. Add cards with your text, duration, and gap settings
3. Configure frame rate, resolution, fonts, and transitions in the Settings panel
4. Choose an output directory and click **Generate**

Output: a folder of numbered transparent PNGs + an `output.fcpxml` timeline file.

## Project Structure

```
main.py               # Entry point
core/
  json_reader.py      # Session load/save, Card dataclass
  session_config.py   # Configuration dataclasses
  font_utils.py       # Cross-platform font resolution
  image_generator.py  # PNG rendering (Pillow)
  fcpxml_generator.py # FCPXML timeline generation
gui/
  app.py              # Main window and orchestration
  cards_panel.py      # Card list and inline editor
  settings_panel.py   # Settings tabs
```
