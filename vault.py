"""
NEXUS — Evidence Vault model
============================
Tracks the veteran's claimed conditions and the evidence supporting
each, flags gaps, and exports an honest claim summary.

Design principle: this module describes EVIDENCE REQUIREMENTS only.
It never suggests symptoms, severity language, or what to tell an
examiner. Gap flags are phrased as missing documents, never as
content to create.
"""

import json
import shutil
import uuid
from datetime import date
from pathlib import Path

from util import app_data_dir

DATA_FILE = app_data_dir() / "nexus_data.json"
DOCS_DIR = app_data_dir() / "documents"

# The three pillars required for every direct service connection claim.
PILLARS = [
    ("diagnosis", "Current diagnosis",
     "A claim needs a currently diagnosed condition from a medical "
     "provider. Symptoms alone, with no diagnosis of record, are "
     "routinely denied."),
    ("inservice", "In-service event / injury / exposure documented",
     "Service treatment records, personnel records, deployment orders, "
     "incident reports, or corroborating lay statements showing the "
     "event or exposure actually happened in service."),
    ("nexus", "Nexus (medical link to service)",
     "A medical opinion connecting the current condition to the "
     "in-service event — 'at least as likely as not.' Presumptive "
     "conditions (PACT Act, Agent Orange, etc.) may not need one."),
]

# Condition-specific evidence the VA typically looks for, beyond the
# three pillars. Honest, document-focused, with the 'why'.
CONDITION_LIBRARY = {
    "Tinnitus": [
        ("audio", "Audiology note or audiogram on file",
         "Tinnitus claims are normally examined alongside audiometric "
         "testing; an audiology record documenting your report of "
         "tinnitus substantially strengthens the file."),
        ("noise", "Noise exposure documentation (MOS, duty stations)",
         "Your MOS and duty history establish the in-service noise "
         "exposure. The VA publishes a Duty MOS Noise Exposure Listing "
         "— some MOSs are conceded as 'highly probable' exposure."),
    ],
    "Hearing Loss": [
        ("audiogram", "Current audiogram meeting 38 CFR 3.385",
         "Hearing loss is only a disability for VA purposes at specific "
         "measured thresholds (3.385). Without a qualifying audiogram, "
         "the claim cannot be granted regardless of other evidence."),
        ("entrance_exit", "Entrance and separation audiograms compared",
         "A measured shift between entry and separation testing is "
         "strong objective evidence of in-service onset."),
        ("noise", "Noise exposure documentation (MOS, duty stations)",
         "Establishes the in-service exposure element."),
    ],
    "PTSD": [
        ("dx_qualified", "Diagnosis from a qualified mental health provider",
         "VA requires a PTSD diagnosis per DSM-5 criteria from a "
         "qualified provider (psychologist/psychiatrist)."),
        ("stressor", "Stressor statement (VA Form 21-0781) completed",
         "Your written account of the in-service stressor(s) — dates, "
         "locations, units, names where possible. Truthful detail helps "
         "the VA verify the event."),
        ("corroboration", "Records corroborating the stressor",
         "Unit records, deployment orders, casualty reports, awards, or "
         "buddy statements. Combat and fear-of-hostile-activity "
         "stressors have relaxed corroboration rules."),
    ],
    "Other Mental Health (depression/anxiety)": [
        ("dx_qualified", "Current diagnosis and treatment records",
         "Ongoing treatment records document both diagnosis and "
         "severity over time."),
        ("markers", "In-service markers or nexus opinion",
         "Performance drops, disciplinary changes, sick-call visits, or "
         "a medical opinion linking the condition to service or to a "
         "service-connected condition (secondary)."),
    ],
    "Back / Neck (spine)": [
        ("imaging", "Imaging (X-ray/MRI) on file",
         "Objective findings support the diagnosis and severity."),
        ("rom", "Range-of-motion findings in treatment records",
         "Spine ratings are driven largely by measured range of motion "
         "and functional loss; documented ROM history matters."),
        ("chronicity", "Treatment records showing chronicity since service",
         "Gaps in treatment are a common denial reason; records (or lay "
         "statements) covering the years since service help show "
         "continuity."),
    ],
    "Knee / Joint": [
        ("imaging", "Imaging on file",
         "Objective findings support diagnosis and severity."),
        ("rom", "Range-of-motion / instability findings documented",
         "Joint ratings turn on measured limitation and instability."),
        ("chronicity", "Treatment records showing chronicity since service",
         "Continuity of symptomatology supports the nexus."),
    ],
    "Migraines": [
        ("log", "Headache treatment records / documented frequency",
         "Migraine ratings depend on frequency and severity of "
         "prostrating attacks as documented by providers over time. A "
         "contemporaneous record of actual episodes (dates, duration, "
         "effect) kept honestly is legitimate and useful evidence."),
        ("rx", "Prescription history for migraine medication",
         "Corroborates diagnosis and ongoing severity."),
    ],
    "Sleep Apnea": [
        ("study", "Sleep study (polysomnography) with diagnosis",
         "OSA claims require a sleep study; a CPAP prescription flows "
         "from it and affects the rating level."),
        ("link", "Nexus to service OR to a service-connected condition",
         "Sleep apnea is frequently claimed secondary (e.g., aggravated "
         "by a service-connected condition). That link must be an "
         "honest medical opinion, not an assumption."),
    ],
    "GERD / Digestive": [
        ("dx", "Diagnosis via treatment records or endoscopy",
         "Objective confirmation of the condition."),
        ("med_link", "If secondary to medication: prescription history",
         "If claiming GERD secondary to NSAIDs or psychiatric "
         "medications for a service-connected condition, the pharmacy "
         "record establishes the chain."),
    ],
    "Radiculopathy": [
        ("emg", "EMG / nerve conduction study or imaging",
         "Objective testing distinguishes radiculopathy from localized "
         "pain and sets the severity."),
        ("spine_link", "Service-connected spine condition identified",
         "Radiculopathy is usually rated secondary to a spine "
         "condition; the primary must be service-connected."),
    ],
    "Hypertension": [
        ("readings", "Serial blood pressure readings of record",
         "Hypertension ratings require documented readings; a single "
         "elevated reading is not a diagnosis."),
        ("basis", "In-service readings, presumptive basis, or nexus",
         "Check PACT Act / Agent Orange presumptions; otherwise "
         "in-service elevated readings or a medical opinion are "
         "needed."),
    ],
    "Other / Not Listed": [],
}

CLAIM_TYPES = ["Direct", "Secondary", "Increase", "Presumptive"]


def evidence_items_for(condition_type: str, claim_type: str):
    """Return the checklist (id, label, why) for a condition."""
    items = list(PILLARS)
    if claim_type == "Secondary":
        items = [i for i in items if i[0] != "inservice"]
        items.insert(1, (
            "primary", "Primary condition is service-connected",
            "A secondary claim requires the primary condition to "
            "already be service-connected (or claimed concurrently)."))
        items = [(
            "diagnosis", items[0][1], items[0][2]
        )] + items[1:]
    if claim_type == "Presumptive":
        items = [i for i in items if i[0] != "nexus"]
        items.append((
            "presumptive_service", "Qualifying service dates/locations "
            "documented",
            "Presumptives require service in specific places/periods "
            "(e.g., PACT Act locations). DD-214 and deployment records "
            "establish this."))
    items += CONDITION_LIBRARY.get(condition_type, [])
    return items


class Vault:
    """Local-only persistence for the veteran's claim workspace."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self.conditions: list[dict] = []
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.conditions = json.loads(
                    self.path.read_text(encoding="utf-8")
                ).get("conditions", [])
            except (json.JSONDecodeError, OSError):
                self.conditions = []
        # Migration: older records lack ids / document lists.
        changed = False
        for c in self.conditions:
            if "id" not in c:
                c["id"] = uuid.uuid4().hex
                changed = True
            if "documents" not in c:
                c["documents"] = []
                changed = True
        if changed:
            self.save()

    def save(self):
        self.path.write_text(
            json.dumps({"conditions": self.conditions}, indent=2),
            encoding="utf-8")

    def add_condition(self, name, ctype, claim_type, secondary_to=""):
        self.conditions.append({
            "id": uuid.uuid4().hex,
            "name": name, "type": ctype, "claim_type": claim_type,
            "secondary_to": secondary_to,
            "evidence": {}, "notes": "", "documents": [],
        })
        self.save()

    def remove_condition(self, index):
        cond = self.conditions.pop(index)
        shutil.rmtree(DOCS_DIR / cond.get("id", "_none_"),
                      ignore_errors=True)
        self.save()

    # ---- document locker (local copies only; nothing leaves the PC) ----
    def docs_dir_for(self, cond) -> Path:
        p = DOCS_DIR / cond["id"]
        p.mkdir(parents=True, exist_ok=True)
        return p

    def add_document(self, index, source: Path) -> dict:
        """Copy a file into the condition's local locker."""
        cond = self.conditions[index]
        dest_dir = self.docs_dir_for(cond)
        dest = dest_dir / source.name
        n = 1
        while dest.exists():
            dest = dest_dir / f"{source.stem}_{n}{source.suffix}"
            n += 1
        shutil.copy2(source, dest)
        rec = {"name": dest.name, "path": str(dest),
               "added": date.today().isoformat()}
        cond["documents"].append(rec)
        self.save()
        return rec

    def remove_document(self, index, doc_index):
        rec = self.conditions[index]["documents"].pop(doc_index)
        Path(rec["path"]).unlink(missing_ok=True)
        self.save()

    def gaps_for(self, cond) -> list[tuple[str, str]]:
        """Return (label, why) for every unchecked evidence item."""
        return [(label, why) for key, label, why
                in evidence_items_for(cond["type"], cond["claim_type"])
                if not cond["evidence"].get(key)]

    def export_summary(self) -> str:
        """Plain-text claim summary the veteran can self-file from or
        hand to a (free) VSO for a second opinion."""
        lines = [
            "=" * 68,
            "NEXUS CLAIM SUMMARY — prepared by the veteran, for the veteran",
            f"Generated: {date.today().isoformat()}",
            "=" * 68,
            "",
            "This summary was produced by a free educational tool. It is",
            "not legal or medical advice. The veteran certifies that all",
            "information is truthful. Filing a false claim is a federal",
            "crime (18 U.S.C. 287; 38 U.S.C. 6102).",
            "",
        ]
        if not self.conditions:
            lines.append("No conditions entered yet.")
        for i, c in enumerate(self.conditions, 1):
            lines.append(f"{i}. {c['name'].upper()}  "
                         f"[{c['claim_type']} claim"
                         + (f", secondary to {c['secondary_to']}"
                            if c['secondary_to'] else "") + "]")
            items = evidence_items_for(c["type"], c["claim_type"])
            for key, label, _ in items:
                mark = "[x]" if c["evidence"].get(key) else "[ ] MISSING:"
                lines.append(f"     {mark} {label}")
            if c.get("notes"):
                lines.append(f"     Notes: {c['notes']}")
            if c.get("documents"):
                lines.append("     Documents on file:")
                for d in c["documents"]:
                    lines.append(f"        - {d['name']} "
                                 f"(added {d['added']})")
            gaps = self.gaps_for(c)
            if gaps:
                lines.append(f"     >> {len(gaps)} evidence gap(s) — "
                             "consider resolving before filing.")
            lines.append("")
        lines += [
            "-" * 68,
            "Next steps: see the Claim Roadmap in NEXUS. File free at",
            "VA.gov. Accredited VSOs (DAV, VFW, American Legion, county",
            "service officers) will also review/file this for FREE.",
            "Never pay a company a percentage of your back pay.",
        ]
        return "\n".join(lines)
