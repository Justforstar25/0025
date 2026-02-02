"""Compute total propellant mass by fuel type using Tsiolkovsky equation.

Assumptions:
- Payload (final mass mf) per launch = 125 tons.
- Mass ratio cap = 10. If required m0/mf exceeds 10, cap at 10.
- Use dv_f.csv columns: 大气dv(km/s), 真空dv(km/s).
- Use enabled workstations from 最优.csv (first data row), saturated at
  134 launches per workstation per year for 65 years.
- Sum propellant mass across all enabled sites.

Output: fuel_totals.csv with columns:
    燃料类型, 大气燃料总重量(吨), 真空燃料总重量(吨), 总CO2排放量(吨)
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Tuple

G0 = 9.80665
PAYLOAD_TONS = 125.0
MASS_RATIO_CAP = None
LAUNCHES_PER_WORKSTATION_PER_YEAR = 134
YEARS = 65

ENGINE_TYPES = {
    "液氧煤油": {"isp_sea": 310.0, "isp_vac": 368.0},
    "液氧液氢": {"isp_sea": 386.0, "isp_vac": 472.0},
    "液氧甲烷": {"isp_sea": 370.0, "isp_vac": 400.0},
}

# CO2 emission factors (tons CO2 per ton propellant)
# Combustion: kerosene 0.96, methane 0.60, hydrogen 0.0
# Extraction: LOX-kerosene 0.51, LOX-methane 0.48, LOX-hydrogen 1.66
CO2_FACTORS = {
    "液氧煤油": 0.96 + 0.51,
    "液氧甲烷": 0.60 + 0.48,
    "液氧液氢": 0.00 + 1.66,
}


def slugify(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    slug = "".join(out).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "site"


def load_dv(csv_path: Path) -> Dict[str, Tuple[float, float]]:
    """Return mapping slug -> (dv_atm_mps, dv_vac_mps)."""
    dv_map: Dict[str, Tuple[float, float]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["发射场"].strip()
            slug = slugify(name)
            dv_atm = float(row["大气dv(km/s)"]) * 1000.0
            dv_vac = float(row["真空dv(km/s)"]) * 1000.0
            dv_map[slug] = (dv_atm, dv_vac)
    return dv_map


def load_workstations(csv_path: Path) -> Dict[str, int]:
    """Return mapping slug -> workstations_in_use from the first data row."""
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)  # use first data row

    ws_map: Dict[str, int] = {}
    for idx, col in enumerate(header):
        if col.endswith("_workstations_in_use"):
            slug = col[: -len("_workstations_in_use")]
            try:
                ws = int(float(row[idx]))
            except ValueError:
                ws = 0
            ws_map[slug] = ws
    return ws_map


def propellant_per_launch(dv: float, isp: float) -> float:
    """Return propellant mass (tons) per launch given dv (m/s) and Isp (s)."""
    ratio = math.exp(dv / (isp * G0))
    if MASS_RATIO_CAP is not None and ratio > MASS_RATIO_CAP:
        ratio = MASS_RATIO_CAP
    return PAYLOAD_TONS * (ratio - 1.0)


def main() -> None:
    base = Path(__file__).resolve().parent
    dv_path = base / "dv_f.csv"
    ws_path = base / "最优.csv"

    dv_map = load_dv(dv_path)
    ws_map = load_workstations(ws_path)

    totals: List[Tuple[str, float, float, float]] = []

    for fuel, isp in ENGINE_TYPES.items():
        total_atm = 0.0
        total_vac = 0.0
        for slug, ws in ws_map.items():
            if ws <= 0:
                continue
            if slug not in dv_map:
                continue
            dv_atm, dv_vac = dv_map[slug]
            launches = ws * LAUNCHES_PER_WORKSTATION_PER_YEAR * YEARS
            atm_per = propellant_per_launch(dv_atm, isp["isp_sea"])
            vac_per = propellant_per_launch(dv_vac, isp["isp_vac"])
            total_atm += atm_per * launches
            total_vac += vac_per * launches
        total_propellant = total_atm + total_vac
        co2 = total_propellant * CO2_FACTORS[fuel]
        totals.append((fuel, total_atm, total_vac, co2))

    out_path = base / "fuel_totals.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["燃料类型", "大气燃料总重量(吨)", "真空燃料总重量(吨)", "总CO2排放量(吨)"])
        for fuel, atm, vac, co2 in totals:
            writer.writerow([fuel, f"{atm:.3f}", f"{vac:.3f}", f"{co2:.3f}"])

    print(f"done: {out_path}")


if __name__ == "__main__":
    main()
