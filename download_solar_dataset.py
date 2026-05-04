#!/usr/bin/env python3
"""
Download solar-related time-series data and build a regression-ready CSV dataset.

Data source:
- Open-Meteo Historical Weather API (no API key required for standard usage)

Main outputs (per timestamp):
- irradiance_wm2
- module_temp_c (estimated from ambient temperature and irradiance)
- power_proxy_w (estimated PV power)
- power_w (measured power if provided, otherwise proxy)

Examples:
  python download_solar_dataset.py

  python download_solar_dataset.py \
      --latitude 37.87 --longitude 138.94 \
      --start-date 2025-04-01 --end-date 2025-10-31 \
      --output data/solar_dataset.csv

  python download_solar_dataset.py \
      --measured-power-csv data/measured_power.csv \
      --output data/solar_dataset_with_power.csv

Expected measured power CSV format:
  timestamp,power_w
  2025-04-01T00:00,0.0
  2025-04-01T01:00,0.0
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def parse_args() -> argparse.Namespace:
    today = date.today()
    # ERA5-like reanalysis can have a delay. Keep defaults safely in the past.
    default_end = today - timedelta(days=7)
    default_start = default_end - timedelta(days=180)

    parser = argparse.ArgumentParser(
        description="Build a solar regression dataset from Open-Meteo historical data."
    )
    parser.add_argument("--latitude", type=float, default=37.8689, help="Site latitude")
    parser.add_argument("--longitude", type=float, default=138.9383, help="Site longitude")
    parser.add_argument(
        "--start-date",
        type=str,
        default=default_start.isoformat(),
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=default_end.isoformat(),
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--timezone",
        type=str,
        default="Asia/Tokyo",
        help="Timezone for returned timestamps",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="era5",
        help="Open-Meteo model (e.g., era5, era5_land, ecmwf_ifs)",
    )

    # Tilt/azimuth are used by global_tilted_irradiance.
    parser.add_argument("--tilt-deg", type=float, default=30.0, help="Panel tilt in degrees")
    parser.add_argument(
        "--azimuth-deg",
        type=float,
        default=0.0,
        help="Panel azimuth in degrees (0=south, -90=east, 90=west)",
    )

    # Simple PV proxy model parameters.
    parser.add_argument(
        "--panel-area-m2", type=float, default=1.0, help="Panel area for power proxy"
    )
    parser.add_argument(
        "--panel-efficiency", type=float, default=0.20, help="Panel efficiency for power proxy"
    )
    parser.add_argument(
        "--temp-coeff-per-c",
        type=float,
        default=-0.004,
        help="Power temperature coefficient (per degC)",
    )
    parser.add_argument(
        "--noct-c",
        type=float,
        default=45.0,
        help="Nominal operating cell temperature (degC)",
    )

    parser.add_argument(
        "--daylight-threshold",
        type=float,
        default=20.0,
        help="Keep rows with irradiance_wm2 >= threshold",
    )
    parser.add_argument(
        "--measured-power-csv",
        type=Path,
        default=None,
        help="Optional CSV with columns: timestamp,power_w",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/solar_dataset_openmeteo.csv"),
        help="Output CSV path",
    )
    return parser.parse_args()


def fetch_open_meteo_data(args: argparse.Namespace) -> dict[str, Any]:
    params = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "timezone": args.timezone,
        "models": args.model,
        "hourly": ",".join(
            [
                "temperature_2m",
                "shortwave_radiation",
                "direct_normal_irradiance",
                "diffuse_radiation",
                "global_tilted_irradiance",
            ]
        ),
        "tilt": args.tilt_deg,
        "azimuth": args.azimuth_deg,
    }
    url = f"{OPEN_METEO_ARCHIVE_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "solar-dataset-builder/1.0"})

    with urlopen(request, timeout=60) as response:
        payload = response.read().decode("utf-8")

    data = json.loads(payload)
    if data.get("error"):
        reason = data.get("reason", "unknown API error")
        raise RuntimeError(f"Open-Meteo API error: {reason}")
    if "hourly" not in data:
        raise RuntimeError("Open-Meteo response has no 'hourly' field")
    return data


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_series(hourly: dict[str, list[Any]], key: str, length: int) -> list[Any]:
    values = hourly.get(key)
    if values is None:
        return [None] * length
    if len(values) != length:
        raise ValueError(f"Length mismatch for '{key}': {len(values)} != {length}")
    return values


def build_records(data: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    hourly = data["hourly"]
    timestamps = hourly.get("time")
    if not timestamps:
        raise RuntimeError("No timestamps in API response")

    n = len(timestamps)
    temperature_2m = extract_series(hourly, "temperature_2m", n)
    ghi = extract_series(hourly, "shortwave_radiation", n)
    dni = extract_series(hourly, "direct_normal_irradiance", n)
    dhi = extract_series(hourly, "diffuse_radiation", n)
    gti = extract_series(hourly, "global_tilted_irradiance", n)

    records: list[dict[str, Any]] = []
    module_temp_gain = (args.noct_c - 20.0) / 800.0

    for i, ts in enumerate(timestamps):
        ambient = as_float(temperature_2m[i])
        ghi_i = as_float(ghi[i])
        dni_i = as_float(dni[i])
        dhi_i = as_float(dhi[i])
        gti_i = as_float(gti[i])

        if ambient is None:
            ambient = 0.0

        # Prefer plane-of-array irradiance when available.
        irradiance = gti_i if gti_i is not None else ghi_i
        if irradiance is None:
            irradiance = 0.0

        irradiance = max(irradiance, 0.0)
        module_temp = ambient + module_temp_gain * irradiance

        temp_factor = 1.0 + args.temp_coeff_per_c * (module_temp - 25.0)
        if temp_factor < 0.0:
            temp_factor = 0.0

        power_proxy = args.panel_area_m2 * args.panel_efficiency * irradiance * temp_factor

        records.append(
            {
                "timestamp": ts,
                "latitude": args.latitude,
                "longitude": args.longitude,
                "irradiance_wm2": irradiance,
                "module_temp_c": module_temp,
                "ambient_temp_c": ambient,
                "ghi_wm2": ghi_i,
                "dni_wm2": dni_i,
                "dhi_wm2": dhi_i,
                "power_proxy_w": power_proxy,
            }
        )

    if args.daylight_threshold is not None:
        records = [r for r in records if r["irradiance_wm2"] >= args.daylight_threshold]

    if not records:
        raise RuntimeError("No rows left after filtering. Try lowering --daylight-threshold.")

    return records


def load_measured_power(path: Path) -> dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(f"Measured power CSV not found: {path}")

    measured: dict[str, float] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        required = {"timestamp", "power_w"}
        missing = required - fieldnames
        if missing:
            raise ValueError(f"Measured power CSV missing columns: {sorted(missing)}")

        for row in reader:
            ts = (row.get("timestamp") or "").strip()
            if not ts:
                continue
            p = as_float(row.get("power_w"))
            if p is None:
                continue
            measured[ts] = p

    return measured


def merge_measured_power(
    records: list[dict[str, Any]], measured: dict[str, float] | None
) -> list[dict[str, Any]]:
    for rec in records:
        ts = rec["timestamp"]
        if measured and ts in measured:
            rec["power_w"] = measured[ts]
            rec["power_source"] = "measured"
        else:
            rec["power_w"] = rec["power_proxy_w"]
            rec["power_source"] = "proxy"
    return records


def write_csv(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "latitude",
        "longitude",
        "irradiance_wm2",
        "module_temp_c",
        "power_w",
        "power_source",
        "ambient_temp_c",
        "ghi_wm2",
        "dni_wm2",
        "dhi_wm2",
        "power_proxy_w",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def main() -> int:
    args = parse_args()

    try:
        data = fetch_open_meteo_data(args)
        records = build_records(data, args)

        measured = None
        if args.measured_power_csv is not None:
            measured = load_measured_power(args.measured_power_csv)

        records = merge_measured_power(records, measured)
        write_csv(records, args.output)

        measured_count = sum(1 for r in records if r.get("power_source") == "measured")
        proxy_count = len(records) - measured_count

        print(f"Saved: {args.output}")
        print(f"Rows: {len(records)}")
        print(f"Power source counts -> measured: {measured_count}, proxy: {proxy_count}")
        print(
            "Model columns ready for regression: irradiance_wm2, module_temp_c, power_w"
        )

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
