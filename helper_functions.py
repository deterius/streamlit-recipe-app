import re
from uuid import uuid4
import os
import uuid
from PIL import Image

def compute_unit_cost(unit, cost, volume_str):
    try:
        cost = float(str(cost).replace("¥", "").replace("$", "").replace(",", "").strip())

        if volume_str:
            volume = float(str(volume_str).strip())
            if volume > 0:
                return round(cost / volume, 4)  # 优先根据单位容量计算

        # fallback if no volume provided
        if unit == "kg":
            return round(cost / 1000, 4)
        elif unit == "斤":
            return round(cost / 500, 4)
        elif unit == "L":
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
                st.switch_page("pages/3_add_recipe.py")

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