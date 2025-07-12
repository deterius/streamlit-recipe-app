import pandas as pd
import json
from datetime import datetime

# File paths
INGREDIENT_FILE = "ingredients.csv"
RECIPE_FILE = "recipes.json"

# Load ingredients and create a mapping by 编号
ingredients_df = pd.read_csv(INGREDIENT_FILE)
ingredients_df["基础单位价格"] = pd.to_numeric(ingredients_df["基础单位价格"], errors="coerce")
ingredients_map = ingredients_df.set_index("编号").to_dict("index")

# Load existing recipes
with open(RECIPE_FILE, "r", encoding="utf-8") as f:
    recipes = json.load(f)

updated_count = 0

for recipe in recipes:
    total_cost = 0
    updated_ings = []

    for ing in recipe["食材"]:
        serial = ing.get("编号")
        qty = ing.get("用量", 0)

        if serial in ingredients_map:
            new_price = ingredients_map[serial]["基础单位价格"]
            subtotal = round(new_price * qty, 2)

            ing["单价"] = new_price
            ing["小计"] = subtotal
            total_cost += subtotal
        else:
            print(f"⚠️ 编号 {serial} not found in ingredients.csv — skipping cost update for this item.")
            # Still try to include the subtotal if already present
            subtotal = ing.get("小计", 0)
            total_cost += subtotal

        updated_ings.append(ing)

    recipe["食材"] = updated_ings
    recipe["总成本"] = round(total_cost, 2)

    try:
        recipe["成本百分比"] = round((total_cost / recipe["售价"]) * 100, 2)
    except Exception as e:
        print(f"⚠️ Error computing 成本百分比 for recipe {recipe.get('编号')}: {e}")
        recipe["成本百分比"] = 0

    recipe["修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_count += 1

# Save updated file
with open(RECIPE_FILE, "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print(f"✅ Finished. Updated {updated_count} recipes with refreshed costs and percentages.")
