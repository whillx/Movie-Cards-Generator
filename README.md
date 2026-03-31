# Movie Cards Generator

A desktop tool for creating professional title cards for film productions — credits, opening titles, and more. Generates transparent PNG images and an FCPXML timeline ready for import into Final Cut Pro or compatible editors.

## Features

- **Card editor** — Add, edit, and delete cards with primary text (e.g. job title) and secondary text (e.g. name), with live treeview updates and multi-select
- **BBCode formatting** — Inline `[b]`, `[i]`, `[bi]`, and `[color=#rrggbb]` tags in card text; `\n` for line breaks
- **PNG export** — Renders transparent RGBA images at your target resolution with full font and colour control
- **FCPXML timeline** — Exports a Final Cut Pro-compatible timeline with Cross Dissolve transitions and frame-accurate rational-number timing
- **Unified session files** — Save and restore your full project (cards + all settings) as a single JSON file
- **Block positioning** — Primary and secondary text move as one unit; a single X/Y anchor and spacing control in the General tab
- **Flexible settings** — Frame rates from 23.976 to 60 fps, resolution presets (720p to 4K), per-card duration and gap control, fade in/out, independent font settings for each text layer

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

1. **Load a session** — click Browse next to *Session File* and open a `.json` file (try `example.json` to get started)
2. **Edit cards** — add, remove, or edit entries in the Cards panel; changes are held in memory until you click **Save**
3. **Configure settings** — set frame rate, resolution, fades, text block position, and font options in the Settings panel
4. **Set output directory** — click Browse next to *Output Dir*
5. **Generate** — click **Generate** to render PNGs and the FCPXML timeline

Output: a `cards/` folder of transparent PNGs + a `timeline.fcpxml` file in the output directory.

## BBCode & newlines

The `primary` and `secondary` text fields support inline formatting:

| Syntax | Effect |
|---|---|
| `\n` | Line break |
| `[b]...[/b]` | Bold |
| `[i]...[/i]` | Italic |
| `[bi]...[/bi]` | Bold + italic |
| `[color=#FF8800]...[/color]` | Colour override (hex) |

Bold/italic variants are resolved automatically from system font files. The regular face is used as a fallback if a variant file cannot be found.

## Session file format

Session files are plain JSON with two top-level keys:

```json
{
  "config": { ... },
  "cards": [
    { "primary": "Directed by", "secondary": "Jane Smith", "duration": 4.0, "gap": 1.0 }
  ]
}
```

See `example.json` for a complete reference.

## Project structure

```
main.py               # Entry point
example.json          # Sample session file (cards + config)
requirements.txt      # Pillow >= 10.0.0
core/
  json_reader.py      # load_session / save_session, Card dataclass
  session_config.py   # SessionConfig / TextConfig dataclasses
  font_utils.py       # Cross-platform font resolution (with bold/italic variant search)
  image_generator.py  # PNG rendering with BBCode inline parser (Pillow)
  fcpxml_generator.py # FCPXML timeline generation (rational-number timecodes)
  utils.py            # index_to_alpha naming helper
gui/
  app.py              # Main window and orchestration
  cards_panel.py      # Card list, inline editor, Add/Delete/Save/Clear
  settings_panel.py   # General, Primary Text, Secondary Text tabs
```
