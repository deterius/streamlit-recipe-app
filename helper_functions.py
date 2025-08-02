import re
from uuid import uuid4
import os
import uuid
from PIL import Image
import streamlit as st
import pandas as pd

def merge_ingredients_into_recipes(recipes, ingredient_csv_path="ingredients.csv"):
    """
    Refresh each recipe’s ingredient info using the latest unit prices from ingredients.csv.
    This avoids having to re-run a sync script manually.
    """
    if not recipes or len(recipes) == 0:
        return recipes

    if not os.path.exists(ingredient_csv_path):
        raise FileNotFoundError(f"Ingredient file not found: {ingredient_csv_path}")

    ingredients_df = pd.read_csv(ingredient_csv_path)
    ingredients_df["基础单位价格"] = pd.to_numeric(ingredients_df["基础单位价格"], errors="coerce")
    ingredient_map = {
    row["编号"]: row.to_dict()
    for _, row in ingredients_df.iterrows()
}

    for recipe in recipes:
        total_cost = 0
        updated_ings = []

        for ing in recipe.get("食材", []):
            serial = ing.get("编号")
            qty = float(ing.get("用量", 0))

            ingredient = ingredient_map.get(serial)
            if ingredient:
                unit_price = compute_unit_cost(
                    unit=ingredient.get("单位"),
                    cost=ingredient.get("单位价格"),
                    volume_str=ingredient.get("单位容量")
                )
                ing["基础单位价格"] = unit_price
                ing["单价"] = unit_price
                ing["小计"] = round(unit_price * qty, 2) if unit_price else 0
                total_cost += ing["小计"]
            else:
                # Keep existing subtotal if ingredient was removed from DB
                subtotal = ing.get("小计", 0)
                total_cost += subtotal

            updated_ings.append(ing)

        recipe["食材"] = updated_ings
        recipe["总成本"] = round(total_cost, 2)

        try:
            recipe["成本百分比"] = round((total_cost / float(recipe.get("售价", 0))) * 100, 2)
        except:
            recipe["成本百分比"] = 0

    return recipes


def calculate_waste_item(ingredients: list) -> dict:
    """Create a waste line item representing 10% of ingredient cost.

    Missing "小计" values are treated as 0 to avoid KeyError."""
    total = sum(i.get("小计", 0) for i in ingredients if i.get("编号") != "WASTE")
    waste_cost = round(total * 0.10, 2)
    return {
        "编号": "WASTE",
        "食材中文名": "损耗",
        "用量": "",
        "单价": "",
        "小计": waste_cost,
        "备注": "估算损耗（10%）",
    }


def clean_ingredient_df(df: pd.DataFrame) -> pd.DataFrame:
    # Columns that should be treated as strings
    string_columns = [
        "编号", "供应商", "食材英文名", "食材中文名", "食材分类", "单位", "修改时间"
    ]

    # Convert to string and fill NaNs with empty string
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")

    # Columns that should be floats
    float_columns = ["单位价格", "单位容量", "基础单位价格"]
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def render_recipe(recipe, index, recipes, save_recipes):
    key_suffix = recipe["编号"]

    # Try to display image (even if missing)
    image_name = recipe.get("主图")
    if image_name:
        image_path = os.path.join("uploaded_images", image_name)
        if os.path.exists(image_path):
            st.image(image_path, width=200, caption="主图预览")
        else:
            st.warning("⚠️ 找不到主图文件")
    else:
        st.info("ℹ️ 此菜谱没有主图")

    # Layout
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**售价**: ¥{recipe['售价']}")
        st.markdown(f"**总成本**: ¥{recipe['总成本']}")
        st.markdown(f"**成本百分比**: {recipe['成本百分比']}%")
        st.markdown(f"**备注**: {recipe['备注']}")
    with col2:
        st.markdown(f"**编号**: {recipe['编号']}")
        st.markdown(f"**创建时间**: {recipe['创建时间']}")
        st.markdown(f"**修改时间**: {recipe['修改时间']}")

    # Ingredients
    st.markdown("### 使用食材 (g/ml)")

    ingredients = recipe.get("食材", [])
    if ingredients:
        import pandas as pd

        df = pd.DataFrame(ingredients)

        # Choose which columns to display and rename for clarity
        display_cols = {
            "食材中文名": "食材",
            "用量": "用量",
            "单位": "单位",
            "基础单位价格": "单价 (¥)",
            "小计": "小计 (¥)",
            "备注": "备注"
        }

        # Filter and rename only existing columns
        filtered = df[[col for col in display_cols.keys() if col in df.columns]]
        filtered = filtered.rename(columns=display_cols)

        st.dataframe(filtered, use_container_width=True)
    else:
        st.write("❌ 无食材数据")

    # Steps
    st.markdown("### 制作步骤")
    steps = recipe.get("步骤", [])

    # Set how many steps per row
    steps_per_row = 3

    # Loop through steps in chunks
    for row_start in range(0, len(steps), steps_per_row):
        cols = st.columns(steps_per_row)
        for idx, step in enumerate(steps[row_start:row_start + steps_per_row]):
            with cols[idx]:
                st.markdown(f"**步骤 {row_start + idx + 1}**")
                img_name = step.get("图片名")
                if img_name:
                    step_img_path = os.path.join("uploaded_images", img_name)
                    if os.path.exists(step_img_path):
                        st.image(step_img_path, use_container_width=True)
                    else:
                        st.warning("⚠️ 找不到步骤图片")
                st.markdown(step.get("描述", "无描述"))

    # Edit / Delete Buttons
    if "confirm_delete_index" not in st.session_state:
        st.session_state.confirm_delete_index = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ 编辑", key=f"edit_btn_{recipe['编号']}"):
            st.session_state.edit_recipe = recipe
            st.session_state.edit_mode = True
            st.switch_page("pages/Add_Recipe.py")

    with col2:
        if st.button("🗑️ 删除", key=f"delete_btn_{recipe['编号']}"):
            st.session_state.confirm_delete_index = index
        if st.session_state.confirm_delete_index == index:
            st.warning(f"你确定要删除菜谱 `{recipe['中文名']}` 吗？这将无法恢复。", icon="⚠️")
            if st.button("✅ 确认删除", key=f"confirm_delete_{key_suffix}"):
                deleted_recipe = recipes.pop(index)
                save_recipes(recipes)
                st.toast("已删除菜谱 ✅")
                st.session_state.confirm_delete_index = None
                st.rerun()


def compute_unit_cost(unit, cost, volume_str):
    try:
        # Normalize and clean cost
        cost = float(str(cost).replace("¥", "").replace("$", "").replace(",", "").strip())

        # Try volume-based calculation first
        if volume_str:
            try:
                volume = float(str(volume_str).strip())
                if volume > 0:
                    return round(cost / volume, 4)
            except ValueError:
                pass  # Fall back to unit-based

        # Normalize unit string
        unit = str(unit).strip().lower()

        # Fallback logic if no valid volume
        if unit in ["kg", "公斤"]:
            return round(cost / 1000, 4)
        elif unit == "斤":
            return round(cost / 500, 4)
        elif unit == "l":
            return round(cost / 1000, 4)
        elif unit in ["g", "ml"]:
            return round(cost, 4)
        else:
            return None  # unknown units
    except Exception as e:
        print(f"⚠️ Error computing unit cost: {e}, cost={cost}, volume_str={volume_str}, unit={unit}")
        return None
  
    
def save_uploaded_file(uploaded_file, filename_hint=None):
    upload_dir = "uploaded_images"
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(uploaded_file.name)[-1].lower()
    
    # Sanitize the filename hint
    if filename_hint:
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in filename_hint)
        unique_filename = f"{safe_name}{ext}"
    else:
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
    file_path = os.path.join(upload_dir, unique_filename)

    # Save and resize
    img = Image.open(uploaded_file)
    img.thumbnail((1024, 1024))  # Adjust size as needed
    img.save(file_path)

    return unique_filename


def display_recipe(recipe):
    key_suffix = recipe["编号"]
    with st.expander(f"{recipe['中文名']} / {recipe['英文名']} — 售价: ¥{recipe['售价']}"):
        st.markdown(f"**编号**: {recipe['编号']}")
        st.markdown(f"**总成本**: ¥{recipe['总成本']}")
        st.markdown(f"**成本百分比**: {recipe['成本百分比']}%")
        st.markdown(f"**创建时间**: {recipe['创建时间']}")
        st.markdown(f"**修改时间**: {recipe['修改时间']}")
        st.markdown(f"**备注**: {recipe['备注']}")

        st.markdown("### 使用食材(g)")
        ingredients_df = recipe.get("食材", [])
        if ingredients_df:
            st.dataframe(ingredients_df, use_container_width=True)
        else:
            st.write("❌ 无食材数据")

        st.markdown("### 制作步骤")
        for i, step in enumerate(recipe.get("步骤", [])):
            st.markdown(f"**步骤 {i+1}**: {step['描述']}")
            if step["图片名"]:
                st.markdown(f"📷 步骤图片: {step['图片名']}")

        if recipe.get("主图"):
            st.markdown(f"🖼️ 主图文件名: {recipe['主图']}")

        if "confirm_delete_index" not in st.session_state:
            st.session_state.confirm_delete_index = None

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ 编辑", key=f"edit_{key_suffix}"):
                st.session_state.edit_recipe = recipe
                st.session_state.edit_mode = True
                st.switch_page("pages/Add_Recipe.py")

        with col2:
            if st.button("🗑️ 删除", key=f"delete_{key_suffix}"):
                st.session_state.confirm_delete_index = key_suffix

            if st.session_state.confirm_delete_index == key_suffix:
                st.warning(f"你确定要删除菜谱 `{recipe['中文名']}` 吗？这将无法恢复。", icon="⚠️")
                if st.button("✅ 确认删除", key=f"confirm_delete_{key_suffix}"):
                    recipes[:] = [r for r in recipes if r["编号"] != recipe["编号"]]

                    # Remove associated images
                    main_img = recipe.get("主图", "")
                    if main_img:
                        main_img_path = os.path.join("uploaded_images", main_img)
                        if os.path.exists(main_img_path):
                            os.remove(main_img_path)

                    for step in recipe.get("步骤", []):
                        step_img = step.get("图片名", "")
                        if step_img:
                            step_img_path = os.path.join("uploaded_images", step_img)
                            if os.path.exists(step_img_path):
                                os.remove(step_img_path)

                    save_recipes(recipes)
                    st.toast("已删除菜谱 ✅")
                    st.session_state.confirm_delete_index = None
                    st.rerun()
