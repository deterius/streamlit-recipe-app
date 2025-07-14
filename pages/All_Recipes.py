import streamlit as st
import json
import os
from helper_functions import render_recipe, merge_ingredients_into_recipes



# path to recipies
RECIPE_FILE = "recipes.json"

# paget setup
st.set_page_config(page_title="所有菜谱", layout="wide")
st.title("📚 所有菜谱")
st.markdown("此页用于查看、编辑或删除已保存的菜谱")


# load recipes file
if os.path.exists(RECIPE_FILE):
    with open(RECIPE_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)
else:
    recipes = []

# ✅ Always merge updated ingredient costs
recipes = merge_ingredients_into_recipes(recipes)


if not recipes:
    st.info("No recipies currently exists")
    st.stop()
    
# Helper file, save updated lists back to file
def save_recipes(updated_list):
    with open(RECIPE_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=2)
        
# --- Category Filtering ---
categories = sorted(list({r.get("分类", "未分类") for r in recipes}))
selected_category = st.selectbox("按菜单分类筛选", ["全部"] + categories)

# Apply filtering or grouping
if selected_category == "全部":
    # Group by category
    grouped = {}
    for r in recipes:
        cat = r.get("分类", "未分类")
        grouped.setdefault(cat, []).append(r)
    
    for cat_name, group in grouped.items():
        st.subheader(f"📂 分类: {cat_name}")
        for index, recipe in enumerate(group):
            with st.expander(f"{recipe['中文名']} / {recipe['英文名']} — 售价: ¥{recipe['售价']}"):
                render_recipe(recipe, index)

else:
    # Show only selected category
    filtered_recipes = [r for r in recipes if r.get("分类") == selected_category]
    for index, recipe in enumerate(filtered_recipes):  
        with st.expander(f"{recipe['中文名']} / {recipe['英文名']} — 售价: ¥{recipe['售价']}"):
            render_recipe(recipe, index)
            
