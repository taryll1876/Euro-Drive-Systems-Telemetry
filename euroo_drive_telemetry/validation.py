from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .data import TelemetryRun
from .sensors import REQUIRED_COLUMNS


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    column: str
    message: str


def validate_run(run: TelemetryRun) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = REQUIRED_COLUMNS.difference(run.columns)
    for column in sorted(missing):
        issues.append(ValidationIssue("error", column, "Required telemetry column is missing."))

    if not run.data:
        return [ValidationIssue("error", "*", "Run contains no telemetry samples.")]

    lengths = {name: len(values) for name, values in run.data.items()}
    expected = max(set(lengths.values()), key=list(lengths.values()).count)
    for name, length in lengths.items():
        if length != expected:
            issues.append(ValidationIssue("error", name, f"Column length {length} differs from expected {expected}."))

    time = run.series("time_s")
    if len(time) < 2:
        issues.append(ValidationIssue("error", "time_s", "At least two time samples are required."))
    elif np.any(np.diff(time) <= 0):
        issues.append(ValidationIssue("error", "time_s", "Timestamps must be strictly increasing."))

    ranges = {
        "throttle_pct": (0, 100),
        "brake_pct": (0, 100),
        "clutch_pct": (0, 100),
        "handbrake_pct": (0, 100),
        "outer_zone_fill_pct": (0, 100),
        "transition_quality_pct": (0, 100),
        "lambda": (0.5, 1.4),
        "coolant_c": (-20, 140),
        "oil_pressure_kpa": (0, 1000),
    }
    for column, (low, high) in ranges.items():
        if column in run.data:
            values = run.series(column)
            finite = values[np.isfinite(values)]
            if len(finite) and (np.min(finite) < low or np.max(finite) > high):
                issues.append(ValidationIssue("warning", column, f"Values fall outside expected range {low}..{high}."))

    for column, values in run.data.items():
        if np.isnan(values).any():
            issues.append(ValidationIssue("warning", column, "Column contains blank or non-finite samples."))
    return issues


def raise_on_errors(run: TelemetryRun) -> None:
    errors = [issue for issue in validate_run(run) if issue.level == "error"]
    if errors:
        details = "; ".join(f"{issue.column}: {issue.message}" for issue in errors)
        raise ValueError(f"{run.run_id} failed telemetry validation: {details}")
