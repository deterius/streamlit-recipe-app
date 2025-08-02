import streamlit as st
import shutil

st.set_page_config(page_title="食材数据库", layout="centered")

import pandas as pd
import os
from datetime import datetime
import unicodedata #for weChat pasting
import datetime
from helper_functions import compute_unit_cost, clean_ingredient_df

# File Name for database
DATA_FILE = "ingredients.csv"
RECIPE_FILE = "recipes.json"

# Column names (in Chinese)
COLUMNS = [
    "编号",          # Reference Number
    "供应商",        # Supplier
    "食材英文名",    # Ingredient En
    "食材中文名",    # Ingredient ZH
    "食材分类",      # Type
    "单位",          # Unit
    "单位价格",      # Cost per Unit
    "单位容量",      # Volume per Unit
    "基础单位价格",    # Base unit cost
    "创建时间",      # Date Created
    "修改时间"       # Date Modified
]

# Category to prefix mapping
CATEGORY_PREFIX = {
    "未加工肉类": "RME",
    "加工肉类": "PME",
    "海鲜类": "SEA",
    "冻品类": "FRZ",
    "调味品": "CON",
    "干货": "DRY",
    "蔬菜": "VEG",
    "预制品": "PRE",
    "厨房用品": "KTC"
}

# Create if no DB exists
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)
    
# Load existing if exists
df = pd.read_csv(DATA_FILE)
df = clean_ingredient_df(df)

st.title("🥬 食材数据库")
st.markdown("Rourou Nanshan")

st.subheader("📋 当前食材列表")
# -- Filtering sidebar or inline
col1, col2 = st.columns(2)
with col1:
    selected_type = st.selectbox("筛选：按食材分类", ["全部"] + list(CATEGORY_PREFIX.keys()))
with col2:
    search_text = st.text_input("搜索食材（中英文）")

# -- Apply filters to DF
filtered_df = df.copy()
if selected_type != "全部":
    filtered_df = filtered_df[filtered_df["食材分类"] == selected_type]
    
# Strip everything from the search and make sure its compatiable with WeChat
search_text = unicodedata.normalize("NFKC", search_text.strip())

if search_text:
    filtered_df = filtered_df[
        filtered_df["食材中文名"].astype(str).str.contains(search_text, case=False, na=False) |
        filtered_df["食材英文名"].astype(str).str.contains(search_text, case=False, na=False)
    ]

# Make sure creation time column is present   
if "创建时间" not in filtered_df.columns:
    filtered_df["创建时间"] = ""
    
# -- Show More recent first 
filtered_df = filtered_df.sort_values("创建时间", ascending=False)
display_df = filtered_df.drop(columns=["创建时间"])

edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    num_rows="dynamic",
    key="editable_ingredients",
    column_config={
        "编号": st.column_config.TextColumn("编号", disabled=True),
        # "单位价格": st.column_config.NumberColumn("单位价格", disabled=True),
        "创建时间": st.column_config.TextColumn("创建时间", disabled=True),
        "修改时间": st.column_config.TextColumn("修改时间", disabled=True),
    }
)
if st.button("💾 保存修改"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create a copy of the full DataFrame to modify
    df_updated = df.copy()

    for i, row in edited_df.iterrows():
        serial = row["编号"]
        full_idx = df[df["编号"] == serial].index
        if not full_idx.empty:
            idx = full_idx[0]
            # Compare only editable columns
            for col in edited_df.columns:
                if col in ["创建时间", "修改时间", "编号", "基础单位价格"]:
                    continue
                if pd.isna(row[col]) and pd.isna(df.at[idx, col]):
                    continue
                if row[col] != df.at[idx, col]:
                    df_updated.at[idx, col] = row[col]
                    df_updated.at[idx, "修改时间"] = now
                    
    # 🔁 Backup before overwrite
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("backups", exist_ok=True)
    backup_path = f"backups/ingredients_backup_{timestamp}.csv"
    shutil.copy(DATA_FILE, backup_path)
    # Backup path for recipes
    recipe_backup_path = f"backups/recipes_backup_{timestamp}.json"
    if os.path.exists(RECIPE_FILE):
        shutil.copy(RECIPE_FILE, recipe_backup_path)

    # Save the full dataset, not the filtered one
    df_updated.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    st.success("✅ 修改已保存（全表已更新）")
    
    import json

    # --- Load updated ingredients ---
    ingredients_df = pd.read_csv(DATA_FILE)
    ingredients_df = clean_ingredient_df(ingredients_df)
    ingredient_map = {
        row["编号"]: row for _, row in ingredients_df.iterrows()
    }

    # --- Load recipes ---
    with open(RECIPE_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    # --- Update recipes ---
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for recipe in recipes:
        updated_ingredients = []
        for item in recipe.get("食材", []):
            serial = item.get("编号")
            ing = ingredient_map.get(serial)
            if ing is None:
                updated_ingredients.append(item)  # Ingredient not found in latest DB
                continue

            # Update cost & names
            item["基础单位价格"] = ing["基础单位价格"]
            item["总成本"] = float(item.get("用量", 0)) * ing["基础单位价格"]
            item["食材英文名"] = ing.get("食材英文名", item.get("食材英文名", ""))
            item["食材中文名"] = ing.get("食材中文名", item.get("食材中文名", ""))
            updated_ingredients.append(item)

        # Update the recipe ingredient list
        recipe["食材"] = updated_ingredients

        # Update cost and percentage
        total_cost = sum(item["总成本"] for item in updated_ingredients)
        recipe["总成本"] = round(total_cost, 2)
        price = float(recipe.get("售价", 0))
        recipe["成本百分比"] = round((total_cost / price) * 100, 2) if price else 0
        recipe["修改时间"] = now

    # --- Save updated recipes ---
    with open(RECIPE_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)


