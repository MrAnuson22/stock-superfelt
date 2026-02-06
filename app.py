# ============================================================
# app.py
# ระบบ stock_superfelt
# ใช้ Google Sheet เป็นฐานข้อมูล
# ============================================================

# -----------------------------
# import ไลบรารีที่จำเป็น
# -----------------------------
import streamlit as st
import pandas as pd

# ใช้เชื่อม Google Sheet
import gspread

# ใช้ยืนยันตัวตนด้วย service account
from google.oauth2.service_account import Credentials


# -----------------------------
# ตั้งค่าหน้าเว็บ
# -----------------------------
st.set_page_config(
    page_title="stock_superfelt",
    page_icon="📦",
    layout="centered"
)


# ============================================================
# ส่วนตั้งค่า Google Sheet
# ============================================================

# ชื่อไฟล์ Google Sheet (ที่ลูกพี่สร้างไว้แล้ว)
SPREADSHEET_NAME = "stock_superfelt"


# ------------------------------------------------------------
# ฟังก์ชันเชื่อมต่อ Google Sheet
# ------------------------------------------------------------
def connect_gsheet():

    # ขอบเขตสิทธิ์ที่ใช้
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # ใช้ credentials จาก Streamlit secrets
    # (ตอน deploy เราจะเอา key ไปใส่ใน secrets)
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    # เปิดไฟล์ตามชื่อ
    sh = client.open(SPREADSHEET_NAME)

    return sh


# ============================================================
# ฟังก์ชันช่วยอ่านข้อมูลจาก worksheet → DataFrame
# ============================================================
def load_sheet_as_df(worksheet):

    data = worksheet.get_all_records()

    if len(data) == 0:
        return pd.DataFrame()

    return pd.DataFrame(data)


# ============================================================
# ฟังก์ชันเขียน DataFrame กลับไปที่ worksheet
# ============================================================
def save_df_to_sheet(worksheet, df):

    worksheet.clear()

    if len(df) == 0:
        return

    worksheet.update(
        [df.columns.values.tolist()] +
        df.values.tolist()
    )


# ============================================================
# ฟังก์ชันเตรียม worksheet ถ้ายังไม่มีให้สร้าง
# ============================================================
def get_or_create_worksheet(sh, title, headers):

    try:
        ws = sh.worksheet(title)
    except:
        ws = sh.add_worksheet(
            title=title,
            rows=1000,
            cols=len(headers)
        )
        ws.append_row(headers)

    return ws


# ============================================================
# เริ่มต้นโปรแกรม
# ============================================================

st.title("📦 stock_superfelt")
st.caption("ระบบจัดการสต๊อก เชื่อม Google Sheet")


# ============================================================
# เชื่อม Google Sheet
# ============================================================

sh = connect_gsheet()


# ============================================================
# เตรียมกระดานทั้งหมด (เรียงตามที่ลูกพี่ต้องการ)
# ============================================================

# -----------------------------
# 1) Stock Roll (พิเศษ)
# -----------------------------
roll_headers = [
    "รุ่นผลิตภัณฑ์",
    "หน้ากว้าง",
    "ความยาว",
    "คงเหลือ"
]

ws_roll = get_or_create_worksheet(
    sh,
    "Stock Roll",
    roll_headers
)

# -----------------------------
# 2) Stock Material
# -----------------------------
normal_headers = [
    "รหัส",
    "ชื่อรายการ",
    "คงเหลือ"
]

ws_material = get_or_create_worksheet(
    sh,
    "Stock Material",
    normal_headers
)

# -----------------------------
# 3) Stock Production
# -----------------------------
ws_production = get_or_create_worksheet(
    sh,
    "Stock Production",
    normal_headers
)

# -----------------------------
# 4) Stock Belt
# -----------------------------
ws_belt = get_or_create_worksheet(
    sh,
    "Stock Belt",
    normal_headers
)


# ============================================================
# เลือกกระดาน
# ============================================================

board_name = st.selectbox(
    "เลือกกระดาน",
    [
        "Stock Roll",
        "Stock Material",
        "Stock Production",
        "Stock Belt"
    ]
)


# ============================================================
# map ชื่อกระดาน → worksheet
# ============================================================

if board_name == "Stock Roll":
    ws = ws_roll
    headers = roll_headers
else:
    if board_name == "Stock Material":
        ws = ws_material
    elif board_name == "Stock Production":
        ws = ws_production
    else:
        ws = ws_belt

    headers = normal_headers


# ============================================================
# โหลดข้อมูลปัจจุบัน
# ============================================================

df = load_sheet_as_df(ws)


# ============================================================
# ------------------------------------------------------------
# ส่วนที่ 1 : แสดงรายการ (ต้องมาก่อน)
# ------------------------------------------------------------
# ============================================================

with st.container(border=True):

    st.subheader("📋 รายการทั้งหมด")

    if df.empty:
        st.info("ยังไม่มีข้อมูล")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


st.divider()


# ============================================================
# ------------------------------------------------------------
# ส่วนที่ 2 : เพิ่ม / แก้ไข
# ------------------------------------------------------------
# ============================================================

with st.container(border=True):

    st.subheader("➕ เพิ่ม / แก้ไขรายการ")

    # --------------------------------------------------------
    # กรณี Stock Roll (แบบพิเศษ)
    # --------------------------------------------------------
    if board_name == "Stock Roll":

        with st.form("form_roll", clear_on_submit=True):

            col1, col2 = st.columns(2)

            with col1:
                model = st.selectbox(
                    "รุ่นผลิตภัณฑ์",
                    ["NMY400", "NMY325", "NMY250", "NMY200", "NMY150"]
                )

                width = st.text_input("หน้ากว้าง")

            with col2:
                length = st.text_input("ความยาว")
                qty = st.number_input("คงเหลือ", min_value=0, step=1)

            submit = st.form_submit_button(
                "บันทึก",
                use_container_width=True
            )

            if submit:

                if width.strip() == "" or length.strip() == "":
                    st.warning("กรุณากรอกข้อมูลให้ครบ")
                else:

                    # ใช้ (รุ่น + หน้ากว้าง + ความยาว) เป็น key
                    if not df.empty:
                        mask = (
                            (df["รุ่นผลิตภัณฑ์"] == model) &
                            (df["หน้ากว้าง"] == width) &
                            (df["ความยาว"] == length)
                        )
                    else:
                        mask = pd.Series(dtype=bool)

                    if mask.any():
                        # แก้ไขของเดิม
                        df.loc[mask, "คงเหลือ"] = qty
                    else:
                        # เพิ่มใหม่
                        new_row = pd.DataFrame(
                            [[model, width, length, qty]],
                            columns=headers
                        )
                        df = pd.concat(
                            [df, new_row],
                            ignore_index=True
                        )

                    save_df_to_sheet(ws, df)
                    st.success("บันทึกเรียบร้อยแล้ว")
                    st.rerun()

    # --------------------------------------------------------
    # กรณีกระดานทั่วไป
    # --------------------------------------------------------
    else:

        with st.form("form_normal", clear_on_submit=True):

            col1, col2 = st.columns(2)

            with col1:
                code = st.text_input("รหัส")
                name = st.text_input("ชื่อรายการ")

            with col2:
                qty = st.number_input("คงเหลือ", min_value=0, step=1)

            submit = st.form_submit_button(
                "บันทึก",
                use_container_width=True
            )

            if submit:

                if code.strip() == "" or name.strip() == "":
                    st.warning("กรุณากรอกข้อมูลให้ครบ")
                else:

                    if not df.empty:
                        mask = df["รหัส"].astype(str) == str(code)
                    else:
                        mask = pd.Series(dtype=bool)

                    if mask.any():
                        df.loc[mask, ["ชื่อรายการ", "คงเหลือ"]] = [
                            name,
                            qty
                        ]
                    else:
                        new_row = pd.DataFrame(
                            [[code, name, qty]],
                            columns=headers
                        )

                        df = pd.concat(
                            [df, new_row],
                            ignore_index=True
                        )

                    save_df_to_sheet(ws, df)
                    st.success("บันทึกเรียบร้อยแล้ว")
                    st.rerun()


st.divider()


# ============================================================
# ------------------------------------------------------------
# ส่วนที่ 3 : ลบรายการ
# ------------------------------------------------------------
# ============================================================

with st.container(border=True):

    st.subheader("🗑 ลบรายการ")

    if df.empty:
        st.info("ยังไม่มีข้อมูล")
    else:

        # ----------------------------------------------------
        # กรณี Stock Roll
        # ----------------------------------------------------
        if board_name == "Stock Roll":

            # สร้าง label ให้เลือกง่าย
            df["__label__"] = (
                df["รุ่นผลิตภัณฑ์"].astype(str)
                + " | "
                + df["หน้ากว้าง"].astype(str)
                + " | "
                + df["ความยาว"].astype(str)
            )

            selected = st.selectbox(
                "เลือกรายการ",
                df["__label__"].tolist()
            )

            if st.button("ลบรายการนี้", use_container_width=True):

                df = df[df["__label__"] != selected]
                df = df.drop(columns=["__label__"])

                save_df_to_sheet(ws, df)
                st.success("ลบเรียบร้อยแล้ว")
                st.rerun()

        # ----------------------------------------------------
        # กรณีกระดานทั่วไป
        # ----------------------------------------------------
        else:

            selected = st.selectbox(
                "เลือกรหัส",
                df["รหัส"].astype(str).tolist()
            )

            if st.button("ลบรายการนี้", use_container_width=True):

                df = df[df["รหัส"].astype(str) != str(selected)]

                save_df_to_sheet(ws, df)
                st.success("ลบเรียบร้อยแล้ว")
                st.rerun()
