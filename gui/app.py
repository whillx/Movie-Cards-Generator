import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.fcpxml_generator import generate_fcpxml
from core.image_generator import generate_images
from core.json_reader import load_session, save_session
from core.session_config import SessionConfig
from gui.cards_panel import CardsPanel
from gui.settings_panel import SettingsPanel


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Movie Cards Generator")
        self.root.minsize(860, 600)

        self._session_path = tk.StringVar()
        self._output_dir   = tk.StringVar()
        self._status       = tk.StringVar(value="Ready.")

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Top bar: file / directory selection ──────────────────────
        top = ttk.Frame(self.root, padding=(8, 8, 8, 4))
        top.pack(fill='x')

        ttk.Label(top, text="Session File:").grid(row=0, column=0, sticky='w')
        ttk.Entry(top, textvariable=self._session_path, width=52).grid(
            row=0, column=1, sticky='ew', padx=4)
        ttk.Button(top, text="Browse…", command=self._browse_session).grid(row=0, column=2)

        ttk.Label(top, text="Output Dir:").grid(row=1, column=0, sticky='w', pady=(4, 0))
        ttk.Entry(top, textvariable=self._output_dir, width=52).grid(
            row=1, column=1, sticky='ew', padx=4, pady=(4, 0))
        ttk.Button(top, text="Browse…", command=self._browse_output).grid(
            row=1, column=2, pady=(4, 0))

        top.columnconfigure(1, weight=1)

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', padx=8)

        # ── Middle: cards list (left) + settings notebook (right) ────
        middle = ttk.PanedWindow(self.root, orient='horizontal')
        middle.pack(fill='both', expand=True, padx=8, pady=4)

        self.cards_panel = CardsPanel(middle, on_cards_changed=self._on_cards_changed)
        middle.add(self.cards_panel, weight=1)

        self.settings_panel = SettingsPanel(
            middle, on_apply_duration_to_all=self._apply_duration_to_all)
        middle.add(self.settings_panel, weight=2)

        # ── Bottom: generate button + progress + status ───────────────
        bottom = ttk.Frame(self.root, padding=(8, 4, 8, 8))
        bottom.pack(fill='x')

        self._generate_btn = ttk.Button(
            bottom, text="Generate", command=self._on_generate)
        self._generate_btn.pack(side='left')

        ttk.Label(bottom, textvariable=self._status).pack(side='left', padx=12)

        self._progress = ttk.Progressbar(bottom, mode='indeterminate', length=140)
        self._progress.pack(side='right')

    # ------------------------------------------------------------------
    # File / directory browsing
    # ------------------------------------------------------------------

    def _browse_session(self):
        path = filedialog.askopenfilename(
            title="Select Session File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self._session_path.set(path)
            self._load_session_file(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self._output_dir.set(path)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_session_file(self, path: str):
        try:
            cards, config = load_session(path)
            self.cards_panel.load_cards(cards)
            if config:
                self.settings_panel.apply_config(config)
                # Restore output dir only if the saved path still exists
                if config.output_dir and os.path.isdir(config.output_dir):
                    self._output_dir.set(config.output_dir)
            self._status.set(f"Loaded {len(cards)} card(s).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load session file:\n{e}")
            self._status.set("Error loading session file.")

    # ------------------------------------------------------------------
    # Card-change callbacks
    # ------------------------------------------------------------------

    def _apply_duration_to_all(self, duration: float, gap: float):
        """Called by SettingsPanel 'Apply to All' — stamps duration and gap on every card."""
        self.cards_panel.apply_global_values(duration, gap)
        self._status.set(f"Applied {duration:.1f}s duration / {gap:.1f}s gap to all cards.")

    def _on_cards_changed(self, cards):
        """Called by CardsPanel.Save — persists cards + current config to the session file."""
        session_path = self._session_path.get().strip()
        if not session_path:
            path = filedialog.asksaveasfilename(
                title="Save Session File",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            if not path:
                return   # user cancelled
            self._session_path.set(path)
            session_path = path
        try:
            config = self._build_config()
            save_session(cards, config, session_path)
            self._status.set("Session saved.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save session:\n{e}")

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _build_config(self) -> SessionConfig:
        values = self.settings_panel.get_config_values()
        return SessionConfig(
            output_dir=self._output_dir.get(),
            **values,
        )

    def _on_generate(self):
        if not self.cards_panel.get_cards():
            messagebox.showwarning("No Cards", "Please load a session file first.")
            return
        output_dir = self._output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("No Output Dir", "Please select an output directory.")
            return

        config = self._build_config()
        self._generate_btn.configure(state='disabled')
        self._progress.start()
        self._status.set("Generating…")

        thread = threading.Thread(
            target=self._run_generation, args=(config,), daemon=True)
        thread.start()

    def _run_generation(self, config: SessionConfig):
        try:
            cards = self.cards_panel.get_cards()
            image_paths = generate_images(cards, config, config.output_dir)
            fcpxml_path = generate_fcpxml(cards, image_paths, config, config.output_dir)
            # Persist the session file (updates saved output_dir too)
            session_path = self._session_path.get().strip()
            if session_path:
                save_session(cards, config, session_path)
            self.root.after(0, self._on_done, len(image_paths), fcpxml_path)
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_done(self, count: int, fcpxml_path: str):
        self._progress.stop()
        self._generate_btn.configure(state='normal')
        self._status.set(f"Done! {count} image(s) + timeline.fcpxml")
        messagebox.showinfo(
            "Done",
            f"Generated {count} card image(s) and FCPXML timeline:\n\n{fcpxml_path}",
        )

    def _on_error(self, error: str):
        self._progress.stop()
        self._generate_btn.configure(state='normal')
        self._status.set("Generation failed.")
        messagebox.showerror("Error", f"Generation failed:\n\n{error}")
