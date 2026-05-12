from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorSpec:
    name: str
    unit: str
    category: str
    description: str
    ideal_range: tuple[float, float] | None = None


DRIFT_SENSOR_SPECS: tuple[SensorSpec, ...] = (
    SensorSpec("time_s", "s", "clock", "Timestamp from run start."),
    SensorSpec("gps_x_m", "m", "position", "Course-relative X position."),
    SensorSpec("gps_y_m", "m", "position", "Course-relative Y position."),
    SensorSpec("speed_kph", "kph", "vehicle", "Ground speed."),
    SensorSpec("yaw_rate_dps", "deg/s", "motion", "Yaw rotation rate."),
    SensorSpec("drift_angle_deg", "deg", "motion", "Vehicle slip/drift angle.", (35, 65)),
    SensorSpec("steering_angle_deg", "deg", "driver", "Steering wheel angle."),
    SensorSpec("throttle_pct", "%", "driver", "Throttle pedal position.", (55, 100)),
    SensorSpec("brake_pct", "%", "driver", "Brake pressure/pedal percentage.", (0, 35)),
    SensorSpec("clutch_pct", "%", "driver", "Clutch pedal position."),
    SensorSpec("handbrake_pct", "%", "driver", "Hydraulic/e-brake input."),
    SensorSpec("gear", "gear", "powertrain", "Selected gear."),
    SensorSpec("rpm", "rpm", "powertrain", "Engine speed."),
    SensorSpec("boost_kpa", "kPa", "powertrain", "Manifold boost pressure."),
    SensorSpec("lambda", "lambda", "powertrain", "Air fuel lambda reading."),
    SensorSpec("coolant_c", "C", "powertrain", "Coolant temperature."),
    SensorSpec("oil_pressure_kpa", "kPa", "powertrain", "Oil pressure."),
    SensorSpec("oil_temp_c", "C", "powertrain", "Oil temperature."),
    SensorSpec("fuel_pressure_kpa", "kPa", "powertrain", "Fuel pressure."),
    SensorSpec("fuel_level_pct", "%", "vehicle", "Fuel level."),
    SensorSpec("front_wheel_speed_kph", "kph", "vehicle", "Front wheel speed."),
    SensorSpec("rear_wheel_speed_kph", "kph", "vehicle", "Rear wheel speed."),
    SensorSpec("tire_temp_fl_c", "C", "tire", "Front-left tire temperature."),
    SensorSpec("tire_temp_fr_c", "C", "tire", "Front-right tire temperature."),
    SensorSpec("tire_temp_rl_c", "C", "tire", "Rear-left tire temperature."),
    SensorSpec("tire_temp_rr_c", "C", "tire", "Rear-right tire temperature."),
    SensorSpec("tire_pressure_fl_kpa", "kPa", "tire", "Front-left tire pressure."),
    SensorSpec("tire_pressure_fr_kpa", "kPa", "tire", "Front-right tire pressure."),
    SensorSpec("tire_pressure_rl_kpa", "kPa", "tire", "Rear-left tire pressure."),
    SensorSpec("tire_pressure_rr_kpa", "kPa", "tire", "Rear-right tire pressure."),
    SensorSpec("suspension_fl_mm", "mm", "chassis", "Front-left suspension travel."),
    SensorSpec("suspension_fr_mm", "mm", "chassis", "Front-right suspension travel."),
    SensorSpec("suspension_rl_mm", "mm", "chassis", "Rear-left suspension travel."),
    SensorSpec("suspension_rr_mm", "mm", "chassis", "Rear-right suspension travel."),
    SensorSpec("lat_g", "g", "motion", "Lateral acceleration."),
    SensorSpec("long_g", "g", "motion", "Longitudinal acceleration."),
    SensorSpec("distance_to_line_m", "m", "judging", "Distance from ideal drift line.", (0, 1.5)),
    SensorSpec("outer_zone_fill_pct", "%", "judging", "Rear bumper/wheel zone fill estimate.", (70, 100)),
    SensorSpec("inner_clip_distance_m", "m", "judging", "Distance to inner clipping point.", (0, 1.0)),
    SensorSpec("transition_quality_pct", "%", "judging", "Transition snap, timing, and stability estimate.", (70, 100)),
    SensorSpec("proximity_to_lead_m", "m", "tandem", "Chase-car distance to lead vehicle."),
    SensorSpec("relative_angle_deg", "deg", "tandem", "Chase vs lead drift angle delta."),
    SensorSpec("relative_speed_kph", "kph", "tandem", "Chase vs lead speed delta."),
)


REQUIRED_COLUMNS = {
    "time_s",
    "gps_x_m",
    "gps_y_m",
    "speed_kph",
    "drift_angle_deg",
    "throttle_pct",
    "brake_pct",
    "distance_to_line_m",
    "outer_zone_fill_pct",
    "inner_clip_distance_m",
    "transition_quality_pct",
}


def sensor_names() -> list[str]:
    return [sensor.name for sensor in DRIFT_SENSOR_SPECS]
