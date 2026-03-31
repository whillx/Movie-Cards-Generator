import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

from core.json_reader import Card


_DEFAULT_DURATION = 2.0
_DEFAULT_GAP      = 0.5


class CardsPanel(ttk.LabelFrame):
    """
    Displays the card list and a live edit area below it.

    Edit flow
    ---------
    - Selecting a row (single click) or adding to selection (Ctrl+click) loads
      the focused card's values into the edit fields.
    - Every keystroke / spinbox change instantly updates the in-memory card
      and refreshes that treeview row — no intermediate button needed.
    - Add    → appends a new blank card and focuses it.
    - Delete → removes all currently selected cards (also bound to <Delete> key).
    - Save   → writes ALL in-memory cards to the JSON file on disk.
    - Clear  → resets every card in memory to empty text + default values;
               does NOT write to disk.
    """

    def __init__(
        self,
        parent,
        on_cards_changed: Optional[Callable[[List[Card]], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, text="Cards", **kwargs)
        self._cards: List[Card] = []
        self._focused_index: int = -1      # card shown in the edit fields
        self._loading: bool = False        # suppress live-update trace while loading
        self._on_cards_changed = on_cards_changed
        self._build()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build(self):
        # ── Treeview ─────────────────────────────────────────────────
        columns = ('num', 'primary', 'secondary', 'duration', 'gap')
        self.tree = ttk.Treeview(
            self, columns=columns, show='headings', selectmode='extended')

        self.tree.heading('num',       text='#')
        self.tree.heading('primary',   text='Primary Text')
        self.tree.heading('secondary', text='Secondary Text')
        self.tree.heading('duration',  text='Dur (s)')
        self.tree.heading('gap',       text='Gap (s)')

        self.tree.column('num',       width=28,  anchor='center', stretch=False)
        self.tree.column('primary',   width=130, anchor='w')
        self.tree.column('secondary', width=130, anchor='w')
        self.tree.column('duration',  width=50,  anchor='center', stretch=False)
        self.tree.column('gap',       width=46,  anchor='center', stretch=False)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Delete>', self._delete_selected)

        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        ttk.Separator(self, orient='horizontal').grid(
            row=1, column=0, columnspan=2, sticky='ew', pady=(4, 0))

        # ── Edit fields ───────────────────────────────────────────────
        edit = ttk.Frame(self, padding=(0, 4, 0, 0))
        edit.grid(row=2, column=0, columnspan=2, sticky='ew')

        self._primary_var   = tk.StringVar()
        self._secondary_var = tk.StringVar()
        self._duration_var  = tk.DoubleVar(value=_DEFAULT_DURATION)
        self._gap_var       = tk.DoubleVar(value=_DEFAULT_GAP)

        # Trace every variable so treeview updates as the user types/spins
        for var in (self._primary_var, self._secondary_var,
                    self._duration_var, self._gap_var):
            var.trace_add('write', self._on_var_change)

        ttk.Label(edit, text="Primary:").grid(row=0, column=0, sticky='w', pady=2)
        ttk.Entry(edit, textvariable=self._primary_var).grid(
            row=0, column=1, sticky='ew', padx=(4, 0), pady=2)

        ttk.Label(edit, text="Secondary:").grid(row=1, column=0, sticky='w', pady=2)
        ttk.Entry(edit, textvariable=self._secondary_var).grid(
            row=1, column=1, sticky='ew', padx=(4, 0), pady=2)

        ttk.Label(edit, text="Duration (s):").grid(row=2, column=0, sticky='w', pady=2)
        ttk.Spinbox(edit, textvariable=self._duration_var,
                    from_=0.1, to=120.0, increment=0.5, width=7).grid(
            row=2, column=1, sticky='w', padx=(4, 0), pady=2)

        ttk.Label(edit, text="Gap (s):").grid(row=3, column=0, sticky='w', pady=2)
        ttk.Spinbox(edit, textvariable=self._gap_var,
                    from_=0.0, to=60.0, increment=0.5, width=7).grid(
            row=3, column=1, sticky='w', padx=(4, 0), pady=2)

        edit.columnconfigure(1, weight=1)

        # ── Buttons ───────────────────────────────────────────────────
        # Icon-style (larger) for Add / Delete; normal size for Save / Clear
        icon_style = ttk.Style()
        icon_style.configure(
            'Icon.TButton',
            font=('TkDefaultFont', 11, 'bold'),
            padding=(8, 4),
        )

        btn_row = ttk.Frame(self, padding=(0, 4, 0, 0))
        btn_row.grid(row=3, column=0, columnspan=2, sticky='ew')

        ttk.Button(btn_row, text="＋ ADD LINE", style='Icon.TButton',
                   command=self._add_card).pack(side='left')
        ttk.Button(btn_row, text="✕ REMOVE LINE", style='Icon.TButton',
                   command=self._delete_selected).pack(side='left', padx=(6, 0))

        ttk.Frame(btn_row, width=12).pack(side='left')   # visual spacer

        ttk.Button(btn_row, text="Save",  command=self._save).pack(side='left')
        ttk.Button(btn_row, text="Clear", command=self._clear).pack(
            side='left', padx=(6, 0))

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_fields(self, card: Card):
        """Load a card's values into the edit fields without triggering live-update."""
        self._loading = True
        self._primary_var.set(card.primary)
        self._secondary_var.set(card.secondary)
        self._duration_var.set(card.duration)
        self._gap_var.set(card.gap)
        self._loading = False

    def _clear_fields(self):
        """Reset edit fields to defaults without triggering live-update."""
        self._loading = True
        self._primary_var.set('')
        self._secondary_var.set('')
        self._duration_var.set(_DEFAULT_DURATION)
        self._gap_var.set(_DEFAULT_GAP)
        self._loading = False

    def _update_tree_row(self, idx: int, card: Card):
        """Update a single treeview row in-place (does not fire <<TreeviewSelect>>)."""
        children = self.tree.get_children()
        if 0 <= idx < len(children):
            self.tree.item(children[idx], values=(
                idx + 1,
                card.primary,
                card.secondary,
                f"{card.duration:.1f}",
                f"{card.gap:.1f}",
            ))

    def _refresh_tree(self):
        """Rebuild the entire treeview from _cards."""
        self.tree.delete(*self.tree.get_children())
        for i, card in enumerate(self._cards, start=1):
            self.tree.insert('', 'end', values=(
                i, card.primary, card.secondary,
                f"{card.duration:.1f}", f"{card.gap:.1f}",
            ))

    def _focus_row(self, idx: int):
        """Select and focus a treeview row by index."""
        children = self.tree.get_children()
        if 0 <= idx < len(children):
            item = children[idx]
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.tree.see(item)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_var_change(self, *_):
        """
        Fires on every edit-field change.
        Instantly updates _cards[_focused_index] and the corresponding treeview row.
        Suppressed while _loading is True (i.e. when we are programmatically
        setting field values).
        """
        if self._loading or self._focused_index < 0:
            return
        try:
            card = Card(
                primary=self._primary_var.get(),
                secondary=self._secondary_var.get(),
                duration=self._duration_var.get(),
                gap=self._gap_var.get(),
            )
        except tk.TclError:
            return   # spinbox has a partial / invalid value — skip this tick
        self._cards[self._focused_index] = card
        self._update_tree_row(self._focused_index, card)

    def _on_select(self, _event=None):
        """Load the focused item's data into the edit fields."""
        focused_iid = self.tree.focus()
        if not focused_iid:
            return
        children = self.tree.get_children()
        if focused_iid not in children:
            return
        idx = children.index(focused_iid)
        self._focused_index = idx
        self._set_fields(self._cards[idx])

    def _add_card(self):
        """Append a new blank card, insert it into the treeview, and focus it."""
        card = Card(primary='', secondary='',
                    duration=_DEFAULT_DURATION, gap=_DEFAULT_GAP)
        self._cards.append(card)
        self.tree.insert('', 'end', values=(
            len(self._cards), '', '', f"{_DEFAULT_DURATION:.1f}", f"{_DEFAULT_GAP:.1f}"))
        self._focused_index = len(self._cards) - 1
        self._focus_row(self._focused_index)
        self._clear_fields()

    def _delete_selected(self, _event=None):
        """Remove all selected cards from memory and the treeview."""
        selected = self.tree.selection()
        if not selected:
            return
        children = list(self.tree.get_children())
        indices = sorted([children.index(iid) for iid in selected], reverse=True)
        for idx in indices:
            del self._cards[idx]

        self._refresh_tree()

        # Focus the nearest surviving card, or clear fields if none left
        if self._cards:
            new_focus = max(0, min(indices[-1], len(self._cards) - 1))
            self._focused_index = new_focus
            self._focus_row(new_focus)
            self._set_fields(self._cards[new_focus])
        else:
            self._focused_index = -1
            self._clear_fields()

    def _save(self):
        """Write ALL in-memory cards to the JSON file."""
        if self._on_cards_changed:
            self._on_cards_changed(list(self._cards))

    def _clear(self):
        """
        Reset every card to empty text and default values in memory only.
        Nothing is written to disk — call Save to persist.
        """
        self._cards = [
            Card(primary='', secondary='', duration=_DEFAULT_DURATION, gap=_DEFAULT_GAP)
            for _ in self._cards
        ]
        self._focused_index = -1
        self._refresh_tree()
        self._clear_fields()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_cards(self, cards: List[Card]) -> None:
        self._cards = list(cards)
        self._focused_index = -1
        self._refresh_tree()
        self._clear_fields()

    def get_cards(self) -> List[Card]:
        return list(self._cards)

    def apply_global_values(self, duration: float, gap: float) -> None:
        """Overwrite duration and gap on every card and notify the caller."""
        for card in self._cards:
            card.duration = duration
            card.gap = gap
        self._refresh_tree()
        if self._focused_index >= 0:
            self._loading = True
            self._duration_var.set(duration)
            self._gap_var.set(gap)
            self._loading = False
        if self._on_cards_changed:
            self._on_cards_changed(list(self._cards))
