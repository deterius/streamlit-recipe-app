import pandas as pd
import os

# File path to your ingredient database
DATA_FILE = "../ingredients.csv"

def compute_unit_cost(unit, cost, volume_str):
    try:
        cost = float(str(cost).replace("¥", "").replace("$", "").replace(",", "").strip())

        if volume_str:
            try:
                volume = float(str(volume_str).strip())
                if volume > 0:
                    return round(cost / volume, 4)
            except ValueError:
                pass  # Ignore and fall back to unit-based logic

        unit = str(unit).strip().lower()

        if unit in ["kg", "公斤"]:
            return round(cost / 1000, 4)
        elif unit == "斤":
            return round(cost / 500, 4)
        elif unit == "l":  # ✅ FIXED: closing bracket typo
            return round(cost / 1000, 4)
        elif unit in ["g", "ml"]:
            return round(cost, 4)
        else:
            return None
    except Exception as e:
        print(f"⚠️ Error computing unit cost: {e}, cost={cost}, volume_str={volume_str}, unit={unit}")
        return None

def update_ingredient_costs():
    if not os.path.exists(DATA_FILE):
        print("❌ ingredients.csv not found.")
        return

    df = pd.read_csv(DATA_FILE)

    # Recalculate all base unit prices
    df["基础单位价格"] = df.apply(
        lambda row: compute_unit_cost(
            row.get("单位"),
            row.get("单位价格"),
            row.get("单位容量")
        ),
        axis=1
    )

    # Save updated file
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    print(f"✅ Updated {len(df)} ingredients and saved to {DATA_FILE}")

if __name__ == "__main__":
    update_ingredient_costs()
