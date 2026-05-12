from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScoringConfig:
    line_error_max_m: float = 3.0
    outer_zone_min_pct: float = 35.0
    clip_error_max_m: float = 2.5
    min_angle_deg: float = 25.0
    target_angle_deg: float = 62.0
    min_throttle_pct: float = 45.0
    target_throttle_pct: float = 95.0
    min_transition_quality_pct: float = 45.0
    line_points: float = 38.0
    zone_points: float = 26.0
    clip_points: float = 16.0
    angle_points: float = 80.0
    style_points: float = 20.0
    line_angle_weight: float = 0.80
    style_weight: float = 0.20


@dataclass(frozen=True)
class EventConfig:
    name: str = "Euroo Drift Test Day"
    track: str = "test-course"
    series: str = "FD-style"
    report_dir: str = "reports"
    export_dir: str = "exports"
    reference_driver: str | None = None
    discord_webhook_url: str | None = None
    ai_provider: str = "rules"
    scoring: ScoringConfig = field(default_factory=ScoringConfig)


def default_config() -> EventConfig:
    return EventConfig()


def write_default_config(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(default_config()), indent=2) + "\n", encoding="utf-8")
    return path


def load_config(path: str | Path | None = None) -> EventConfig:
    if path is None:
        env_path = os.getenv("EUROO_TELEMETRY_CONFIG")
        path = env_path if env_path else "euroo_event.json"
    path = Path(path)
    if not path.exists():
        return default_config()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _event_config_from_dict(raw)


def _event_config_from_dict(raw: dict[str, Any]) -> EventConfig:
    scoring_raw = raw.get("scoring", {})
    scoring = ScoringConfig(**{key: value for key, value in scoring_raw.items() if key in ScoringConfig.__dataclass_fields__})
    fields = {key: value for key, value in raw.items() if key in EventConfig.__dataclass_fields__ and key != "scoring"}
    return EventConfig(**fields, scoring=scoring)
