import streamlit as st
from ui_bien_dong_lich_day import render_bien_dong_lich_day
from ui_day_bu import render_day_bu
from ui_day_thay_hsg import render_day_thay_hsg
from ui_doi_mat_khau import render_doi_mat_khau
from ui_ke_khai_bieu_1c import render_ke_khai_bieu_1c

# Import các giao diện đã được chuyển đổi sang Streamlit
# (Giả định các file module giao diện đã có hàm render tương ứng)
try:
  from ui_xem_tkb import render_xem_tkb
except ImportError:
  render_xem_tkb = None

try:
  from ui_so_bao_giang_ca_nhan import render_so_bao_giang_ca_nhan
except ImportError:
  render_so_bao_giang_ca_nhan = None

try:
  from ui_pkg import render_pkg
except ImportError:
  render_pkg = None


def inject_custom_css():
  st.markdown(
      """
    <style>
    /* CSS Chung cho giao diện Streamlit */
    .stRadio label {
        font-weight: 600 !important;
        font-size: 15px !important;
    }
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


def render_main_teacher(session):
  inject_custom_css()
  tengv = session.get("tengv", "Giáo viên")
  to_bm = session.get("to_bo_mon", "Toán")

  # Sidebar menu điều hướng
  with st.sidebar:
    st.markdown(
        f"<h3 style='color: #1a5276;'>Xin chào,</h3><h4>{tengv}</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color: #555; font-style: italic;'>Tổ bộ môn: {to_bm}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    menu_chon = st.radio(
        "CHỨC NĂNG GIẢNG DẠY",
        options=[
            "📅 Xem TKB cá nhân",
            "⛔ Báo Nghỉ dạy",
            "🟢 Đăng ký Dạy Bù",
            "🟡 Đăng ký Dạy Thay & HSG",
            "📖 Sổ Báo Giảng cá nhân",
            "📊 Xem Kê khai giờ (PKG)",
            "🔑 Đổi mật khẩu",
        ],
    )

    st.divider()
    if st.button(
        "🚪 Đăng xuất", type="primary", use_container_width=True
    ):
      st.session_state.clear()
      st.rerun()

  # Hiển thị nội dung tương ứng theo lựa chọn trên Sidebar
  if menu_chon == "📅 Xem TKB cá nhân":
    if render_xem_tkb:
      render_xem_tkb(session)
    else:
      st.info(
          "Module `ui_xem_tkb.py` đang được cập nhật hiển thị Streamlit."
      )

  elif menu_chon == "⛔ Báo Nghỉ dạy":
    render_bien_dong_lich_day(session)

  elif menu_chon == "🟢 Đăng ký Dạy Bù":
    render_day_bu(session)

  elif menu_chon == "🟡 Đăng ký Dạy Thay & HSG":
    render_day_thay_hsg(session)

  elif menu_chon == "📖 Sổ Báo Giảng cá nhân":
    if render_so_bao_giang_ca_nhan:
      render_so_bao_giang_ca_nhan(session)
    else:
      st.info(
          "Module `ui_so_bao_giang_ca_nhan.py` đang được cập nhật hiển thị"
          " Streamlit."
      )

  elif menu_chon == "📊 Xem Kê khai giờ (PKG)":
    # Có thể linh hoạt gọi biểu 1C hoặc PKG cá nhân tùy chọn
    render_ke_khai_bieu_1c(session)

  elif menu_chon == "🔑 Đổi mật khẩu":
    render_doi_mat_khau(session)