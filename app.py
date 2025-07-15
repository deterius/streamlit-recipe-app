import streamlit as st
import pandas as pd
import os
from datetime import datetime
import unicodedata #for weChat pasting

from helper_functions import compute_unit_cost

st.set_page_config(page_title="食材数据库", layout="wide")


pages = {
    "🥬 Ingredients": [
        st.Page("pages/All_Ingredients.py", title="View Ingredients"),
        st.Page("pages/Add_Ingredient.py", title="Add Ingredient"),
    ],
    "📖 Recipes": [
        st.Page("pages/All_Recipes.py", title="All Recipes"),
        st.Page("pages/Add_Recipe.py", title="Add Recipe"),
    ],
}

pg = st.navigation(pages)
pg.run()

# # File Name for database
# DATA_FILE = "ingredients.csv"

# # Column names (in Chinese)
# COLUMNS = [
#     "编号",          # Reference Number
#     "供应商",        # Supplier
#     "食材英文名",    # Ingredient En
#     "食材中文名",    # Ingredient ZH
#     "食材分类",      # Type
#     "单位",          # Unit
#     "单位价格",      # Cost per Unit
#     "单位容量",      # Volume per Unit
#     "基础单位价格",    # Base unit cost
#     "创建时间",      # Date Created
#     "修改时间"       # Date Modified
# ]

# # Category to prefix mapping
# CATEGORY_PREFIX = {
#     "未加工肉类": "RME",
#     "加工肉类": "PME",
#     "海鲜类": "SEA",
#     "冻品类": "FRZ",
#     "调味品": "CON",
#     "干货": "DRY",
#     "蔬菜": "VEG",
#     "预制品": "PRE",
#     "厨房用品": "KTC"
# }

# # Create if no DB exists
# if not os.path.exists(DATA_FILE):
#     pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)
    
# # Load existing if exists
# df = pd.read_csv(DATA_FILE)

# st.title("🥬 食材数据库")
# st.markdown("Rourou Nanshan")

# st.subheader("📋 当前食材列表")
# # -- Filtering sidebar or inline
# col1, col2 = st.columns(2)
# with col1:
#     selected_type = st.selectbox("筛选：按食材分类", ["全部"] + list(CATEGORY_PREFIX.keys()))
# with col2:
#     search_text = st.text_input("搜索食材（中英文）")

# # -- Apply filters to DF
# filtered_df = df.copy()
# if selected_type != "全部":
#     filtered_df = filtered_df[filtered_df["食材分类"] == selected_type]
    
# # Strip everything from the search and make sure its compatiable with WeChat
# search_text = unicodedata.normalize("NFKC", search_text.strip())

# if search_text:
#     filtered_df = filtered_df[
#         filtered_df["食材中文名"].astype(str).str.contains(search_text, case=False, na=False) |
#         filtered_df["食材英文名"].astype(str).str.contains(search_text, case=False, na=False)
#     ]
    
# # -- Show More recent first 
# filtered_df = filtered_df.sort_values("创建时间", ascending=False)
# st.dataframe(filtered_df)

# # -- 1. Pick unit outside of the form to trigger re-run
# if "unit_selected" not in st.session_state:
#     st.session_state.unit_selected = "g"
    
# st.session_state.unit_selected = st.selectbox(
#     "单位",
#     ["g", "kg", "ml", "L", "个", "盒", "瓶", "包", "斤", "其他"],
#     key="unit_selectbox"
# )


# #Add new ingredients
# with st.form("ingredient_form"):
#     supplier = st.text_input("供应商", key="supplier_input")
#     name_en = st.text_input("食材英文名", key="name_en_input")
#     name_zh = st.text_input("食材中文名", key="name_zh_input")
    
#     type_options= list(CATEGORY_PREFIX.keys())
    
#     food_type = st.selectbox("食材分类", type_options, key="type_selectbox")
#     cost = st.number_input("单位价格", min_value=0.0, format="%.4f", key="cost_input")
    
#     volume = ""
#     if st.session_state.unit_selected in ["盒", "瓶", "包"]:
#         volume = st.text_input("单位容量（请输入数字，单位为 g 或 ml）", key="volume_input")
        
#     # - Check if the format is correct
#     if st.session_state.unit_selected in ["盒", "瓶", "包"] and not volume.strip().isdigit():
#         st.error("请输入一个整数，例如 1000，单位为 g 或 ml。")
#     # -- Preview for bottles, boxes and such
#     try_preview = None
#     if st.session_state.unit_selected in ["盒", "瓶", "包", "kg", "L", "斤"] and cost > 0:
#         if st.session_state.unit_selected in ["盒", "瓶", "包"]:
#             if volume.strip().isdigit():
#                 try_preview = compute_unit_cost(st.session_state.unit_selected, cost, volume)
#         else:
#             try_preview = compute_unit_cost(st.session_state.unit_selected, cost, volume)

#     if try_preview is not None:
#         st.info(f"自动计算基础单位价格：¥{try_preview:.4f} / g 或 ml")

        
#     submitted = st.form_submit_button("添加食材")
    
    
    
#     if submitted:
#         # check for duplicates
#         if not name_en or not name_zh:
#             st.warning("请输入食材中英文名。")
#         elif((df["食材中文名"]== name_zh)).any():
#             st.warning("该食材已经存在。")
#         else:
#             now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             #Generate ref number based on category
#             prefix = CATEGORY_PREFIX.get(food_type, "UNK")
#             existing = df[df["食材分类"] == food_type]
#             next_num = len(existing) + 1
#             ref_number = f"{prefix}-{next_num:04d}"
#             normalized_cost = compute_unit_cost(st.session_state.unit_selected, cost, volume)
            
#             new_row = pd.DataFrame([[
#                 ref_number, supplier, name_en, name_zh, food_type,
#                 st.session_state.unit_selected, cost, volume, normalized_cost, now, now
#             ]], columns=COLUMNS)
            
#             new_row.to_csv(DATA_FILE, mode="a", header=False, index=False)
#             st.success(f"成功添加：{name_zh} / {name_en}（编号：{ref_number}）")
            
#             # reset to empyt fields
#             st.session_state["supplier_input"] = ""
#             st.session_state["name_en_input"] = ""
#             st.session_state["name_zh_input"] = ""
#             st.session_state["type_selectbox"] = list(CATEGORY_PREFIX.keys())[0]
#             st.session_state["cost_input"] = 0.0
#             if "volume_input" in st.session_state:
#                 st.session_state["volume_input"] = ""
#             st.experimental_rerun()