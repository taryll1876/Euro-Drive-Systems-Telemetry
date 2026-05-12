from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import ScoringConfig
from .data import TelemetryRun, normalize, percentile, stable_mean


@dataclass(frozen=True)
class DriftScore:
    line: float
    angle: float
    style: float
    total: float
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonDelta:
    metric: str
    driver_value: float
    reference_value: float
    delta: float
    advice: str


FD_2026_POINTS = {
    "qualifying_bonus": {1: 3, 2: 2, 3: 1},
    "seeding_battle_win": 3,
    "main_event_battle_win": 10,
}


def score_run(run: TelemetryRun, config: ScoringConfig | None = None) -> DriftScore:
    config = config or ScoringConfig()
    line_error = run.series("distance_to_line_m")
    zone_fill = run.series("outer_zone_fill_pct")
    clip_error = run.series("inner_clip_distance_m")
    angle = np.abs(run.series("drift_angle_deg"))
    transition = run.series("transition_quality_pct")
    throttle = run.series("throttle_pct")
    brake = run.series("brake_pct")
    handbrake = run.series("handbrake_pct")

    line_score = (
        config.line_points * stable_mean(normalize(line_error, 0.0, config.line_error_max_m, invert=True))
        + config.zone_points * stable_mean(normalize(zone_fill, config.outer_zone_min_pct, 100.0))
        + config.clip_points * stable_mean(normalize(clip_error, 0.0, config.clip_error_max_m, invert=True))
    )
    angle_score = config.angle_points * stable_mean(normalize(angle, config.min_angle_deg, config.target_angle_deg))

    throttle_commitment = stable_mean(normalize(throttle, config.min_throttle_pct, config.target_throttle_pct))
    smoothness_penalty = min(1.0, _roughness(throttle) + _roughness(brake) + 0.6 * _roughness(handbrake))
    style_score = config.style_points * (
        0.45 * stable_mean(normalize(transition, config.min_transition_quality_pct, 100.0))
        + 0.35 * throttle_commitment
        + 0.20 * (1.0 - smoothness_penalty)
    )

    line_score = float(np.clip(line_score, 0, config.angle_points))
    angle_score = float(np.clip(angle_score, 0, config.angle_points))
    style_score = float(np.clip(style_score, 0, config.style_points))

    automated_line_angle = (
        config.line_angle_weight
        * 100.0
        / max(config.angle_points, 1e-9)
        * (0.5 * line_score + 0.5 * angle_score)
    )
    style_component = (config.style_weight / max(config.style_points, 1e-9)) * style_score * 100.0
    total = float(np.clip(automated_line_angle + style_component, 0, 100))
    notes = tuple(_score_notes(run, line_score, angle_score, style_score))
    return DriftScore(round(line_score, 2), round(angle_score, 2), round(style_score, 2), round(total, 2), notes)


def compare_runs(driver: TelemetryRun, reference: TelemetryRun) -> list[ComparisonDelta]:
    metrics = [
        ("avg_speed_kph", "speed_kph", "Higher mid-drift speed with the same line is worth chasing."),
        ("p90_angle_deg", "drift_angle_deg", "Look for more committed angle without mid-corner corrections."),
        ("avg_throttle_pct", "throttle_pct", "Earlier, steadier throttle helps style and tire smoke."),
        ("avg_brake_pct", "brake_pct", "Use braking as a deliberate tool, not a panic correction."),
        ("avg_line_error_m", "distance_to_line_m", "Tighter line error means better clipping point precision."),
        ("avg_zone_fill_pct", "outer_zone_fill_pct", "Fill the outer zones deeper and hold them longer."),
        ("avg_transition_quality_pct", "transition_quality_pct", "Sharper but settled transitions improve style."),
    ]
    deltas: list[ComparisonDelta] = []
    for metric, column, advice in metrics:
        reducer = percentile if metric.startswith("p90") else stable_mean
        lhs = reducer(np.abs(driver.series(column)), 90) if reducer is percentile else reducer(driver.series(column))
        rhs = reducer(np.abs(reference.series(column)), 90) if reducer is percentile else reducer(reference.series(column))
        deltas.append(ComparisonDelta(metric, round(lhs, 2), round(rhs, 2), round(lhs - rhs, 2), advice))
    return deltas


def championship_points(
    qualifying_rank: int | None = None,
    seeding_battle_wins: int = 0,
    main_event_battle_wins: int = 0,
) -> int:
    bonus = FD_2026_POINTS["qualifying_bonus"].get(qualifying_rank or 0, 0)
    return (
        bonus
        + seeding_battle_wins * FD_2026_POINTS["seeding_battle_win"]
        + main_event_battle_wins * FD_2026_POINTS["main_event_battle_win"]
    )


def _roughness(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 3:
        return 0.0
    return float(np.clip(np.mean(np.abs(np.diff(finite))) / 35.0, 0.0, 1.0))


def _score_notes(run: TelemetryRun, line_score: float, angle_score: float, style_score: float) -> list[str]:
    notes: list[str] = []
    if stable_mean(run.series("distance_to_line_m")) > 1.25:
        notes.append("Line: car is drifting wide of the intended path; review clipping point approach.")
    if stable_mean(run.series("outer_zone_fill_pct")) < 70:
        notes.append("Line: outer zones are under-filled; carry the rear bumper deeper into the zone.")
    if percentile(np.abs(run.series("drift_angle_deg")), 90) < 45:
        notes.append("Angle: peak angle is conservative; add commitment at initiation.")
    if style_score < 13:
        notes.append("Style: inputs look busy; smooth pedal/handbrake overlap through transitions.")
    if not notes:
        notes.append("Run is balanced: focus on small gains in proximity to line and transition timing.")
    return notes
