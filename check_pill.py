import csv
import json
from pathlib import Path

latest = max(Path("output").glob("*.json"), key=lambda p: p.stat().st_mtime)

stock = {}
with open("inventory.csv", "r", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        stock[row["Ten_Thuoc"].strip()] = row["Ton_Kho"].strip()

with open(latest, "r", encoding="utf-8") as f:
    items = json.load(f)

results = []
for item in items:
    full_name = str(item.get("full_name", "")).strip()
    qty = stock.get(full_name)
    results.append(
        {
            "full_name": full_name,
            "co_trong_db": qty is not None,
            "ton_kho": qty if qty is not None else "KHONG_TIM_THAY",
        }
    )

Path("check").mkdir(exist_ok=True)
out_file = Path("check") / f"check_{latest.stem}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({"source_file": str(latest), "results": results}, f, ensure_ascii=False, indent=2)

print(f"Saved: {out_file}")
