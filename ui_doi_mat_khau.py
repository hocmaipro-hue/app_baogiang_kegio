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
    .stTextInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_doi_mat_khau(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>ĐỔI MẬT KHẨU ĐĂNG"
      " NHẬP</h4>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; color: #555; font-style: italic;'>Tài"
      f" khoản: {tengv} ({magv})</p>",
      unsafe_allow_html=True,
  )

  # Form đổi mật khẩu
  with st.form("form_doi_mk"):
    p_old = st.text_input("Mật khẩu hiện tại:", type="password", value="")
    p_new = st.text_input("Mật khẩu mới:", type="password", value="")
    p_confirm = st.text_input("Nhập lại MK mới:", type="password", value="")

    submitted = st.form_submit_button(
        "💾 Lưu Mật Khẩu Mới", type="primary", use_container_width=True
    )

    if submitted:
      p_old_clean = p_old.strip()
      p_new_clean = p_new.strip()
      p_conf_clean = p_confirm.strip()

      if not p_old_clean or not p_new_clean or not p_conf_clean:
        st.warning("Vui lòng nhập đầy đủ cả 3 ô mật khẩu!")
      elif p_new_clean != p_conf_clean:
        st.error(
            "Mật khẩu mới và Nhập lại mật khẩu không khớp nhau!"
        )
      elif p_old_clean == p_new_clean:
        st.warning(
            "Mật khẩu mới không được trùng với mật khẩu cũ!"
        )
      else:
        conn = None
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()

          # 1. Kiểm tra mật khẩu cũ
          cur.execute(
              "SELECT matkhau FROM giao_vien WHERE magv = %s", (magv,)
          )
          row = cur.fetchone()

          if not row or (row[0] and str(row[0]).strip() != p_old_clean):
            st.error("Mật khẩu hiện tại không chính xác!")
            cur.close()
            conn.close()
          else:
            # 2. Cập nhật mật khẩu mới
            cur.execute(
                "UPDATE giao_vien SET matkhau = %s WHERE magv = %s",
                (p_new_clean, magv),
            )
            conn.commit()
            cur.close()
            conn.close()

            st.success(
                "Đã đổi mật khẩu thành công!\nHãy ghi nhớ mật khẩu mới cho lần"
                " đăng nhập sau."
            )
        except Exception as e:
          if conn:
            conn.rollback()
          st.error(f"Không thể đổi mật khẩu: {e}")