"""NEXUS — Qt6 pages. Designed for everyone: keyboard navigable,
large click targets, plain language, scalable text."""

import json
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMessageBox, QPushButton, QScrollArea,
    QTextBrowser, QTextEdit, QVBoxLayout, QWidget,
)

from util import resource_path
from va_math import Rating, combine
from vault import CLAIM_TYPES, CONDITION_LIBRARY, Vault, evidence_items_for

with open(resource_path("content/education.json"), encoding="utf-8") as f:
    EDU = json.load(f)
with open(resource_path("content/glossary.json"), encoding="utf-8") as f:
    GLOSSARY = json.load(f)

GOLD = "#e3b94f"


def _page(title: str, subtitle: str = ""):
    """Standard page scaffold: returns (widget, body_layout)."""
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(28, 22, 28, 16)
    lay.setSpacing(10)
    h = QLabel(title)
    h.setObjectName("H1")
    lay.addWidget(h)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("Sub")
        s.setWordWrap(True)
        lay.addWidget(s)
    return w, lay


def _sections_html(sections) -> str:
    parts = []
    for title, body in sections:
        parts.append(
            f"<h3 style='color:{GOLD}; margin-bottom:4px'>{title}</h3>"
            f"<p style='margin-top:2px; line-height:140%'>{body}</p>")
    return "".join(parts)


class RoadmapPage(QWidget):
    def __init__(self):
        super().__init__()
        w, lay = _page("Claim Roadmap — File It Yourself, Free",
                       "The complete path from records to decision "
                       "review. Every step costs $0.")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(w)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(_sections_html(EDU["roadmap"]))
        lay.addWidget(browser, 1)


class CPPrepPage(QWidget):
    def __init__(self):
        super().__init__()
        w, lay = _page("C&P Exam Prep",
                       "Accurate, complete, honest — including your "
                       "worst days. Nothing more, nothing less.")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(w)
        browser = QTextBrowser()
        browser.setHtml(_sections_html(EDU["cp_prep"]))
        lay.addWidget(browser, 1)


class _ListDetailPage(QWidget):
    """Shared list-left / detail-right layout (Benefits, Glossary)."""

    def __init__(self, title, subtitle, entries: dict, searchable=False):
        super().__init__()
        self.entries = entries
        w, lay = _page(title, subtitle)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(w)

        if searchable:
            self.search = QLineEdit()
            self.search.setPlaceholderText(
                "Type to search terms and definitions\u2026")
            self.search.setClearButtonEnabled(True)
            self.search.textChanged.connect(self._refresh)
            lay.addWidget(self.search)
        else:
            self.search = None

        row = QHBoxLayout()
        row.setSpacing(12)
        lay.addLayout(row, 1)
        self.listw = QListWidget()
        self.listw.setMaximumWidth(340)
        self.listw.currentTextChanged.connect(self._show)
        row.addWidget(self.listw)
        self.detail = QTextBrowser()
        row.addWidget(self.detail, 1)
        self._refresh()

    def _refresh(self):
        q = self.search.text().lower() if self.search else ""
        self.listw.clear()
        for name in sorted(self.entries):
            if q in name.lower() or q in self.entries[name].lower():
                self.listw.addItem(name)
        if self.listw.count():
            self.listw.setCurrentRow(0)
        else:
            self.detail.setHtml("")

    def _show(self, name):
        if name:
            self.detail.setHtml(
                f"<h3 style='color:{GOLD}'>{name}</h3>"
                f"<p style='line-height:145%'>{self.entries[name]}</p>")


class BenefitsPage(_ListDetailPage):
    def __init__(self):
        super().__init__(
            "Benefits Explorer",
            "Every major benefit tied to a rating — including the ones "
            "most often left on the table.", EDU["benefits"])


class GlossaryPage(_ListDetailPage):
    def __init__(self):
        super().__init__(
            "VA Terminology in Plain English",
            "Tap any term. No jargon survives this page.",
            GLOSSARY, searchable=True)


class CalculatorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.ratings: list[Rating] = []
        w, lay = _page("VA Math — Combined Ratings Calculator",
                       "Ratings are not added together. Each new rating "
                       "applies only to your remaining capacity — add "
                       "yours to see the real math, step by step.")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(w)

        row = QHBoxLayout()
        row.setSpacing(8)
        lay.addLayout(row)
        self.pct = QComboBox()
        self.pct.addItems([f"{p}%" for p in range(10, 101, 10)])
        self.pct.setAccessibleName("Rating percentage")
        row.addWidget(QLabel("Rating:"))
        row.addWidget(self.pct)
        self.cond = QLineEdit()
        self.cond.setPlaceholderText("Condition name (optional)")
        row.addWidget(self.cond, 1)
        self.bilateral = QCheckBox("Bilateral (paired limb)")
        row.addWidget(self.bilateral)
        add = QPushButton("Add rating")
        add.setObjectName("Primary")
        add.clicked.connect(self._add)
        row.addWidget(add)
        clear = QPushButton("Clear all")
        clear.clicked.connect(self._clear)
        row.addWidget(clear)

        self.listw = QListWidget()
        self.listw.setMaximumHeight(170)
        lay.addWidget(self.listw)
        hint = QLabel("Double-click an entry to remove it.")
        hint.setObjectName("Sub")
        lay.addWidget(hint)
        self.listw.itemDoubleClicked.connect(self._remove)

        self.result = QLabel("Combined rating: —")
        self.result.setObjectName("Result")
        lay.addWidget(self.result)
        self.steps = QTextEdit()
        self.steps.setReadOnly(True)
        self.steps.setObjectName("Mono")
        lay.addWidget(self.steps, 1)
        note = QLabel("Compensation amounts change every year — check "
                      "current rates at va.gov/disability/"
                      "compensation-rates.")
        note.setObjectName("Sub")
        note.setWordWrap(True)
        lay.addWidget(note)

    def _add(self):
        r = Rating(int(self.pct.currentText().rstrip("%")),
                   self.cond.text().strip(),
                   self.bilateral.isChecked())
        self.ratings.append(r)
        tag = "  [bilateral]" if r.bilateral else ""
        self.listw.addItem(f"{r.percent}%  {r.label or '(unnamed)'}{tag}")
        self.cond.clear()
        self.bilateral.setChecked(False)
        self._recalc()

    def _remove(self, item):
        i = self.listw.row(item)
        self.listw.takeItem(i)
        self.ratings.pop(i)
        self._recalc()

    def _clear(self):
        self.ratings.clear()
        self.listw.clear()
        self._recalc()

    def _recalc(self):
        res = combine(self.ratings)
        self.result.setText(
            f"Combined rating: {res.rounded}%   (exact {res.exact:.1f})"
            if self.ratings else "Combined rating: —")
        self.steps.setPlainText("\n".join(res.steps))


class VaultPage(QWidget):
    def __init__(self):
        super().__init__()
        self.vault = Vault()
        w, lay = _page("Evidence Vault",
                       "Track each condition against the evidence the VA "
                       "actually decides on. Gaps are flagged so you can "
                       "close them before filing. Everything stays on "
                       "this computer.")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(w)

        form = QHBoxLayout()
        form.setSpacing(8)
        lay.addLayout(form)
        self.name_e = QLineEdit()
        self.name_e.setPlaceholderText("Condition name")
        form.addWidget(self.name_e, 1)
        self.type_cb = QComboBox()
        self.type_cb.addItems(list(CONDITION_LIBRARY))
        self.type_cb.setCurrentText("Other / Not Listed")
        self.type_cb.setAccessibleName("Evidence template")
        form.addWidget(self.type_cb)
        self.claim_cb = QComboBox()
        self.claim_cb.addItems(CLAIM_TYPES)
        self.claim_cb.setAccessibleName("Claim type")
        form.addWidget(self.claim_cb)
        add = QPushButton("Add condition")
        add.setObjectName("Primary")
        add.clicked.connect(self._add)
        form.addWidget(add)

        row = QHBoxLayout()
        row.setSpacing(12)
        lay.addLayout(row, 1)

        left = QVBoxLayout()
        row.addLayout(left)
        self.listw = QListWidget()
        self.listw.setMaximumWidth(330)
        self.listw.currentRowChanged.connect(lambda _i: self._render())
        left.addWidget(self.listw, 1)
        btns = QHBoxLayout()
        left.addLayout(btns)
        rm = QPushButton("Remove")
        rm.clicked.connect(self._remove)
        btns.addWidget(rm)
        exp = QPushButton("Export summary")
        exp.setObjectName("Primary")
        exp.clicked.connect(self._export)
        btns.addWidget(exp)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        row.addWidget(self.scroll, 1)

        self._refresh()

    # ------------------------------------------------------------------
    def _add(self):
        name = self.name_e.text().strip()
        if not name:
            QMessageBox.information(self, "NEXUS",
                                    "Enter a condition name first.")
            return
        self.vault.add_condition(name, self.type_cb.currentText(),
                                 self.claim_cb.currentText())
        self.name_e.clear()
        self._refresh(select=len(self.vault.conditions) - 1)

    def _remove(self):
        i = self.listw.currentRow()
        if i < 0:
            return
        name = self.vault.conditions[i]["name"]
        if QMessageBox.question(
                self, "NEXUS", f"Remove '{name}' and its checklist?"
        ) == QMessageBox.StandardButton.Yes:
            self.vault.remove_condition(i)
            self._refresh()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export claim summary", "nexus_claim_summary.txt",
            "Text file (*.txt)")
        if path:
            from pathlib import Path
            Path(path).write_text(self.vault.export_summary(),
                                  encoding="utf-8")
            QMessageBox.information(
                self, "NEXUS",
                "Summary exported.\n\nYou can file yourself at VA.gov — "
                "or hand this to a free accredited VSO for a second "
                "opinion. Never pay a percentage of your back pay.")

    # ------------------------------------------------------------------
    def _badge(self, cond):
        n = len(self.vault.gaps_for(cond))
        return "\u2713  " if n == 0 else f"\u26a0 {n}  "

    def _refresh(self, select=None):
        self.listw.blockSignals(True)
        self.listw.clear()
        for c in self.vault.conditions:
            self.listw.addItem(self._badge(c) + c["name"])
        self.listw.blockSignals(False)
        if self.vault.conditions:
            self.listw.setCurrentRow(
                select if select is not None else 0)
        self._render()

    def _render(self):
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)
        i = self.listw.currentRow()
        if i < 0 or i >= len(self.vault.conditions):
            empty = QLabel("Add or select a condition to see its "
                           "evidence checklist.")
            empty.setObjectName("Sub")
            v.addWidget(empty)
            v.addStretch(1)
            self.scroll.setWidget(inner)
            return
        cond = self.vault.conditions[i]
        title = QLabel(f"{cond['name']}  ({cond['claim_type']} claim)")
        title.setObjectName("H2")
        v.addWidget(title)
        for key, label, why in evidence_items_for(cond["type"],
                                                  cond["claim_type"]):
            cb = QCheckBox(label)
            cb.setChecked(bool(cond["evidence"].get(key)))
            cb.toggled.connect(
                lambda checked, k=key, idx=i: self._toggle(idx, k,
                                                           checked))
            v.addWidget(cb)
            whyl = QLabel(why)
            whyl.setWordWrap(True)
            whyl.setObjectName(
                "WhyOk" if cond["evidence"].get(key) else "WhyGap")
            whyl.setContentsMargins(34, 0, 0, 8)
            v.addWidget(whyl)
        gaps = self.vault.gaps_for(cond)
        verdict = QLabel(
            "\u2713 No evidence gaps flagged for this condition."
            if not gaps else
            f"\u26a0 {len(gaps)} gap(s) flagged above. Closing them "
            "before filing matters more than anything else you can do.")
        verdict.setWordWrap(True)
        verdict.setObjectName("WhyOk" if not gaps else "VerdictGap")
        v.addWidget(verdict)

        # ---- document locker -------------------------------------
        dt = QLabel("Document locker")
        dt.setObjectName("H2")
        dt.setContentsMargins(0, 14, 0, 0)
        v.addWidget(dt)
        dhint = QLabel("Attach copies of your actual evidence — rating "
                       "letters, audiograms, imaging, buddy statements. "
                       "Copies are stored only on this computer.")
        dhint.setWordWrap(True)
        dhint.setObjectName("Sub")
        v.addWidget(dhint)
        for di, doc in enumerate(cond.get("documents", [])):
            row = QHBoxLayout()
            row.setSpacing(8)
            name = QLabel(f"\U0001f4c4 {doc['name']}   "
                          f"(added {doc['added']})")
            name.setObjectName("Sub")
            row.addWidget(name, 1)
            openb = QPushButton("Open")
            openb.clicked.connect(
                lambda _c, p=doc["path"]: QDesktopServices.openUrl(
                    QUrl.fromLocalFile(p)))
            row.addWidget(openb)
            rmb = QPushButton("Remove")
            rmb.clicked.connect(
                lambda _c, idx=i, d=di: self._remove_doc(idx, d))
            row.addWidget(rmb)
            v.addLayout(row)
        attach = QPushButton("\uff0b Attach document(s)")
        attach.setObjectName("Primary")
        attach.clicked.connect(lambda _c, idx=i: self._attach(idx))
        v.addWidget(attach, alignment=Qt.AlignLeft)

        v.addStretch(1)
        self.scroll.setWidget(inner)

    def _toggle(self, idx, key, checked):
        self.vault.conditions[idx]["evidence"][key] = checked
        self.vault.save()
        item = self.listw.item(idx)
        item.setText(self._badge(self.vault.conditions[idx])
                     + self.vault.conditions[idx]["name"])
        self._render()

    def _attach(self, idx):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Attach evidence documents", "",
            "Documents (*.pdf *.png *.jpg *.jpeg *.tif *.tiff "
            "*.doc *.docx *.txt);;All files (*)")
        for p in paths:
            self.vault.add_document(idx, Path(p))
        if paths:
            self._render()

    def _remove_doc(self, idx, doc_index):
        doc = self.vault.conditions[idx]["documents"][doc_index]
        if QMessageBox.question(
                self, "NEXUS",
                f"Remove '{doc['name']}' from the locker?\n(Only the "
                "copy stored by NEXUS is deleted — your original file "
                "is untouched.)") == QMessageBox.StandardButton.Yes:
            self.vault.remove_document(idx, doc_index)
            self._render()
