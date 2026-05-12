from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class FormulaDriftEvent:
    round: int
    championship: str
    name: str
    venue: str
    city: str
    state: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class FormulaDriftDriver:
    name: str
    car_number: str
    championship: str
    rookie: bool = False
    promoted_from: str | None = None
    previous_series_rank: int | None = None
    previous_series_points: int | None = None


@dataclass(frozen=True)
class FormulaDriftStanding:
    rank: int
    car_number: str
    driver: str
    qualifying_points: int
    main_event_points: int
    total_points: int
    rookie: bool = False


FD_2026_SOURCES = {
    "pro_schedule": "https://www.formulad.com/",
    "prospec_schedule": "https://www.formulad.com/prospec",
    "pro_drivers": "https://www.formulad.com/drivers/pro",
    "pro_standings": "https://www.formulad.com/standings/2026/pro",
    "prospec_2025_standings": "https://www.formulad.com/standings/2025/pro2",
    "prospec_to_pro_note": "https://news.formulad.com/2026/fd-news/formula-drift-pro-championship-qualifying-results-from-round-1-in-long-beach/",
}


PRO_SCHEDULE_2026: tuple[FormulaDriftEvent, ...] = (
    FormulaDriftEvent(1, "PRO", "Streets of Long Beach", "Streets of Long Beach", "Long Beach", "CA", "2026-04-10", "2026-04-11"),
    FormulaDriftEvent(2, "PRO", "Road to the Championship", "Road Atlanta", "Atlanta", "GA", "2026-05-07", "2026-05-09"),
    FormulaDriftEvent(3, "PRO", "Scorched", "Orlando Speed World", "Orlando", "FL", "2026-05-29", "2026-05-30"),
    FormulaDriftEvent(4, "PRO", "Battle at the Springs", "Stafford Motor Speedway", "Stafford", "CT", "2026-06-18", "2026-06-20"),
    FormulaDriftEvent(5, "PRO", "Midwest Mayhem", "Indianapolis Raceway Park", "Indianapolis", "IN", "2026-07-30", "2026-08-01"),
    FormulaDriftEvent(6, "PRO", "Throwdown", "Evergreen Speedway", "Seattle", "WA", "2026-08-21", "2026-08-22"),
    FormulaDriftEvent(7, "PRO", "High Stakes", "The Bullring at Las Vegas Motor Speedway", "Las Vegas", "NV", "2026-09-24", "2026-09-26"),
    FormulaDriftEvent(8, "PRO", "Shoreline Showdown", "Streets of Long Beach", "Long Beach", "CA", "2026-10-23", "2026-10-24"),
)


PROSPEC_SCHEDULE_2026: tuple[FormulaDriftEvent, ...] = (
    FormulaDriftEvent(1, "PROSPEC", "Road to the Championship", "Road Atlanta", "Atlanta", "GA", "2026-05-07", "2026-05-09"),
    FormulaDriftEvent(2, "PROSPEC", "Battle at the Springs", "Stafford Motor Speedway", "Stafford", "CT", "2026-06-18", "2026-06-20"),
    FormulaDriftEvent(3, "PROSPEC", "Midwest Mayhem", "Indianapolis Raceway Park", "Indianapolis", "IN", "2026-07-30", "2026-08-01"),
    FormulaDriftEvent(4, "PROSPEC", "High Stakes", "The Bullring at Las Vegas Motor Speedway", "Las Vegas", "NV", "2026-09-24", "2026-09-26"),
)


PRO_DRIVERS_2026: tuple[FormulaDriftDriver, ...] = (
    FormulaDriftDriver("Adam LZ", "5", "PRO"),
    FormulaDriftDriver("Andy Hateley", "98", "PRO"),
    FormulaDriftDriver("Aurimas Bakchis", "723", "PRO"),
    FormulaDriftDriver("Ben Hobson", "213", "PRO"),
    FormulaDriftDriver("Branden Sorensen", "513", "PRO"),
    FormulaDriftDriver("Chris Forsberg", "64", "PRO"),
    FormulaDriftDriver("Cody Buchanan", "272", "PRO", True, "2025 PROSPEC", 1, 130),
    FormulaDriftDriver("Cole Richards", "11", "PRO", True, "2025 PROSPEC", 5, 100),
    FormulaDriftDriver("Connor O'Sullivan", "107", "PRO"),
    FormulaDriftDriver("Conor Shanahan", "79", "PRO"),
    FormulaDriftDriver("Dan Burkett", "34", "PRO"),
    FormulaDriftDriver("Daniel Stuke", "527", "PRO"),
    FormulaDriftDriver("Derek Madison", "27", "PRO"),
    FormulaDriftDriver("Diego Higa", "169", "PRO"),
    FormulaDriftDriver("Dylan Hughes", "129", "PRO"),
    FormulaDriftDriver("Federico Sceriffo", "117", "PRO"),
    FormulaDriftDriver("Fredric Aasbo", "151", "PRO"),
    FormulaDriftDriver("Hiroya Minowa", "168", "PRO"),
    FormulaDriftDriver("Jack Shanahan", "59", "PRO"),
    FormulaDriftDriver("James Deane", "130", "PRO"),
    FormulaDriftDriver("Jeff Jones", "818", "PRO"),
    FormulaDriftDriver("Jhonnattan Castro", "17", "PRO"),
    FormulaDriftDriver("Ken Gushi", "21", "PRO"),
    FormulaDriftDriver("Matt Field", "777", "PRO"),
    FormulaDriftDriver("Nate Chen", "4", "PRO", True, "2025 PROSPEC", 2, 110),
    FormulaDriftDriver("Rome Charpentier", "171", "PRO"),
    FormulaDriftDriver("Rudy Hansen", "119", "PRO"),
    FormulaDriftDriver("Ryan Litteral", "909", "PRO"),
    FormulaDriftDriver("Ryan Tuerck", "411", "PRO"),
    FormulaDriftDriver("Simen Olsen", "707", "PRO"),
    FormulaDriftDriver("Tommy Lemaire", "233", "PRO"),
    FormulaDriftDriver("Trenton Beechum", "999", "PRO"),
    FormulaDriftDriver("Vaughn Gittin Jr", "25", "PRO"),
    FormulaDriftDriver("Wataru Masuyama", "530", "PRO"),
)


PRO_STANDINGS_AFTER_LONG_BEACH_2026: tuple[FormulaDriftStanding, ...] = (
    FormulaDriftStanding(1, "79", "Conor Shanahan", 1, 50, 51),
    FormulaDriftStanding(2, "151", "Fredric Aasbo", 1, 40, 41),
    FormulaDriftStanding(3, "59", "Jack Shanahan", 3, 30, 33),
    FormulaDriftStanding(4, "11", "Cole Richards", 1, 30, 31, True),
    FormulaDriftStanding(5, "723", "Aurimas Bakchis", 1, 20, 21),
    FormulaDriftStanding(6, "513", "Branden Sorensen", 1, 20, 21),
    FormulaDriftStanding(7, "169", "Diego Higa", 1, 20, 21),
    FormulaDriftStanding(8, "129", "Dylan Hughes", 1, 20, 21),
    FormulaDriftStanding(9, "130", "James Deane", 4, 10, 14),
    FormulaDriftStanding(10, "64", "Chris Forsberg", 2, 10, 12),
    FormulaDriftStanding(11, "411", "Ryan Tuerck", 1, 10, 11),
    FormulaDriftStanding(12, "168", "Hiroya Minowa", 1, 10, 11),
    FormulaDriftStanding(13, "213", "Ben Hobson", 1, 10, 11),
    FormulaDriftStanding(14, "707", "Simen Olsen", 1, 10, 11),
    FormulaDriftStanding(15, "818", "Jeff Jones", 1, 10, 11),
    FormulaDriftStanding(16, "909", "Ryan Litteral", 1, 10, 11),
    FormulaDriftStanding(17, "5", "Adam LZ", 1, 0, 1),
    FormulaDriftStanding(18, "777", "Matt Field", 1, 0, 1),
    FormulaDriftStanding(19, "34", "Dan Burkett", 1, 0, 1),
    FormulaDriftStanding(20, "4", "Nate Chen", 1, 0, 1, True),
    FormulaDriftStanding(21, "527", "Daniel Stuke", 1, 0, 1),
    FormulaDriftStanding(22, "233", "Tommy Lemaire", 1, 0, 1),
    FormulaDriftStanding(23, "999", "Trenton Beechum", 1, 0, 1),
    FormulaDriftStanding(24, "107", "Connor O'Sullivan", 1, 0, 1),
    FormulaDriftStanding(25, "272", "Cody Buchanan", 1, 0, 1, True),
    FormulaDriftStanding(26, "21", "Ken Gushi", 1, 0, 1),
    FormulaDriftStanding(27, "117", "Federico Sceriffo", 1, 0, 1),
    FormulaDriftStanding(28, "98", "Andy Hateley", 1, 0, 1),
    FormulaDriftStanding(29, "530", "Wataru Masuyama", 1, 0, 1),
    FormulaDriftStanding(30, "17", "Jhonnattan Castro", 1, 0, 1),
    FormulaDriftStanding(31, "119", "Rudy Hansen", 1, 0, 1),
    FormulaDriftStanding(32, "27", "Derek Madison", 1, 0, 1),
    FormulaDriftStanding(33, "171", "Rome Charpentier", 0, 0, 0),
)


PROSPEC_TO_PRO_2026: tuple[FormulaDriftDriver, ...] = tuple(driver for driver in PRO_DRIVERS_2026 if driver.promoted_from)


def find_pro_driver(name_or_number: str) -> FormulaDriftDriver | None:
    target = name_or_number.strip().lower()
    for driver in PRO_DRIVERS_2026:
        if driver.name.lower() == target or driver.car_number == target:
            return driver
    return None


def find_pro_standing(name_or_number: str) -> FormulaDriftStanding | None:
    target = name_or_number.strip().lower()
    for standing in PRO_STANDINGS_AFTER_LONG_BEACH_2026:
        if standing.driver.lower() == target or standing.car_number == target:
            return standing
    return None


def fd_2026_reference_payload() -> dict[str, object]:
    return {
        "sources": FD_2026_SOURCES,
        "notes": [
            "Formula Drift's 2026 PROSPEC driver page was still showing Coming Soon when this dataset was added.",
            "PRO standings are current after Round 1 Long Beach and marked preliminary by Formula Drift.",
            "PROSPEC-to-PRO drivers are tracked from their 2025 PROSPEC standings and 2026 PRO rookie listing.",
        ],
        "pro_schedule": [asdict(item) for item in PRO_SCHEDULE_2026],
        "prospec_schedule": [asdict(item) for item in PROSPEC_SCHEDULE_2026],
        "pro_drivers": [asdict(item) for item in PRO_DRIVERS_2026],
        "prospec_to_pro": [asdict(item) for item in PROSPEC_TO_PRO_2026],
        "pro_standings_after_long_beach": [asdict(item) for item in PRO_STANDINGS_AFTER_LONG_BEACH_2026],
    }


def export_fd_2026_reference(output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = fd_2026_reference_payload()
    json_path = output_dir / "formula_drift_2026_reference.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    csv_specs = {
        "fd_2026_pro_schedule.csv": PRO_SCHEDULE_2026,
        "fd_2026_prospec_schedule.csv": PROSPEC_SCHEDULE_2026,
        "fd_2026_pro_drivers.csv": PRO_DRIVERS_2026,
        "fd_2026_prospec_to_pro.csv": PROSPEC_TO_PRO_2026,
        "fd_2026_pro_standings_after_long_beach.csv": PRO_STANDINGS_AFTER_LONG_BEACH_2026,
    }
    paths = [json_path]
    for filename, rows in csv_specs.items():
        path = output_dir / filename
        _write_dataclass_csv(path, rows)
        paths.append(path)
    return paths


def _write_dataclass_csv(path: Path, rows: tuple[object, ...]) -> None:
    if not rows:
        return
    first = asdict(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(first))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
