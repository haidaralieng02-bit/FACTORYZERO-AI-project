import pandas as pd

from tools.telemetry import (
    analyze_telemetry,
    normalize_telemetry_columns,
    validate_telemetry,
)


def test_normal_telemetry():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=4, freq="h"),
            "temperature": [60, 61, 62, 63],
            "current": [20, 21, 21, 22],
        }
    )
    r = analyze_telemetry(df)
    assert r["status"] == "NORMAL"
    assert r["severity"] == "NORMAL"


def test_abnormal_telemetry():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=4, freq="h"),
            "temperature": [60, 90, 92, 94],
            "current": [20, 35, 36, 37],
            "vibration": [2, 8, 9, 10],
        }
    )
    r = analyze_telemetry(df)
    assert r["severity"] == "HIGH"
    assert len(r["threshold_breaches"]) == 3


def test_live_csv_aliases_are_normalized_and_detected():
    """Regression test for the LIVE serious test CSV schema."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-03", periods=4, freq="h"),
            "temperature_c": [86, 89, 92, 94],
            "vibration_mm_s": [8.2, 9.1, 10.2, 11.3],
            "current_a": [33, 34, 36, 37],
            "voltage_v": [461, 459, 458, 457],
            "rpm": [1495, 1470, 1440, 1405],
            "power_kw": [16.0, 16.8, 17.5, 18.2],
        }
    )

    normalized = normalize_telemetry_columns(df)
    assert {"temperature", "vibration", "current", "voltage", "rpm", "power"}.issubset(
        normalized.columns
    )

    result = analyze_telemetry(df)

    assert result["status"] == "ANOMALY"
    assert result["severity"] == "HIGH"
    assert {x["parameter"] for x in result["threshold_breaches"]} == {
        "temperature",
        "vibration",
        "current",
    }
    assert result["statistics"]["temperature"]["max"] == 94.0
    assert result["statistics"]["vibration"]["max"] == 11.3
    assert result["statistics"]["current"]["max"] == 37.0


def test_case_and_punctuation_variants_are_supported():
    df = pd.DataFrame(
        {
            "Date Time": pd.date_range("2026-01-01", periods=3, freq="h"),
            "Temp-C": [60, 61, 62],
            "Motor Current (A)": [20, 21, 22],
            "Vibration RMS": [2, 3, 4],
        }
    )
    assert validate_telemetry(df) == []
    result = analyze_telemetry(df)
    assert result["status"] == "NORMAL"
    assert set(["temperature", "current", "vibration"]).issubset(
        result["detected_parameters"]
    )


def test_missing_timestamp():
    df = pd.DataFrame({"temperature": [1, 2]})
    assert validate_telemetry(df)


def test_timestamp_only_is_rejected():
    df = pd.DataFrame(
        {"timestamp": pd.date_range("2026-01-01", periods=2, freq="h")}
    )
    errors = validate_telemetry(df)
    assert any("numeric measurement" in e for e in errors)
