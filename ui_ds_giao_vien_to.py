import pandas as pd
import psycopg2
import streamlit as st
from config import DB_URI


def inject_custom_css():
  st.markdown(
      """
    <style>
    /* CSS Nút tròn mềm mại chuẩn Mobile & Desktop */
    div.stButton > button {
        border-radius: 24px !important;
        border: 1px solid #d0d7de !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.25s ease-in-out !important;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.06) !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.12) !important;
        border-color: #1c2833 !important;
        color: #1c2833 !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1c2833, #2c3e50) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2c3e50, #34495e) !important;
        color: white !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_ds_giao_vien_to(session):
  inject_custom_css()
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #1c2833;'>DANH SÁCH GIÁO VIÊN -"
      f" TỔ: {str(to_bm).upper()}</h4>",
      unsafe_allow_html=True,
  )

  # Nút tải lại danh sách
  c1, c2, c3 = st.columns([2, 1, 2])
  with c2:
    if st.button("🔄 Tải lại", type="primary", use_container_width=True):
      st.rerun()

  st.write("")

  # Tải dữ liệu từ CSDL
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT magv, tengv, role, COALESCE(chuc_vu, ''), COALESCE(dinh_muc_tiet, 0)
            FROM giao_vien 
            WHERE to_bo_mon = %s 
            ORDER BY magv ASC
        """,
        (to_bm,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
      df_gv = pd.DataFrame(
          rows,
          columns=[
              "Mã GV",
              "Họ và Tên",
              "Vai trò",
              "Chức vụ",
              "Định mức tiết",
          ],
      )
      st.dataframe(df_gv, use_container_width=True, hide_index=True)
    else:
      st.info(f"Chưa có giáo viên nào trong Tổ {to_bm}.")

  except Exception as e:
    st.error(f"Không thể tải danh sách GV tổ: {e}")