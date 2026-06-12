"""
NEXUS v0.1 — Veteran Disability Claims Education Tool
=====================================================
Free, nonprofit, runs 100% locally. No network access. No telemetry.

Run:  python main.py   (requires Python 3.10+ with Tkinter — included
                        in the standard python.org Windows installer)

INTEGRITY: This tool supports LEGITIMATE claims only. Filing a false
claim with the VA is a federal crime (18 U.S.C. 287; 38 U.S.C. 6102).
This application is educational only — it is not legal advice, medical
advice, or VSO representation.
"""

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font, messagebox, ttk

from va_math import Rating, combine
from pages import BenefitsPage, CPPrepPage, RoadmapPage, VaultPage

APP_NAME = "NEXUS"
APP_VERSION = "0.2.0"
BASE_DIR = Path(__file__).resolve().parent
ACK_FILE = BASE_DIR / ".acknowledged"

FRAUD_WARNING = (
    "Filing a false or exaggerated VA claim is a FEDERAL CRIME "
    "(18 U.S.C. \u00a7 287; 38 U.S.C. \u00a7 6102) punishable by fines and "
    "imprisonment, and can result in loss of all benefits."
)
DISCLAIMER = (
    "NEXUS is a free educational tool. It is NOT a lawyer, doctor, or "
    "accredited representative, and nothing in it is legal or medical "
    "advice. You are solely responsible for the accuracy of anything "
    "you file. Always verify with VA.gov and work with an accredited "
    "VSO, attorney, or claims agent."
)

# ---------------------------------------------------------------- colors
BG = "#1e2430"
PANEL = "#283042"
ACCENT = "#c5a55a"      # muted gold
TEXT = "#e8e8e8"
SUBTLE = "#9aa4b5"
WARN_BG = "#3a2626"
WARN_FG = "#f0b9b9"


class DisclaimerGate(tk.Toplevel):
    """Modal shown on every launch until acknowledged this session.
    The main app stays disabled until the user affirmatively accepts."""

    def __init__(self, master, on_accept):
        super().__init__(master, bg=BG)
        self.on_accept = on_accept
        self.title(f"{APP_NAME} — Read Before Using")
        self.geometry("560x420")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._decline)

        tk.Label(self, text="Before you begin", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 16, "bold")).pack(pady=(18, 8))

        body = tk.Label(
            self, justify="left", wraplength=510, bg=BG, fg=TEXT,
            font=("Segoe UI", 10),
            text=(f"\u26a0  {FRAUD_WARNING}\n\n{DISCLAIMER}\n\n"
                  "This tool will help you understand the system and "
                  "organize honest, well-documented claims. It will not "
                  "help you exaggerate, fabricate, or game anything."))
        body.pack(padx=24, anchor="w")

        self.var = tk.IntVar(value=0)
        tk.Checkbutton(
            self, variable=self.var, bg=BG, fg=TEXT, selectcolor=PANEL,
            activebackground=BG, activeforeground=TEXT, wraplength=480,
            justify="left", font=("Segoe UI", 10, "bold"),
            text=("I understand that filing false claims is a federal "
                  "crime, that this tool is educational only, and that I "
                  "am responsible for what I file."),
            command=self._toggle).pack(padx=24, pady=14, anchor="w")

        row = tk.Frame(self, bg=BG)
        row.pack(pady=4)
        self.btn = tk.Button(row, text="I Agree — Continue", state="disabled",
                             command=self._accept, bg=ACCENT, fg="#1a1a1a",
                             font=("Segoe UI", 10, "bold"), padx=16, pady=6,
                             relief="flat", disabledforeground="#777")
        self.btn.pack(side="left", padx=6)
        tk.Button(row, text="Exit", command=self._decline, bg=PANEL, fg=TEXT,
                  font=("Segoe UI", 10), padx=16, pady=6,
                  relief="flat").pack(side="left", padx=6)

    def _toggle(self):
        self.btn.config(state="normal" if self.var.get() else "disabled")

    def _accept(self):
        self.destroy()
        self.on_accept()

    def _decline(self):
        self.master.destroy()
        sys.exit(0)


class CalculatorPage(tk.Frame):
    """VA combined ratings calculator with step-by-step explanation."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.ratings: list[Rating] = []

        tk.Label(self, text="VA Math — Combined Ratings Calculator",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 15, "bold")
                 ).pack(anchor="w", padx=20, pady=(16, 2))
        tk.Label(self, text=("Ratings are not added — each new rating "
                             "applies only to your remaining capacity. "
                             "Add your ratings to see the real math."),
                 bg=BG, fg=SUBTLE, wraplength=640, justify="left",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20)

        entry_row = tk.Frame(self, bg=BG)
        entry_row.pack(anchor="w", padx=20, pady=10)

        tk.Label(entry_row, text="Rating:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.pct = ttk.Combobox(entry_row, width=5, state="readonly",
                                values=[str(p) for p in range(10, 101, 10)])
        self.pct.set("10")
        self.pct.pack(side="left", padx=6)

        tk.Label(entry_row, text="Condition (optional):", bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 0))
        self.label_entry = tk.Entry(entry_row, width=22, bg=PANEL, fg=TEXT,
                                    insertbackground=TEXT, relief="flat")
        self.label_entry.pack(side="left", padx=6, ipady=3)

        self.bi_var = tk.IntVar()
        tk.Checkbutton(entry_row, text="Bilateral (paired limb)",
                       variable=self.bi_var, bg=BG, fg=TEXT,
                       selectcolor=PANEL, activebackground=BG,
                       activeforeground=TEXT,
                       font=("Segoe UI", 9)).pack(side="left", padx=8)

        tk.Button(entry_row, text="+ Add", command=self.add_rating,
                  bg=ACCENT, fg="#1a1a1a", relief="flat", padx=12,
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        tk.Button(entry_row, text="Clear", command=self.clear,
                  bg=PANEL, fg=TEXT, relief="flat", padx=12,
                  font=("Segoe UI", 9)).pack(side="left")

        self.listbox = tk.Listbox(self, bg=PANEL, fg=TEXT, relief="flat",
                                  height=6, font=("Consolas", 10),
                                  selectbackground=ACCENT,
                                  highlightthickness=0)
        self.listbox.pack(fill="x", padx=20)
        self.listbox.bind("<Double-Button-1>", self.remove_selected)
        tk.Label(self, text="Double-click an entry to remove it.",
                 bg=BG, fg=SUBTLE, font=("Segoe UI", 8)).pack(anchor="w",
                                                              padx=20)

        self.result_lbl = tk.Label(self, text="Combined rating: —", bg=BG,
                                   fg=ACCENT, font=("Segoe UI", 18, "bold"))
        self.result_lbl.pack(anchor="w", padx=20, pady=(10, 2))

        self.steps = tk.Text(self, bg=PANEL, fg=TEXT, relief="flat",
                             height=10, wrap="word", font=("Consolas", 9),
                             state="disabled", padx=10, pady=8)
        self.steps.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        tk.Label(self, text=("Compensation amounts change annually — look "
                             "up current rates at va.gov/disability/"
                             "compensation-rates."), bg=BG, fg=SUBTLE,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20,
                                            pady=(0, 10))

    def add_rating(self):
        r = Rating(int(self.pct.get()),
                   self.label_entry.get().strip(),
                   bool(self.bi_var.get()))
        self.ratings.append(r)
        tag = " [bilateral]" if r.bilateral else ""
        self.listbox.insert("end",
                            f" {r.percent:>3}%  {r.label or '(unnamed)'}"
                            f"{tag}")
        self.label_entry.delete(0, "end")
        self.bi_var.set(0)
        self.recalc()

    def remove_selected(self, _event):
        sel = self.listbox.curselection()
        if sel:
            self.ratings.pop(sel[0])
            self.listbox.delete(sel[0])
            self.recalc()

    def clear(self):
        self.ratings.clear()
        self.listbox.delete(0, "end")
        self.recalc()

    def recalc(self):
        res = combine(self.ratings)
        self.result_lbl.config(
            text=f"Combined rating: {res.rounded}%   "
                 f"(exact value {res.exact:.1f})" if self.ratings
            else "Combined rating: —")
        self.steps.config(state="normal")
        self.steps.delete("1.0", "end")
        self.steps.insert("1.0", "\n".join(res.steps))
        self.steps.config(state="disabled")


class GlossaryPage(tk.Frame):
    """Searchable plain-English glossary of VA terminology."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        with open(BASE_DIR / "content" / "glossary.json",
                  encoding="utf-8") as f:
            self.terms = json.load(f)

        tk.Label(self, text="VA Terminology in Plain English", bg=BG,
                 fg=ACCENT, font=("Segoe UI", 15, "bold")
                 ).pack(anchor="w", padx=20, pady=(16, 6))

        search_row = tk.Frame(self, bg=BG)
        search_row.pack(fill="x", padx=20)
        tk.Label(search_row, text="Search:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).pack(side="left")
        self.query = tk.Entry(search_row, bg=PANEL, fg=TEXT, relief="flat",
                              insertbackground=TEXT, width=30)
        self.query.pack(side="left", padx=8, ipady=3)
        self.query.bind("<KeyRelease>", lambda e: self.refresh())

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        self.listbox = tk.Listbox(body, bg=PANEL, fg=TEXT, relief="flat",
                                  width=28, font=("Segoe UI", 10),
                                  selectbackground=ACCENT,
                                  selectforeground="#1a1a1a",
                                  highlightthickness=0, exportselection=False)
        self.listbox.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.show_term)

        self.detail = tk.Text(body, bg=PANEL, fg=TEXT, relief="flat",
                              wrap="word", font=("Segoe UI", 11),
                              state="disabled", padx=14, pady=12)
        self.detail.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.refresh()

    def refresh(self):
        q = self.query.get().lower()
        self.listbox.delete(0, "end")
        for term in sorted(self.terms):
            if q in term.lower() or q in self.terms[term].lower():
                self.listbox.insert("end", f"  {term}")

    def show_term(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        term = self.listbox.get(sel[0]).strip()
        self.detail.config(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", f"{term}\n\n{self.terms[term]}")
        self.detail.config(state="disabled")


class PlaceholderPage(tk.Frame):
    def __init__(self, master, title, blurb):
        super().__init__(master, bg=BG)
        tk.Label(self, text=title, bg=BG, fg=ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w",
                                                     padx=20, pady=(16, 6))
        tk.Label(self, text=blurb + "\n\n(Coming in a future build.)",
                 bg=BG, fg=SUBTLE, wraplength=620, justify="left",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=20)


class NexusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION} — Veteran Claims Education")
        self.geometry("960x640")
        self.configure(bg=BG)
        self.minsize(820, 560)
        self.withdraw()
        DisclaimerGate(self, self._start)

    def _start(self):
        self.deiconify()
        self._build_ui()

    def _build_ui(self):
        # Sidebar -------------------------------------------------------
        sidebar = tk.Frame(self, bg=PANEL, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="NEXUS", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 18, "bold")).pack(pady=(22, 2))
        tk.Label(sidebar, text="by vets, for vets", bg=PANEL, fg=SUBTLE,
                 font=("Segoe UI", 8, "italic")).pack(pady=(0, 18))

        # Content area + persistent warning footer ----------------------
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(right, bg=BG)
        self.content.pack(fill="both", expand=True)
        tk.Label(right, text="\u26a0 " + FRAUD_WARNING, bg=WARN_BG,
                 fg=WARN_FG, font=("Segoe UI", 8), wraplength=720,
                 justify="left", padx=10, pady=5
                 ).pack(side="bottom", fill="x")

        self.pages = {
            "Claim Roadmap": RoadmapPage(self.content),
            "Evidence Vault": VaultPage(self.content),
            "Calculator": CalculatorPage(self.content),
            "Benefits Explorer": BenefitsPage(self.content),
            "C&P Exam Prep": CPPrepPage(self.content),
            "Glossary": GlossaryPage(self.content),
        }

        self.buttons = {}
        for name in self.pages:
            b = tk.Button(sidebar, text=name, anchor="w", relief="flat",
                          bg=PANEL, fg=TEXT, padx=18, pady=8,
                          activebackground=BG, activeforeground=ACCENT,
                          font=("Segoe UI", 10), bd=0,
                          command=lambda n=name: self.show(n))
            b.pack(fill="x")
            self.buttons[name] = b

        tk.Label(sidebar, text=f"v{APP_VERSION} \u2022 100% local\n"
                               "no network \u2022 no tracking",
                 bg=PANEL, fg=SUBTLE, font=("Segoe UI", 7)
                 ).pack(side="bottom", pady=12)

        self.show("Claim Roadmap")

    def show(self, name):
        for n, page in self.pages.items():
            page.pack_forget()
            self.buttons[n].config(bg=PANEL, fg=TEXT)
        self.pages[name].pack(fill="both", expand=True)
        self.buttons[name].config(bg=BG, fg=ACCENT)


if __name__ == "__main__":
    NexusApp().mainloop()
