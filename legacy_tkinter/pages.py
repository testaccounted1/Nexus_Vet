"""NEXUS — v0.2 pages: Evidence Vault, Roadmap, Benefits, C&P Prep."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from vault import CLAIM_TYPES, CONDITION_LIBRARY, Vault, evidence_items_for

BASE_DIR = Path(__file__).resolve().parent
BG = "#1e2430"
PANEL = "#283042"
ACCENT = "#c5a55a"
TEXT = "#e8e8e8"
SUBTLE = "#9aa4b5"
FLAG = "#e8a0a0"
OK = "#9fd49f"

with open(BASE_DIR / "content" / "education.json", encoding="utf-8") as f:
    EDU = json.load(f)


def _heading(parent, text):
    tk.Label(parent, text=text, bg=BG, fg=ACCENT,
             font=("Segoe UI", 15, "bold")).pack(anchor="w",
                                                 padx=20, pady=(16, 6))


class _ScrollText(tk.Frame):
    """Read-only scrollable text panel with simple section styling."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.text = tk.Text(self, bg=PANEL, fg=TEXT, relief="flat",
                            wrap="word", font=("Segoe UI", 11),
                            padx=16, pady=12, spacing3=6)
        sb = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.tag_configure("h", foreground=ACCENT,
                                font=("Segoe UI", 12, "bold"),
                                spacing1=10)
        self.text.tag_configure("sub", foreground=SUBTLE,
                                font=("Segoe UI", 10))

    def add_section(self, title, body):
        self.text.insert("end", title + "\n", "h")
        self.text.insert("end", body + "\n")

    def finish(self):
        self.text.config(state="disabled")


class RoadmapPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        _heading(self, "Claim Roadmap — File It Yourself, Free")
        tk.Label(self, text=("The complete DIY path from records to "
                             "decision review. Filing costs $0 at every "
                             "step."), bg=BG, fg=SUBTLE,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        panel = _ScrollText(self)
        panel.pack(fill="both", expand=True, padx=20, pady=10)
        for title, body in EDU["roadmap"]:
            panel.add_section(title, body)
        panel.finish()


class BenefitsPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        _heading(self, "Benefits Explorer")
        tk.Label(self, text=("Every major benefit tied to a rating — "
                             "including the ones most commonly left on "
                             "the table."), bg=BG, fg=SUBTLE,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox = tk.Listbox(body, bg=PANEL, fg=TEXT, relief="flat",
                                  width=32, font=("Segoe UI", 10),
                                  selectbackground=ACCENT,
                                  selectforeground="#1a1a1a",
                                  highlightthickness=0,
                                  exportselection=False)
        self.listbox.pack(side="left", fill="y")
        for name in EDU["benefits"]:
            self.listbox.insert("end", f"  {name}")
        self.listbox.bind("<<ListboxSelect>>", self._show)
        self.detail = tk.Text(body, bg=PANEL, fg=TEXT, relief="flat",
                              wrap="word", font=("Segoe UI", 11),
                              state="disabled", padx=14, pady=12)
        self.detail.pack(side="left", fill="both", expand=True,
                         padx=(10, 0))

    def _show(self, _e):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0]).strip()
        self.detail.config(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", f"{name}\n\n{EDU['benefits'][name]}")
        self.detail.config(state="disabled")


class CPPrepPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        _heading(self, "C&P Exam Prep — Accurate, Complete, Honest")
        panel = _ScrollText(self)
        panel.pack(fill="both", expand=True, padx=20, pady=10)
        for title, body in EDU["cp_prep"]:
            panel.add_section(title, body)
        panel.finish()


class VaultPage(tk.Frame):
    """Per-condition evidence checklist with gap flags and export."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.vault = Vault()
        _heading(self, "Evidence Vault")
        tk.Label(self, text=("Track each condition against the evidence "
                             "the VA actually decides on. Gaps are "
                             "flagged so you can fix them BEFORE filing. "
                             "Data stays in nexus_data.json on this "
                             "computer only."),
                 bg=BG, fg=SUBTLE, wraplength=660, justify="left",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20)

        # ---- add-condition row
        row = tk.Frame(self, bg=BG)
        row.pack(anchor="w", padx=20, pady=8)
        tk.Label(row, text="Condition name:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.name_e = tk.Entry(row, width=20, bg=PANEL, fg=TEXT,
                               insertbackground=TEXT, relief="flat")
        self.name_e.grid(row=1, column=0, padx=(0, 8), ipady=3)
        tk.Label(row, text="Evidence template:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        self.type_cb = ttk.Combobox(row, width=26, state="readonly",
                                    values=list(CONDITION_LIBRARY))
        self.type_cb.set("Other / Not Listed")
        self.type_cb.grid(row=1, column=1, padx=(0, 8))
        tk.Label(row, text="Claim type:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")
        self.claim_cb = ttk.Combobox(row, width=11, state="readonly",
                                     values=CLAIM_TYPES)
        self.claim_cb.set("Direct")
        self.claim_cb.grid(row=1, column=2, padx=(0, 8))
        tk.Button(row, text="+ Add", command=self._add, bg=ACCENT,
                  fg="#1a1a1a", relief="flat", padx=12,
                  font=("Segoe UI", 9, "bold")).grid(row=1, column=3)

        # ---- main split: condition list | checklist
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(4, 8))
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y")
        self.listbox = tk.Listbox(left, bg=PANEL, fg=TEXT, relief="flat",
                                  width=30, font=("Segoe UI", 10),
                                  selectbackground=ACCENT,
                                  selectforeground="#1a1a1a",
                                  highlightthickness=0,
                                  exportselection=False)
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._render())
        btns = tk.Frame(left, bg=BG)
        btns.pack(fill="x", pady=4)
        tk.Button(btns, text="Remove", command=self._remove, bg=PANEL,
                  fg=TEXT, relief="flat", font=("Segoe UI", 8),
                  padx=8).pack(side="left")
        tk.Button(btns, text="Export Claim Summary", command=self._export,
                  bg=ACCENT, fg="#1a1a1a", relief="flat",
                  font=("Segoe UI", 8, "bold"), padx=8).pack(side="left",
                                                             padx=6)

        right_wrap = tk.Frame(body, bg=PANEL)
        right_wrap.pack(side="left", fill="both", expand=True,
                        padx=(10, 0))
        self.canvas = tk.Canvas(right_wrap, bg=PANEL,
                                highlightthickness=0)
        sb = ttk.Scrollbar(right_wrap, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=PANEL)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self._refresh_list()

    # ---- actions ------------------------------------------------------
    def _add(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showinfo("NEXUS", "Enter a condition name first.")
            return
        self.vault.add_condition(name, self.type_cb.get(),
                                 self.claim_cb.get())
        self.name_e.delete(0, "end")
        self._refresh_list(select_last=True)

    def _remove(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        cond = self.vault.conditions[sel[0]]
        if messagebox.askyesno("NEXUS", f"Remove '{cond['name']}' and its "
                                        "checklist?"):
            self.vault.remove_condition(sel[0])
            self._refresh_list()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="nexus_claim_summary.txt",
            filetypes=[("Text file", "*.txt")])
        if path:
            Path(path).write_text(self.vault.export_summary(),
                                  encoding="utf-8")
            messagebox.showinfo(
                "NEXUS", "Summary exported.\n\nYou can file yourself at "
                "VA.gov, or hand this to a free accredited VSO for a "
                "second opinion.")

    # ---- rendering ----------------------------------------------------
    def _refresh_list(self, select_last=False):
        self.listbox.delete(0, "end")
        for c in self.vault.conditions:
            n_gaps = len(self.vault.gaps_for(c))
            badge = "\u2713" if n_gaps == 0 else f"\u26a0 {n_gaps}"
            self.listbox.insert("end", f" {badge}  {c['name']}")
        if select_last and self.vault.conditions:
            self.listbox.selection_set("end")
        self._render()

    def _render(self):
        for w in self.inner.winfo_children():
            w.destroy()
        sel = self.listbox.curselection()
        if not sel:
            tk.Label(self.inner, text="Add or select a condition to see "
                                      "its evidence checklist.",
                     bg=PANEL, fg=SUBTLE, font=("Segoe UI", 10),
                     pady=20, padx=16).pack(anchor="w")
            return
        cond = self.vault.conditions[sel[0]]
        idx = sel[0]
        tk.Label(self.inner, text=f"{cond['name']}  "
                                  f"({cond['claim_type']} claim)",
                 bg=PANEL, fg=ACCENT, font=("Segoe UI", 12, "bold"),
                 padx=14, pady=8).pack(anchor="w")
        for key, label, why in evidence_items_for(cond["type"],
                                                  cond["claim_type"]):
            var = tk.IntVar(value=1 if cond["evidence"].get(key) else 0)
            cb = tk.Checkbutton(
                self.inner, text=label, variable=var, bg=PANEL,
                fg=TEXT, selectcolor=BG, activebackground=PANEL,
                activeforeground=TEXT, wraplength=420, justify="left",
                font=("Segoe UI", 10, "bold"),
                command=lambda k=key, v=var, i=idx: self._toggle(i, k, v))
            cb.pack(anchor="w", padx=14)
            tk.Label(self.inner, text=why, bg=PANEL,
                     fg=(OK if cond["evidence"].get(key) else FLAG),
                     wraplength=430, justify="left",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=38,
                                                pady=(0, 6))
        gaps = self.vault.gaps_for(cond)
        verdict = ("\u2713 No evidence gaps flagged for this condition."
                   if not gaps else
                   f"\u26a0 {len(gaps)} gap(s) flagged above. Resolving "
                   "them before filing typically matters more than "
                   "anything else you can do.")
        tk.Label(self.inner, text=verdict, bg=PANEL,
                 fg=(OK if not gaps else FLAG),
                 font=("Segoe UI", 10, "bold"), wraplength=440,
                 justify="left", padx=14, pady=10).pack(anchor="w")

    def _toggle(self, idx, key, var):
        self.vault.conditions[idx]["evidence"][key] = bool(var.get())
        self.vault.save()
        # refresh list badge without losing selection
        cur = self.listbox.curselection()
        self.listbox.delete(0, "end")
        for c in self.vault.conditions:
            n_gaps = len(self.vault.gaps_for(c))
            badge = "\u2713" if n_gaps == 0 else f"\u26a0 {n_gaps}"
            self.listbox.insert("end", f" {badge}  {c['name']}")
        if cur:
            self.listbox.selection_set(cur[0])
        self._render()
