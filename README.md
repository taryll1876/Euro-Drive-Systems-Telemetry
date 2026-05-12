# Euroo Drive Systems Telemetry

Drift telemetry analyser and virtual spotter for comparing drivers, visualising throttle/brake/angle/line, scoring runs, and writing driver reports after each pass.

## What It Does

- Loads CSV telemetry runs with drift-specific sensors.
- Scores line, angle, and style with a 2026-style telemetry model: automated line/angle plus a style component.
- Compares a driver against another run or reference driver.
- Shows an Arcade dashboard with pedals, drift angle, transition quality, line map, and sensor snapshot.
- Generates Markdown reports for drivers after each run.
- Includes a rule-based AI drift engineer that can later be swapped for an LLM-backed coach.
- Includes Discord webhook support for posting reports.
- Includes a Link ECU CAN decoding scaffold for user-defined CAN streams.
- Includes FD-style championship point helpers.

## Quick Start

```powershell
uv sync
uv run euroo-sample-data
uv run euroo-telemetry
```

Create an editable production event config:

```powershell
uv run euroo-telemetry --init-config euroo_event.json
```

Write reports instead of opening the dashboard:

```powershell
uv run euroo-telemetry --report
```

Validate, report, and export a full event batch:

```powershell
uv run euroo-telemetry --config euroo_event.json .\runs\driver_a.csv .\runs\driver_b.csv --validate
uv run euroo-telemetry --config euroo_event.json .\runs\driver_a.csv .\runs\driver_b.csv --report --export
```

Export the built-in 2026 Formula Drift reference package:

```powershell
uv run euroo-telemetry --config euroo_event.json --fd-2026-reference
```

Load your own runs:

```powershell
uv run euroo-telemetry .\runs\driver_a.csv .\runs\driver_b.csv --track "Road Atlanta"
```

## Dashboard Controls

- `TAB`: switch primary driver.
- `R`: switch reference driver.
- `S`: write a driver report to `reports/`.

## CSV Input

Required columns:

```text
time_s,gps_x_m,gps_y_m,speed_kph,drift_angle_deg,throttle_pct,brake_pct,
distance_to_line_m,outer_zone_fill_pct,inner_clip_distance_m,transition_quality_pct
```

The included `euroo_drive_telemetry/sensors.py` file lists a larger drift sensor schema: pedals, wheel speeds, tire temperatures/pressures, suspension travel, engine data, proximity, relative angle, relative speed, line error, clipping distances, and transition quality.

## Scoring Model

This prototype follows the spirit of Formula Drift's 2026 telemetry direction:

- Line and angle are quantified from vehicle data.
- Style remains a separate 20-point component.
- Total run score is out of 100.

The scoring code is intentionally configurable and series-neutral. It is not an official Formula Drift judging implementation.

Use `euroo_event.example.json` or `--init-config` to tune:

- Line error, outer-zone fill, and clipping distance targets.
- Minimum and target drift angle.
- Throttle commitment and transition quality thresholds.
- Line/angle and style weighting.
- Report/export directories and optional Discord webhook.

Championship point helpers use the 2026 Formula Drift sporting regulation basics:

- Qualifying bonus: first 3, second 2, third 1.
- Seeding bracket battle win: 3.
- Main event battle win: 10.

## 2026 Formula Drift Reference Data

The tool includes a static 2026 Formula Drift reference layer in `euroo_drive_telemetry/fd_2026.py`:

- 8-round PRO schedule.
- 4-round PROSPEC schedule.
- 2026 PRO driver roster with car numbers and rookie flags.
- Current 2026 PRO standings after Round 1 Long Beach.
- PROSPEC-to-PRO rookie bridge for Cody Buchanan, Nate Chen, and Cole Richards, including their 2025 PROSPEC rank/points.

The official 2026 PROSPEC driver page was still showing `Coming Soon` when this update was added, so the production dataset marks that as unavailable instead of inventing a roster.

## Link ECU Hook

`euroo_drive_telemetry/link_ecu.py` contains a starting CAN decoder. Link ECU supports user-defined CAN streams, so the exact CAN IDs and byte layouts should match the stream you configure in PCLink. The default examples use common dash-style IDs as placeholders, not a universal map.

Useful next hardware steps:

- Configure PCLink CAN as a user-defined transmit stream.
- Set the stream bitrate to match your CAN adapter.
- Export the stream layout and mirror those IDs/signals in `LINK_ECU_BASE_SIGNALS`.
- Install the optional CAN dependency with `uv sync --extra can`.

## Discord Reports

Reports are Markdown files. To send one to Discord:

```python
from euroo_drive_telemetry.discord_support import post_report_to_discord

post_report_to_discord("https://discord.com/api/webhooks/...", "reports/akira_run_01_driver_report.md")
```

Or set `discord_webhook_url` in `euroo_event.json` and run:

```powershell
uv run euroo-telemetry --config euroo_event.json --report --discord
```

## Production Workflow

1. Configure the event with `uv run euroo-telemetry --init-config euroo_event.json`.
2. Generate or import CSV telemetry into a `runs/` folder.
3. Run `uv run euroo-telemetry --config euroo_event.json .\runs\*.csv --validate`.
4. Fix any validation errors before trusting scores.
5. Run `uv run euroo-telemetry --config euroo_event.json .\runs\*.csv --report --export`.
6. Review `reports/` for driver-ready coaching and `exports/standings.csv` for event standings.
7. Open the Arcade dashboard with the same files for visual driver comparison.
8. Run `uv run euroo-telemetry --config euroo_event.json --fd-2026-reference` when you need the current FD schedule/roster/points reference files in `exports/`.

## AI Engineer

The default `ai_provider` is `rules`, which is deterministic and works offline. Set `"ai_provider": "openai"` and provide `OPENAI_API_KEY` to enable LLM-generated coaching. If the API is unavailable, reports fall back to the rule engine.

## Project Map

- `euroo_drive_telemetry/app.py`: Arcade interface and CLI.
- `euroo_drive_telemetry/data.py`: CSV loading and telemetry run model.
- `euroo_drive_telemetry/scoring.py`: line, angle, style, comparison, standings points.
- `euroo_drive_telemetry/config.py`: event/scoring configuration.
- `euroo_drive_telemetry/session.py`: batch event session and standings model.
- `euroo_drive_telemetry/validation.py`: CSV and sensor quality checks.
- `euroo_drive_telemetry/export.py`: standings CSV and session JSON exports.
- `euroo_drive_telemetry/fd_2026.py`: Formula Drift 2026 schedule, PRO roster, standings, and PROSPEC-to-PRO data.
- `euroo_drive_telemetry/report.py`: automatic driver report writer.
- `euroo_drive_telemetry/ai_engineer.py`: feedback engine.
- `euroo_drive_telemetry/link_ecu.py`: Link ECU CAN protocol hook.
- `euroo_drive_telemetry/sample_data.py`: synthetic drift runs.
- `tests/`: focused checks for scoring, reports, and CAN decoding.

## References

- Formula Drift 2026 qualifying telemetry announcement: https://news.formulad.com/2026/fd-news/formula-drift-announces-major-2026-competition-format-changes-in-partnership-with-race-data-labs/
- Formula Drift 2026 sporting regulations: https://www.formulad.com/rulebook
- Link ECU CAN setup: https://support.linkecu.com/hc/en-us/articles/1500002420301-CAN-Setup
