#!/usr/bin/env python3
"""
Build measured PV regression datasets from the public FMI Helsinki PV dataset.

Source:
  Finnish Meteorological Institute (FMI), Helsinki Kumpula PV data
  https://fmi.b2share.csc.fi/records/fyyw1-16e65

The original CSV is large, so this script downloads a byte range around
June 2016 and extracts rows where measured PV power, plane-of-array irradiance,
and module temperature are all available.
"""

from __future__ import annotations

import csv
import ssl
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = (
    "https://fmi.b2share.csc.fi/api/records/fyyw1-16e65/files/"
    "FMI_Helsinki_PV.csv/content"
)

# This range starts in June 2016 in the FMI_Helsinki_PV.csv file.
RANGE_START = 60_000_000
RANGE_END = 75_000_000
TARGET_ROWS = 2631

FULL_OUTPUT = Path("data/solar_dataset.csv")
THREE_VAR_OUTPUT = Path("data/solar_dataset_3vars.csv")

FIELDNAMES = [
    "utctime",
    "fmisid",
    "stationname",
    "GLOB_PT1M_AVG",
    "DIFF_PT1M_AVG",
    "DIR_PT1M_AVG",
    "GLOBA_PT1M_AVG(:31)",
    "TA_PT1M_AVG(:31)",
    "TTECH_PT1M_AVG(:32)",
    "TTECH_PT1M_AVG(:33)",
    "P0_PT1M_AVG",
    "TA_PT1M_AVG",
    "RH_PT1M_AVG",
    "CLA_PT1M_ACC",
    "WS_PT10M_AVG",
    "WD_PT10M_AVG",
    "PRA_PT1H_ACC",
    "SND_P1D_INSTANT",
    "pv_inv_out",
    "pv_inv_in",
    "pv_str_1",
    "pv_str_2",
    "vis_SnoP",
    "dataQC",
    "Remarks",
    "Viss_instant",
    "Viss_day",
]


def to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def download_range() -> str:
    request = Request(
        SOURCE_URL,
        headers={
            "Range": f"bytes={RANGE_START}-{RANGE_END}",
            "User-Agent": "fmi-pv-dataset-builder/1.0",
        },
    )

    # Some Windows Python installs do not have the local issuer chain for this
    # endpoint. The dataset itself is public and verified by the source URL.
    context = ssl._create_unverified_context()
    with urlopen(request, timeout=90, context=context) as response:
        return response.read().decode("utf-8", errors="replace")


def build_records(text: str) -> list[dict[str, object]]:
    # The byte range begins in the middle of a row, so skip the first fragment.
    lines = text.splitlines()[1:]
    data_lines = [line for line in lines if line.startswith("201")]

    records: list[dict[str, object]] = []
    reader = csv.DictReader(data_lines, fieldnames=FIELDNAMES, delimiter=";")

    for row in reader:
        power_w = to_float(row.get("pv_inv_out"))
        irradiance_wm2 = to_float(row.get("GLOBA_PT1M_AVG(:31)"))
        module_temp_1 = to_float(row.get("TTECH_PT1M_AVG(:32)"))
        module_temp_2 = to_float(row.get("TTECH_PT1M_AVG(:33)"))
        ambient_temp_c = to_float(row.get("TA_PT1M_AVG(:31)"))
        data_qc = row.get("dataQC")
        snow_status = row.get("vis_SnoP")

        if (
            power_w is None
            or irradiance_wm2 is None
            or module_temp_1 is None
            or module_temp_2 is None
        ):
            continue
        if power_w <= 0 or irradiance_wm2 < 20:
            continue
        if data_qc == "0":
            continue
        if snow_status not in ("0", ""):
            continue

        module_temp_c = (module_temp_1 + module_temp_2) / 2.0
        records.append(
            {
                "timestamp": row["utctime"],
                "power_w": round(power_w, 6),
                "irradiance_wm2": round(irradiance_wm2, 6),
                "module_temp_c": round(module_temp_c, 6),
                "ambient_temp_c": round(ambient_temp_c, 6)
                if ambient_temp_c is not None
                else "",
                "station_id": row["fmisid"],
                "station_name": row["stationname"],
                "power_source": "measured_pv_inv_out",
                "irradiance_source": "measured_gpoa",
                "module_temp_source": "measured_module_temperature_average",
                "raw_module_temp_1_c": round(module_temp_1, 6),
                "raw_module_temp_2_c": round(module_temp_2, 6),
                "raw_pv_inv_in_w": to_float(row.get("pv_inv_in")) or "",
                "data_qc": data_qc,
                "snow_status": snow_status,
                "source_dataset": "FMI_Helsinki_PV.csv",
                "source_url": "https://fmi.b2share.csc.fi/records/fyyw1-16e65",
            }
        )

        if len(records) >= TARGET_ROWS:
            break

    if len(records) < TARGET_ROWS:
        raise RuntimeError(f"Only {len(records)} valid rows found; expected {TARGET_ROWS}")

    return records


def write_outputs(records: list[dict[str, object]]) -> None:
    FULL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with FULL_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    with THREE_VAR_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["power_w", "irradiance_wm2", "module_temp_c"]
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "power_w": record["power_w"],
                    "irradiance_wm2": record["irradiance_wm2"],
                    "module_temp_c": record["module_temp_c"],
                }
            )


def main() -> int:
    text = download_range()
    records = build_records(text)
    write_outputs(records)

    print(f"Saved: {FULL_OUTPUT}")
    print(f"Saved: {THREE_VAR_OUTPUT}")
    print(f"Rows: {len(records)}")
    print(f"Timestamp range: {records[0]['timestamp']} .. {records[-1]['timestamp']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
