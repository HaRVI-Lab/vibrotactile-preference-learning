#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Styled Tkinter interface for the haptic preference learning application.

This UI keeps the same behaviour as the classic interface but presents controls
in a more polished layout tailored for user studies.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Sequence

import threading
import time

import numpy as np

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .session import PreferenceSession, SessionMode, GroundTruthKind, moving_average

try:
    from PIL import Image, ImageTk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore
    ImageTk = None  # type: ignore
from pathlib import Path
from datetime import datetime
import json

matplotlib.rcParams.setdefault("font.family", "DejaVu Sans")
matplotlib.rcParams.setdefault("axes.unicode_minus", False)

UNCERTAINTY_DESCRIPTIONS = {
    1: "Very unsure",
    2: "Somewhat unsure",
    3: "Neutral",
    4: "Somewhat sure",
    5: "Very sure",
}


class AudioPreferenceStudyApp:
    """Redesigned Tkinter front-end wrapping :class:`PreferenceSession`."""

    def __init__(
        self,
        root: tk.Tk,
        session: Optional[PreferenceSession] = None,
        fixed_mode: Optional[SessionMode] = None,
    ) -> None:
        self.root = root
        self.root.title("Haptic Preference Learning — Study UI")
        self.root.geometry("1600x980")
        self.root.minsize(1320, 860)
        self.root.configure(bg="#f3f4f8")

        self.session = session or PreferenceSession()
        self.fixed_mode = fixed_mode

        # Runtime state
        self.current_candidate = None
        self.current_audio_data = {}
        self.selected_choice: Optional[str] = None

        # Tk variables
        self.mode_var = tk.StringVar(value=SessionMode.USER.value)
        self.gt_func_var = tk.StringVar(value=GroundTruthKind.GAUSSIAN_CENTER.value)
        self.auto_play_var = tk.BooleanVar(value=False)
        self.level_var = tk.IntVar(value=3)
        self.max_iter_var = tk.IntVar(value=self.session.state.max_iterations)
        self.iter_var = tk.StringVar(value="0")
        self.last_pick_var = tk.StringVar(value="Last choice: N/A")
        self.rec_best_var = tk.StringVar(value="Rec*: N/A")
        self.cand_var_A = tk.StringVar(value="Haptic A: pending")
        self.cand_var_B = tk.StringVar(value="Haptic B: pending")

        # Widgets cached for state updates
        self.progress: Optional[ttk.Progressbar] = None
        self.start_btn: Optional[ttk.Button] = None
        self.stop_btn: Optional[ttk.Button] = None
        self.reset_btn: Optional[ttk.Button] = None
        self.next_btn: Optional[ttk.Button] = None
        self.chooseA: Optional[ttk.Button] = None
        self.chooseB: Optional[ttk.Button] = None
        self.playA: Optional[ttk.Button] = None
        self.playB: Optional[ttk.Button] = None
        self.nb: Optional[ttk.Notebook] = None
        self.tab_audio: Optional[ttk.Frame] = None
        self.tab_log: Optional[ttk.Frame] = None
        self.tab_map: Optional[ttk.Frame] = None
        self.fig_map = None
        self.canvas_map = None
        self.log_text: Optional[tk.Text] = None
        self.gt_label: Optional[ttk.Label] = None
        self.mode_card: Optional[ttk.Labelframe] = None
        self.gt_row: Optional[ttk.Frame] = None
        self.level_buttons: list[ttk.Radiobutton] = []
        self.iter_indicator_var = tk.StringVar(value=f"0 / {self.session.state.max_iterations}")

        self._test_poll_job: Optional[str] = None
        self._last_drawn_iteration: int = -1
        self._exported_data: bool = False
        self._icons: dict[str, tk.PhotoImage] = {}

        self._build_style()
        if self.fixed_mode is not None:
            self.mode_var.set(self.fixed_mode.value)
        self._build_ui()
        self._init_plots()
        self._bind_shortcuts()
        self._apply_fixed_mode_settings()

        if self.fixed_mode is not None:
            self.mode_var.set(self.fixed_mode.value)
            self._update_gt_visibility()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_style(self) -> None:
        self._header_bg = "#f3f4f8"
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Study.TFrame", background=self._header_bg)
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Title.TLabel", font=("Helvetica", 22, "bold"), background="#f3f4f8", foreground="#1f2933")
        style.configure("Subtitle.TLabel", font=("Helvetica", 10), background="#f3f4f8", foreground="#6b7280")
        style.configure("CardTitle.TLabel", font=("Helvetica", 12, "bold"), background="#ffffff", foreground="#1f2933")
        style.configure("Info.TLabel", font=("Helvetica", 11), background="#ffffff", foreground="#374151")
        style.configure("Muted.TLabel", font=("Helvetica", 10), background="#ffffff", foreground="#6b7280")

        style.configure("Accent.TButton", font=("Helvetica", 12, "bold"), padding=(10, 8))
        style.configure("Secondary.TButton", font=("Helvetica", 11), padding=(8, 6))
        style.configure("Danger.TButton", font=("Helvetica", 11), padding=(8, 6), foreground="#b91c1c")
        style.configure("Choice.TButton", font=("Helvetica", 12, "bold"), padding=(12, 10))

        style.configure("Card.TLabelframe", background="#ffffff", borderwidth=0, relief=tk.SOLID, padding=16)
        style.configure("Card.TLabelframe.Label", font=("Helvetica", 12, "bold"), background="#ffffff", foreground="#111827")

        style.configure("Sidebar.TFrame", background="#ffffff")
        style.configure("Metric.TLabel", font=("Helvetica", 24, "bold"), background="#ffffff", foreground="#111827")
        style.configure("MetricCaption.TLabel", font=("Helvetica", 10), background="#ffffff", foreground="#6b7280")

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, style="Study.TFrame", padding=(20, 16))
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container, style="Study.TFrame")
        header.pack(fill=tk.X, pady=(0, 14))
        header_row = ttk.Frame(header, style="Study.TFrame")
        header_row.pack(fill=tk.X)
        ttk.Label(header_row, text="Haptic Preference Learning", style="Title.TLabel").pack(
            side=tk.LEFT, anchor="w"
        )
        branding = ttk.Frame(header_row, style="Study.TFrame")
        branding.pack(side=tk.RIGHT, anchor="n", padx=6)
        max_icon_height = 64
        usc_icon = self._load_icon("usc", max_height=max_icon_height)
        if usc_icon is not None:
            tk.Label(branding, image=usc_icon, bg=self._header_bg, borderwidth=0, highlightthickness=0).pack(
                side=tk.LEFT, padx=(0, 8), anchor="n"
            )
        else:
            tk.Label(branding, text="USC", font=("Helvetica", 22, "bold"), bg=self._header_bg).pack(
                side=tk.LEFT, padx=(0, 8), anchor="n"
            )
        harvi_icon = self._load_icon("harvi", max_height=max_icon_height)
        if harvi_icon is not None:
            tk.Label(branding, image=harvi_icon, bg=self._header_bg, borderwidth=0, highlightthickness=0).pack(
                side=tk.LEFT, anchor="n"
            )
        else:
            tk.Label(branding, text="Harvi Lab", font=("Helvetica", 22, "bold"), bg=self._header_bg).pack(
                side=tk.LEFT, anchor="n"
            )

        ttk.Label(
            header,
            text="Interactive Gaussian-process haptic preference exploration",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Frame(container, style="Study.TFrame")
        body.pack(fill=tk.BOTH, expand=True)

        sidebar = ttk.Frame(body, style="Sidebar.TFrame", padding=(18, 18))
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        sidebar.configure(width=520)

        main_area = ttk.Frame(body, style="Study.TFrame", padding=(0, 0))
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self._build_sidebar(sidebar)
        self._build_main_area(main_area)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        # Session controls
        session_card = ttk.Labelframe(parent, text="Session control", style="Card.TLabelframe")
        session_card.pack(fill=tk.X, pady=(0, 14))

        iter_box = ttk.Frame(session_card, style="Panel.TFrame")
        iter_box.pack(fill=tk.X)
        ttk.Label(iter_box, textvariable=self.iter_indicator_var, style="Metric.TLabel").pack(side=tk.LEFT)
        ttk.Label(iter_box, text="Current / max iterations", style="MetricCaption.TLabel").pack(side=tk.LEFT, padx=(10, 0))

        control_row = ttk.Frame(session_card, style="Panel.TFrame")
        control_row.pack(fill=tk.X, pady=(14, 0))
        self.start_btn = ttk.Button(control_row, text="Start", style="Accent.TButton", command=self._start_session)
        self.stop_btn = ttk.Button(
            control_row, text="Pause", style="Secondary.TButton", command=self._stop_session, state=tk.DISABLED
        )
        self.reset_btn = ttk.Button(
            control_row, text="Reset", style="Secondary.TButton", command=self._reset
        )
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.stop_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=8)
        self.reset_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)

        max_row = ttk.Frame(session_card, style="Panel.TFrame")
        max_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(max_row, text="Max iterations", style="Muted.TLabel").pack(side=tk.LEFT)
        self.max_iter_entry = ttk.Spinbox(
            max_row,
            from_=1,
            to=200,
            textvariable=self.max_iter_var,
            width=6,
            command=self._update_max_iters,
        )
        self.max_iter_entry.pack(side=tk.LEFT, padx=(8, 0))

        progress_card = ttk.Frame(session_card, style="Panel.TFrame")
        progress_card.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(progress_card, text="Progress", style="Muted.TLabel").pack(anchor="w")
        self.progress = ttk.Progressbar(progress_card, orient=tk.HORIZONTAL, mode="determinate",
                                        maximum=self.session.state.max_iterations)
        self.progress.pack(fill=tk.X, pady=(6, 0))

        # Mode settings
        mode_card = ttk.Labelframe(parent, text="Session Mode", style="Card.TLabelframe")
        self.mode_card = mode_card
        if self.fixed_mode is None:
            mode_card.pack(fill=tk.X, pady=(0, 14))
        mode_row = ttk.Frame(mode_card, style="Panel.TFrame")
        mode_row.pack(fill=tk.X)
        if self.fixed_mode is None:
            ttk.Radiobutton(
                mode_row,
                text="User Study",
                variable=self.mode_var,
                value=SessionMode.USER.value,
                command=self._on_mode_change,
            ).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Radiobutton(
                mode_row,
                text="Auto Test",
                variable=self.mode_var,
                value=SessionMode.TEST.value,
                command=self._on_mode_change,
            ).pack(side=tk.LEFT)
        else:
            ttk.Label(mode_row, text=self.mode_var.get(), style="Info.TLabel").pack(side=tk.LEFT)

        gt_row = ttk.Frame(mode_card, style="Panel.TFrame")
        self.gt_row = gt_row
        gt_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(gt_row, text="Ground truth function", style="Muted.TLabel").pack(side=tk.LEFT)
        self.gt_combo = ttk.Combobox(
            gt_row,
            textvariable=self.gt_func_var,
            state="readonly",
            width=24,
            values=[kind.value for kind in GroundTruthKind],
        )
        self.gt_combo.pack(side=tk.LEFT, padx=(6, 0))

        ttk.Checkbutton(mode_card, text="Auto play A → B", variable=self.auto_play_var).pack(anchor="w", pady=(10, 0))

        # Candidate display
        playback_card = ttk.Labelframe(parent, text="Playback & selection", style="Card.TLabelframe")
        playback_card.pack(fill=tk.X, pady=(0, 14))

        audio_row = ttk.Frame(playback_card, style="Panel.TFrame")
        audio_row.pack(fill=tk.X)

        audioA = ttk.Frame(audio_row, style="Panel.TFrame")
        audioA.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10))
        ttk.Label(audioA, text="Haptic A", style="CardTitle.TLabel").pack(anchor="w")
        self.playA = ttk.Button(audioA, text="▶ Play A", style="Secondary.TButton", command=lambda: self._play(1))
        self.playA.pack(fill=tk.X, pady=(6, 0))
        self.chooseA = ttk.Button(
            audioA,
            text="Choose A",
            style="Choice.TButton",
            command=lambda: self._choose("A"),
            state=tk.DISABLED,
        )
        self.chooseA.pack(fill=tk.X, pady=(8, 0))

        audioB = ttk.Frame(audio_row, style="Panel.TFrame")
        audioB.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        ttk.Label(audioB, text="Haptic B", style="CardTitle.TLabel").pack(anchor="w")
        self.playB = ttk.Button(audioB, text="▶ Play B", style="Secondary.TButton", command=lambda: self._play(2))
        self.playB.pack(fill=tk.X, pady=(6, 0))
        self.chooseB = ttk.Button(
            audioB,
            text="Choose B",
            style="Choice.TButton",
            command=lambda: self._choose("B"),
            state=tk.DISABLED,
        )
        self.chooseB.pack(fill=tk.X, pady=(8, 0))

        # Uncertainty selection
        level_card = ttk.Labelframe(parent, text="Uncertainty level", style="Card.TLabelframe")
        level_card.pack(fill=tk.X, pady=(0, 14))

        options_frame = ttk.Frame(level_card, style="Panel.TFrame")
        options_frame.pack(fill=tk.X)
        for col in range(5):
            options_frame.columnconfigure(col, weight=1)

        self.level_buttons.clear()
        for idx, level in enumerate(range(1, 6)):
            btn = ttk.Radiobutton(
                options_frame,
                text=str(level),
                variable=self.level_var,
                value=level,
                command=lambda lvl=level: self._on_level_changed(lvl),
                width=3,
            )
            btn.grid(row=0, column=idx, padx=4, pady=(0, 2))
            ttk.Label(
                options_frame,
                text=UNCERTAINTY_DESCRIPTIONS[level],
                style="Muted.TLabel",
                justify=tk.CENTER,
                wraplength=100,
            ).grid(row=1, column=idx, padx=4, pady=(2, 0))
            self.level_buttons.append(btn)

        self.level_label = ttk.Label(level_card, text="", style="Info.TLabel")
        self.level_label.pack(pady=(10, 0))
        self._on_level_changed(self.level_var.get())

        # Action area
        action_card = ttk.Labelframe(parent, text="Actions", style="Card.TLabelframe")
        action_card.pack(fill=tk.X)
        self.next_btn = ttk.Button(
            action_card,
            text="Submit & next pair",
            style="Accent.TButton",
            command=self._submit_and_next,
            state=tk.DISABLED,
        )
        self.next_btn.pack(fill=tk.X)
        ttk.Label(action_card, textvariable=self.last_pick_var, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

        self._update_gt_visibility()

    def _build_main_area(self, parent: ttk.Frame) -> None:
        summary = ttk.Frame(parent, style="Panel.TFrame", padding=(6, 6))
        summary.pack(fill=tk.X, pady=(0, 8))
        self.gt_label = ttk.Label(summary, text="", style="Muted.TLabel")
        self.gt_label.pack(side=tk.LEFT)
        ttk.Label(summary, textvariable=self.rec_best_var, style="Info.TLabel").pack(side=tk.RIGHT)

        notebook_card = ttk.Frame(parent, style="Panel.TFrame")
        notebook_card.pack(fill=tk.BOTH, expand=True)

        self.nb = ttk.Notebook(notebook_card)
        self.nb.pack(fill=tk.BOTH, expand=True)
        self.tab_audio = ttk.Frame(self.nb)
        self.tab_map = ttk.Frame(self.nb)
        self.tab_log = ttk.Frame(self.nb)
        self._apply_tab_layout_for_mode()

        audio_info = ttk.Frame(self.tab_audio, padding=(12, 10))
        audio_info.pack(fill=tk.X)
        ttk.Label(audio_info, textvariable=self.cand_var_A, style="Info.TLabel").pack(anchor="w")
        ttk.Label(audio_info, textvariable=self.cand_var_B, style="Info.TLabel").pack(anchor="w", pady=(4, 8))

        self.log_text = tk.Text(self.tab_log, height=10, background="#111827", foreground="#f9fafb")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------ #
    # Plot initialisation
    # ------------------------------------------------------------------ #
    def _init_plots(self) -> None:

        self.fig_audio = Figure(figsize=(8.6, 5.4))
        self.canvas_audio = FigureCanvasTkAgg(self.fig_audio, master=self.tab_audio)
        self.canvas_audio.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._draw_audio()

    # ------------------------------------------------------------------ #
    # Layout utilities
    # ------------------------------------------------------------------ #
    def _apply_tab_layout_for_mode(self) -> None:
        try:
            for tab_id in list(self.nb.tabs()):
                self.nb.forget(tab_id)
        except Exception:
            pass

        if self.mode_var.get() == SessionMode.USER.value:
            self.nb.add(self.tab_audio, text="Waveforms")
            self.nb.add(self.tab_log, text="Log")
            for child in self.tab_map.winfo_children():
                child.destroy()
            self.fig_map = None
            self.canvas_map = None
        else:
            self.nb.add(self.tab_audio, text="Waveforms")
            self.nb.add(self.tab_map, text="GT vs GP")
            self.nb.add(self.tab_log, text="Log")
            for child in self.tab_map.winfo_children():
                child.destroy()
            self.fig_map = Figure(figsize=(11, 6.5))
            self.canvas_map = FigureCanvasTkAgg(self.fig_map, master=self.tab_map)
            self.canvas_map.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _load_icon(self, name: str, max_height: int = 64) -> Optional[tk.PhotoImage]:
        if name in self._icons:
            return self._icons[name]
        assets_dir = Path(__file__).resolve().parent / "logo"
        candidate_paths = []
        for path in assets_dir.glob("*"):
            if not path.is_file():
                continue
            if path.stem.lower() == name.lower():
                candidate_paths.append(path)
        if not candidate_paths:
            for ext in (".png", ".gif", ".jpg", ".jpeg"):
                path = assets_dir / f"{name}{ext}"
                if path.is_file():
                    candidate_paths.append(path)
        for path in candidate_paths:
            try:
                if Image is not None and ImageTk is not None:
                    with Image.open(path) as img:
                        img = img.convert("RGBA")
                        if max_height and img.height > 0:
                            ratio = max_height / img.height
                            new_width = max(int(img.width * ratio), 1)
                            resample = getattr(Image, "LANCZOS", Image.BICUBIC)
                            img = img.resize((new_width, max_height), resample=resample)
                        photo = ImageTk.PhotoImage(img)
                else:
                    photo = tk.PhotoImage(file=path)
                    if max_height and photo.height() > max_height:
                        factor = max(int(photo.height() / max_height), 1)
                        photo = photo.subsample(factor)
            except Exception:
                photo = None
            else:
                if photo is not None:
                    self._icons[name] = photo
                    return photo
        return None

    def _update_gt_visibility(self) -> None:
        if getattr(self, "gt_combo", None) is None:
            return
        if self.mode_var.get() == SessionMode.TEST.value:
            self.gt_combo.configure(state="readonly")
            if self.gt_row is not None and self.gt_row.winfo_manager() == "":
                self.gt_row.pack(fill=tk.X, pady=(8, 0))
            if self.gt_label is not None:
                self.gt_label.configure(text="GT*: [45.0, 50.0, 50.0, 0.0]")
        else:
            self.gt_combo.configure(state="disabled")
            if self.gt_row is not None and self.gt_row.winfo_manager() != "":
                self.gt_row.pack_forget()
            if self.gt_label is not None:
                self.gt_label.configure(text="")

    def _apply_fixed_mode_settings(self) -> None:
        if self.fixed_mode is None:
            return
        if self.mode_card is not None and self.mode_card.winfo_manager() != "":
            self.mode_card.pack_forget()
        self.mode_var.set(self.fixed_mode.value)

        if self.fixed_mode is SessionMode.USER:
            if self.gt_row is not None and self.gt_row.winfo_manager() != "":
                self.gt_row.pack_forget()
            if self.gt_label is not None:
                self.gt_label.configure(text="")
            if self.gt_combo is not None:
                self.gt_combo.configure(state="disabled")
        elif self.fixed_mode is SessionMode.TEST:
            if self.gt_row is not None and self.gt_row.winfo_manager() == "":
                self.gt_row.pack(fill=tk.X, pady=(8, 0))
            if self.gt_combo is not None:
                self.gt_combo.configure(state="readonly")
            if self.chooseA is not None:
                self.chooseA.config(state=tk.DISABLED)
            if self.chooseB is not None:
                self.chooseB.config(state=tk.DISABLED)
            if self.next_btn is not None:
                if self.next_btn.winfo_manager():
                    self.next_btn.pack_forget()
            self.last_pick_var.set("Automatic test in progress — system decides")

    # ------------------------------------------------------------------ #
    # Event binding
    # ------------------------------------------------------------------ #
    def _bind_shortcuts(self) -> None:
        self.root.bind("<Key-a>", lambda _: self._choose("A"))
        self.root.bind("<Key-b>", lambda _: self._choose("B"))
        self.root.bind("<Return>", lambda _: self._submit_and_next())

    # ------------------------------------------------------------------ #
    # Session control
    # ------------------------------------------------------------------ #
    def _start_session(self) -> None:
        try:
            mode = SessionMode.USER if self.mode_var.get() == SessionMode.USER.value else SessionMode.TEST
            max_iters = int(self.max_iter_var.get())
            gt_label = self.gt_func_var.get()
            self.session.start(mode, max_iters, gt_label)
        except Exception as exc:
            messagebox.showerror("Start error", str(exc))
            return

        self.iter_var.set("0")
        self.iter_indicator_var.set(f"0 / {self.session.state.max_iterations}")
        self._exported_data = False
        if self.progress is not None:
            self.progress.configure(maximum=self.session.state.max_iterations, value=0)
        self.last_pick_var.set("Last choice: N/A")
        self.rec_best_var.set("Rec*: N/A")
        self.cand_var_A.set("Haptic A: pending")
        self.cand_var_B.set("Haptic B: pending")
        self.level_var.set(3)
        self._on_level_changed(self.level_var.get())
        self.current_candidate = None
        self.current_audio_data.clear()
        self._last_drawn_iteration = -1
        self._cancel_test_poll()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.chooseA.config(state=tk.NORMAL if mode is SessionMode.USER else tk.DISABLED)
        self.chooseB.config(state=tk.NORMAL if mode is SessionMode.USER else tk.DISABLED)

        if mode is SessionMode.TEST:
            ideal = self.session.ideal_phys
            self.gt_label.configure(
                text=f"GT*: [{ideal[0]:.1f}, {ideal[1]:.1f}, {ideal[2]:.1f}, {ideal[3]:.1f}]"
            )
            self._log("Automatic test started.\n")
            self.session.run_test_loop()
            self._schedule_test_poll()
        else:
            self.gt_label.configure(text="")
            self._log("User study started.\n")
            self._prepare_user_query()

    def _stop_session(self) -> None:
        self.session.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.DISABLED)
        self.chooseA.config(state=tk.DISABLED)
        self.chooseB.config(state=tk.DISABLED)
        self._cancel_test_poll()

    def _reset(self) -> None:
        self.session.reset()
        self.current_candidate = None
        self.current_audio_data.clear()
        self.iter_var.set("0")
        if self.progress is not None:
            self.progress.configure(value=0)
        self.iter_indicator_var.set(f"0 / {self.session.state.max_iterations}")
        self.last_pick_var.set("Last choice: N/A")
        self.rec_best_var.set("Rec*: N/A")
        self.cand_var_A.set("Haptic A: pending")
        self.cand_var_B.set("Haptic B: pending")
        self.level_var.set(3)
        self._on_level_changed(self.level_var.get())
        self._exported_data = False
        self._cancel_test_poll()
        self.log_text.delete("1.0", tk.END)
        self._draw_audio()
        if self.session.state.mode is SessionMode.TEST:
            self._draw_map()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.NORMAL)
        self.chooseA.config(state=tk.DISABLED)
        self.chooseB.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self._update_gt_visibility()

    def _update_max_iters(self) -> None:
        try:
            value = int(self.max_iter_var.get())
        except Exception:
            value = self.session.state.max_iterations
        value = max(1, value)
        self.session.state.max_iterations = value
        if self.progress is not None:
            self.progress.configure(maximum=value)
        self.iter_indicator_var.set(f"{self.session.state.current_iteration} / {value}")

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def _prepare_user_query(self) -> None:
        try:
            candidate = self.session.generate_user_query()
        except Exception as exc:
            messagebox.showerror("Generation error", str(exc))
            return

        if not candidate:
            messagebox.showwarning("Notice", "Session is not running.")
            return

        self.current_candidate = candidate
        self.current_audio_data = candidate.audio_data
        p1_phys, p2_phys = candidate.physical
        self.cand_var_A.set(
            f"A: amplitude {p1_phys[0]:.1f} | frequency {p1_phys[1]:.1f} | density {p1_phys[2]:.1f} | gradient {p1_phys[3]:.1f}"
        )
        self.cand_var_B.set(
            f"B: amplitude {p2_phys[0]:.1f} | frequency {p2_phys[1]:.1f} | density {p2_phys[2]:.1f} | gradient {p2_phys[3]:.1f}"
        )

        self.selected_choice = None
        self.last_pick_var.set("Last choice: N/A")
        self.chooseA.config(state=tk.NORMAL)
        self.chooseB.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.DISABLED)

        self._draw_audio()
        if self.session.state.mode is SessionMode.TEST:
            self._draw_map()

        if self.auto_play_var.get():
            def auto_play() -> None:
                try:
                    self.session.audio.stop_audio()
                    self.session.audio.play_audio(self.current_audio_data[1]["x"], blocking=True)
                    time.sleep(0.1)
                    self.session.audio.stop_audio()
                    self.session.audio.play_audio(self.current_audio_data[2]["x"], blocking=True)
                    self.session.audio.stop_audio()
                except Exception:
                    pass

            threading.Thread(target=auto_play, daemon=True).start()

    def _submit_and_next(self) -> None:
        if self.session.state.mode is not SessionMode.USER or not self.current_candidate:
            return
        if self.selected_choice not in ("A", "B"):
            messagebox.showwarning("Notice", "Please select a preferred haptic first.")
            return
        try:
            self.session.audio.stop_audio()
        except Exception:
            pass
        try:
            level = int(self.level_var.get())
            self.session.record_user_choice(self.selected_choice, level)
        except Exception as exc:
            messagebox.showerror("Submit error", str(exc))
            return

        iteration = self.session.state.current_iteration
        self.iter_var.set(str(iteration))
        self.iter_indicator_var.set(f"{iteration} / {self.session.state.max_iterations}")
        if self.progress is not None:
            self.progress.configure(value=iteration)
        self._log_pair("User", level, self.selected_choice)
        self.selected_choice = None
        self.next_btn.config(state=tk.DISABLED)

        self._update_recommendation_label()
        if self.session.state.mode is SessionMode.TEST:
            self._draw_map()

        if iteration >= self.session.state.max_iterations:
            self.chooseA.config(state=tk.DISABLED)
            self.chooseB.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL)
            if self.session.rec_best.parameters is not None:
                params = self.session.rec_best.parameters
                self._log(
                    "[Final] Recommendation: "
                    f"[{params[0]:.2f}, {params[1]:.2f}, {params[2]:.2f}, {params[3]:.2f}]\n"
                )
            else:
                self._log("[Final] Recommendation: N/A\n")
            self._persist_study_data()
            messagebox.showinfo("Complete", f"Finished {iteration} iterations.")
            return
        else:
            self._prepare_user_query()

    def _on_level_changed(self, *_args) -> None:
        val = int(self.level_var.get())
        val = max(1, min(5, val))
        self.level_var.set(val)
        self.level_label.config(text=f"Current level: {val} ({UNCERTAINTY_DESCRIPTIONS.get(val, '')})")

    def _choose(self, label: str) -> None:
        if self.session.state.mode is not SessionMode.USER:
            return
        if not self.current_candidate:
            return
        if label not in ("A", "B"):
            return
        self.selected_choice = label
        self.last_pick_var.set(f"Last choice: {label}")
        self.next_btn.config(state=tk.NORMAL)

    def _play(self, which: int) -> None:
        if which not in (1, 2) or which not in self.current_audio_data:
            messagebox.showwarning("Notice", "Start the session to load haptic clips.")
            return
        try:
            self.session.audio.stop_audio()
            data = self.current_audio_data[which]["x"]
            ok = self.session.audio.play_audio(data, blocking=False)
            if not ok:
                messagebox.showwarning("Haptic", "Playback failed. Please check the haptic device.")
        except Exception as exc:
            messagebox.showerror("Haptic error", str(exc))

    def _persist_study_data(self) -> None:
        if self._exported_data:
            return
        snapshot = {
            "mode": self.session.state.mode.value,
            "max_iterations": self.session.state.max_iterations,
            "completed_iterations": self.session.state.current_iteration,
            "preferences": self.session.preference_history,
            "uncertainties": self.session.uncertainty_history,
            "info_gain": self.session.info_gain_history,
            "query_distance": self.session.query_distance_history,
            "parameters": [list(map(float, np.asarray(p).tolist())) for p in self.session.parameter_history_phys],
            "recommendation_history": [list(map(float, np.asarray(p).tolist())) for p in self.session.rec_history_phys],
            "final_recommendation": (list(map(float, np.asarray(self.session.rec_best.parameters).tolist())) if self.session.rec_best.parameters is not None else None),
            "timestamp": datetime.now().isoformat(),
        }
        base_dir = Path.cwd() / "data"
        base_dir.mkdir(exist_ok=True)
        date_prefix = datetime.now().strftime("%Y%m%d")
        counter = 1
        while True:
            exp_id = f"{date_prefix}_{counter:02d}"
            exp_dir = base_dir / exp_id
            if not exp_dir.exists():
                exp_dir.mkdir()
                break
            counter += 1
        json_path = exp_dir / "session.json"
        json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        log_text = self.log_text.get("1.0", tk.END).strip() if self.log_text is not None else ""
        (exp_dir / "log.txt").write_text(log_text, encoding="utf-8")
        self._exported_data = True

    def _poll_test_session(self) -> None:
        if self.session.state.mode is not SessionMode.TEST:
            self._cancel_test_poll()
            return

        iteration = self.session.state.current_iteration
        self.iter_var.set(str(iteration))
        self.iter_indicator_var.set(f"{iteration} / {self.session.state.max_iterations}")
        if self.progress is not None:
            self.progress.configure(value=min(iteration, self.session.state.max_iterations))

        if self.session.rec_best.parameters is not None:
            params = self.session.rec_best.parameters
            self.rec_best_var.set(
                f"Rec*: [{params[0]:.1f}, {params[1]:.1f}, {params[2]:.1f}, {params[3]:.1f}]"
            )

        if iteration != self._last_drawn_iteration:
            self._draw_map()
            self._last_drawn_iteration = iteration

        if not self.session.state.running:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.reset_btn.config(state=tk.NORMAL)
            self._cancel_test_poll()
            if self.session.rec_best.parameters is not None:
                dist = float(np.linalg.norm(self.session.rec_best.parameters - self.session.ideal_phys))
                params = self.session.rec_best.parameters
                self._log(
                    "[Final-Test] Recommendation: "
                    f"[{params[0]:.2f}, {params[1]:.2f}, {params[2]:.2f}, {params[3]:.2f}]\n"
                )
                messagebox.showinfo(
                    "Recommendation",
                    (
                        "Automatic test complete.\n"
                        f"Recommended parameters:\n"
                        f"[{self.session.rec_best.parameters[0]:.2f}, {self.session.rec_best.parameters[1]:.2f}, "
                        f"{self.session.rec_best.parameters[2]:.2f}, {self.session.rec_best.parameters[3]:.2f}]\n"
                        f"Distance to GT: {dist:.3f}"
                    ),
                )
            else:
                messagebox.showinfo("Test complete", f"Ran {iteration} iterations.")
            self._persist_study_data()
            return

        self._test_poll_job = self.root.after(250, self._poll_test_session)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _update_recommendation_label(self) -> None:
        rec = self.session.rec_best.parameters
        if rec is None:
            self.rec_best_var.set("Rec*: N/A")
        else:
            self.rec_best_var.set(
                f"Rec*: [{rec[0]:.1f}, {rec[1]:.1f}, {rec[2]:.1f}, {rec[3]:.1f}]"
            )

    def _schedule_test_poll(self) -> None:
        self._test_poll_job = self.root.after(250, self._poll_test_session)

    def _cancel_test_poll(self) -> None:
        if self._test_poll_job is not None:
            self.root.after_cancel(self._test_poll_job)
            self._test_poll_job = None

    def _log(self, text: str) -> None:
        try:
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _fmt_phys(self, phys: Sequence[float]) -> str:
        return f"[A={phys[0]:.2f}, F={phys[1]:.2f}, D={phys[2]:.2f}, G={phys[3]:.2f}]"

    def _log_pair(self, mode_tag: str, level: int, choice: str) -> None:
        if not self.current_candidate:
            return
        p1_phys, p2_phys = self.current_candidate.physical
        extra = []
        if not np.isnan(self.current_candidate.info_gain):
            extra.append(f"EIG={self.current_candidate.info_gain:.3f}")
        extra.append(f"Dist={self.current_candidate.query_distance:.3f}")
        extra_str = (" | " + ", ".join(extra)) if extra else ""
        line = (
            f"[{mode_tag}] Iter {self.session.state.current_iteration:02d} | "
            f"A {self._fmt_phys(p1_phys)} vs B {self._fmt_phys(p2_phys)} | "
            f"pick={choice} | level={level}{extra_str}\n"
        )
        self._log(line)

    # ------------------------------------------------------------------ #
    # Plotting (reused from classic UI)
    # ------------------------------------------------------------------ #
    def _draw_audio(self) -> None:
        if self.fig_audio is None or self.canvas_audio is None:
            return
        self.fig_audio.clear()
        ax = self.fig_audio.add_subplot(111)
        if 1 in self.current_audio_data and 2 in self.current_audio_data:
            t1 = self.current_audio_data[1]["t"]
            x1 = self.current_audio_data[1]["x"]
            t2 = self.current_audio_data[2]["t"]
            x2 = self.current_audio_data[2]["x"]
            ax.plot(t1, x1, label="Haptic A", linewidth=1.2)
            ax.plot(t2, x2, label="Haptic B", linewidth=1.2, alpha=0.85)
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No haptic yet — start the session", ha="center", va="center")
            ax.set_xlim(0, 1)
            ax.set_ylim(-1, 1)
        ax.set_title("Current waveforms")
        ax.grid(True, alpha=0.3)
        self.fig_audio.tight_layout()
        self.canvas_audio.draw_idle()

    def _draw_map(self) -> None:
        if self.session.state.mode is not SessionMode.TEST:
            return
        if self.fig_map is None or self.canvas_map is None or self.session.gp is None:
            return

        gp = self.session.gp
        param_ranges = self.session.audio.param_ranges
        self.fig_map.clear()
        ax11 = self.fig_map.add_subplot(221, projection="3d")
        ax12 = self.fig_map.add_subplot(222, projection="3d")
        ax21 = self.fig_map.add_subplot(223, projection="3d")
        ax22 = self.fig_map.add_subplot(224, projection="3d")

        xs = np.linspace(*param_ranges["amplitude"], 31)
        ys = np.linspace(*param_ranges["frequency"], 31)
        X, Y = np.meshgrid(xs, ys)
        Z_gt = np.zeros_like(X)
        Z_gp = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                phys = [X[i, j], Y[i, j], 50.0, 0.0]
                Z_gt[i, j] = self.session.gt_value(phys)
                try:
                    mu = gp.mean1pt(gp.normalize_parameters(phys))
                    Z_gp[i, j] = float(mu[0] if isinstance(mu, (list, tuple, np.ndarray)) else mu)
                except Exception:
                    Z_gp[i, j] = 0.0
        ax11.plot_surface(X, Y, Z_gt, cmap="coolwarm", alpha=0.9)
        ax11.set_title("GT: Amp×Freq @ (D=50,G=0)")
        ax11.set_xlabel("Amp")
        ax11.set_ylabel("Freq")
        ax11.set_zlabel("GT")
        ax12.plot_surface(X, Y, Z_gp, cmap="viridis", alpha=0.9)
        ax12.set_title("GP: Amp×Freq @ (D=50,G=0)")
        ax12.set_xlabel("Amp")
        ax12.set_ylabel("Freq")
        ax12.set_zlabel("GP mean")

        ideal = self.session.ideal_phys
        ax11.scatter(ideal[0], ideal[1], self.session.gt_value([ideal[0], ideal[1], 50.0, 0.0]), marker="*", s=120)
        if self.session.rec_best.parameters is not None:
            rec = self.session.rec_best.parameters
            zc = self.session.gt_value([rec[0], rec[1], 50.0, 0.0])
            ax11.scatter(rec[0], rec[1], zc, marker="x", s=80)
            try:
                mu = gp.mean1pt(gp.normalize_parameters([rec[0], rec[1], 50.0, 0.0]))
                zgp = float(mu[0] if isinstance(mu, (list, tuple, np.ndarray)) else mu)
            except Exception:
                zgp = 0.0
            ax12.scatter(rec[0], rec[1], zgp, marker="x", s=80)
        try:
            mu_star = gp.mean1pt(gp.normalize_parameters([ideal[0], ideal[1], 50.0, 0.0]))
            mu_star = float(mu_star[0] if isinstance(mu_star, (list, tuple, np.ndarray)) else mu_star)
        except Exception:
            mu_star = 0.0
        ax12.scatter(ideal[0], ideal[1], mu_star, marker="*", s=120)

        xs = np.linspace(*param_ranges["density"], 31)
        ys = np.linspace(*param_ranges["gradient"], 31)
        X, Y = np.meshgrid(xs, ys)
        Z_gt = np.zeros_like(X)
        Z_gp = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                phys = [45.0, 50.0, X[i, j], Y[i, j]]
                Z_gt[i, j] = self.session.gt_value(phys)
                try:
                    mu = gp.mean1pt(gp.normalize_parameters(phys))
                    Z_gp[i, j] = float(mu[0] if isinstance(mu, (list, tuple, np.ndarray)) else mu)
                except Exception:
                    Z_gp[i, j] = 0.0

        ax21.plot_surface(X, Y, Z_gt, cmap="coolwarm", alpha=0.9)
        ax21.set_title("GT: Density×Gradient @ (A=45,F=50)")
        ax21.set_xlabel("Density")
        ax21.set_ylabel("Gradient")
        ax21.set_zlabel("GT")
        ax22.plot_surface(X, Y, Z_gp, cmap="viridis", alpha=0.9)
        ax22.set_title("GP: Density×Gradient @ (A=45,F=50)")
        ax22.set_xlabel("Density")
        ax22.set_ylabel("Gradient")
        ax22.set_zlabel("GP mean")

        ax21.scatter(ideal[2], ideal[3], self.session.gt_value([45.0, 50.0, ideal[2], ideal[3]]), marker="*", s=120)
        if self.session.rec_best.parameters is not None:
            rec = self.session.rec_best.parameters
            zc = self.session.gt_value([45.0, 50.0, rec[2], rec[3]])
            ax21.scatter(rec[2], rec[3], zc, marker="x", s=80)
            try:
                mu = gp.mean1pt(gp.normalize_parameters([45.0, 50.0, rec[2], rec[3]]))
                zgp = float(mu[0] if isinstance(mu, (list, tuple, np.ndarray)) else mu)
            except Exception:
                zgp = 0.0
            ax22.scatter(rec[2], rec[3], zgp, marker="x", s=80)
        try:
            mu_star = gp.mean1pt(gp.normalize_parameters([45.0, 50.0, ideal[2], ideal[3]]))
            mu_star = float(mu_star[0] if isinstance(mu_star, (list, tuple, np.ndarray)) else mu_star)
        except Exception:
            mu_star = 0.0
        ax22.scatter(ideal[2], ideal[3], mu_star, marker="*", s=120)

        self.fig_map.tight_layout()
        self.canvas_map.draw_idle()

    # ------------------------------------------------------------------ #
    def _on_mode_change(self) -> None:
        self._apply_tab_layout_for_mode()
        self._update_gt_visibility()

    def _on_close(self) -> None:
        try:
            self.session.audio.stop_audio()
            close_fn = getattr(self.session.audio, "close", None)
            if callable(close_fn):
                close_fn()
        finally:
            self.root.destroy()


def main() -> int:
    print("Haptic Preference Learning — Study UI")
    print("=" * 48)
    try:
        root = tk.Tk()
        app = AudioPreferenceStudyApp(root)
        root.mainloop()
    except Exception as exc:
        print(f"Failed to launch study UI: {exc}")
        return 1
    return 0


def user_main() -> int:
    print("Haptic Preference Learning — Study UI (User Study)")
    print("=" * 60)
    try:
        root = tk.Tk()
        app = AudioPreferenceStudyApp(root, fixed_mode=SessionMode.USER)
        root.mainloop()
    except Exception as exc:
        print(f"Failed to launch user study UI: {exc}")
        return 1
    return 0


def test_main() -> int:
    print("Haptic Preference Learning — Study UI (Auto Test)")
    print("=" * 58)
    try:
        root = tk.Tk()
        app = AudioPreferenceStudyApp(root, fixed_mode=SessionMode.TEST)
        root.mainloop()
    except Exception as exc:
        print(f"Failed to launch auto test UI: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
