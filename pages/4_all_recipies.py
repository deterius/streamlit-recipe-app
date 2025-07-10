import streamlit as st
import json
import os


# path to recipies
RECIPE_FILE = "recipes.json"

# paget setup
st.set_page_config(page_title="所有菜谱", layout="wide")
st.title("📚 所有菜谱")
st.markdown("此页用于查看、编辑或删除已保存的菜谱")

# load recipes file
if os.path.exists(RECIPE_FILE):
    with open(RECIPE_FILE, "r", encoding="utf-8") as f:
        recipes =json.load(f)
else:
    recipes = []

if not recipes:
    st.info("No recipies currently exists")
    st.stop()
    
# Helper file, save updated lists back to file
def save_recipes(updated_list):
    with open(RECIPE_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=2)
        
#loop through each recipes and display info
for index, recipe in enumerate(recipes):
    with st.expander(f"{recipe['中文名']} / {recipe['英文名']} — 售价: ¥{recipe['售价']}"):
        st.markdown(f"**编号**: {recipe['编号']}")
        st.markdown(f"**总成本**: ¥{recipe['总成本']}")
        st.markdown(f"**成本百分比**: {recipe['成本百分比']}%")
        st.markdown(f"**创建时间**: {recipe['创建时间']}")
        st.markdown(f"**修改时间**: {recipe['修改时间']}")
        st.markdown(f"**备注**: {recipe['备注']}")
        
        # show ingredients use
        st.markdown("### 使用食材(g)")
        ingredients_df = recipe.get("食材", [])
        if ingredients_df:
            st.dataframe(ingredients_df, use_container_width=True)
        else:
            st.write("❌ 无食材数据")
            
        #show steps
        st.markdown("### 制作步骤")
        for i, step in enumerate(recipe.get("步骤", [])):
            st.markdown(f"**步骤 {i+1}**: {step['描述']}")
            if step["图片名"]:
                st.markdown(f"📷 步骤图片: {step['图片名']}")
                
        #show main image filename (or later the image itself)
        if recipe.get("主图"):
            st.markdown(f"🖼️ 主图文件名: {recipe['主图']}")
            
        # --- Buttons to edit or delete ---
        if "confirm_delete_index" not in st.session_state:
            st.session_state.confirm_delete_index = None
        col1, col2 =st.columns(2)
        with col1:
            if st.button("✏️ 编辑", key=f"edit_{index}"):
                st.session_state.edit_recipe = recipe
                st.session_state.edit_mode = True
                st.switch_page("pages/3_add_recipe.py")  # or just "3_add_recipe" if using named pages

                
        with col2:
            if st.button("🗑️ 删除", key=f"delete_{index}"):
                st.session_state.confirm_delete_index = index

            if st.session_state.confirm_delete_index == index:
                st.warning(f"你确定要删除菜谱 `{recipe['中文名']}` 吗？这将无法恢复。", icon="⚠️")
                if st.button("✅ 确认删除", key=f"confirm_delete_{index}"):
                    deleted_recipe = recipes.pop(index)

                    # Remove associated main image
                    main_img = deleted_recipe.get("主图", "")
                    if main_img:
                        main_img_path = os.path.join("uploaded_images", main_img)
                        if os.path.exists(main_img_path):
                            os.remove(main_img_path)

                    # Remove associated step images
                    for step in deleted_recipe.get("步骤", []):
                        step_img = step.get("图片名", "")
                        if step_img:
                            step_img_path = os.path.join("uploaded_images", step_img)
                            if os.path.exists(step_img_path):
                                os.remove(step_img_path)
                                
                    save_recipes(recipes)
                    st.toast("已删除菜谱 ✅")
                    st.session_state.confirm_delete_index = None
                    st.rerun()