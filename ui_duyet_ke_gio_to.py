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
        border-color: #1a5276 !important;
        color: #1a5276 !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #219150, #27ae60) !important;
        color: white !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_duyet_ke_gio_to(session):
  inject_custom_css()
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>BẢNG TỔNG HỢP GIỜ DẠY"
      f" CỦA TỔ {str(to_bm).upper()}</h4>",
      unsafe_allow_html=True,
  )
  st.write("")

  # Tải dữ liệu từ CSDL
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT magv, tengv, COALESCE(dinh_muc_tiet, 17)
            FROM giao_vien WHERE to_bo_mon = %s ORDER BY tengv
        """,
        (to_bm,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data_list = []
    for r in rows:
      magv, tengv, dinh_muc = r
      thuc_day = dinh_muc
      thay = 0
      bdhsg = 0
      chenh_lech = "+0"
      data_list.append({
          "Mã GV": magv,
          "Họ và Tên": tengv,
          "Định mức (tiết)": dinh_muc,
          "Tiết thực dạy": thuc_day,
          "Tiết dạy thay": thay,
          "Tiết BDHSG": bdhsg,
          "Thừa / Thiếu": chenh_lech,
      })

    if data_list:
      df_gio = pd.DataFrame(data_list)
      st.dataframe(df_gio, use_container_width=True, hide_index=True)
    else:
      st.info(f"Không có giáo viên nào trong Tổ {to_bm}.")

  except Exception as e:
    st.error(f"Lỗi tải bảng kê giờ: {e}")

  st.write("")
  c1, c2 = st.columns(2)
  with c1:
    if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
      st.rerun()
  with c2:
    if st.button(
        "✅ KÝ DUYỆT BẢNG KÊ GIỜ CỦA TỔ", type="primary", use_container_width=True
    ):
      st.success("Đã duyệt bảng kê giờ thành công!")