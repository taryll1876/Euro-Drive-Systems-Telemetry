from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from .sensors import sensor_names


def make_sample_run(path: str | Path, driver: str, aggression: float, precision: float, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sensor_names()
    t = np.linspace(0, 38, 380)
    phase = np.linspace(0, 5 * np.pi, len(t))
    transition = np.abs(np.sin(phase))
    throttle = np.clip(58 + 30 * aggression + 12 * np.sin(phase + 0.8) + rng.normal(0, 5, len(t)), 0, 100)
    brake = np.clip(9 + 20 * transition * (1.15 - aggression) + rng.normal(0, 2.2, len(t)), 0, 100)
    handbrake = np.clip(55 * (transition > 0.94) * (1.05 - precision) + rng.normal(0, 1.5, len(t)), 0, 100)
    angle = np.clip(33 + 26 * aggression + 10 * np.sin(phase) + rng.normal(0, 3.2, len(t)), 0, 78)
    speed = np.clip(78 + 22 * aggression + 8 * np.cos(phase * 0.6) - brake * 0.16 + rng.normal(0, 2.5, len(t)), 25, 150)
    line_error = np.clip(1.9 - 1.35 * precision + 0.45 * np.sin(phase * 1.4) + rng.normal(0, 0.24, len(t)), 0, 3.2)
    zone_fill = np.clip(52 + 42 * precision + 9 * np.sin(phase - 0.2) + rng.normal(0, 5, len(t)), 0, 100)
    clip = np.clip(1.6 - 1.15 * precision + 0.35 * np.cos(phase) + rng.normal(0, 0.18, len(t)), 0, 2.8)
    quality = np.clip(54 + 37 * precision + 9 * aggression - 0.35 * handbrake + rng.normal(0, 4, len(t)), 0, 100)
    x = np.cumsum(np.cos(phase / 2) * speed / 120)
    y = np.cumsum(np.sin(phase / 2) * speed / 120)

    base = {
        "time_s": t,
        "gps_x_m": x,
        "gps_y_m": y,
        "speed_kph": speed,
        "yaw_rate_dps": angle * 2.7,
        "drift_angle_deg": angle,
        "steering_angle_deg": -angle * 8 + rng.normal(0, 35, len(t)),
        "throttle_pct": throttle,
        "brake_pct": brake,
        "clutch_pct": np.clip(rng.normal(2, 1, len(t)), 0, 100),
        "handbrake_pct": handbrake,
        "gear": np.full(len(t), 3),
        "rpm": np.clip(5200 + throttle * 28 + rng.normal(0, 180, len(t)), 2500, 9200),
        "boost_kpa": np.clip(-20 + throttle * 2.0 + rng.normal(0, 10, len(t)), -80, 220),
        "lambda": np.clip(0.84 + rng.normal(0, 0.018, len(t)), 0.7, 1.1),
        "coolant_c": np.linspace(86, 93, len(t)),
        "oil_pressure_kpa": np.clip(430 + rng.normal(0, 18, len(t)), 300, 620),
        "oil_temp_c": np.linspace(91, 108, len(t)),
        "fuel_pressure_kpa": np.clip(390 + rng.normal(0, 12, len(t)), 300, 480),
        "fuel_level_pct": np.linspace(64, 61, len(t)),
        "front_wheel_speed_kph": speed,
        "rear_wheel_speed_kph": speed + throttle * 0.22,
        "tire_temp_fl_c": np.linspace(72, 82, len(t)),
        "tire_temp_fr_c": np.linspace(73, 84, len(t)),
        "tire_temp_rl_c": np.linspace(86, 124, len(t)),
        "tire_temp_rr_c": np.linspace(87, 128, len(t)),
        "tire_pressure_fl_kpa": np.linspace(220, 226, len(t)),
        "tire_pressure_fr_kpa": np.linspace(221, 228, len(t)),
        "tire_pressure_rl_kpa": np.linspace(184, 199, len(t)),
        "tire_pressure_rr_kpa": np.linspace(185, 202, len(t)),
        "suspension_fl_mm": 42 + 8 * np.sin(phase),
        "suspension_fr_mm": 41 - 8 * np.sin(phase),
        "suspension_rl_mm": 38 + 6 * np.cos(phase),
        "suspension_rr_mm": 38 - 6 * np.cos(phase),
        "lat_g": np.clip(angle / 70 + rng.normal(0, 0.05, len(t)), 0, 1.5),
        "long_g": np.clip((throttle - brake) / 100 + rng.normal(0, 0.04, len(t)), -1.2, 1.2),
        "distance_to_line_m": line_error,
        "outer_zone_fill_pct": zone_fill,
        "inner_clip_distance_m": clip,
        "transition_quality_pct": quality,
        "proximity_to_lead_m": np.clip(2.5 + rng.normal(0, 0.4, len(t)), 0.3, 8),
        "relative_angle_deg": rng.normal(0, 4, len(t)),
        "relative_speed_kph": rng.normal(0, 5, len(t)),
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for i in range(len(t)):
            writer.writerow({name: f"{base[name][i]:.4f}" for name in columns})
    return path


def generate_samples(output_dir: str | Path = "sample_runs") -> list[Path]:
    output_dir = Path(output_dir)
    return [
        make_sample_run(output_dir / "akira_run_01.csv", "Akira", aggression=0.76, precision=0.78, seed=12),
        make_sample_run(output_dir / "mika_run_01.csv", "Mika", aggression=0.62, precision=0.91, seed=22),
        make_sample_run(output_dir / "lex_run_01.csv", "Lex", aggression=0.9, precision=0.64, seed=32),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Euroo Drive Systems sample drift telemetry.")
    parser.add_argument("--output-dir", default="sample_runs")
    args = parser.parse_args()
    for path in generate_samples(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
