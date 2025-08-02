import streamlit as st
import pandas as pd
from datetime import datetime
import os, json
from helper_functions import save_uploaded_file

# --- INITIALIZE STATE ---
if "mode" not in st.session_state:
    st.session_state.mode = "new"  # "new" or "edit"

if "edit_recipe" not in st.session_state:
    st.session_state.edit_recipe = None
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []
if "steps" not in st.session_state:
    st.session_state.steps = []

# On entering in edit mode, populate fields; else start fresh
if st.session_state.mode == "edit" and st.session_state.edit_recipe:
    recipe = st.session_state.edit_recipe
else:
    recipe = None

# --- PAGE CONFIG ---
st.set_page_config(page_title="新增菜谱")
st.title("🍽️ 新增 / 编辑 菜谱")

# --- SWITCH TO NEW MODE ---
if st.session_state.mode == "edit":
    if st.button("🆕 新建菜谱"):
        st.session_state.mode = "new"
        st.session_state.edit_recipe = None
        st.session_state.ingredients = []
        st.session_state.steps = []
        st.experimental_rerun()

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
    category = st.selectbox(
        "分类",
        options=[""] + sorted(df_ing["食材分类"].dropna().unique().tolist()),
        index=(
            ([""] + sorted(df_ing["食材分类"].dropna().unique().tolist())).index(recipe["分类"])
            if recipe else 0
        )
    )
    price = st.number_input("售价 (¥)", value=recipe["售价"] if recipe else 0.0, min_value=0.0, step=0.5)
    notes = st.text_area("备注", value=recipe["备注"] if recipe else "")
with col2:
    img = st.file_uploader("主图（选填）", type=["jpg", "png"])
    main_img = recipe["主图"] if recipe else ""
    if img:
        if name_en.strip():
            main_img = save_uploaded_file(img, f"{name_en.strip()}_main")
        else:
            st.warning("请输入英文名后再上传图片")

# --- ADD INGREDIENT FORM ---
with st.expander("🧂 添加食材"):
    ing_cat = st.selectbox("食材分类筛选", options=[""] + sorted(df_ing["食材分类"].dropna().unique().tolist()))
    df_filt = df_ing[df_ing["食材分类"] == ing_cat] if ing_cat else df_ing
    choices = df_filt["编号"].tolist()
    labels = [f"{r['食材中文名']} ({r['编号']})" for _, r in df_filt.iterrows()]
    sel = st.selectbox("选择食材", options=[""] + labels)
    qty = st.number_input("用量 (g/ml)", min_value=0.0, step=1.0, key="qty")
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
            st.session_state.qty = 0.0
            st.session_state.ing_note = ""

# --- DISPLAY CURRENT INGREDIENTS ---
if st.session_state.ingredients:
    st.table(pd.DataFrame(st.session_state.ingredients))

# --- ADD STEP FORM ---
with st.expander("📷 添加步骤"):
    desc = st.text_area("步骤描述", key="step_desc")
    step_img = st.file_uploader("步骤图片(选填)", type=["jpg", "png"], key="step_img")
    if st.button("➕ 添加步骤"):
        img_name = ""
        if step_img:
            img_name = save_uploaded_file(step_img, f"{name_en}_step_{len(st.session_state.steps)+1}")
        st.session_state.steps.append({"描述": desc, "图片名": img_name})
        st.success("步骤已添加")
        st.session_state.step_desc = ""
        st.session_state.step_img = None

# --- DISPLAY STEPS ---
for i, s in enumerate(st.session_state.steps):
    st.markdown(f"**步骤 {i+1}:** {s['描述']}")

# --- SAVE RECIPE ---
if st.button("✅ 保存菜谱"):
    if not (name_en and name_zh and st.session_state.ingredients and st.session_state.steps and price > 0):
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
            "SKUID": recipe.get("SKUID", "") if recipe else ""
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
        st.experimental_rerun()
