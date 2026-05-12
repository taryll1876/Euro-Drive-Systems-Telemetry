from __future__ import annotations

from pathlib import Path
from time import sleep

import requests


def post_report_to_discord(
    webhook_url: str,
    report_path: str | Path,
    content: str | None = None,
    retries: int = 2,
) -> None:
    report_path = Path(report_path)
    payload = {"content": content or f"New Euroo Drive Systems telemetry report: {report_path.name}"}
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with report_path.open("rb") as handle:
                response = requests.post(
                    webhook_url,
                    data=payload,
                    files={"file": (report_path.name, handle, "text/markdown")},
                    timeout=15,
                )
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Discord report upload failed after {retries + 1} attempts.") from last_error
