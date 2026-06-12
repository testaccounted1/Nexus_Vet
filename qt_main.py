"""
NEXUS — Veteran Disability Claims Education Tool (Qt6 edition)
==============================================================
Free, nonprofit, 100% local. No network. No telemetry. Ever.

Run from source:  python qt_main.py   (pip install PySide6)
Or build NEXUS.exe + installer with build_windows.bat.

INTEGRITY: supports LEGITIMATE claims only. Filing a false claim is a
federal crime (18 U.S.C. 287; 38 U.S.C. 6102). Educational tool only —
not legal advice, medical advice, or accredited representation.
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QDialog, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from util import load_settings, resource_path, save_settings

APP_NAME = "NEXUS"
APP_VERSION = "0.4.0"

FRAUD_WARNING = (
    "Filing a false or exaggerated VA claim is a FEDERAL CRIME "
    "(18 U.S.C. \u00a7 287; 38 U.S.C. \u00a7 6102) punishable by fines "
    "and imprisonment, and can result in loss of all benefits.")
DISCLAIMER = (
    "NEXUS is a free educational tool. It is NOT a lawyer, doctor, or "
    "accredited representative, and nothing in it is legal or medical "
    "advice. You are solely responsible for the accuracy of anything "
    "you file. Verify everything at VA.gov; accredited VSOs will help "
    "you for free.")


# ---------------------------------------------------------------- theme
def build_qss(scale: float, high_contrast: bool) -> str:
    s = lambda px: f"{round(px * scale)}px"  # noqa: E731
    if high_contrast:
        bg, panel, panel2 = "#000000", "#0a0a0a", "#141414"
        text, sub, gold = "#ffffff", "#e0e0e0", "#ffd700"
        border, gap, ok = "#ffffff", "#ff8080", "#80ff80"
        warnbg, warnfg = "#400000", "#ffd0d0"
    else:
        bg, panel, panel2 = "#141925", "#1b2231", "#222a3c"
        text, sub, gold = "#e9ecf2", "#9aa4b5", "#e3b94f"
        border, gap, ok = "#323d56", "#e8a0a0", "#9fd49f"
        warnbg, warnfg = "#3a2626", "#f0b9b9"
    return f"""
    QWidget {{ background:{bg}; color:{text};
        font-family:'Segoe UI','Noto Sans',sans-serif;
        font-size:{s(14)}; }}
    QLabel#H1 {{ color:{gold}; font-size:{s(22)}; font-weight:700;
        background:transparent; }}
    QLabel#H2 {{ color:{gold}; font-size:{s(17)}; font-weight:700;
        background:transparent; padding-bottom:{s(4)}; }}
    QLabel#Sub {{ color:{sub}; font-size:{s(12)};
        background:transparent; }}
    QLabel#Result {{ color:{gold}; font-size:{s(24)}; font-weight:700;
        background:transparent; padding:{s(6)} 0; }}
    QLabel#WhyGap {{ color:{gap}; font-size:{s(12)};
        background:transparent; }}
    QLabel#WhyOk {{ color:{ok}; font-size:{s(12)};
        background:transparent; }}
    QLabel#VerdictGap {{ color:{gap}; font-size:{s(14)};
        font-weight:700; background:transparent; padding-top:{s(8)}; }}
    QLabel#Brand {{ color:{gold}; font-size:{s(24)}; font-weight:800;
        background:transparent; }}
    QLabel#Tag {{ color:{sub}; font-size:{s(10)};
        background:transparent; }}
    QFrame#Sidebar, #Sidebar QWidget {{ background:{panel}; }}
    QPushButton {{ background:{panel2}; border:1px solid {border};
        border-radius:{s(9)}; padding:{s(9)} {s(16)};
        min-height:{s(24)}; }}
    QPushButton:hover {{ border-color:{gold}; }}
    QPushButton:focus {{ border:2px solid {gold}; }}
    QPushButton#Primary {{ background:{gold}; color:#16181d;
        font-weight:700; border:none; }}
    QPushButton[nav="true"] {{ background:transparent; border:none;
        text-align:left; padding:{s(12)} {s(20)}; border-radius:{s(9)};
        font-size:{s(15)}; color:{text}; }}
    QPushButton[nav="true"]:hover {{ background:{panel2}; }}
    QPushButton[nav="true"]:checked {{ background:{panel2};
        color:{gold}; font-weight:700; }}
    QPushButton[acc="true"] {{ min-width:{s(34)}; padding:{s(6)};
        font-weight:700; }}
    QLineEdit, QComboBox {{ background:{panel2};
        border:1px solid {border}; border-radius:{s(8)};
        padding:{s(8)}; min-height:{s(22)}; }}
    QLineEdit:focus, QComboBox:focus {{ border:2px solid {gold}; }}
    QComboBox QAbstractItemView {{ background:{panel2}; color:{text};
        selection-background-color:{gold};
        selection-color:#16181d; }}
    QListWidget {{ background:{panel}; border:1px solid {border};
        border-radius:{s(10)}; padding:{s(6)}; }}
    QListWidget::item {{ padding:{s(10)}; border-radius:{s(6)}; }}
    QListWidget::item:selected {{ background:{gold}; color:#16181d; }}
    QTextBrowser, QTextEdit {{ background:{panel};
        border:1px solid {border}; border-radius:{s(10)};
        padding:{s(10)}; }}
    QTextEdit#Mono {{ font-family:Consolas,monospace;
        font-size:{s(12)}; }}
    QCheckBox {{ spacing:{s(10)}; font-weight:600;
        background:transparent; }}
    QCheckBox::indicator {{ width:{s(22)}; height:{s(22)};
        border:2px solid {border}; border-radius:{s(5)};
        background:{panel2}; }}
    QCheckBox::indicator:checked {{ background:{gold};
        border-color:{gold}; }}
    QCheckBox:focus {{ color:{gold}; }}
    QLabel#WarnBar {{ background:{warnbg}; color:{warnfg};
        font-size:{s(11)}; padding:{s(7)} {s(12)}; }}
    QScrollArea {{ border:none; background:{panel}; }}
    QScrollBar:vertical {{ background:{panel}; width:{s(14)}; }}
    QScrollBar::handle:vertical {{ background:{border};
        border-radius:{s(6)}; min-height:{s(30)}; }}
    QDialog {{ background:{bg}; }}
    QMessageBox QLabel {{ background:transparent; }}
    """


# ------------------------------------------------------- disclaimer gate
class DisclaimerGate(QDialog):
    """Shown on every launch; the app will not open without affirmative
    acknowledgment."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Read Before Using")
        self.setModal(True)
        self.setMinimumWidth(620)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(14)
        h = QLabel("Before you begin")
        h.setObjectName("H1")
        lay.addWidget(h)
        body = QLabel(
            f"\u26a0  {FRAUD_WARNING}\n\n{DISCLAIMER}\n\n"
            "This tool will help you understand the system and organize "
            "honest, well-documented claims. It will not help you "
            "exaggerate, fabricate, or game anything.")
        body.setWordWrap(True)
        lay.addWidget(body)
        self.ack = QCheckBox(
            "I understand that filing false claims is a federal crime, "
            "that this tool is educational only, and that I am "
            "responsible for what I file.")
        self.ack.toggled.connect(lambda on: self.go.setEnabled(on))
        lay.addWidget(self.ack)
        row = QHBoxLayout()
        lay.addLayout(row)
        self.go = QPushButton("I Agree — Continue")
        self.go.setObjectName("Primary")
        self.go.setEnabled(False)
        self.go.clicked.connect(self.accept)
        row.addWidget(self.go)
        quit_b = QPushButton("Exit")
        quit_b.clicked.connect(self.reject)
        row.addWidget(quit_b)
        row.addStretch(1)


TOUR_STEPS = [
    ("Welcome to NEXUS",
     "NEXUS helps you understand, build, and file your own VA "
     "disability claim — honestly, and completely free. This quick "
     "tour takes about a minute. You can replay it any time from the "
     "sidebar."),
    ("Claim Roadmap",
     "Your starting point. Ten plain-English steps from 'get your "
     "records' to 'read your decision' — including how to lock in "
     "your back-pay date before you even finish your claim, and what "
     "to do if the VA gets it wrong. Every step costs $0."),
    ("Evidence Vault",
     "Add each condition you honestly believe is connected to your "
     "service. NEXUS shows the exact evidence the VA looks for and "
     "flags what's missing — like a tinnitus claim with no audiogram "
     "on file. Attach copies of your real documents in the locker. "
     "Everything stays on this computer."),
    ("Rating Calculator",
     "VA percentages don't simply add up — 50% plus 50% is 80%, not "
     "100%. The calculator shows the real math, step by step, "
     "including the bilateral factor for paired limbs."),
    ("Benefits Explorer",
     "Ratings unlock more than a monthly payment: health care, the "
     "home-loan fee exemption, education for your family, and more. "
     "This page lists the benefits veterans most often leave on the "
     "table."),
    ("C&P Exam Prep and Glossary",
     "Know what the exam measures and your rights when you're there. "
     "The golden rule: accurate and complete — your worst days "
     "included, nothing more and nothing less. And when the VA "
     "speaks jargon, the Glossary translates."),
    ("You're in control",
     "Larger text? Press A+ in the sidebar. Better contrast? One "
     "click. NEXUS never connects to the internet, never sells "
     "anything, and never asks for a cut. If you ever want a second "
     "set of eyes, accredited VSOs help for free. This claim is "
     "yours. Let's build it right."),
]


class TourDialog(QDialog):
    """One-minute first-launch tour. Big text, two buttons, no traps."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to NEXUS")
        self.setModal(True)
        self.setMinimumSize(640, 380)
        self.i = 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 26, 30, 20)
        lay.setSpacing(14)
        self.title = QLabel()
        self.title.setObjectName("H1")
        lay.addWidget(self.title)
        self.body = QLabel()
        self.body.setWordWrap(True)
        lay.addWidget(self.body)
        lay.addStretch(1)
        self.step = QLabel()
        self.step.setObjectName("Tag")
        lay.addWidget(self.step)
        row = QHBoxLayout()
        lay.addLayout(row)
        self.back = QPushButton("\u2190 Back")
        self.back.clicked.connect(lambda: self._go(-1))
        row.addWidget(self.back)
        self.next = QPushButton("Next \u2192")
        self.next.setObjectName("Primary")
        self.next.clicked.connect(lambda: self._go(+1))
        row.addWidget(self.next)
        row.addStretch(1)
        skip = QPushButton("Skip tour")
        skip.clicked.connect(self.accept)
        row.addWidget(skip)
        self._show()

    def _show(self):
        t, b = TOUR_STEPS[self.i]
        self.title.setText(t)
        self.body.setText(b)
        self.step.setText(f"Step {self.i + 1} of {len(TOUR_STEPS)}")
        self.back.setEnabled(self.i > 0)
        self.next.setText("Get started \u2713"
                          if self.i == len(TOUR_STEPS) - 1
                          else "Next \u2192")

    def _go(self, d):
        if self.i + d >= len(TOUR_STEPS):
            self.accept()
            return
        self.i = max(0, self.i + d)
        self._show()


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.settings = load_settings()
        self.setWindowTitle(f"{APP_NAME} \u2014 Veteran Claims Education"
                            f"  v{APP_VERSION}")
        self.resize(1120, 740)
        self.setMinimumSize(940, 620)

        from qt_pages import (BenefitsPage, CalculatorPage, CPPrepPage,
                              GlossaryPage, RoadmapPage, VaultPage)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(0)
        root.addLayout(main_row, 1)

        # Sidebar --------------------------------------------------------
        from PySide6.QtWidgets import QFrame
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(248)
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(14, 22, 14, 14)
        sv.setSpacing(4)
        brand = QLabel("\u2605 NEXUS")
        brand.setObjectName("Brand")
        sv.addWidget(brand)
        tag = QLabel("by vets, for vets \u2022 always free")
        tag.setObjectName("Tag")
        sv.addWidget(tag)
        sv.addSpacing(16)

        self.stack = QStackedWidget()
        self.pages = [
            ("Claim Roadmap", RoadmapPage()),
            ("Evidence Vault", VaultPage()),
            ("Rating Calculator", CalculatorPage()),
            ("Benefits Explorer", BenefitsPage()),
            ("C&P Exam Prep", CPPrepPage()),
            ("Glossary", GlossaryPage()),
        ]
        group = QButtonGroup(self)
        group.setExclusive(True)
        for i, (name, page) in enumerate(self.pages):
            self.stack.addWidget(page)
            b = QPushButton(name)
            b.setProperty("nav", "true")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _c, idx=i:
                              self.stack.setCurrentIndex(idx))
            group.addButton(b)
            sv.addWidget(b)
            if i == 0:
                b.setChecked(True)
        sv.addStretch(1)

        # Accessibility controls -----------------------------------------
        acc_label = QLabel("Accessibility")
        acc_label.setObjectName("Tag")
        sv.addWidget(acc_label)
        acc = QHBoxLayout()
        sv.addLayout(acc)
        smaller = QPushButton("A\u2212")
        smaller.setProperty("acc", "true")
        smaller.setToolTip("Make text smaller")
        smaller.clicked.connect(lambda: self._scale(-0.15))
        acc.addWidget(smaller)
        bigger = QPushButton("A+")
        bigger.setProperty("acc", "true")
        bigger.setToolTip("Make text bigger")
        bigger.clicked.connect(lambda: self._scale(+0.15))
        acc.addWidget(bigger)
        self.hc = QPushButton("Contrast")
        self.hc.setProperty("acc", "true")
        self.hc.setCheckable(True)
        self.hc.setChecked(self.settings["high_contrast"])
        self.hc.setToolTip("Toggle high-contrast mode")
        self.hc.toggled.connect(self._toggle_contrast)
        acc.addWidget(self.hc)

        ver = QLabel(f"v{APP_VERSION} \u2022 100% local \u2022 "
                     "no network \u2022 no tracking")
        ver.setObjectName("Tag")
        sv.addWidget(ver)
        replay = QPushButton("Replay welcome tour")
        replay.setProperty("nav", "true")
        replay.setCursor(Qt.PointingHandCursor)
        replay.clicked.connect(lambda: TourDialog().exec())
        sv.addWidget(replay)

        main_row.addWidget(sidebar)
        main_row.addWidget(self.stack, 1)

        warn = QLabel("\u26a0 " + FRAUD_WARNING)
        warn.setObjectName("WarnBar")
        warn.setWordWrap(True)
        root.addWidget(warn)

    # ---------------------------------------------------------------
    def _scale(self, delta):
        self.settings["text_scale"] = round(
            min(1.75, max(0.85, self.settings["text_scale"] + delta)), 2)
        save_settings(self.settings)
        self._apply_theme()

    def _toggle_contrast(self, on):
        self.settings["high_contrast"] = on
        save_settings(self.settings)
        self._apply_theme()

    def _apply_theme(self):
        self.app.setStyleSheet(build_qss(self.settings["text_scale"],
                                         self.settings["high_contrast"]))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon = QIcon(str(resource_path("assets/nexus.png")))
    app.setWindowIcon(icon)
    settings = load_settings()
    app.setStyleSheet(build_qss(settings["text_scale"],
                                settings["high_contrast"]))
    gate = DisclaimerGate()
    gate.setWindowIcon(icon)
    if gate.exec() != QDialog.Accepted:
        sys.exit(0)
    if not settings.get("tour_done"):
        TourDialog().exec()
        settings["tour_done"] = True
        save_settings(settings)
    win = MainWindow(app)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
