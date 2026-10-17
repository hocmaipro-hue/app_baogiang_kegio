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
        border-color: #1a5276 !important;
        color: #1a5276 !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a5276, #2980b9) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #154360, #1a5276) !important;
        color: white !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_nhan_su_va_duyet(session):
  inject_custom_css()
  tengv = get_val(session, "tengv", "Tổ trưởng")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>Bảng điều khiển Tổ"
      f" trưởng: {to_bm}</h4>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; color: #555; font-style: italic;'>Xin"
      f" chào Thầy/Cô: {tengv}</p>",
      unsafe_allow_html=True,
  )
  st.write("")

  # Nút chức năng kiểm tra tiến độ PPCT trong tổ
  c1, c2, c3 = st.columns([1, 2, 1])
  with c2:
    if st.button(
        "📊 Kiểm tra tiến độ PPCT của giáo viên trong tổ",
        type="primary",
        use_container_width=True,
    ):
      st.success(
          "Tính năng kiểm tra tiến độ PPCT trong tổ đang hoạt động bình thường!"
      )