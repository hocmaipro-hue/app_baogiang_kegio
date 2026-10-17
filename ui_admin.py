from datetime import datetime, timedelta
import tempfile
import pandas as pd
import psycopg2
import streamlit as st
from config import DB_URI
from doc_tkb import kiem_tra_tuan_ton_tai, nap_tkb_tu_excel, xoa_toan_bo_tkb


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
        border-color: #3182ce !important;
        color: #3182ce !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }
    /* Nút chính Primary tròn nổi bật */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #219150, #27ae60) !important;
        color: white !important;
    }
    /* Đổi góc bo các ô input/selectbox trên mobile */
    .stTextInput input, .stSelectbox div, .stNumberInput input, .stDateInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def ensure_cau_hinh_table():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS cau_hinh (khoa VARCHAR(50) PRIMARY"
        " KEY, gia_tri TEXT);"
    )
    conn.commit()
    cur.close()
    conn.close()
  except Exception:
    pass


def load_ngay_bat_dau():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'"
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
      return row[0]
  except Exception:
    pass
  return "2026-09-07"


def render_admin_dashboard(session):
  inject_custom_css()
  ensure_cau_hinh_table()
  tengv = get_val(session, "tengv", "Quản trị viên")

  # Banner tiêu đề
  st.markdown(
      f"""
    <div style="background: linear-gradient(135deg, #ffffff, #f8f9fa); padding: 16px; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
        <h3 style="color: #b03a2e; margin: 0 0 6px 0; font-size: 18px;">TRUNG TÂM QUẢN TRỊ TOÀN TRƯỜNG - BGH</h3>
        <p style="color: #4a5568; font-size: 13px; margin: 0;">Xin chào: <b>{tengv}</b> &nbsp;|&nbsp; Quyền hạn: BGH/ADMIN</p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # Khối 1: Công việc cá nhân
  st.markdown("##### 📌 Công Việc Giảng Dạy Cá Nhân")
  col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
  with col1:
    if st.button("📅 TKB Cá Nhân", use_container_width=True):
      st.session_state.current_page = "xem_tkb"
      st.rerun()
  with col2:
    if st.button("📖 Sổ Báo Giảng", use_container_width=True):
      st.session_state.current_page = "so_bao_giang"
      st.rerun()
  with col3:
    if st.button("📊 Kê Khai Giờ", use_container_width=True):
      st.session_state.current_page = "pkg"
      st.rerun()
  with col4:
    if st.button("📝 Biến Động Lịch", use_container_width=True):
      st.session_state.current_page = "bien_dong"
      st.rerun()
  with col5:
    if st.button("🔑 Đổi Mật Khẩu", use_container_width=True):
      st.session_state.current_page = "doi_mat_khau"
      st.rerun()

  st.divider()

  # Khối 2: Cấu hình năm học
  st.markdown("##### ⚙️ Cài Đặt Thông Số Năm Học")
  c1, c2 = st.columns([3, 2])
  default_date_str = load_ngay_bat_dau()
  try:
    default_date = datetime.strptime(default_date_str, "%Y-%m-%d").date()
  except Exception:
    default_date = datetime.strptime("2026-09-07", "%Y-%m-%d").date()

  with c1:
    ngay_bd_input = st.date_input(
        "Ngày bắt đầu năm học (Thứ 2 Tuần 1):", value=default_date
    )
  with c2:
    st.write("")
    st.write("")
    if st.button("💾 Lưu Cài Đặt", type="primary", use_container_width=True):
      ngay_str = ngay_bd_input.strftime("%Y-%m-%d")
      try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(
            """
                    INSERT INTO cau_hinh (khoa, gia_tri) VALUES ('ngay_bat_dau_nam_hoc', %s)
                    ON CONFLICT (khoa) DO UPDATE SET gia_tri = EXCLUDED.gia_tri
                """,
            (ngay_str,),
        )
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"Đã lưu ngày bắt đầu năm học: {ngay_str}")
      except Exception as e:
        st.error(f"Không thể lưu cấu hình: {e}")

  st.divider()

  # Khối 3: Quản trị nhân sự
  st.markdown("##### 👥 Quản Lý Nhân Sự & Giám Sát Chuyên Môn")
  q1, q2 = st.columns(2)
  with q1:
    if st.button("👥 Quản lý Giáo viên (Excel)", use_container_width=True):
      st.session_state.current_page = "quan_ly_gv"
      st.rerun()
  with q2:
    if st.button("📝 Giám sát Đơn Nghỉ / Dạy Bù", use_container_width=True):
      st.session_state.current_page = "admin_quan_ly_bien_dong"
      st.rerun()

  if st.button(
      "📈 Bảng Thống Kê & Đối Chiếu Giờ Dạy Toàn Trường",
      use_container_width=True,
  ):
    st.session_state.current_page = "admin_thong_ke_gio"
    st.rerun()

  st.divider()

  # Khối 4: TKB
  st.markdown("##### 📅 Nhập / Xóa Thời Khóa Biểu Excel")
  if st.button("🗑️ XÓA SẠCH TOÀN BỘ TKB TRÊN SERVER", use_container_width=True):
    if st.checkbox("Xác nhận xóa TKB?", key="confirm_del_tkb"):
      try:
        success, msg = xoa_toan_bo_tkb()
        if success:
          st.success(msg)
        else:
          st.error(msg)
      except Exception as e:
        st.error(f"Lỗi: {e}")

  st.markdown("---")
  col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
  with col_t1:
    uploaded_file = st.file_uploader(
        "Chọn file Excel TKB", type=["xlsx", "xls"]
    )
  with col_t2:
    tuan_val = st.number_input(
        "Áp dụng Tuần:", min_value=1, max_value=45, value=1
    )
  with col_t3:
    base_dt = ngay_bd_input
    ngay_ad_calc = base_dt + timedelta(days=(int(tuan_val) - 1) * 7)
    ngay_ad_input = st.date_input("Từ Ngày:", value=ngay_ad_calc)

  if st.button(
      "📥 Tiến hành Import TKB", type="primary", use_container_width=True
  ):
    if not uploaded_file:
      st.warning("Vui lòng chọn file Excel TKB!")
    else:
      so_tiet_cu = kiem_tra_tuan_ton_tai(int(tuan_val))
      if so_tiet_cu > 0:
        st.warning(f"⚠️ Tuần {tuan_val} đã có {so_tiet_cu} tiết học trong CSDL!")

      with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

      try:
        with st.spinner(f"Đang Import Tuần {tuan_val}..."):
          kq = nap_tkb_tu_excel(
              tmp_path,
              ap_dung_tu_tuan=int(tuan_val),
              ap_dung_tu_ngay=ngay_ad_input.strftime("%Y-%m-%d"),
          )
          success, msg = (
              kq
              if isinstance(kq, tuple)
              else (True, f"Bóc tách thành công Tuần {tuan_val}!")
          )
          if success:
            st.success(msg)
          else:
            st.error(msg)
      except Exception as e:
        st.error(f"Lỗi Import: {e}")