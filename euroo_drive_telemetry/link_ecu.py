from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CANSignal:
    name: str
    can_id: int
    start_byte: int
    length: int
    scale: float
    offset: float = 0.0
    signed: bool = False


LINK_ECU_BASE_SIGNALS: tuple[CANSignal, ...] = (
    CANSignal("rpm", 0x3E8, 0, 2, 1.0),
    CANSignal("throttle_pct", 0x3E8, 2, 1, 0.5),
    CANSignal("boost_kpa", 0x3E8, 3, 2, 1.0, signed=True),
    CANSignal("lambda", 0x3E9, 0, 2, 0.001),
    CANSignal("coolant_c", 0x3E9, 2, 1, 1.0, -40.0),
    CANSignal("oil_pressure_kpa", 0x3E9, 3, 2, 1.0),
    CANSignal("fuel_pressure_kpa", 0x3EA, 0, 2, 1.0),
    CANSignal("gear", 0x3EA, 2, 1, 1.0),
)


def decode_frame(can_id: int, payload: bytes, signals: Iterable[CANSignal] = LINK_ECU_BASE_SIGNALS) -> dict[str, float]:
    decoded: dict[str, float] = {}
    for signal in signals:
        if signal.can_id != can_id:
            continue
        raw = payload[signal.start_byte : signal.start_byte + signal.length]
        if len(raw) != signal.length:
            continue
        value = int.from_bytes(raw, byteorder="big", signed=signal.signed)
        decoded[signal.name] = value * signal.scale + signal.offset
    return decoded


class LinkECUStream:
    """Thin wrapper for a future live CAN stream using python-can."""

    def __init__(self, channel: str = "can0", bitrate: int = 1_000_000, interface: str = "socketcan") -> None:
        self.channel = channel
        self.bitrate = bitrate
        self.interface = interface

    def read_once(self) -> dict[str, float]:
        try:
            import can  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the optional 'can' extra to read live Link ECU CAN frames.") from exc

        bus = can.interface.Bus(channel=self.channel, interface=self.interface, bitrate=self.bitrate)
        message = bus.recv(timeout=1.0)
        if message is None:
            return {}
        return decode_frame(message.arbitration_id, bytes(message.data))
