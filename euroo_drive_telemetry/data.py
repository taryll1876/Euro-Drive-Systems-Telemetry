from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .sensors import REQUIRED_COLUMNS


@dataclass
class TelemetryRun:
    driver: str
    run_id: str
    track: str
    data: dict[str, np.ndarray]
    source_path: Path | None = None

    @property
    def duration_s(self) -> float:
        time = self.data.get("time_s", np.array([0.0]))
        return float(time[-1] - time[0]) if len(time) else 0.0

    @property
    def sample_count(self) -> int:
        return len(next(iter(self.data.values()))) if self.data else 0

    @property
    def sample_rate_hz(self) -> float:
        if self.sample_count < 2 or self.duration_s <= 0:
            return 0.0
        return float((self.sample_count - 1) / self.duration_s)

    @property
    def columns(self) -> set[str]:
        return set(self.data)

    def series(self, name: str, default: float = 0.0) -> np.ndarray:
        if name in self.data:
            return self.data[name]
        length = len(next(iter(self.data.values()))) if self.data else 0
        return np.full(length, default, dtype=float)


def load_run_csv(path: str | Path, driver: str | None = None, run_id: str | None = None, track: str = "unknown") -> TelemetryRun:
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")

    missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
    if missing:
        raise ValueError(f"{path} is missing required telemetry columns: {sorted(missing)}")

    columns: dict[str, list[float]] = {name: [] for name in reader.fieldnames}
    for row in rows:
        for name in columns:
            columns[name].append(_to_float(row.get(name, "")))

    return TelemetryRun(
        driver=driver or path.stem.split("_")[0].replace("-", " ").title(),
        run_id=run_id or path.stem,
        track=track,
        data={name: np.asarray(values, dtype=float) for name, values in columns.items()},
        source_path=path,
    )


def load_runs(paths: Iterable[str | Path], track: str = "unknown") -> list[TelemetryRun]:
    return [load_run_csv(path, track=track) for path in paths]


def normalize(values: np.ndarray, low: float, high: float, invert: bool = False) -> np.ndarray:
    clipped = np.clip((values - low) / max(high - low, 1e-9), 0.0, 1.0)
    return 1.0 - clipped if invert else clipped


def stable_mean(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if len(finite) else 0.0


def percentile(values: np.ndarray, q: float) -> float:
    finite = values[np.isfinite(values)]
    return float(np.percentile(finite, q)) if len(finite) else 0.0


def _to_float(value: str | None) -> float:
    if value in ("", None):
        return np.nan
    try:
        return float(value)
    except ValueError:
        return np.nan
