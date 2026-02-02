"""Compute 1-year water supply cost with a two-phase elevator schedule.

Assumptions:
- Annual water use: 1,387,000 tons.
- Recycling rate: 90% (deficit = 10%).
- First 102 days: elevator runs at full capacity to build reserve.
- Remaining 263 days: elevator only covers the 10% deficit.
- Target reserve: 50% of annual use.
- Cost per ton and annual capacity are read from water_cost.csv.

Outputs: water_schedule_cost.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Tuple

ANNUAL_USE_TONS = 1_387_000.0
RECOVERY_RATE = 0.90
DEFICIT_RATE = 1.0 - RECOVERY_RATE
RESERVE_FRACTION = 0.50
DAYS_FULL = 102
DAYS_DEFICIT = 263
DAYS_PER_YEAR = 365


def load_cost_and_capacity(csv_path: Path) -> Tuple[float, float]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        cost_per_ton = float(row["cost_per_ton_亿美元/吨"])
        capacity_per_year = float(row["capacity_per_year_吨/年"])
    return cost_per_ton, capacity_per_year


def main() -> None:
    base = Path(__file__).resolve().parent
    src = base / "water_cost.csv"
    cost_per_ton, capacity_per_year = load_cost_and_capacity(src)

    capacity_per_day = capacity_per_year / DAYS_PER_YEAR
    deficit_per_year = ANNUAL_USE_TONS * DEFICIT_RATE
    deficit_per_day = deficit_per_year / DAYS_PER_YEAR

    delivered_full = capacity_per_day * DAYS_FULL
    deficit_full = deficit_per_day * DAYS_FULL
    reserve_target = ANNUAL_USE_TONS * RESERVE_FRACTION

    reserve_filled = max(delivered_full - deficit_full, 0.0)
    remaining_reserve = max(reserve_target - reserve_filled, 0.0)

    delivered_deficit = deficit_per_day * DAYS_DEFICIT
    total_delivered = delivered_full + delivered_deficit
    total_cost = total_delivered * cost_per_ton

    out_path = base / "water_schedule_cost.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "annual_use_tons",
                "deficit_per_year_tons",
                "reserve_target_tons",
                "delivered_full_tons",
                "delivered_deficit_tons",
                "total_delivered_tons",
                "reserve_filled_tons",
                "remaining_reserve_tons",
                "cost_per_ton_亿美元/吨",
                "total_cost_亿美元",
            ]
        )
        writer.writerow(
            [
                f"{ANNUAL_USE_TONS:.3f}",
                f"{deficit_per_year:.3f}",
                f"{reserve_target:.3f}",
                f"{delivered_full:.3f}",
                f"{delivered_deficit:.3f}",
                f"{total_delivered:.3f}",
                f"{reserve_filled:.3f}",
                f"{remaining_reserve:.3f}",
                f"{cost_per_ton:.6f}",
                f"{total_cost:.6f}",
            ]
        )

    print(f"done: {out_path}")


if __name__ == "__main__":
    main()
