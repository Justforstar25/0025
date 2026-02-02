"""Plot cumulative cost vs days for elevator+recovery and ground+recovery plans.

Data sources:
- water_cost.csv: capacity_per_year_吨/年
- elevator_ground_cost.csv: per-ton costs for elevator/ground (亿美元/吨)
Assumptions:
- Annual use = 1,387,000 tons
- Recycling rate = 90% -> deficit rate 10%
- Days: 0..365
- Elevator+recovery: first 102 days elevator at full capacity (fills reserve),
    then remaining days elevator covers only the 10% deficit.
- Ground+recovery: same schedule, but elevator is replaced by ground.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Tuple, List

import matplotlib.pyplot as plt
from matplotlib import font_manager

ANNUAL_USE_TONS = 1_387_000.0
RECOVERY_RATE = 0.90
DEFICIT_RATE = 1.0 - RECOVERY_RATE
DAYS_FULL = 102
DAYS_PER_YEAR = 365


def read_capacity(csv_path: Path) -> float:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        return float(row["capacity_per_year_吨/年"])


def read_costs(csv_path: Path) -> Tuple[float, float]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    elevator = next(r for r in rows if r["类型"] == "电梯平均")
    ground = next(r for r in rows if r["类型"] == "地面平均")
    return float(elevator["每吨价格(亿美元/吨)"]), float(ground["每吨价格(亿美元/吨)"])


def cumulative_costs() -> Tuple[List[int], List[float], List[float]]:
    base = Path(__file__).resolve().parent
    capacity_per_year = read_capacity(base / "water_cost.csv")
    cost_elev, cost_ground = read_costs(base / "elevator_ground_cost.csv")

    capacity_per_day = capacity_per_year / DAYS_PER_YEAR
    deficit_per_day = (ANNUAL_USE_TONS * DEFICIT_RATE) / DAYS_PER_YEAR

    days = list(range(0, DAYS_PER_YEAR + 1))
    elevator_recovery = [0.0]
    ground_recovery = [0.0]

    for d in range(1, DAYS_PER_YEAR + 1):
        if d <= DAYS_FULL:
            # full capacity in early phase
            elevator_recovery.append(elevator_recovery[-1] + capacity_per_day * cost_elev)
            ground_recovery.append(ground_recovery[-1] + capacity_per_day * cost_ground)
        else:
            # only cover 10% deficit
            elevator_recovery.append(elevator_recovery[-1] + deficit_per_day * cost_elev)
            ground_recovery.append(ground_recovery[-1] + deficit_per_day * cost_ground)

    return days, elevator_recovery, ground_recovery


def main() -> None:
    # Prefer a CJK-capable font if available
    for font_name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "PingFang SC"]:
        try:
            font_manager.findfont(font_name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [font_name]
            break
        except Exception:
            continue
    plt.rcParams["axes.unicode_minus"] = False

    days, elevator_recovery, ground_recovery = cumulative_costs()

    plt.figure(figsize=(10, 6))
    plt.plot(days, elevator_recovery, label="Elevator + Recovery")
    plt.plot(days, ground_recovery, label="Ground + Recovery")

    plt.xlabel("Days")
    plt.ylabel("Cumulative Cost (Billion USD)")
    plt.title("Water Supply Cost Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)

    out_path = Path(__file__).resolve().parent / "water_cost_plot.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"done: {out_path}")


if __name__ == "__main__":
    main()
