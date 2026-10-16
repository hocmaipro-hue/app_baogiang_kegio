import streamlit as st
from auth import authenticate_user  # Gọi trực tiếp hàm xác thực từ file auth.py của bạn

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hệ Thống Báo Giảng & Kê Giờ - THPT Nguyễn Việt Hồng",
    page_icon="🌸",
    layout="wide",
)


def hien_thiep_an_yen(tengv):
  """Hiển thị thiệp thơ an yên, màu sắc phong cảnh hữu tình, thư thái trên web"""
  st.markdown(
      """
        <style>
        .thiep-container {
            background-color: #E8F8F5;
            border: 2px solid #A3E4D7;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin: 20px auto;
            max-width: 600px;
        }
        .tieu-de-gv {
            font-family: 'Times New Roman', Times, serif;
            font-size: 24px;
            font-weight: bold;
            color: #117A65;
            margin-bottom: 15px;
        }
        .bai-tho {
            font-family: 'Times New Roman', Times, serif;
            font-size: 18px;
            font-style: italic;
            color: #1A5276;
            background-color: #F4F6F6;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #D5D8DC;
            line-height: 1.6;
            margin: 15px 0;
            white-space: pre-line;
        }
        .loi-chuc {
            font-family: 'Times New Roman', Times, serif;
            font-size: 16px;
            color: #5D6D7E;
            margin-top: 15px;
        }
        .tac-gia {
            font-family: 'Times New Roman', Times, serif;
            font-size: 15px;
            font-weight: bold;
            font-style: italic;
            color: #B7950B;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      f"""
    <div class="thiep-container">
        <div class="tieu-de-gv">🌿 Kính tặng Thầy/Cô: {tengv}</div>
        <div class="bai-tho">
            “Bụi phấn bay bay mỉm miệng cười,<br>
            Bảng đen nâng bước tuổi đôi mươi.<br>
            Rời trang giáo án lòng thanh thản,<br>
            Một đóa an yên nở giữa đời.”
        </div>
        <div class="loi-chuc">Chúc Thầy/Cô một ngày giảng dạy an vui, nhẹ nhàng và trọn vẹn!</div>
        <div class="tac-gia">— Thân ái: Tác giả Nguyễn Văn Phong —</div>
    </div>
    """,
      unsafe_allow_html=True,
  )


def main():
  # Khởi tạo Session State
  if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
  if "session_data" not in st.session_state:
    st.session_state.session_data = None
  if "show_greeting" not in st.session_state:
    st.session_state.show_greeting = False

  # 1. GIAO DIỆN ĐĂNG NHẬP
  if not st.session_state.logged_in:
    st.markdown(
        "<h2 style='text-align: center; color: #0d47a1;'>HỆ THỐNG QUẢN LÝ BÁO"
        " GIẢNG & KÊ GIỜ</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #555;'>Trường THPT Nguyễn Việt"
        " Hồng - Cần Thơ</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      with st.form("login_form"):
        magv = st.text_input("Mã Giáo Viên hoặc Họ Tên").strip()
        matkhau = st.text_input("Mật khẩu", type="password").strip()
        submit_btn = st.form_submit_button(
            "Đăng nhập", use_container_width=True
        )

        if submit_btn:
          try:
            # Gọi hàm xác thực chuẩn từ auth.py
            session = authenticate_user(magv, matkhau)
          except Exception:
            session = None

          if session:
            st.session_state.session_data = session
            st.session_state.show_greeting = True
            st.rerun()
          else:
            st.error(
                "Sai tài khoản/mật khẩu hoặc CSDL chưa có dữ liệu giáo viên!"
            )
    return

  # 2. HIỆN THIỆP THƠ AN YÊN SAU KHI ĐĂNG NHẬP THÀNH CÔNG
  session = st.session_state.session_data
  tengv = session.get("tengv", "Thầy/Cô")

  if st.session_state.show_greeting:
    hien_thiep_an_yen(tengv)
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1.5, 2])
    with col_btn2:
      if st.button(
          "🌸 Nhận An Yên & Bắt Đầu 🌸",
          use_container_width=True,
          type="primary",
      ):
        st.session_state.show_greeting = False
        st.rerun()
    return

  # 3. GIAO DIỆN CHÍNH DỰA TRÊN VAI TRÒ (ROLE)
  role = session.get("role")

  # Thanh sidebar điều hướng hệ thống
  st.sidebar.title("Hệ Thống Báo Giảng")
  st.sidebar.write(
      f"**GV:** {session.get('tengv')} ({session.get('magv', '')})"
  )
  st.sidebar.write(f"**Vai trò:** {role}")
  if st.sidebar.button("Đăng xuất", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.session_data = None
    st.session_state.show_greeting = False
    st.rerun()

  st.sidebar.divider()

  # Phân quyền hiển thị giao diện chức năng tương ứng
  if role == "TO_TRUONG":
    st.title("🌟 Bảng Điều Khiển Tổ Trưởng Chuyên Môn")
    try:
      from ui_to_truong_dashboard import run_to_truong_dashboard

      run_to_truong_dashboard(session)
    except ImportError:
      st.info(
          "Đang ở chế độ Tổ trưởng. Giao diện chức năng đang được chuyển đổi"
          " sang Streamlit."
      )

  elif role == "ADMIN":
    st.title("⚙️ Bảng Điều Khiển Quản Trị Viên (Admin)")
    try:
      from ui_admin import run_admin_dashboard

      run_admin_dashboard(session)
    except ImportError:
      st.info(
          "Đang ở chế độ Admin. Giao diện chức năng đang được chuyển đổi sang"
          " Streamlit."
      )

  else:
    st.title("📖 Sổ Báo Giảng Giáo Viên")
    try:
      from ui_main import run_main_dashboard

      run_main_dashboard(session)
    except ImportError:
      st.info(
          "Đang ở chế độ Giáo viên. Giao diện chức năng đang được chuyển đổi"
          " sang Streamlit."
      )


if __name__ == "__main__":
  main()
