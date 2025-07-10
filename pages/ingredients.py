import streamlit as st

st.set_page_config(page_title="食材数据库", layout="centered")

import pandas as pd
import os
from datetime import datetime
import unicodedata #for weChat pasting

from helper_functions import compute_unit_cost

# File Name for database
DATA_FILE = "ingredients.csv"

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
    
# -- Show More recent first 
filtered_df = filtered_df.sort_values("创建时间", ascending=False)
display_df = filtered_df.drop(columns=["创建时间"])
st.dataframe(display_df)

