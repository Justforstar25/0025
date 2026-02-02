"""Compute cost per ton (in 亿美元/吨) for space elevator vs ground launch.

Assumptions:
- Use dv_f.csv column 总f (derived from dv) as cost factor.
- Cost per launch (no maintenance): cost_launch = c * m * f
- Payload per launch = 125 tons.
- Cost per ton = cost_launch / payload
- Output two rows: 电梯平均, 地面平均
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

C = 0.00713
M = 125.0
PAYLOAD_TONS = 125.0


def load_rows(csv_path: Path) -> List[Tuple[str, float]]:
    rows: List[Tuple[str, float]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["发射场"].strip()
            f_total = float(row["总f"])
            rows.append((name, f_total))
    return rows


def is_elevator(name: str) -> bool:
    return name.lower().startswith("space elevator")


def main() -> None:
    base = Path(__file__).resolve().parent
    csv_path = base / "dv_f.csv"
    rows = load_rows(csv_path)

    elevator_costs: List[float] = []
    ground_costs: List[float] = []

    for name, f_total in rows:
        cost_launch = C * M * f_total
        cost_per_ton = cost_launch / PAYLOAD_TONS
        if is_elevator(name):
            elevator_costs.append(cost_per_ton)
        else:
            ground_costs.append(cost_per_ton)

    elevator_avg = sum(elevator_costs) / len(elevator_costs) if elevator_costs else 0.0
    ground_avg = sum(ground_costs) / len(ground_costs) if ground_costs else 0.0

    out_path = base / "elevator_ground_cost.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["类型", "每吨价格(亿美元/吨)"])
        writer.writerow(["电梯平均", f"{elevator_avg:.6f}"])
        writer.writerow(["地面平均", f"{ground_avg:.6f}"])

    print(f"done: {out_path}")


if __name__ == "__main__":
    main()
