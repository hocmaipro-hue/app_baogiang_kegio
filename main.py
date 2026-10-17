import streamlit as st
from models import create_all_tables
from ui_login import render_login_page

# 1. CẤU HÌNH TRANG STREAMLIT
st.set_page_config(
    page_title="Hệ Thống Quản Lý Giờ Dạy & Kê Khai - THPT Nguyễn Việt Hồng",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. TỰ ĐỘNG KHỞI TẠO CẤU TRÚC CSDL (SUPABASE) KHI CHẠY ỨNG DỤNG
if "db_initialized" not in st.session_state:
  try:
    create_all_tables()
    st.session_state["db_initialized"] = True
  except Exception as e:
    print(f"Lỗi khởi tạo CSDL: {e}")


# 3. CSS TÙY CHỈNH NÚT BẤM TRÒN MỀM MẠI & GIAO DIỆN THIỆP THƠ
def apply_custom_styles():
  st.markdown(
      """
    <style>
    /* CSS Nút bấm tròn mềm mại (Pill Buttons) */
    div.stButton > button {
        border-radius: 24px !important;
        border: 1px solid #1abc9c !important;
        padding: 8px 22px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 4px 14px rgba(26, 188, 156, 0.3) !important;
        background-color: #16a085 !important;
        color: white !important;
    }

    /* CSS Thẻ Thiệp Thơ An Yên */
    .thiep-an-yen {
        background-color: #ffffff;
        border: 2px solid #a3e4d7;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .thiep-tho-box {
        background-color: #f4f6f6;
        border: 1px solid #d5dbdb;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
        font-family: 'Times New Roman', serif;
        font-size: 17px;
        font-style: italic;
        color: #1a5276;
        line-height: 1.6;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


# 4. DIALOG/MODAL THIỆP THƠ AN YÊN
@st.dialog("🌸 Gửi Chút An Yên Đến Thầy/Cô")
def hien_thiep_an_yen_dialog(tengv):
  st.markdown(
      f"<h4 style='color: #117a65; text-align: center; font-family: \"Times"
      f" New Roman\";'>🌿 Kính tặng Thầy/Cô: {tengv}</h4>",
      unsafe_allow_html=True,
  )

  tho_html = """
    <div class="thiep-tho-box">
        “Bụi phấn bay bay mỉm miệng cười,<br>
        Bảng đen nâng bước tuổi đôi mươi.<br>
        Rời trang giáo án lòng thanh thản,<br>
        Một đóa an yên nở giữa đời.”
    </div>
    """
  st.markdown(tho_html, unsafe_allow_html=True)

  st.markdown(
      "<p style='color: #5d6d7e; text-align: center; font-family: \"Times"
      " New Roman\"; font-size: 15px;'>Chúc Thầy/Cô một ngày giảng dạy an vui,"
      " nhẹ nhàng và trọn vẹn!</p>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='color: #b7950b; text-align: center; font-family: \"Times"
      " New Roman\"; font-weight: bold; font-style: italic;'>— Thân ái: Tác giả"
      " Nguyễn Văn Phong —</p>",
      unsafe_allow_html=True,
  )

  st.write("")
  if st.button(
      "🌸 Nhận An Yên & Bắt Đầu 🌸",
      use_container_width=True,
      type="primary",
  ):
    st.session_state["da_xem_thiep"] = True
    st.rerun()


# 5. HÀM ĐIỀU HƯỚNG MÀN HÌNH CHÍNH DỰA VÀO VAI TRÒ (ROLE)
def render_main_dashboard(session):
  role = session.get("role", "GV")
  tengv = session.get("tengv", "Thầy/Cô")

  # Tự động bật Thiệp An Yên lần đầu khi vừa đăng nhập thành công
  if not st.session_state.get("da_xem_thiep", False):
    hien_thiep_an_yen_dialog(tengv)

  # Thanh Sidebar Điều hướng & Thông tin đăng nhập
  st.sidebar.title("📌 Menu Chức Năng")
  st.sidebar.markdown(f"👤 Tài khoản: **{tengv}**")
  st.sidebar.markdown(f"🔑 Vai trò: **{role}**")

  if st.sidebar.button("🚪 Đăng Xuất", use_container_width=True):
    st.session_state.clear()
    st.rerun()

  st.sidebar.divider()

  # Điều hướng màn hình theo vai trò (Role-based Routing)
  if role == "ADMIN":
    from ui_admin import render_admin_dashboard

    render_admin_dashboard(session)

  elif role == "TO_TRUONG":
    from ui_to_truong_dashboard import render_to_truong_dashboard

    render_to_truong_dashboard(session)

  else:  # GIÁO VIÊN THƯỜNG ('GV')
    from ui_main import render_user_dashboard

    render_user_dashboard(session)


# 6. ĐIỂM KHỞI CHẠY LỰA CHỌN MÀN HÌNH (ENTRYPOINT)
def main():
  apply_custom_styles()

  # Kiểm tra trạng thái đăng nhập trong st.session_state
  if "user_session" not in st.session_state or not st.session_state.get(
      "authenticated", False
  ):
    render_login_page()
  else:
    render_main_dashboard(st.session_state.user_session)


if __name__ == "__main__":
  main()