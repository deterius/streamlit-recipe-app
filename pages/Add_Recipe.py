import streamlit as st
import pandas as pd
from datetime import datetime
import os, json
from helper_functions import save_uploaded_file

# --- INITIALIZE STATE ---
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "edit_recipe" not in st.session_state:
    st.session_state.edit_recipe = None
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []
if "steps" not in st.session_state:
    st.session_state.steps = []

# On entering edit mode, populate fields and session_state
if st.session_state.edit_mode and st.session_state.edit_recipe:
    recipe = st.session_state.edit_recipe

    # Populate ingredients only once when page first loads
    if not st.session_state.ingredients:
        st.session_state.ingredients = recipe.get("食材", [])

    if not st.session_state.steps:
        st.session_state.steps = recipe.get("步骤", [])
else:
    recipe = None

# --- PAGE CONFIG ---
st.set_page_config(page_title="新增菜谱")
st.title("🍽️ 新增 / 编辑 菜谱")
# --- CLEAR ALL FIELDS BUTTON ---
if st.button("🧹 清空所有字段，开始新建菜谱", type="primary"):
    st.session_state.edit_mode = False
    st.session_state.edit_recipe = None
    st.session_state.mode = "new"
    st.session_state.ingredients = []
    st.session_state.steps = []
    st.rerun()

# --- SWITCH TO NEW MODE ---
if st.session_state.get("mode") == "edit":
    if st.button("🆕 新建菜谱"):
        st.session_state.mode = "new"
        st.session_state.edit_recipe = None
        st.session_state.ingredients = []
        st.session_state.steps = []
        st.rerun()

# --- LOAD DATABASES ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ING_FILE = os.path.join(BASE_DIR, "ingredients.csv")
REC_FILE = os.path.join(BASE_DIR, "recipes.json")
df_ing = pd.read_csv(ING_FILE)
df_ing["基础单位价格"] = pd.to_numeric(df_ing["基础单位价格"], errors="coerce")

# --- RECIPE INFO ---
col1, col2 = st.columns(2)
with col1:
    name_en = st.text_input("英文名", value=recipe["英文名"] if recipe else "")
    name_zh = st.text_input("中文名", value=recipe["中文名"] if recipe else "")
    CATEGORIES = [
        "BBQ/烤肉", "Seafood/海鲜", "Soups/汤", "Appetizers/小吃", 
        "Late Night Snacks/下酒菜", "Semi-finished/半成品", 
        "Small dishes/小菜", "Bento/便当"
    ]
    category = st.selectbox(
        "菜单分类", CATEGORIES,
        index=CATEGORIES.index(recipe["分类"]) if recipe and recipe.get("分类") in CATEGORIES else 0
    )
    price = st.number_input("售价 (¥)", value=recipe["售价"] if recipe else 0.0, min_value=0.0, step=0.5)
    notes = st.text_area("备注", value=recipe["备注"] if recipe else "")
    skuid = st.text_input("SKUID", value=recipe.get("SKUID", "") if recipe else "")
with col2:
    img = st.file_uploader("主图（选填）", type=["jpg", "png"])
    
    # Use existing image if editing
    main_img = recipe["主图"] if recipe else ""

    # Save new uploaded image
    if img:
        if name_en.strip():
            main_img = save_uploaded_file(img, f"{name_en.strip()}_main")
        else:
            st.warning("请输入英文名后再上传图片")

    # Display preview if there's a main image path
    if main_img:
        img_path = os.path.join("uploaded_images", main_img)
        if os.path.exists(img_path):
            st.image(img_path, width=250, caption="主图预览")
        else:
            st.warning("⚠️ 找不到主图文件")

# --- ADD INGREDIENT FORM ---
with st.expander("🧂 添加食材"):
    ing_cat = st.selectbox("食材分类筛选", options=[""] + sorted(df_ing["食材分类"].dropna().unique().tolist()))
    df_filt = df_ing[df_ing["食材分类"] == ing_cat] if ing_cat else df_ing
    choices = df_filt["编号"].tolist()
    labels = [f"{r['食材中文名']} ({r['编号']})" for _, r in df_filt.iterrows()]
    sel = st.selectbox("选择食材", options=[""] + labels)
    qty = st.number_input("用量 (g/ml)", min_value=0.0, step=1.0, key="ing_qty")
    note = st.text_input("备注（选填）", key="ing_note")
    if st.button("➕ 添加食材"):
        if sel and qty > 0:
            code = sel.split("(")[-1].strip(")")
            row = df_ing[df_ing["编号"] == code].iloc[0]
            subtotal = qty * row["基础单位价格"]
            st.session_state.ingredients.append({
                "编号": code, "食材中文名": row["食材中文名"],
                "用量": qty, "单价": row["基础单位价格"],
                "小计": subtotal, "备注": note
            })
            st.success(f"添加: {row['食材中文名']} x{qty}g")
            st.rerun()

# --- DISPLAY CURRENT INGREDIENTS ---
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.ingredients:
        st.markdown("### 当前食材")

        df_ing_table = pd.DataFrame(st.session_state.ingredients)

        edited_df = st.data_editor(
            df_ing_table,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "编号": st.column_config.TextColumn(disabled=True),
                "食材中文名": st.column_config.TextColumn(disabled=True),
                "单价": st.column_config.NumberColumn(disabled=True, format="%.4f"),
                "小计": st.column_config.NumberColumn(disabled=True, format="%.2f"),
                "用量": st.column_config.NumberColumn(step=1.0, format="%.1f"),
                "备注": st.column_config.TextColumn(),
                "基础单位价格": st.column_config.NumberColumn(disabled=True, format="%.4f"),
                
            },
            key="editable_ingredients"
        )
        st.session_state.ingredients = edited_df.to_dict("records")
with col2:
        st.markdown("### 🗑️ 删除单个食材")
        for i, ing in enumerate(st.session_state.ingredients):
            cols = st.columns([6, 1])
            cols[0].text(f"🧂 {ing['食材中文名']} (用量: {ing['用量']}g)")
            if cols[1].button("❌", key=f"del_ing_{i}"):
                st.session_state.ingredients.pop(i)
                st.rerun()

       

# --- ADD STEP FORM ---
with st.expander("📷 添加步骤"):
    step_desc = st.text_area("步骤描述")
    step_img = st.file_uploader("步骤图片(选填)", type=["jpg", "png"])
    if st.button("➕ 添加步骤"):
        img_name = ""
        if step_img:
            img_name = save_uploaded_file(step_img, f"{name_en}_step_{len(st.session_state.steps)+1}")
        st.session_state.steps.append({"描述": step_desc, "图片名": img_name})
        st.success("步骤已添加")
        st.rerun()

    
# --- DISPLAY & EDIT STEPS ---
st.markdown("### 📝 当前步骤列表")
for i, step in enumerate(st.session_state.steps):
    st.markdown(f"**步骤 {i+1}**")

    with st.form(f"edit_step_form_{i}", clear_on_submit=False):
        edited_desc = st.text_area("描述", value=step["描述"], key=f"step_desc_{i}")
        new_img = st.file_uploader("替换步骤图片（可选）", type=["jpg", "png"], key=f"step_img_{i}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if col1.form_submit_button("💾 更新步骤"):
                st.session_state.steps[i]["描述"] = edited_desc
                if new_img:
                    img_name = save_uploaded_file(new_img, f"{name_en}_step_{i+1}")
                    st.session_state.steps[i]["图片名"] = img_name
                st.success("步骤已更新 ✅")
                st.rerun()
        with col2:
            if col2.form_submit_button("❌ 删除此步骤"):
                st.session_state.steps.pop(i)
                st.success("步骤已删除 🗑️")
                st.rerun()

    # Preview image
    if step.get("图片名"):
        st.image(os.path.join("uploaded_images", step["图片名"]), width=250, caption=f"步骤 {i+1} 图片")

# --- SAVE RECIPE ---
if st.button("✅ 保存菜谱"):
    if not (name_en and name_zh and st.session_state.ingredients and price > 0):
        st.warning("请填写完整：中英文名、至少一个食材、步骤、售价")
    else:
        recs = json.load(open(REC_FILE, encoding="utf-8")) if os.path.exists(REC_FILE) else []
        rid = recipe["编号"] if recipe else f"RC-{len(recs)+1:04d}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new = {
            "编号": rid, "英文名": name_en, "中文名": name_zh, "分类": category,
            "售价": price, "总成本": round(sum(i["小计"] for i in st.session_state.ingredients), 2),
            "成本百分比": round(sum(i["小计"] for i in st.session_state.ingredients)/price*100,2),
            "食材": st.session_state.ingredients, "步骤": st.session_state.steps,
            "备注": notes, "主图": main_img, "创建时间": recipe["创建时间"] if recipe else now, "修改时间": now,
            "SKUID": skuid
        }
        if recipe:
            idx = next(i for i,r in enumerate(recs) if r["编号"] == rid)
            recs[idx] = new
        else:
            recs.append(new)
        json.dump(recs, open(REC_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        st.success("✅ 保存成功！")
        st.session_state.mode = "new"
        st.session_state.ingredients = []
        st.session_state.steps = []

        import time
        time.sleep(1)  # optional: short delay to show success

        st.switch_page("pages/All_Recipes.py")