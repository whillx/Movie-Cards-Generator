import tkinter as tk
from tkinter import ttk, colorchooser, font as tkfont
from typing import Callable, Optional

from core.session_config import SessionConfig, TextConfig


FRAME_RATES = ["23.976", "24", "25", "29.97", "30", "50", "59.94", "60"]
RESOLUTION_PRESETS = ["1920x1080", "3840x2160", "1280x720", "2048x1080", "4096x2160", "Custom"]


class SettingsPanel(ttk.Notebook):
    """
    A tabbed settings panel with three tabs:
      - General        : frame rate, resolution, fade in/out, duration override,
                         text block position and spacing
      - Primary Text   : font, size, color, line height
      - Secondary Text : font, size, color, line height
    """

    def __init__(
        self,
        parent,
        on_apply_duration_to_all: Optional[Callable[[float, float], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._on_apply_duration_to_all = on_apply_duration_to_all

        self._general_vars: dict = {}
        self._primary_vars: dict = {}
        self._secondary_vars: dict = {}

        self._build_general_tab()
        self._build_text_tab("Primary Text",   self._primary_vars,   default_size=60)
        self._build_text_tab("Secondary Text", self._secondary_vars, default_size=48)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_general_tab(self):
        frame = ttk.Frame(self, padding=12)
        self.add(frame, text="General")

        v = self._general_vars
        v['frame_rate']        = tk.StringVar(value="24")
        v['res_preset']        = tk.StringVar(value="1920x1080")
        v['res_w']             = tk.IntVar(value=1920)
        v['res_h']             = tk.IntVar(value=1080)
        v['fade_in']           = tk.DoubleVar(value=0.5)
        v['fade_out']          = tk.DoubleVar(value=0.5)
        v['override_duration'] = tk.BooleanVar(value=False)
        v['global_duration']   = tk.DoubleVar(value=3.0)
        v['global_gap']        = tk.DoubleVar(value=0.5)
        v['block_x_percent']   = tk.DoubleVar(value=50.0)
        v['block_y_percent']   = tk.DoubleVar(value=50.0)
        v['block_spacing']     = tk.IntVar(value=20)

        row = 0

        # Frame rate
        ttk.Label(frame, text="Frame Rate:").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Combobox(
            frame, textvariable=v['frame_rate'], values=FRAME_RATES,
            width=10, state='readonly',
        ).grid(row=row, column=1, sticky='w', pady=4)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # Resolution preset
        ttk.Label(frame, text="Resolution:").grid(row=row, column=0, sticky='w', pady=4)
        res_combo = ttk.Combobox(
            frame, textvariable=v['res_preset'], values=RESOLUTION_PRESETS,
            width=14, state='readonly',
        )
        res_combo.grid(row=row, column=1, columnspan=3, sticky='w', pady=4)
        res_combo.bind('<<ComboboxSelected>>', self._on_res_preset_change)
        row += 1

        # Custom W × H
        ttk.Label(frame, text="Width:").grid(row=row, column=0, sticky='w', pady=2)
        ttk.Spinbox(frame, textvariable=v['res_w'], from_=1, to=7680, width=7).grid(
            row=row, column=1, sticky='w', pady=2)
        ttk.Label(frame, text="Height:").grid(row=row, column=2, sticky='w', pady=2, padx=(8, 0))
        ttk.Spinbox(frame, textvariable=v['res_h'], from_=1, to=4320, width=7).grid(
            row=row, column=3, sticky='w', pady=2)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # Fade in / fade out
        ttk.Label(frame, text="Fade In (s):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(
            frame, textvariable=v['fade_in'], from_=0.0, to=30.0,
            increment=0.1, width=7,
        ).grid(row=row, column=1, sticky='w', pady=4)
        row += 1

        ttk.Label(frame, text="Fade Out (s):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(
            frame, textvariable=v['fade_out'], from_=0.0, to=30.0,
            increment=0.1, width=7,
        ).grid(row=row, column=1, sticky='w', pady=4)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # Duration override checkbox + "Apply to All" button on the same row
        ttk.Checkbutton(
            frame, text="Override all durations",
            variable=v['override_duration'],
        ).grid(row=row, column=0, columnspan=2, sticky='w', pady=4)

        ttk.Button(
            frame, text="Apply to All", command=self._on_apply_to_all,
        ).grid(row=row, column=2, columnspan=2, sticky='w', pady=4, padx=(8, 0))
        row += 1

        # Global duration + global gap — always editable so "Apply to All" works freely
        ttk.Label(frame, text="Global Duration (s):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(
            frame, textvariable=v['global_duration'],
            from_=0.1, to=120.0, increment=0.5, width=7,
        ).grid(row=row, column=1, sticky='w', pady=4)

        ttk.Label(frame, text="Global Gap (s):").grid(
            row=row, column=2, sticky='w', pady=4, padx=(12, 0))
        ttk.Spinbox(
            frame, textvariable=v['global_gap'],
            from_=0.0, to=60.0, increment=0.5, width=7,
        ).grid(row=row, column=3, sticky='w', pady=4)
        row += 1

        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # Text block position
        ttk.Label(frame, text="Text Block X (%):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(
            frame, textvariable=v['block_x_percent'],
            from_=0.0, to=100.0, increment=1.0, width=7,
        ).grid(row=row, column=1, sticky='w', pady=4)

        ttk.Label(frame, text="Text Block Y (%):").grid(
            row=row, column=2, sticky='w', pady=4, padx=(12, 0))
        ttk.Spinbox(
            frame, textvariable=v['block_y_percent'],
            from_=0.0, to=100.0, increment=1.0, width=7,
        ).grid(row=row, column=3, sticky='w', pady=4)
        row += 1

        ttk.Label(frame, text="Text Spacing (px):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(
            frame, textvariable=v['block_spacing'],
            from_=0, to=500, increment=1, width=7,
        ).grid(row=row, column=1, sticky='w', pady=4)

        frame.columnconfigure(1, weight=1)

    def _build_text_tab(self, label: str, v: dict, default_size: int):
        frame = ttk.Frame(self, padding=12)
        self.add(frame, text=label)

        fonts = sorted(tkfont.families())
        v['font']        = tk.StringVar(value="Arial")
        v['size']        = tk.IntVar(value=default_size)
        v['color']       = tk.StringVar(value="#FFFFFF")
        v['line_height'] = tk.IntVar(value=10)

        row = 0

        # Font family
        ttk.Label(frame, text="Font:").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Combobox(frame, textvariable=v['font'], values=fonts, width=24).grid(
            row=row, column=1, columnspan=2, sticky='ew', pady=4)
        row += 1

        # Font size
        ttk.Label(frame, text="Size (px):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(frame, textvariable=v['size'], from_=8, to=500, width=7).grid(
            row=row, column=1, sticky='w', pady=4)
        row += 1

        # Line height (spacing between wrapped lines)
        ttk.Label(frame, text="Line Height (px):").grid(row=row, column=0, sticky='w', pady=4)
        ttk.Spinbox(frame, textvariable=v['line_height'], from_=0, to=300, width=7).grid(
            row=row, column=1, sticky='w', pady=4)
        row += 1

        # Color picker
        ttk.Label(frame, text="Color:").grid(row=row, column=0, sticky='w', pady=4)
        color_row = ttk.Frame(frame)
        color_row.grid(row=row, column=1, columnspan=2, sticky='w', pady=4)

        swatch = tk.Label(color_row, width=3, relief='solid', bg=v['color'].get())
        swatch.pack(side='left', padx=(0, 6))
        v['_color_swatch'] = swatch

        def pick_color(var=v['color'], sw=swatch):
            result = colorchooser.askcolor(color=var.get(), title=f"Pick {label} Color")
            if result and result[1]:
                var.set(result[1])
                sw.configure(bg=result[1])

        ttk.Button(color_row, text="Choose…", command=pick_color).pack(side='left')

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_res_preset_change(self, _event=None):
        preset = self._general_vars['res_preset'].get()
        if preset == "Custom":
            return
        try:
            w, h = preset.split('x')
            self._general_vars['res_w'].set(int(w))
            self._general_vars['res_h'].set(int(h))
        except ValueError:
            pass

    def _on_apply_to_all(self):
        """Fire the callback with the current global duration and gap values."""
        if self._on_apply_duration_to_all:
            self._on_apply_duration_to_all(
                self._general_vars['global_duration'].get(),
                self._general_vars['global_gap'].get(),
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_config_values(self) -> dict:
        """Return all current settings as a dict ready to unpack into SessionConfig."""
        gv = self._general_vars
        pv = self._primary_vars
        sv = self._secondary_vars
        return {
            'frame_rate':        gv['frame_rate'].get(),
            'resolution_width':  gv['res_w'].get(),
            'resolution_height': gv['res_h'].get(),
            'fade_in':           gv['fade_in'].get(),
            'fade_out':          gv['fade_out'].get(),
            'override_duration': gv['override_duration'].get(),
            'global_duration':   gv['global_duration'].get(),
            'global_gap':        gv['global_gap'].get(),
            'block_x_percent':   gv['block_x_percent'].get(),
            'block_y_percent':   gv['block_y_percent'].get(),
            'block_spacing':     gv['block_spacing'].get(),
            'primary_text': TextConfig(
                font=pv['font'].get(),
                size=pv['size'].get(),
                color=pv['color'].get(),
                line_height=pv['line_height'].get(),
            ),
            'secondary_text': TextConfig(
                font=sv['font'].get(),
                size=sv['size'].get(),
                color=sv['color'].get(),
                line_height=sv['line_height'].get(),
            ),
        }

    def apply_config(self, config: SessionConfig) -> None:
        """Populate all widgets from a saved SessionConfig."""
        gv = self._general_vars
        gv['frame_rate'].set(config.frame_rate)
        gv['res_w'].set(config.resolution_width)
        gv['res_h'].set(config.resolution_height)
        preset = f"{config.resolution_width}x{config.resolution_height}"
        gv['res_preset'].set(preset if preset in RESOLUTION_PRESETS else "Custom")
        gv['fade_in'].set(config.fade_in)
        gv['fade_out'].set(config.fade_out)
        gv['override_duration'].set(config.override_duration)
        gv['global_duration'].set(config.global_duration)
        gv['global_gap'].set(config.global_gap)
        gv['block_x_percent'].set(config.block_x_percent)
        gv['block_y_percent'].set(config.block_y_percent)
        gv['block_spacing'].set(config.block_spacing)

        for v, tc in [
            (self._primary_vars,   config.primary_text),
            (self._secondary_vars, config.secondary_text),
        ]:
            v['font'].set(tc.font)
            v['size'].set(tc.size)
            v['color'].set(tc.color)
            v['line_height'].set(tc.line_height)
            if '_color_swatch' in v:
                v['_color_swatch'].configure(bg=tc.color)
