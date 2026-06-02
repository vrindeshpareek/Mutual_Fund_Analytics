from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MFAPI_URL = "https://api.mfapi.in/mf/{scheme_code}"

SCHEMES = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip",
}


def fetch_scheme_nav(scheme_code: str) -> dict[str, Any]:
    response = requests.get(MFAPI_URL.format(scheme_code=scheme_code), timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("data"):
        raise ValueError(f"No NAV records returned for scheme code {scheme_code}")
    return payload


def latest_record(scheme_code: str, expected_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("meta", {})
    latest = payload["data"][0]
    return {
        "scheme_code": scheme_code,
        "expected_scheme_name": expected_name,
        "api_scheme_name": metadata.get("scheme_name"),
        "fund_house": metadata.get("fund_house"),
        "scheme_type": metadata.get("scheme_type"),
        "scheme_category": metadata.get("scheme_category"),
        "date": latest.get("date"),
        "nav": latest.get("nav"),
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }


def history_frame(scheme_code: str, expected_name: str, payload: dict[str, Any]) -> pd.DataFrame:
    metadata = payload.get("meta", {})
    frame = pd.DataFrame(payload.get("data", []))
    frame.insert(0, "scheme_code", scheme_code)
    frame.insert(1, "expected_scheme_name", expected_name)
    frame.insert(2, "api_scheme_name", metadata.get("scheme_name"))
    frame.insert(3, "fund_house", metadata.get("fund_house"))
    return frame


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    latest_rows: list[dict[str, Any]] = []
    history_frames: list[pd.DataFrame] = []

    for scheme_code, expected_name in SCHEMES.items():
        payload = fetch_scheme_nav(scheme_code)
        latest_rows.append(latest_record(scheme_code, expected_name, payload))
        history_frames.append(history_frame(scheme_code, expected_name, payload))
        print(f"Fetched {expected_name} ({scheme_code})")

    latest_df = pd.DataFrame(latest_rows)
    history_df = pd.concat(history_frames, ignore_index=True)

    latest_path = RAW_DIR / "live_nav_latest.csv"
    history_path = RAW_DIR / "mfapi_nav_history_key_schemes.csv"

    latest_df.to_csv(latest_path, index=False)
    history_df.to_csv(history_path, index=False)

    print(f"\nSaved latest NAV CSV: {latest_path}")
    print(f"Saved full fetched NAV history CSV: {history_path}")
    print("\nLatest NAV records:")
    print(latest_df)


if __name__ == "__main__":
    main()
