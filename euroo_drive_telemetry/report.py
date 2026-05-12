from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .ai_engineer import AIDriftEngineer
from .config import EventConfig, default_config
from .data import TelemetryRun
from .fd_2026 import find_pro_driver, find_pro_standing
from .scoring import championship_points, compare_runs, score_run
from .validation import validate_run


def write_driver_report(
    run: TelemetryRun,
    output_dir: str | Path,
    reference: TelemetryRun | None = None,
    qualifying_rank: int | None = None,
    main_event_battle_wins: int = 0,
    seeding_battle_wins: int = 0,
    config: EventConfig | None = None,
) -> Path:
    config = config or default_config()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    score = score_run(run, config.scoring)
    engineer = AIDriftEngineer(config=config)
    points = championship_points(qualifying_rank, seeding_battle_wins, main_event_battle_wins)
    validation = validate_run(run)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    path = output_dir / f"{run.run_id}_driver_report.md"

    lines = [
        f"# Euroo Drive Systems Run Report: {run.driver}",
        "",
        f"- Generated: {timestamp}",
        f"- Event: {config.name}",
        f"- Track: {run.track}",
        f"- Series model: {config.series}",
        f"- Run: {run.run_id}",
        f"- Duration: {run.duration_s:.2f}s",
        f"- Score: {score.total}/100",
        f"- Telemetry line component: {score.line}/{config.scoring.angle_points:.0f}",
        f"- Telemetry angle component: {score.angle}/{config.scoring.angle_points:.0f}",
        f"- Style component: {score.style}/{config.scoring.style_points:.0f}",
        f"- FD-style championship points estimate: {points}",
        f"- Validation: {sum(issue.level == 'error' for issue in validation)} errors, "
        f"{sum(issue.level == 'warning' for issue in validation)} warnings",
        "",
        "## AI Engineer Notes",
        "",
    ]
    lines.extend(f"- {item}" for item in engineer.review(run, reference))
    official_driver = find_pro_driver(run.driver)
    official_standing = find_pro_standing(run.driver)
    if official_driver or official_standing:
        lines.extend(["", "## 2026 Formula Drift Context", ""])
        if official_driver:
            rookie = "yes" if official_driver.rookie else "no"
            lines.append(f"- PRO roster: #{official_driver.car_number} {official_driver.name}, rookie: {rookie}.")
            if official_driver.promoted_from:
                lines.append(
                    f"- PROSPEC-to-PRO: {official_driver.promoted_from} rank "
                    f"{official_driver.previous_series_rank}, {official_driver.previous_series_points} points."
                )
        if official_standing:
            lines.append(
                f"- Current PRO points after Long Beach: rank {official_standing.rank}, "
                f"{official_standing.total_points} total "
                f"({official_standing.qualifying_points} qualifying, {official_standing.main_event_points} main event)."
            )
    if reference:
        lines.extend(["", f"## Comparison Against {reference.driver}", ""])
        for delta in compare_runs(run, reference):
            lines.append(
                f"- {delta.metric}: {delta.driver_value} vs {delta.reference_value} "
                f"({delta.delta:+.2f}). {delta.advice}"
            )
    if validation:
        lines.extend(["", "## Data Quality", ""])
        for issue in validation:
            lines.append(f"- {issue.level.upper()} {issue.column}: {issue.message}")
    lines.extend(["", "## Next Run Targets", ""])
    lines.extend(f"- {note}" for note in score.notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
