import os
import pandas as pd
import plotly.express as px
import streamlit as st

TITLE = "📊 Dashboard การจัดการขยะ"  # แก้ชื่อหัวข้อตรงนี้ให้ตรงกับข้อมูล
SOURCE = "https://data.go.th/dataset/gdpublish-69-dnp01-11-01"
DATA_FILE = "data.csv"
MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
          "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title(TITLE)
st.caption(f"แหล่งข้อมูล: {SOURCE}")


@st.cache_data
def load(path):
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("อ่านไฟล์ไม่ได้")


if not os.path.exists(DATA_FILE):
    st.error("ไม่พบไฟล์ data.csv")
    st.stop()

df = load(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]
for c in df.columns:
    if c == "ปี":
        df[c] = df[c].astype(str)

num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = [c for c in df.columns if c not in num_cols and df[c].nunique() > 1]


def idx(cols, key):
    for i, c in enumerate(cols):
        if key in c:
            return i
    return 0


# ---------- Sidebar widgets ----------
st.sidebar.header("ตัวกรอง")
fcol = st.sidebar.selectbox("กรองตามคอลัมน์", cat_cols, index=idx(cat_cols, "สังกัด"))
opts = sorted(df[fcol].dropna().astype(str).unique())
chosen = st.sidebar.multiselect("เลือกค่า", opts, default=opts)
if chosen:
    df = df[df[fcol].astype(str).isin(chosen)]

kpi_col = st.sidebar.selectbox("ตัวเลขสำหรับ KPI", num_cols)

# ---------- KPI ----------
c1, c2, c3 = st.columns(3)
c1.metric("จำนวนแถว", f"{len(df):,}")
c2.metric(f"ผลรวม {kpi_col}", f"{df[kpi_col].sum():,.1f}")
c3.metric(f"ค่าเฉลี่ย {kpi_col}", f"{df[kpi_col].mean():,.1f}")

with st.expander("ดูตารางข้อมูล"):
    st.dataframe(df, width="stretch")

# ---------- Chart 1: Bar ----------
st.subheader("กราฟที่ 1: เปรียบเทียบตามหมวดหมู่ (Bar chart)")
a, b, c, d = st.columns(4)
x = a.selectbox("หมวดหมู่", cat_cols, index=idx(cat_cols, "หน่วยงาน"))
y = b.selectbox("ค่าตัวเลข", num_cols, key="by")
agg = c.radio("การรวมค่า", ["sum", "mean"],
              format_func=lambda s: "ผลรวม" if s == "sum" else "ค่าเฉลี่ย", horizontal=True)
top = d.slider("แสดง Top N", 5, 30, 15)

g = df.groupby(x)[y].agg(agg).reset_index().nlargest(top, y)
fig1 = px.bar(g, x=y, y=x, orientation="h", color=y, color_continuous_scale="Blues")
fig1.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(350, top * 28))
st.plotly_chart(fig1)

# ---------- Chart 2: Line ----------
st.subheader("กราฟที่ 2: แนวโน้ม (Line chart)")
a, b, c = st.columns(3)
lx = a.selectbox("แกน X", cat_cols, index=idx(cat_cols, "เดือน"), key="lx")
ly = b.selectbox("ค่าตัวเลข", num_cols, index=min(1, len(num_cols) - 1), key="ly")
split = c.selectbox("แยกเส้นตาม", ["ไม่แยก"] + [k for k in cat_cols if k != lx])

keys = [lx] + ([] if split == "ไม่แยก" else [split])
g2 = df.groupby(keys, as_index=False)[ly].sum()
is_month = set(g2[lx].astype(str)) <= set(MONTHS)
if not is_month:
    g2 = g2.sort_values(lx)
fig2 = px.line(g2, x=lx, y=ly, color=None if split == "ไม่แยก" else split,
               markers=True, category_orders={lx: MONTHS} if is_month else None)
st.plotly_chart(fig2)
