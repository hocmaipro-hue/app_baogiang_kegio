import streamlit as st
from ui_admin_thong_ke_gio import render_admin_thong_ke_gio
from ui_bien_dong_lich_day import render_bien_dong_lich_day
from ui_doi_mat_khau import render_doi_mat_khau
from ui_quan_ly_giao_vien import render_quan_ly_giao_vien
from ui_quan_ly_ppct import render_quan_ly_ppct
from ui_so_bao_giang_ca_nhan import render_so_bao_giang_ca_nhan

# Import các module giao diện đã được chuyển đổi sang Streamlit
try:
  from ui_xem_tkb import render_xem_tkb
except ImportError:
  render_xem_tkb = None

try:
  from ui_duyet_so_bao_giang import render_duyet_so_bao_giang
except ImportError:
  render_duyet_so_bao_giang = None


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
    .stRadio label {
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_to_truong_dashboard(session):
  inject_custom_css()
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Chuyên môn")

  # Sidebar menu điều hướng
  with st.sidebar:
    st.markdown(
        f"<h3 style='color: #1a5276;'>Xin chào:</h3><h4>{tengv} [TỔ"
        " TRƯỜNG]</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color: #555; font-style: italic;'>Tổ bộ môn: {to_bm}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("##### 📖 CÔNG VIỆC CÁ NHÂN")
    menu_canhan = [
        "📅 1. Xem Thời khóa biểu",
        "📝 2. Đăng ký Biến động (Nghỉ/Bù/Thay/HSG)",
        "📖 3. Quản lý Sổ Báo Giảng cá nhân",
    ]

    st.markdown("##### 👥 QUẢN LÝ CHUYÊN MÔN CỦA TỔ")
    menu_to = [
        "📚 4. Quản lý Phân phối chương trình (PPCT)",
        "👥 5. Duyệt Sổ Báo Giảng & Nghỉ bù của Tổ",
        "📊 6. Thống Kê & Đối Chiếu Giờ Dạy Của Tổ",
        "👥 7. Quản lý DS Giáo viên trong Tổ",
        "🔑 8. Đổi mật khẩu cá nhân",
    ]

    selected_menu = st.radio(
        "CHỌN CHỨC NĂNG THAO TÁC:", options=menu_canhan + menu_to
    )

    st.divider()
    if st.button(
        "🚪 Đăng xuất hệ thống", type="primary", use_container_width=True
    ):
      st.session_state.clear()
      st.rerun()

  # Hiển thị màn hình chức năng tương ứng
  if selected_menu == "📅 1. Xem Thời khóa biểu":
    if render_xem_tkb:
      render_xem_tkb(session)
    else:
      st.info("Module xem Thời khóa biểu đang được đồng bộ.")

  elif selected_menu == "📝 2. Đăng ký Biến động (Nghỉ/Bù/Thay/HSG)":
    render_bien_dong_lich_day(session)

  elif selected_menu == "📖 3. Quản lý Sổ Báo Giảng cá nhân":
    render_so_bao_giang_ca_nhan(session)

  elif selected_menu == "📚 4. Quản lý Phân phối chương trình (PPCT)":
    render_quan_ly_ppct(session)

  elif selected_menu == "👥 5. Duyệt Sổ Báo Giảng & Nghỉ bù của Tổ":
    if render_duyet_so_bao_giang:
      render_duyet_so_bao_giang(session)
    else:
      st.info("Module Duyệt Sổ báo giảng đang được đồng bộ.")

  elif selected_menu == "📊 6. Thống Kê & Đối Chiếu Giờ Dạy Của Tổ":
    render_admin_thong_ke_gio(session)

  elif selected_menu == "👥 7. Quản lý DS Giáo viên trong Tổ":
    render_quan_ly_giao_vien(session)

  elif selected_menu == "🔑 8. Đổi mật khẩu cá nhân":
    render_doi_mat_khau(session)


if __name__ == "__main__":
  # Demo chạy thử giao diện Dashboard
  if "user_session" not in st.session_state:
    st.session_state.user_session = {
        "magv": "GV01",
        "tengv": "TUYÊN",
        "to_bo_mon": "Toán",
        "role": "TO_TRUONG",
    }
  render_to_truong_dashboard(st.session_state.user_session)