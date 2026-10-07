import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard ข้อมูลจาก data.go.th")
st.caption("แหล่งข้อมูล: https://data.go.th/dataset/gdpublish-69-dnp01-11-01")

DATA_FILE = "data.csv"  # วางไฟล์ CSV ไว้โฟลเดอร์เดียวกับ app.py


@st.cache_data
def load(src):
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            if hasattr(src, "seek"):
                src.seek(0)
            return pd.read_csv(src, encoding=enc)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise ValueError("อ่านไฟล์ไม่ได้")


if os.path.exists(DATA_FILE):
    df = load(DATA_FILE)
else:
    up = st.file_uploader("อัปโหลดไฟล์ CSV", type="csv")
    if up is None:
        st.info("ยังไม่มี data.csv — อัปโหลดไฟล์เพื่อเริ่มต้น")
        st.stop()
    df = load(up)

df.columns = [str(c).strip() for c in df.columns]
num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = [c for c in df.columns if c not in num_cols]

# ---------- Interactive widgets ----------
st.sidebar.header("ตัวกรอง")
if cat_cols:
    fcol = st.sidebar.selectbox("กรองตามคอลัมน์", cat_cols)
    opts = sorted(df[fcol].dropna().astype(str).unique())
    chosen = st.sidebar.multiselect("เลือกค่า", opts, default=opts[:10])
    if chosen:
        df = df[df[fcol].astype(str).isin(chosen)]

# ---------- KPI ----------
c1, c2, c3 = st.columns(3)
c1.metric("จำนวนแถว", f"{len(df):,}")
c2.metric("จำนวนคอลัมน์", len(df.columns))
if num_cols:
    c3.metric(f"ผลรวม {num_cols[0]}", f"{df[num_cols[0]].sum():,.0f}")

with st.expander("ดูตารางข้อมูล"):
    st.dataframe(df, use_container_width=True)

# ---------- Chart 1: Bar ----------
st.subheader("กราฟที่ 1: Bar chart")
if cat_cols:
    x = st.selectbox("แกน X (หมวดหมู่)", cat_cols, key="bx")
    if num_cols:
        y = st.selectbox("แกน Y (ค่าตัวเลข)", num_cols, key="by")
        g = df.groupby(x, as_index=False)[y].sum().nlargest(20, y)
    else:
        g = df[x].value_counts().head(20).reset_index()
        g.columns = [x, "count"]
        y = "count"
    st.plotly_chart(px.bar(g, x=x, y=y, color=y), use_container_width=True)

# ---------- Chart 2: Line / Histogram ----------
st.subheader("กราฟที่ 2: Line / Histogram")
if num_cols:
    kind = st.radio("ชนิดกราฟ", ["Histogram", "Line"], horizontal=True)
    v = st.selectbox("คอลัมน์ตัวเลข", num_cols, key="v")
    if kind == "Histogram":
        fig = px.histogram(df, x=v, nbins=30)
    else:
        xcol = st.selectbox("แกน X", df.columns.tolist(), key="lx")
        fig = px.line(df.sort_values(xcol), x=xcol, y=v)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("ไม่พบคอลัมน์ตัวเลขสำหรับกราฟที่ 2")
