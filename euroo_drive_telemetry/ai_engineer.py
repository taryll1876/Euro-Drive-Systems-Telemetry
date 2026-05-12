from __future__ import annotations

import os

from .config import EventConfig, default_config
from .data import TelemetryRun
from .scoring import compare_runs, score_run
from .validation import validate_run


class AIDriftEngineer:
    """Rule-based feedback now, LLM-backed feedback later when API credentials exist."""

    def __init__(self, config: EventConfig | None = None) -> None:
        self.config = config or default_config()

    def review(self, run: TelemetryRun, reference: TelemetryRun | None = None) -> list[str]:
        if self.config.ai_provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                generated = self._openai_review(run, reference)
            except Exception:
                generated = []
            if generated:
                return generated

        score = score_run(run, self.config.scoring)
        feedback = [
            f"Run score {score.total}/100: line {score.line}/{self.config.scoring.angle_points:.0f}, "
            f"angle {score.angle}/{self.config.scoring.angle_points:.0f}, "
            f"style {score.style}/{self.config.scoring.style_points:.0f}.",
            *score.notes,
        ]
        for issue in validate_run(run):
            if issue.level == "error":
                feedback.append(f"Data quality: fix {issue.column} before trusting this run. {issue.message}")
        if reference:
            for delta in compare_runs(run, reference):
                if abs(delta.delta) >= _threshold(delta.metric):
                    direction = "higher" if delta.delta > 0 else "lower"
                    feedback.append(
                        f"{delta.metric}: {run.driver} is {abs(delta.delta)} {direction} than {reference.driver}. {delta.advice}"
                    )
        return feedback

    def _openai_review(self, run: TelemetryRun, reference: TelemetryRun | None) -> list[str]:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return []

        score = score_run(run, self.config.scoring)
        prompt = (
            "You are a professional drift engineer. Give concise driver coaching for one run. "
            f"Driver={run.driver}. Score={score.total}. Line={score.line}. Angle={score.angle}. Style={score.style}. "
            f"Notes={'; '.join(score.notes)}."
        )
        if reference:
            prompt += f" Reference driver={reference.driver}. Comparison={compare_runs(run, reference)}."
        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("EUROO_OPENAI_MODEL", "gpt-5.4-mini"),
            input=prompt,
        )
        text = getattr(response, "output_text", "")
        return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


def _threshold(metric: str) -> float:
    if metric.endswith("_m"):
        return 0.35
    if metric.endswith("_deg"):
        return 4.0
    return 6.0
