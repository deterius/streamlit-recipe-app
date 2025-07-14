import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(".."))
from helper_functions import compute_unit_cost  # reuse your function

CATEGORY_PREFIX = {
    "未加工肉类": "RME", "加工肉类": "PME", "海鲜类": "SEA",
    "冻品类": "FRZ", "调味品": "CON", "干货": "DRY",
    "蔬菜": "VEG", "预制品": "PRE", "厨房用品": "KTC"
}

# Load your CSV
df = pd.read_csv("../ingredients.csv")

# Don't prefill values! Let Pandas assign them
df["编号"] = ""
df["创建时间"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
df["修改时间"] = df["创建时间"]

# Compute 编号 and 基础单位价格
for i, row in df.iterrows():
    # Skip if 编号 already exists and is non-empty
    if pd.notna(row["编号"]) and str(row["编号"]).strip() != "":
        continue

    # Create serial number
    prefix = CATEGORY_PREFIX.get(row["食材分类"], "UNK")
    count_in_category = df[df["食材分类"] == row["食材分类"]].index.get_loc(i) + 1
    serial = f"{prefix}-{count_in_category:04d}"
    df.at[i, "编号"] = serial

    # Compute normalized cost
    normalized_cost = compute_unit_cost(
        unit=row["单位"],
        cost=row["单位价格"],
        volume_str=str(row["单位容量"]) if pd.notna(row["单位容量"]) else ""
    )
    df.at[i, "基础单位价格"] = normalized_cost

# Final export
df = df[[
    "编号", "供应商", "食材英文名", "食材中文名", "食材分类",
    "单位", "单位价格", "单位容量", "基础单位价格", "创建时间", "修改时间"
]]
df.to_csv("../ingredients.csv", index=False)
print("✅ Exported to ingredients.csv")
