from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import EventConfig
from .data import TelemetryRun, load_run_csv
from .scoring import DriftScore, championship_points, score_run
from .validation import ValidationIssue, validate_run


@dataclass
class DriverResult:
    run: TelemetryRun
    score: DriftScore
    qualifying_rank: int | None = None
    seeding_battle_wins: int = 0
    main_event_battle_wins: int = 0
    validation: list[ValidationIssue] = field(default_factory=list)

    @property
    def points(self) -> int:
        return championship_points(self.qualifying_rank, self.seeding_battle_wins, self.main_event_battle_wins)


@dataclass
class EventSession:
    config: EventConfig
    results: list[DriverResult]

    @property
    def reference(self) -> TelemetryRun | None:
        if self.config.reference_driver:
            target = self.config.reference_driver.lower()
            for result in self.results:
                if result.run.driver.lower() == target or result.run.run_id.lower() == target:
                    return result.run
        return self.results[0].run if self.results else None

    def standings(self) -> list[DriverResult]:
        return sorted(self.results, key=lambda result: (result.points, result.score.total), reverse=True)


def build_session(paths: list[str | Path], config: EventConfig) -> EventSession:
    runs = [load_run_csv(path, track=config.track) for path in paths]
    ordered = sorted(runs, key=lambda run: score_run(run, config.scoring).total, reverse=True)
    ranks = {run.run_id: index + 1 for index, run in enumerate(ordered)}
    results = [
        DriverResult(
            run=run,
            score=score_run(run, config.scoring),
            qualifying_rank=ranks.get(run.run_id),
            validation=validate_run(run),
        )
        for run in runs
    ]
    return EventSession(config=config, results=results)
