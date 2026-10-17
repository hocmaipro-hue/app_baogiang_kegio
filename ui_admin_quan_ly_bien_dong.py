import pandas as pd
import psycopg2
import streamlit as st
from config import DB_URI


def inject_custom_css():
  st.markdown(
      """
    <style>
    div.stButton > button {
        border-radius: 24px !important;
        border: 1px solid #d0d7de !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def ensure_column_gv_day_thay():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS gv_day_thay"
        " VARCHAR(100);"
    )
    conn.commit()
    cur.close()
    conn.close()
  except Exception:
    pass


def get_to_bo_mon_list():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT to_bo_mon FROM giao_vien WHERE to_bo_mon IS NOT NULL"
    )
    tos = ["Tất cả"] + [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return tos
  except Exception:
    return ["Tất cả"]


def render_admin_quan_ly_bien_dong(session):
  inject_custom_css()
  ensure_column_gv_day_thay()

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>GIÁM SÁT & QUẢN LÝ"
      " LỊCH NGHỈ / DẠY BÙ TOÀN TRƯỜNG</h4>",
      unsafe_allow_html=True,
  )

  f1, f2, f3 = st.columns([2, 2, 1])
  with f1:
    tos = get_to_bo_mon_list()
    to_sel = st.selectbox("Tổ bộ môn:", options=tos)
  with f2:
    loai_options = [
        "Tất cả",
        "Nghỉ dạy",
        "Dạy bù",
        "Dạy thay",
        "Bồi dưỡng HSG",
    ]
    loai_sel = st.selectbox("Loại việc:", options=loai_options)
  with f3:
    st.write("")
    st.write("")
    if st.button("🔄 Tải lại", use_container_width=True):
      st.rerun()

  try:
    conn = psycopg2.connect(DB_URI)
    sql = """
            SELECT b.id, b.magv, g.tengv, g.to_bo_mon, b.loai, b.ngay, b.buoi, 
                   b.tiet_tkb, COALESCE(b.lop,''), COALESCE(b.gv_day_thay,''), 
                   COALESCE(b.ly_do,''), b.trang_thai
            FROM bien_dong_lich_day b
            LEFT JOIN giao_vien g ON b.magv = g.magv
            WHERE 1=1
        """
    params = []
    if to_sel != "Tất cả":
      sql += " AND g.to_bo_mon = %s"
      params.append(to_sel)
    if loai_sel != "Tất cả":
      sql += " AND b.loai = %s"
      params.append(loai_sel)

    sql += " ORDER BY b.ngay DESC, b.tiet_tkb ASC"

    df = pd.read_sql(sql, conn, params=params)
    conn.close()
  except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    df = pd.DataFrame()

  if not df.empty:
    df.columns = [
        "ID",
        "Mã GV",
        "Họ và Tên",
        "Tổ",
        "Loại việc",
        "Ngày",
        "Buổi",
        "Tiết",
        "Lớp",
        "GV dạy thay",
        "Lý do",
        "Trạng thái",
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("##### 🗑️ Xóa đơn báo cáo sai")
    c_id, c_btn = st.columns([2, 1])
    with c_id:
      rec_id_del = st.number_input(
          "Nhập ID dòng cần xóa:", min_value=1, step=1
      )
    with c_btn:
      st.write("")
      st.write("")
      if st.button(
          "Xóa báo cáo này", type="primary", use_container_width=True
      ):
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()
          cur.execute(
              "DELETE FROM bien_dong_lich_day WHERE id = %s", (int(rec_id_del),)
          )
          conn.commit()
          cur.close()
          conn.close()
          st.success(f"Đã xóa thành công ID {rec_id_del}!")
          st.rerun()
        except Exception as e:
          st.error(f"Không thể xóa: {e}")
  else:
    st.info("Không tìm thấy dữ liệu phù hợp.")