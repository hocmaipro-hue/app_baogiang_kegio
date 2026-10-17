from auth import authenticate_user
import streamlit as st


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
        border-color: #27ae60 !important;
        color: #27ae60 !important;
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
    .stTextInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def render_login(on_success_callback=None):
  inject_custom_css()

  # Căn giữa khung đăng nhập cho đẹp mắt
  _, col_mid, _ = st.columns([1, 2, 1])

  with col_mid:
    st.markdown(
        "<h3 style='text-align: center; color: #1a5276;'>HỆ THỐNG QUẢN LÝ BÁO"
        " GIẢNG</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #555; font-style:"
        " italic;'>Trường THPT Nguyễn Việt Hồng</p>",
        unsafe_allow_html=True,
    )

    with st.form("form_login"):
      magv_input = st.text_input("Mã giáo viên (MAGV):", value="")
      pass_input = st.text_input("Mật khẩu:", type="password", value="")

      submitted = st.form_submit_button(
          "Đăng nhập", type="primary", use_container_width=True
      )

      if submitted:
        magv = magv_input.strip()
        pwd = pass_input.strip()

        if not magv or not pwd:
          st.warning("Vui lòng nhập đầy đủ Mã giáo viên và Mật khẩu!")
        else:
          session = authenticate_user(magv, pwd)
          if session:
            st.success(
                f"Chào mừng {session.get('tengv', '')}"
                f" ({session.get('role', '')})!"
            )
            # Lưu session vào Streamlit state
            st.session_state.authenticated = True
            st.session_state.user_session = session

            if on_success_callback:
              on_success_callback(session)
            st.rerun()
          else:
            st.error("Mã giáo viên hoặc mật khẩu không đúng!")


# Hàm tương thích ngược nếu `main.py` gọi render_login_page
def render_login_page(on_success_callback=None):
  render_login(on_success_callback)