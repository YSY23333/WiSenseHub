"""Create a tiny deterministic CSV used only to demonstrate the pipeline."""
from pathlib import Path
import csv
import math


output = Path(__file__).parent / "data" / "synthetic_csi.csv"
output.parent.mkdir(parents=True, exist_ok=True)
fields = ["timestamp_s"] + [f"{part}_l0_s{sub}" for sub in range(4) for part in ("real", "imag")]
with output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for index in range(198):
        timestamp = index / 50.0 + (0.001 if index % 7 == 0 else 0.0)
        row = {"timestamp_s": f"{timestamp:.6f}"}
        for sub in range(4):
            phase = 2 * math.pi * (0.25 + sub * 0.05) * timestamp
            row[f"real_l0_s{sub}"] = f"{math.cos(phase):.7f}"
            row[f"imag_l0_s{sub}"] = f"{math.sin(phase):.7f}"
        writer.writerow(row)
print(output)

