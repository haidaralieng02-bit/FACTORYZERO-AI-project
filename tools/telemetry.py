from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd


# Deterministic engineering thresholds. These are intentionally independent of
# the LLM/RAG layer: documents provide evidence and maintenance guidance, but
# they must not decide whether telemetry is abnormal.
THRESHOLDS = {
    "temperature": 85.0,
    "vibration": 7.0,
    "current": 30.0,
    "voltage": 480.0,
}

# Common real-world CSV header variants -> one canonical internal name.
# Matching is case-insensitive after punctuation/whitespace normalization.
COLUMN_ALIASES = {
    "timestamp": {
        "timestamp",
        "time",
        "datetime",
        "date_time",
        "date",
        "event_time",
        "recorded_at",
        "recorded_time",
    },
    "temperature": {
        "temperature",
        "temperature_c",
        "temp",
        "temp_c",
        "motor_temperature",
        "motor_temperature_c",
        "bearing_temperature",
        "bearing_temperature_c",
    },
    "vibration": {
        "vibration",
        "vibration_rms",
        "vibration_mm_s",
        "vibration_rms_mm_s",
        "vibration_mms",
        "vibration_velocity",
        "vibration_velocity_mm_s",
        "rms_vibration",
    },
    "current": {
        "current",
        "current_a",
        "motor_current",
        "motor_current_a",
        "phase_current",
        "phase_current_a",
        "amps",
        "amperage",
    },
    "voltage": {
        "voltage",
        "voltage_v",
        "line_voltage",
        "line_voltage_v",
        "motor_voltage",
        "motor_voltage_v",
    },
    "rpm": {
        "rpm",
        "speed",
        "speed_rpm",
        "motor_rpm",
        "motor_speed_rpm",
    },
    "power": {
        "power",
        "power_kw",
        "motor_power",
        "motor_power_kw",
    },
}

# Reverse lookup is built once so normalization is deterministic.
_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias: canonical
    for canonical, aliases in COLUMN_ALIASES.items()
    for alias in aliases
}


def _normalize_header(value: object) -> str:
    """Normalize a CSV header for case/punctuation-insensitive matching."""
    text = str(value).strip().lower()
    for char in ("-", " ", "/", "\\", ".", "(", ")", "[", "]"):
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def normalize_telemetry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy with common telemetry header variants mapped to canonical names.

    Unknown columns are preserved. If two input columns map to the same
    canonical name, the first recognized column is kept and the duplicate is
    preserved under a unique normalized name rather than silently overwriting
    data.
    """
    if df is None:
        return df

    work = df.copy()
    used: set[str] = set()
    renamed: dict[object, str] = {}

    for original in work.columns:
        normalized = _normalize_header(original)
        canonical = _ALIAS_TO_CANONICAL.get(normalized, normalized or "unnamed_column")

        if canonical in used:
            # Preserve duplicate information instead of silently replacing it.
            suffix = 2
            candidate = f"{canonical}_{suffix}"
            while candidate in used:
                suffix += 1
                candidate = f"{canonical}_{suffix}"
            canonical = candidate

        renamed[original] = canonical
        used.add(canonical)

    work = work.rename(columns=renamed)
    return work


def load_telemetry(source: str | bytes) -> pd.DataFrame:
    if isinstance(source, bytes):
        return normalize_telemetry_columns(pd.read_csv(BytesIO(source)))
    return normalize_telemetry_columns(pd.read_csv(source))


def validate_telemetry(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if df is None or df.empty:
        return ["The telemetry file is empty."]

    work = normalize_telemetry_columns(df)
    if "timestamp" not in work.columns:
        errors.append(
            "The telemetry file does not contain a recognizable timestamp column "
            "(for example: timestamp, time, datetime, or date_time)."
        )

    # At least one numeric measurement must be available. This catches files
    # containing only timestamps before they reach the agent/RAG layers.
    if "timestamp" in work.columns:
        numeric_measurements = [
            c for c in work.columns
            if c != "timestamp" and pd.api.types.is_numeric_dtype(
                pd.to_numeric(work[c], errors="coerce")
            )
        ]
        if not numeric_measurements:
            errors.append("The telemetry file does not contain any numeric measurement columns.")

    return errors


def _trend(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, values, 1)[0])


def analyze_telemetry(df: pd.DataFrame) -> dict[str, Any]:
    errors = validate_telemetry(df)
    if errors:
        raise ValueError(" ".join(errors))

    work = normalize_telemetry_columns(df)
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    work = work.dropna(subset=["timestamp"]).copy()

    if work.empty:
        raise ValueError("No valid timestamp values were found.")

    stats: dict[str, dict[str, float]] = {}
    breaches: list[dict[str, Any]] = []
    params: list[str] = []
    observations: list[str] = []

    for col in work.columns:
        if col == "timestamp":
            continue

        numeric = pd.to_numeric(work[col], errors="coerce").dropna()
        if numeric.empty:
            continue

        params.append(col)
        slope = _trend(numeric)
        first = float(numeric.iloc[0])
        last = float(numeric.iloc[-1])

        stats[col] = {
            "min": float(numeric.min()),
            "max": float(numeric.max()),
            "average": float(numeric.mean()),
            "std": float(numeric.std(ddof=0)),
            "slope": slope,
            "first": first,
            "last": last,
            "percentage_change": float(((last - first) / first) * 100) if first else 0.0,
        }

        # Threshold checks use canonical names, so temperature_c/current_a/etc.
        # are treated exactly like temperature/current.
        if col in THRESHOLDS:
            threshold = THRESHOLDS[col]
            count = int((numeric > threshold).sum())
            if count:
                breaches.append(
                    {
                        "parameter": col,
                        "threshold": threshold,
                        "breach_count": count,
                        "max": float(numeric.max()),
                    }
                )
                observations.append(
                    f"{col} exceeded the configured threshold of {threshold:g}."
                )

        if len(numeric) > 1 and abs(slope) > 0.02:
            observations.append(
                f"{col} shows a {'rising' if slope > 0 else 'falling'} trend "
                f"(slope {slope:.3f} per sample)."
            )

    severity = "NORMAL"
    if len(breaches) >= 3:
        severity = "HIGH"
    elif len(breaches) == 2:
        severity = "MEDIUM"
    elif len(breaches) == 1:
        severity = "LOW"

    return {
        "status": "ANOMALY" if breaches else "NORMAL",
        "severity": severity,
        "observations": observations,
        "detected_parameters": params,
        "threshold_breaches": breaches,
        "trend_summary": (
            f"Detected {len(breaches)} threshold breach group(s) across "
            f"{len(params)} telemetry parameter(s)."
        ),
        "possible_domains": ["electrical", "mechanical"] if breaches else [],
        "statistics": stats,
    }
