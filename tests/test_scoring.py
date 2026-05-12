from pathlib import Path

from euroo_drive_telemetry.data import load_run_csv
from euroo_drive_telemetry.config import load_config, write_default_config
from euroo_drive_telemetry.export import export_session_json, export_standings_csv
from euroo_drive_telemetry.fd_2026 import (
    PRO_DRIVERS_2026,
    PRO_SCHEDULE_2026,
    PRO_STANDINGS_AFTER_LONG_BEACH_2026,
    PROSPEC_SCHEDULE_2026,
    PROSPEC_TO_PRO_2026,
    export_fd_2026_reference,
    find_pro_driver,
    find_pro_standing,
)
from euroo_drive_telemetry.link_ecu import decode_frame
from euroo_drive_telemetry.report import write_driver_report
from euroo_drive_telemetry.sample_data import generate_samples
from euroo_drive_telemetry.scoring import championship_points, score_run
from euroo_drive_telemetry.session import build_session
from euroo_drive_telemetry.validation import validate_run


def test_sample_run_scores_and_report(tmp_path: Path) -> None:
    paths = generate_samples(tmp_path / "runs")
    run = load_run_csv(paths[0], track="test")
    reference = load_run_csv(paths[1], track="test")

    score = score_run(run)
    assert 0 <= score.total <= 100
    assert score.notes

    report = write_driver_report(run, tmp_path / "reports", reference, qualifying_rank=1, main_event_battle_wins=2)
    text = report.read_text(encoding="utf-8")
    assert "Euroo Drive Systems Run Report" in text
    assert "FD-style championship points estimate: 23" in text


def test_fd_style_points() -> None:
    assert championship_points(qualifying_rank=1, main_event_battle_wins=4) == 43
    assert championship_points(qualifying_rank=3, seeding_battle_wins=2) == 7
    assert championship_points(qualifying_rank=9) == 0


def test_event_session_exports_and_validation(tmp_path: Path) -> None:
    config_path = write_default_config(tmp_path / "event.json")
    config = load_config(config_path)
    paths = generate_samples(tmp_path / "runs")
    session = build_session(paths, config)

    assert len(session.results) == 3
    assert session.standings()[0].score.total >= session.standings()[-1].score.total
    assert not [issue for issue in validate_run(session.results[0].run) if issue.level == "error"]

    standings = export_standings_csv(session, tmp_path / "exports")
    summary = export_session_json(session, tmp_path / "exports")
    assert standings.exists()
    assert summary.exists()


def test_link_ecu_decode_frame() -> None:
    decoded = decode_frame(0x3E8, bytes([0x1F, 0x40, 160, 0x00, 0x64, 0, 0, 0]))
    assert decoded["rpm"] == 8000
    assert decoded["throttle_pct"] == 80
    assert decoded["boost_kpa"] == 100


def test_formula_drift_2026_reference_exports(tmp_path: Path) -> None:
    assert len(PRO_SCHEDULE_2026) == 8
    assert len(PROSPEC_SCHEDULE_2026) == 4
    assert len(PRO_DRIVERS_2026) == 34
    assert {driver.name for driver in PROSPEC_TO_PRO_2026} == {"Cody Buchanan", "Cole Richards", "Nate Chen"}
    assert find_pro_driver("272").previous_series_points == 130
    assert find_pro_standing("Conor Shanahan").total_points == 51

    paths = export_fd_2026_reference(tmp_path / "fd")
    assert len(paths) == 6
    assert all(path.exists() for path in paths)
