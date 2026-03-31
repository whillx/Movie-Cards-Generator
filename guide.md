# Movie Cards Generator
#### A simple tool for creating main titles or closing titles for the films.

## Expected output
- The tool reads a **session file** (JSON), generates a transparent PNG for each title card and stores them in a `cards/` subfolder inside the output directory.
- Images are named with alphabetic suffixes (e.g. `card_aaa.png`, `card_aab.png`) to prevent editing software from mistakenly treating them as an image sequence.
- The tool generates an FCPXML timeline (`timeline.fcpxml`) that can be imported by Final Cut Pro and compatible editing software, containing the generated title cards with Cross Dissolve fade-in / fade-out transitions and optional blank gaps between cards.
- The duration and gap of each card are specified in the session file and can be overridden globally from the GUI.

## Tech specs
- Should be portable.
- Should store the generated images and FCPXML in a user-specified directory.
- Use Python and tkinter for scripting and GUI.
- All session data (cards + settings) is saved in a single session JSON file chosen by the user.
- The output directory path is remembered inside the session file and restored automatically when the session is loaded.

## Example files
- The tool includes an `example.json` session file for testing purposes.

## Session file format
The session file is a single JSON file containing two top-level keys:

### `config`
All GUI settings:
- `output_dir` — last-used output directory path (restored on load).
- `frame_rate` — FCPXML timecode frame rate string.
- `resolution_width` / `resolution_height` — output image resolution.
- `fade_in` / `fade_out` — Cross Dissolve transition duration in seconds.
- `override_duration` — boolean; when true, global duration/gap override per-card values during generation.
- `global_duration` / `global_gap` — global override values in seconds.
- `primary_text` / `secondary_text` — text layer settings (font, size, color, x_percent, y_percent, line_height).

### `cards`
Array of card objects, each with four fields:
- `primary` — the job title line (can be left empty).
- `secondary` — the name line; if left empty, only the primary text is drawn, vertically centred.
- `duration` — how long the card clip is on the timeline (seconds).
- `gap` — blank black gap inserted after the card on the timeline (seconds).

## FCPXML structure
- Fades use the **Cross Dissolve** transition (`FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265`).
- Each card produces: a fade-in transition, a video clip, a fade-out transition, a structural gap (fade-out tail), and an optional blank gap.
- All time values are snapped to frame boundaries using rational arithmetic to avoid floating-point drift.

## Project structure
```
main.py                  # entry point
example.json             # sample session file (cards + config)
requirements.txt         # Pillow >= 10.0.0
core/
  json_reader.py         # load_session / save_session (cards + config in one file)
  session_config.py      # dataclasses + session_config_from_dict helper
  font_utils.py          # resolve font names to TTF file paths
  image_generator.py     # render transparent PNGs via Pillow
  fcpxml_generator.py    # build FCPXML with Cross Dissolve fades and gaps
  utils.py               # shared helpers (index_to_alpha naming)
gui/
  app.py                 # main window, wires all panels together
  cards_panel.py         # card list + inline editor
  settings_panel.py      # tabbed settings notebook
```

## GUI — Session file
- **Session File:** field + Browse button at the top of the window.
- Loading a session file restores both the card list and all settings in one step.
- The last-used output directory is also restored if the path still exists on disk.

## GUI — Cards panel
- The card list shows all loaded cards with their primary text, secondary text, duration, and gap.
- Multi-select is supported: single click selects one row; **Ctrl+click** adds/removes rows from the selection.
- Clicking a row loads that card's values into the edit fields below.
- **Live update:** every keystroke or spinbox change instantly updates the in-memory card list and the corresponding treeview row — no intermediate button required.
- **＋ (Add)** — appends a new blank card and focuses it (large icon button).
- **✕ (Delete)** — removes all selected cards; also triggered by the **Delete** key (large icon button).
- **Save** — writes the entire in-memory card list **and** the current settings to the session file on disk. If no session file is loaded yet, a Save As dialog is shown so the user can choose a location.
- **Clear** — resets every card in memory to empty text, default duration (2 s) and default gap (0.5 s). Does **not** write to disk — click Save afterwards to persist.

## GUI — General settings tab
- **Frame Rate** — dropdown; used for FCPXML timecode generation (23.976 / 24 / 25 / 29.97 / 30 / 50 / 59.94 / 60 fps).
- **Resolution** — preset dropdown plus custom Width × Height spinboxes.
- **Fade In / Fade Out** — duration in seconds for the Cross Dissolve transition applied to each card.
- **Override all durations** checkbox — when checked, the global duration and global gap values are used for every card during generation (per-card JSON values are ignored).
- **Global Duration / Global Gap** spinboxes — always editable regardless of the checkbox.
- **Apply to All** button — stamps the current global duration and global gap onto every card in memory and saves to the session file immediately, allowing individual cards to be adjusted afterwards.

## GUI — Primary Text / Secondary Text tabs
Both text layers share the same set of controls:
- **Font** — system font family picker (uses tkinter font families).
- **Size (px)** — font size in pixels.
- **Line Height (px)** — extra pixel spacing between lines when text contains line breaks (`\n`).
- **Color** — color swatch + picker dialog.
- **Position X / Y (%)** — position of the text anchor as a percentage of the image width / height; text is centred on that point.
