"""Auto-detect the kind of each sheet in an uploaded Excel file.

Detection works on a normalized signature of the header row (set of words).
Each detector advertises:
  - kind: stable identifier used by the frontend and ingestor registry
  - target_table: schema-qualified destination (or "(à créer)")
  - ready: whether the corresponding ingestor + target table actually exist
  - granularity: 'day' | 'minute' | 'metadata' — to flag timestamp expectations
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


def _normalize(s: object) -> str:
    if s is None:
        return ""
    text = str(s).strip().lower()
    # strip accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def _signature(values: list[object]) -> set[str]:
    return {_normalize(v) for v in values if v is not None and _normalize(v)}


@dataclass
class SheetAnalysis:
    name: str
    rows: int
    detected_kind: str  # 'unknown' if no detector matched
    target_table: str
    ready: bool
    header_row: int  # 1-indexed row where the header was located
    columns: list[str] = field(default_factory=list)
    preview: list[list[Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    granularity: str = "day"  # 'day' | 'minute' | 'metadata' | 'wide'

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "rows": self.rows,
            "detected_kind": self.detected_kind,
            "target_table": self.target_table,
            "ready": self.ready,
            "header_row": self.header_row,
            "columns": self.columns,
            "preview": self.preview,
            "warnings": self.warnings,
            "granularity": self.granularity,
        }


# ----------------------------------------------------------------------------
# Detectors
# ----------------------------------------------------------------------------


@dataclass
class _Detector:
    kind: str
    target_table: str
    ready: bool
    granularity: str
    required: list[str]
    optional: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def matches(self, sig: set[str]) -> int:
        """Return a score: number of required keywords matched, or -1 if any is missing."""
        for key in self.required:
            if not any(key in s for s in sig):
                return -1
        score = len(self.required)
        for key in self.optional:
            if any(key in s for s in sig):
                score += 1
        return score


_DETECTORS: list[_Detector] = [
    # --- Already supported in production ---
    _Detector(
        kind="daily_production",
        target_table="production.daily_production",
        ready=True,
        granularity="day",
        required=["date", "production journaliere", "huile", "eau"],
        optional=["puits", "watercut", "water oil ratio"],
        warnings=["Watercut en fraction (0-1) sera converti en %."],
    ),
    # --- Sprint 2 (tables / ingestors not built yet) ---
    _Detector(
        kind="failures",
        target_table="maintenance.failures",
        ready=False,
        granularity="day",
        required=["date de notification", "well", "bloc"],
        optional=["reservoir segment", "pompe"],
        warnings=["Sera ingéré dans `maintenance.failures` (sprint 2)."],
    ),
    _Detector(
        kind="interventions",
        target_table="maintenance.interventions",
        ready=False,
        granularity="minute",
        required=["well", "activity type", "operation", "job end"],
        optional=["description", "reservoir segment", "bloc"],
        warnings=["Granularité minute — `intervention_date` sera un TIMESTAMPTZ."],
    ),
    _Detector(
        kind="stimulation",
        target_table="maintenance.stimulation_jobs (à créer)",
        ready=False,
        granularity="minute",
        required=["well", "operation", "job end", "stim fluid"],
        optional=["res seg", "bloc"],
        warnings=["Table cible à créer en sprint 2."],
    ),
    _Detector(
        kind="capex",
        target_table="maintenance.well_capex_jobs (à créer)",
        ready=False,
        granularity="minute",
        required=["well", "activity type", "operation", "job end"],
        optional=["description", "completion", "phase"],
        warnings=[
            "Schéma similaire à `interventions` mais semantics différent — table dédiée prévue.",
        ],
    ),
    _Detector(
        kind="downtime",
        target_table="maintenance.well_downtime (à créer)",
        ready=False,
        granularity="day",
        required=["well", "start_date", "category"],
        optional=["reservoir segment", "bloc"],
        warnings=["Table cible à créer en sprint 2."],
    ),
    _Detector(
        kind="water_injection",
        target_table="production.water_injection (à créer)",
        ready=False,
        granularity="day",
        required=["date", "injection"],
        optional=["injecteur", "kbj", "kilo baril", "reservoir"],
        warnings=[
            "Format wide (1 colonne par injecteur). L'ingestor fera l'unpivot.",
        ],
    ),
    _Detector(
        kind="well_pressure",
        target_table="production.well_pressure (à créer)",
        ready=False,
        granularity="minute",
        required=["pression", "puits"],
        warnings=[
            "Format wide non standard (4 puits côte à côte). Parser dédié requis.",
            "Granularité seconde par puits — `measured_at` sera TIMESTAMPTZ.",
        ],
    ),
    _Detector(
        kind="drilling_phase",
        target_table="(métadonnées — non ingéré)",
        ready=False,
        granularity="metadata",
        required=["forage"],
        warnings=["Métadonnées projet — ignorées par défaut."],
    ),
]


def _stringify_preview_row(row: list[object]) -> list[Any]:
    out: list[Any] = []
    for v in row:
        if v is None:
            out.append(None)
        elif isinstance(v, (str, int, float, bool)):
            out.append(v)
        else:
            # datetime, Decimal, etc.
            out.append(str(v))
    return out


def _find_header_row(raw: pd.DataFrame, max_scan: int = 8) -> tuple[int, list[str]]:
    """Find the first row that looks like a header (mostly non-empty strings).

    Returns (1-indexed row number, list of header strings). Falls back to row 1.
    """
    best_idx = 0
    best_score = -1
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i].tolist()
        non_null = [v for v in row if v is not None and str(v).strip() != ""]
        # heuristic: header rows are mostly strings, few datetimes/numbers
        str_count = sum(1 for v in non_null if isinstance(v, str))
        if str_count >= 3 and str_count > best_score:
            best_score = str_count
            best_idx = i
    headers = [str(v).strip() if v is not None else "" for v in raw.iloc[best_idx].tolist()]
    return best_idx + 1, headers


def _detect_kind(headers: list[str], sheet_name: str) -> _Detector | None:
    sig = _signature(headers)
    sig.add(_normalize(sheet_name))  # the sheet name itself can carry a hint

    best_score = 0
    best: _Detector | None = None
    for det in _DETECTORS:
        score = det.matches(sig)
        if score > best_score:
            best_score = score
            best = det
    return best


def analyze_workbook(file_path: Path) -> list[SheetAnalysis]:
    """Open the workbook and analyse each sheet — read-only, no DB writes."""
    xl = pd.ExcelFile(file_path)
    out: list[SheetAnalysis] = []

    for name in xl.sheet_names:
        try:
            raw = xl.parse(sheet_name=name, header=None, nrows=12)
        except Exception as exc:
            out.append(SheetAnalysis(
                name=name, rows=0, detected_kind="unknown",
                target_table="—", ready=False, header_row=1,
                warnings=[f"Erreur lecture: {exc}"],
            ))
            continue

        # Total row count (including blank trailing rows). Read just for shape.
        try:
            full = xl.parse(sheet_name=name, header=None)
            total_rows = len(full.dropna(how="all"))
        except Exception:
            total_rows = len(raw)

        header_row, headers = _find_header_row(raw)
        det = _detect_kind(headers, name)

        # Preview rows = the 3 rows after the header
        preview: list[list[Any]] = []
        try:
            data_start = header_row  # 0-indexed in raw → header_row (since 1-indexed)
            preview_raw = raw.iloc[data_start:data_start + 3].values.tolist()
            preview = [_stringify_preview_row(r) for r in preview_raw]
        except Exception:
            preview = []

        if det is None:
            out.append(SheetAnalysis(
                name=name, rows=total_rows, detected_kind="unknown",
                target_table="—", ready=False, header_row=header_row,
                columns=[h for h in headers if h],
                preview=preview,
                warnings=["Type d'onglet non reconnu — sera ignoré à l'import."],
                granularity="metadata",
            ))
            continue

        out.append(SheetAnalysis(
            name=name,
            rows=total_rows,
            detected_kind=det.kind,
            target_table=det.target_table,
            ready=det.ready,
            header_row=header_row,
            columns=[h for h in headers if h],
            preview=preview,
            warnings=list(det.warnings),
            granularity=det.granularity,
        ))

    return out
