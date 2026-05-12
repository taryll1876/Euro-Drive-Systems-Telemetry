from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .session import EventSession


def export_standings_csv(session: EventSession, output_dir: str | Path | None = None) -> Path:
    output_dir = Path(output_dir or session.config.export_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "standings.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "driver",
                "run_id",
                "score",
                "line",
                "angle",
                "style",
                "qualifying_rank",
                "points",
                "validation_errors",
                "validation_warnings",
            ],
        )
        writer.writeheader()
        for rank, result in enumerate(session.standings(), start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "driver": result.run.driver,
                    "run_id": result.run.run_id,
                    "score": result.score.total,
                    "line": result.score.line,
                    "angle": result.score.angle,
                    "style": result.score.style,
                    "qualifying_rank": result.qualifying_rank,
                    "points": result.points,
                    "validation_errors": sum(issue.level == "error" for issue in result.validation),
                    "validation_warnings": sum(issue.level == "warning" for issue in result.validation),
                }
            )
    return path


def export_session_json(session: EventSession, output_dir: str | Path | None = None) -> Path:
    output_dir = Path(output_dir or session.config.export_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "session_summary.json"
    payload = {
        "event": asdict(session.config),
        "standings": [
            {
                "driver": result.run.driver,
                "run_id": result.run.run_id,
                "track": result.run.track,
                "score": asdict(result.score),
                "qualifying_rank": result.qualifying_rank,
                "points": result.points,
                "validation": [asdict(issue) for issue in result.validation],
            }
            for result in session.standings()
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
