import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import uuid

from helper_functions import save_uploaded_file

# session state check:
if "selected_category" not in st.session_state:
    st.session_state.selected_category = ""

if "selected_ingredient" not in st.session_state:
    st.session_state.selected_ingredient = ""

if "ingredient_qty" not in st.session_state:
    st.session_state.ingredient_qty = 0.0
    
if st.session_state.get("clear_fields", False):
    st.session_state.selected_category = ""
    st.session_state.selected_ingredient = ""
    st.session_state.ingredient_qty = 0.0
    st.session_state.clear_fields = False

# Check for edit mode
edit_mode = st.session_state.get("edit_mode", False)
edit_recipe = st.session_state.get("edit_recipe", None)

if "recipe_ingredients" not in st.session_state:
    st.session_state.recipe_ingredients = []

if "procedure_steps" not in st.session_state:
    st.session_state.procedure_steps = []
    
if edit_mode and edit_recipe:
    if not st.session_state.recipe_ingredients:
        st.session_state.recipe_ingredients = edit_recipe["食材"]
    if not st.session_state.procedure_steps:
        st.session_state.procedure_steps = edit_recipe["步骤"]

# --- CONFIG ---
st.set_page_config(page_title="新增菜谱", layout="centered")
st.markdown("此页用于添加新菜谱")

# recipie editing mode
if st.session_state.get("go_to_add_recipe"):
    st.session_state.go_to_add_recipe = False # reset flag
    st.rerun()

# Step 1: Recipe Info
st.title("新增菜谱")

col1, col2 =st.columns(2)
with col1:
    # Menu classification
    CATEGORIES = [
        "BBQ/烤肉", "Seafood/海鲜", "Soups/汤", "Appetizers/小吃", 
        "Late Night Snacks/下酒菜", "Semi-finished/半成品", 
        "Small dishes/小菜", "Bento/便当"
    ]
    recipe_category = st.selectbox("菜单分类", CATEGORIES, index=0 if not edit_mode else CATEGORIES.index(edit_recipe["分类"]) if edit_recipe.get("分类") in CATEGORIES else 0)

    # Load values based on edit or new mode
    recipe_name_en = edit_recipe["英文名"] if edit_mode and edit_recipe else ""
    recipe_name_zh = edit_recipe["中文名"] if edit_mode and edit_recipe else ""
    selling_price = edit_recipe["售价"] if edit_mode and edit_recipe else 0.0



    # Load ingredients database
    INGREDIENT_FILE = "ingredients.csv"
    RECIPE_FILE = "recipes.json"
    ingredient_df = pd.read_csv(INGREDIENT_FILE)
    ingredient_df["基础单位价格"] = pd.to_numeric(ingredient_df["基础单位价格"], errors='coerce')


    # Step 1: Recipe Info
    st.subheader("📝 菜谱基本信息")

    recipe_name_en = st.text_input("菜谱英文名")
    recipe_name_zh = st.text_input("菜谱中文名")
    selling_price = st.number_input("售价（人民币）", min_value=0.0, step=0.5)

with col2:
    # (Step 3: Procedure & images)
    st.subheader("📷 主图和备注")
    current_main_img = edit_recipe["主图"] if edit_mode and edit_recipe else ""
    if current_main_img:
        st.markdown(f"🖼️ 当前主图: {current_main_img}")
        st.image(os.path.join("uploaded_images", current_main_img), width=400, caption="当前主图")
        
    main_img = st.file_uploader("上传新主图（将替换现有图片）", type=["jpg", "jpeg", "png"])
    main_img_name = ""
    # Only try to save image if both recipe name and image are present
    if main_img:
        if recipe_name_en.strip():
            main_img_name = save_uploaded_file(main_img, f"{recipe_name_en.strip()}_main")
        else:
            st.warning("⚠️ 请先输入菜谱英文名，再上传主图！")


    notes = st.text_area("备注 / Notes", value=edit_recipe["备注"] if edit_mode and edit_recipe else "")

# Step 2: Add ingredients
st.subheader("🧂 添加食材")

# Session state to hold added ingredients
if "recipe_ingredients" not in st.session_state:
    st.session_state.recipe_ingredients = []

# Ingredient selector
categories = ingredient_df["食材分类"].dropna().unique().tolist()
categories.sort()

st.session_state.selected_category = st.selectbox(
    "选择食材分类", [""] + categories,
    index=([""] + categories).index(st.session_state.selected_category)
)

filtered_df = ingredient_df[ingredient_df["食材分类"] == st.session_state.selected_category] if st.session_state.selected_category else ingredient_df
ingredient_names = filtered_df["食材中文名"].tolist()

# ingredient selector

st.session_state.selected_ingredient = st.selectbox(
    "选择食材", [""] + ingredient_names,
    index=([""] + ingredient_names).index(st.session_state.selected_ingredient) if st.session_state.selected_ingredient in ingredient_names else 0
)

# quantity input
st.number_input("使用量（g 或 ml）", min_value=0.0, step=1.0, key="ingredient_qty")
# ing note
ingredient_note = st.text_input("备注（例如：约10片）", key="ingredient_note")

if st.button("➕ 添加到菜谱"):
        
    if st.session_state.selected_ingredient:
        ing = filtered_df[filtered_df["食材中文名"] == st.session_state.selected_ingredient].iloc[0]
        qty = st.session_state.ingredient_qty
        st.write("DEBUG", qty, ing["基础单位价格"])
        subtotal = qty * ing["基础单位价格"]
        st.session_state.recipe_ingredients.append({
            "编号": ing["编号"],
            "食材中文名": ing["食材中文名"],
            "用量": qty,
            "单价": ing["基础单位价格"],
            "小计": subtotal,
            "备注": ingredient_note
        })
        st.success(f"已添加：{ing['食材中文名']}，用量：{qty}")
        st.session_state.clear_fields = True
        st.rerun()

       


# Display current ingredients
if st.session_state.recipe_ingredients:
    st.subheader("📋 当前使用食材")
    
    # show each ingredient with a delete option
    for i, ing in enumerate(st.session_state.recipe_ingredients):
        cols = st.columns([3,3,2,2,1])
        cols[0].markdown(f"**{ing['食材中文名']}**")
        cols[1].markdown(f"用量(g/ml): {ing['用量']}")
        cols[2].markdown(f"单价: ¥{ing['单价']:.2f}")
        cols[3].markdown(f"小计: ¥{ing['小计']:.2f}")
        if cols[4].button("❌", key=f"delete_ing_{i}"):
            st.session_state.recipe_ingredients.pop(i)
            st.rerun()
    
    # Summary
    total_cost = sum(i["小计"] for i in st.session_state.recipe_ingredients)
    st.markdown(f"**总成本：¥{total_cost:.2f}**")

    if selling_price:
        cost_pct = total_cost / selling_price * 100
        st.markdown(f"**成本百分比：{cost_pct:.1f}%**")
        
    # Optional: Clear all button
    if st.button("🧹 清空所有食材"):
        st.session_state.recipe_ingredients = []
        st.rerun()




# Step 3: Procedure steps
st.subheader("📸 制作步骤（每步可添加图片）")
with st.form("step_form", clear_on_submit=True):
    step_desc = st.text_area("步骤描述", key="step_desc")
    step_img = st.file_uploader("上传步骤图片（可选）", type=["jpg", "jpeg", "png"], key="step_img")
    add_step = st.form_submit_button("添加步骤")
    if add_step:
        if not step_desc.strip():
            st.warning("请输入步骤描述")
        else:
            step_img_name = step_img.name if step_img else ""
            if step_img:
                step_index = len(st.session_state.procedure_steps) + 1
                step_img_name = save_uploaded_file(step_img, f"{recipe_name_en}_step_{step_index}")
            st.session_state.procedure_steps.append({
                "描述": step_desc.strip(),
                "图片名": step_img_name
            })
            st.success("步骤已添加")

if st.session_state.procedure_steps:
    st.markdown("### ✅ 当前步骤")
    for i, step in enumerate(st.session_state.procedure_steps):
        st.markdown(f"**步骤 {i+1}：** {step['描述']}")
        if step["图片名"]:
            st.markdown(f"📷 当前步骤图片：{step['图片名']}")
            st.caption("当前步骤图片预览：")
            st.image(os.path.join("uploaded_images", step["图片名"]), width=300, caption=f"步骤 {i+1} 图片")
            
        new_step_img = st.file_uploader("替换步骤图片（可选）", type=["jpg", "jpeg", "png"], key=f"replace_step_img_{i}")
        if new_step_img:
            new_img_name = save_uploaded_file(new_step_img, f"{recipe_name_en}_step_{i+1}")
            st.session_state.procedure_steps[i]["图片名"] = new_img_name
            st.success(f"步骤 {i+1} 图片已更新 ✅")

        if st.button(f"❌ 删除步骤 {i+1}", key=f"del_step_{i}"):
            st.session_state.procedure_steps.pop(i)
            st.rerun()
            
        
            

# -- Save recipe
st.subheader("💾 保存菜谱")
if st.button("保存菜谱"):
    if not recipe_name_en or not recipe_name_zh:
        st.warning("请输入菜谱中英文名")
    elif not st.session_state.recipe_ingredients:
        st.warning("请至少添加一个食材")
    elif not st.session_state.procedure_steps:
        st.warning("请至少添加一个步骤")
    elif not selling_price:
        st.warning("请输入售价")
    else:
        # Load existing
        if os.path.exists(RECIPE_FILE):
            with open(RECIPE_FILE, "r", encoding="utf-8") as f:
                existing_recipes = json.load(f)
        else:
            existing_recipes = []

        # --- Generate recipe ID and timestamps ---
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modified_at = created_at
        
        if edit_mode and edit_recipe:
            recipe_id = edit_recipe["编号"]
            created_at = edit_recipe["创建时间"]
        else:
            # Ensure unique recipe ID
            existing_ids = [r["编号"] for r in existing_recipes]
            num = 1
            while True:
                candidate = f"RC-{num:04d}"
                if candidate not in existing_ids:
                    recipe_id = candidate
                    break
                num += 1
        

        total_cost = sum(i["小计"] for i in st.session_state.recipe_ingredients)
        cost_pct = round(total_cost / selling_price * 100, 2)

        new_recipe = {
            "编号": recipe_id,
            "英文名": recipe_name_en,
            "中文名": recipe_name_zh,
            "分类": recipe_category,
            "售价": selling_price,
            "总成本": round(total_cost, 2),
            "成本百分比": cost_pct,
            "食材": st.session_state.recipe_ingredients,
            "步骤": st.session_state.procedure_steps,
            "备注": notes,
            "主图": main_img_name if main_img else current_main_img,
            "创建时间": created_at,
            "修改时间": created_at
        }

        if edit_mode and edit_recipe:
            found = False  
            for i, r in enumerate(existing_recipes):
                if r["编号"] == edit_recipe["编号"]:
                    new_recipe["编号"] = edit_recipe["编号"]
                    new_recipe["创建时间"] = edit_recipe["创建时间"]
                    new_recipe["修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    existing_recipes[i] = new_recipe
                    found = True
                    break
            if not found:
                existing_recipes.append(new_recipe)
        else:
            existing_recipes.append(new_recipe)
        
        with open(RECIPE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_recipes, f, ensure_ascii=False, indent=2)

        # Immediately read it back to verify
        with open(RECIPE_FILE, "r", encoding="utf-8") as f:
            data_check = json.load(f)
        st.write("✅ JSON file contents after write:", data_check)
            

        st.success(f"菜谱 {recipe_name_zh} / {recipe_name_en} 已保存 ✅")

        st.session_state.edit_mode = False
        st.session_state.edit_recipe = None
        
        # Reset session
        st.session_state.recipe_ingredients = []
        st.session_state.procedure_steps = []
