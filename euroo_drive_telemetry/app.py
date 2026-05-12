from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

from .ai_engineer import AIDriftEngineer
from .config import EventConfig, load_config, write_default_config
from .data import TelemetryRun, load_run_csv, stable_mean
from .discord_support import post_report_to_discord
from .export import export_session_json, export_standings_csv
from .fd_2026 import export_fd_2026_reference
from .report import write_driver_report
from .sample_data import generate_samples
from .scoring import score_run
from .session import build_session
from .validation import validate_run


WIDTH = 1280
HEIGHT = 760
PANEL = (20, 24, 32)
INK = (235, 240, 244)
MUTED = (148, 162, 174)
ACCENT = (0, 207, 181)
WARN = (246, 173, 85)
BRAKE = (255, 91, 91)
THROTTLE = (101, 220, 114)
ANGLE = (118, 171, 255)
LINE = (255, 210, 90)


class TelemetryDashboard:
    def __init__(self, runs: list[TelemetryRun], config: EventConfig) -> None:
        import arcade

        self.arcade = arcade
        self.window = arcade.Window(WIDTH, HEIGHT, "Euroo Drive Systems Telemetry Spotter")
        self.window.background_color = (10, 13, 18)
        self.runs = runs
        self.config = config
        self.focus = 0
        self.reference = 1 if len(runs) > 1 else 0
        self.engineer = AIDriftEngineer(config=config)
        self.window.on_draw = self.on_draw
        self.window.on_key_press = self.on_key_press

    def run(self) -> None:
        self.arcade.run()

    @property
    def run_a(self) -> TelemetryRun:
        return self.runs[self.focus]

    @property
    def run_b(self) -> TelemetryRun | None:
        if len(self.runs) < 2 or self.reference == self.focus:
            return None
        return self.runs[self.reference]

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        arcade = self.arcade
        if symbol == arcade.key.TAB:
            self.focus = (self.focus + 1) % len(self.runs)
            if self.reference == self.focus:
                self.reference = (self.reference + 1) % len(self.runs)
        elif symbol == arcade.key.R:
            self.reference = (self.reference + 1) % len(self.runs)
            if self.reference == self.focus:
                self.reference = (self.reference + 1) % len(self.runs)
        elif symbol == arcade.key.S:
            report = write_driver_report(self.run_a, self.config.report_dir, self.run_b, config=self.config)
            print(f"Report written: {report}")

    def on_draw(self) -> None:
        arcade = self.arcade
        self.window.clear()
        score = score_run(self.run_a, self.config.scoring)
        ref_score = score_run(self.run_b, self.config.scoring) if self.run_b else None
        self._text("EUROO DRIVE SYSTEMS", 32, 718, 18, ACCENT, bold=True)
        self._text(f"{self.config.name} - drift telemetry spotter", 32, 692, 13, MUTED)
        self._text("TAB driver  |  R reference  |  S write report", 990, 718, 12, MUTED)

        self._card(28, 510, 356, 150, "Driver")
        self._text(self.run_a.driver, 52, 610, 28, INK, bold=True)
        self._text(f"{self.run_a.run_id}  /  {self.run_a.track}", 52, 582, 12, MUTED)
        self._text(f"Score {score.total:.1f}", 52, 548, 24, ACCENT, bold=True)
        if ref_score and self.run_b:
            self._text(f"Reference {self.run_b.driver}: {ref_score.total:.1f}", 52, 524, 13, MUTED)

        self._card(404, 510, 400, 150, "Judging Model")
        self._bar("Line", score.line / self.config.scoring.angle_points, 430, 606, LINE)
        self._bar("Angle", score.angle / self.config.scoring.angle_points, 430, 566, ANGLE)
        self._bar("Style", score.style / self.config.scoring.style_points, 430, 526, WARN)

        self._card(824, 510, 428, 150, "Spotter Calls")
        for i, note in enumerate(self.engineer.review(self.run_a, self.run_b)[:4]):
            self._text(f"- {note[:78]}", 848, 614 - i * 24, 11, INK if i == 0 else MUTED)

        self._card(28, 292, 594, 190, "Pedals")
        self._plot(self.run_a, "throttle_pct", 58, 328, 520, 112, THROTTLE, 0, 100)
        self._plot(self.run_a, "brake_pct", 58, 328, 520, 112, BRAKE, 0, 100)
        self._legend(70, 306, [("Throttle", THROTTLE), ("Brake", BRAKE)])

        self._card(650, 292, 602, 190, "Angle And Style")
        self._plot(self.run_a, "drift_angle_deg", 682, 328, 520, 112, ANGLE, 0, 80)
        self._plot(self.run_a, "transition_quality_pct", 682, 328, 520, 112, WARN, 0, 100)
        self._legend(694, 306, [("Drift angle", ANGLE), ("Transition quality", WARN)])

        self._card(28, 40, 594, 220, "Line Map")
        self._map(self.run_a, 64, 70, 510, 150, ACCENT)
        if self.run_b:
            self._map(self.run_b, 64, 70, 510, 150, MUTED)
            self._legend(70, 52, [(self.run_a.driver, ACCENT), (self.run_b.driver, MUTED)])

        self._card(650, 40, 602, 220, "Sensor Snapshot")
        stats = [
            ("Avg speed", f"{stable_mean(self.run_a.series('speed_kph')):.1f} kph"),
            ("P90 angle", f"{np.percentile(np.abs(self.run_a.series('drift_angle_deg')), 90):.1f} deg"),
            ("Line error", f"{stable_mean(self.run_a.series('distance_to_line_m')):.2f} m"),
            ("Zone fill", f"{stable_mean(self.run_a.series('outer_zone_fill_pct')):.1f}%"),
            ("Oil pressure", f"{stable_mean(self.run_a.series('oil_pressure_kpa')):.0f} kPa"),
            ("Lambda", f"{stable_mean(self.run_a.series('lambda')):.3f}"),
            ("Rear tire temp", f"{stable_mean((self.run_a.series('tire_temp_rl_c') + self.run_a.series('tire_temp_rr_c')) / 2):.1f} C"),
            ("Boost", f"{stable_mean(self.run_a.series('boost_kpa')):.0f} kPa"),
        ]
        for i, (label, value) in enumerate(stats):
            x = 680 + (i % 2) * 276
            y = 214 - (i // 2) * 42
            self._text(label, x, y, 11, MUTED)
            self._text(value, x, y - 20, 17, INK, bold=True)

    def _card(self, x: float, y: float, w: float, h: float, title: str) -> None:
        self.arcade.draw_lrbt_rectangle_filled(x, x + w, y, y + h, PANEL)
        self.arcade.draw_lrbt_rectangle_outline(x, x + w, y, y + h, (43, 52, 64), 1)
        self._text(title.upper(), x + 18, y + h - 28, 10, MUTED, bold=True)

    def _text(self, text: str, x: float, y: float, size: int, color: tuple[int, int, int], bold: bool = False) -> None:
        self.arcade.draw_text(text, x, y, color, size, font_name=("Arial",), bold=bold)

    def _bar(self, label: str, pct: float, x: float, y: float, color: tuple[int, int, int]) -> None:
        pct = float(np.clip(pct, 0, 1))
        self._text(label, x, y + 4, 12, INK)
        self.arcade.draw_lrbt_rectangle_filled(x + 82, x + 328, y, y + 18, (32, 40, 50))
        self.arcade.draw_lrbt_rectangle_filled(x + 82, x + 82 + 246 * pct, y, y + 18, color)
        self._text(f"{pct * 100:.0f}%", x + 340, y + 1, 12, MUTED)

    def _plot(self, run: TelemetryRun, column: str, x: float, y: float, w: float, h: float, color: tuple[int, int, int], low: float, high: float) -> None:
        values = np.nan_to_num(run.series(column), nan=low)
        if len(values) < 2:
            return
        points = []
        step = max(1, len(values) // 180)
        sampled = values[::step]
        for i, value in enumerate(sampled):
            px = x + w * i / max(len(sampled) - 1, 1)
            py = y + h * np.clip((value - low) / max(high - low, 1e-9), 0, 1)
            points.append((px, py))
        self.arcade.draw_line_strip(points, color, 2)

    def _map(self, run: TelemetryRun, x: float, y: float, w: float, h: float, color: tuple[int, int, int]) -> None:
        xs = run.series("gps_x_m")
        ys = run.series("gps_y_m")
        if len(xs) < 2:
            return
        xspan = max(float(np.max(xs) - np.min(xs)), 1e-9)
        yspan = max(float(np.max(ys) - np.min(ys)), 1e-9)
        points = [
            (x + (float(px) - float(np.min(xs))) / xspan * w, y + (float(py) - float(np.min(ys))) / yspan * h)
            for px, py in zip(xs[::4], ys[::4])
        ]
        self.arcade.draw_line_strip(points, color, 3)

    def _legend(self, x: float, y: float, items: list[tuple[str, tuple[int, int, int]]]) -> None:
        for i, (label, color) in enumerate(items):
            lx = x + i * 126
            self.arcade.draw_circle_filled(lx, y + 7, 5, color)
            self._text(label, lx + 12, y, 11, MUTED)


def _default_paths() -> list[Path]:
    sample_dir = Path("sample_runs")
    paths = sorted(sample_dir.glob("*.csv"))
    if not paths:
        paths = generate_samples(sample_dir)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Euroo Drive Systems telemetry analyser.")
    parser.add_argument("runs", nargs="*", help="Telemetry CSV files to load.")
    parser.add_argument("--config", default=None, help="Event JSON config path.")
    parser.add_argument("--init-config", default=None, help="Write a default production event config and exit.")
    parser.add_argument("--track", default=None)
    parser.add_argument("--report", action="store_true", help="Write reports instead of opening Arcade.")
    parser.add_argument("--export", action="store_true", help="Export standings CSV and session JSON.")
    parser.add_argument("--validate", action="store_true", help="Print validation issues and exit.")
    parser.add_argument("--discord", action="store_true", help="Post generated reports to the configured Discord webhook.")
    parser.add_argument("--fd-2026-reference", action="store_true", help="Export 2026 Formula Drift schedule, drivers, standings, and PROSPEC-to-PRO data.")
    args = parser.parse_args()

    if args.init_config:
        print(write_default_config(args.init_config))
        return

    config = load_config(args.config)
    if args.track:
        config = EventConfig(**{**config.__dict__, "track": args.track})

    if args.fd_2026_reference:
        for path in export_fd_2026_reference(config.export_dir):
            print(path)
        if not args.runs and not args.report and not args.export:
            return

    paths = [Path(path) for path in args.runs] if args.runs else _default_paths()
    runs = [load_run_csv(path, track=config.track) for path in paths]

    if args.validate:
        failed = False
        for run in runs:
            issues = validate_run(run)
            print(f"{run.run_id}: {len([i for i in issues if i.level == 'error'])} errors, {len([i for i in issues if i.level == 'warning'])} warnings")
            for issue in issues:
                print(f"  {issue.level.upper()} {issue.column}: {issue.message}")
                failed = failed or issue.level == "error"
        raise SystemExit(1 if failed else 0)

    session = build_session(paths, config)

    if args.export:
        print(export_standings_csv(session))
        print(export_session_json(session))
        if not args.report:
            return

    if args.report:
        reference = session.reference
        webhook = config.discord_webhook_url or os.getenv("EUROO_DISCORD_WEBHOOK")
        for result in session.results:
            report = write_driver_report(
                result.run,
                config.report_dir,
                reference if reference is not result.run else None,
                qualifying_rank=result.qualifying_rank,
                main_event_battle_wins=result.main_event_battle_wins,
                seeding_battle_wins=result.seeding_battle_wins,
                config=config,
            )
            print(report)
            if args.discord:
                if not webhook:
                    raise SystemExit("Discord posting requested but no webhook is configured.")
                post_report_to_discord(webhook, report)
        return

    try:
        TelemetryDashboard(runs, config).run()
    except ImportError as exc:
        raise SystemExit("Arcade is not installed. Install dependencies with: uv sync") from exc


if __name__ == "__main__":
    main()
