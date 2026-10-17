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
    .stTextInput input, .stSelectbox div {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_quan_ly_giao_vien(session):
  inject_custom_css()
  user_role = str(get_val(session, "role", "")).upper()
  user_to = get_val(session, "to_bo_mon", "")

  title_text = (
      "QUẢN LÝ TẤT CẢ CÁC CỘT GIÁO VIÊN [ADMIN]"
      if user_role in ["ADMIN", "BGH"]
      else f"DANH SÁCH GIÁO VIÊN - TỔ {str(user_to).upper()}"
  )

  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>{title_text}</h4>",
      unsafe_allow_html=True,
  )

  # ================= KHUNG 1: THÊM LẺ (CƠ BẢN) =================
  with st.expander("➕ Thêm 1 Giáo viên mới (Cơ bản)", expanded=False):
    with st.form("form_them_gv_le"):
      c1, c2, c3, c4 = st.columns(4)
      with c1:
        txt_magv = st.text_input("Mã GV:", value="")
      with c2:
        txt_tengv = st.text_input("Họ tên:", value="")
      with c3:
        if user_role in ["ADMIN", "BGH"]:
          txt_to = st.text_input("Tổ bộ môn:", value="Toán")
        else:
          txt_to = st.text_input("Tổ bộ môn:", value=user_to, disabled=True)
      with c4:
        cbo_role = st.selectbox(
            "Vai trò:", options=["GV", "TO_TRUONG", "ADMIN"]
        )

      submitted_add = st.form_submit_button(
          "Thêm nhanh GV", type="primary", use_container_width=True
      )
      if submitted_add:
        mgv = txt_magv.strip().upper()
        tgv = txt_tengv.strip()
        to_bm = txt_to.strip()

        if not mgv or not tgv:
          st.warning("Vui lòng nhập ít nhất Mã GV và Họ tên!")
        else:
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                """
                            INSERT INTO giao_vien (magv, tengv, to_bo_mon, role, matkhau)
                            VALUES (%s, %s, %s, %s, '123456')
                            ON CONFLICT (magv) DO NOTHING;
                        """,
                (mgv, tgv, to_bm, cbo_role),
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(
                f"Đã thêm giáo viên: {tgv} (Mật khẩu mặc định: 123456)"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Không thể thêm GV: {e}")

  st.divider()

  # ================= KHUNG 2: BẢNG DỮ LIỆU & CHỈNH SỬA =================
  st.markdown("##### 📋 Danh sách giáo viên")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    if user_role in ["ADMIN", "BGH"]:
      cur.execute("SELECT * FROM giao_vien ORDER BY magv ASC")
    else:
      cur.execute(
          "SELECT * FROM giao_vien WHERE to_bo_mon = %s ORDER BY magv ASC",
          (user_to,),
      )

    all_columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
      df_gv = pd.DataFrame(rows, columns=all_columns)
      st.dataframe(df_gv, use_container_width=True, hide_index=True)

      st.write("")
      # Chọn mã GV để thực hiện hành động
      magv_list = [str(r[all_columns.index("magv")]) for r in rows]
      selected_magv = st.selectbox(
          "Chọn Mã GV để thao tác (Sửa / Reset MK / Xóa):", options=magv_list
      )

      c_b1, c_b2, c_b3 = st.columns(3)
      with c_b1:
        if st.button("🔑 Reset MK (123456)", use_container_width=True):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "UPDATE giao_vien SET matkhau = '123456' WHERE magv = %s",
                (selected_magv,),
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(
                f"Đã đặt lại mật khẩu của {selected_magv} về 123456!"
            )
          except Exception as e:
            st.error(f"Không thể đổi mật khẩu: {e}")

      with c_b2:
        if st.button("❌ Xóa giáo viên này", use_container_width=True):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM giao_vien WHERE magv = %s", (selected_magv,)
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Đã xóa thành công giáo viên {selected_magv}!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể xóa: {e}")

      with c_b3:
        if user_role in ["ADMIN", "BGH"]:
          if st.button(
              "⚠️ Xóa TOÀN BỘ danh sách", type="primary", use_container_width=True
          ):
            try:
              conn = psycopg2.connect(DB_URI)
              cur = conn.cursor()
              cur.execute("DELETE FROM giao_vien;")
              conn.commit()
              cur.close()
              conn.close()
              st.success("Đã xóa toàn bộ danh sách giáo viên!")
              st.rerun()
            except Exception as e:
              st.error(f"Lỗi xóa toàn bộ: {e}")

      # Form chỉnh sửa chi tiết các cột của giáo viên được chọn
      st.markdown("---")
      st.markdown(f"##### ✏️ Chỉnh sửa thông tin cho GV: `{selected_magv}`")
      selected_row_data = df_gv[df_gv["magv"] == selected_magv].iloc[0]

      with st.form("form_sua_gv"):
        updated_vals = {}
        for col in all_columns:
          if col == "magv":
            st.text_input(
                f"{col} (Không sửa):",
                value=str(selected_row_data[col]),
                disabled=True,
            )
          else:
            updated_vals[col] = st.text_input(
                f"{col}:", value=str(selected_row_data[col])
            )

        submitted_update = st.form_submit_button(
            "💾 LƯU THAY ĐỔI TẤT CẢ CỘT",
            type="primary",
            use_container_width=True,
        )
        if submitted_update:
          try:
            cols_to_update = [c for c in all_columns if c != "magv"]
            set_clause = ", ".join([f"{c} = %s" for c in cols_to_update])
            vals = [
                (
                    None
                    if updated_vals[c].strip() == ""
                    else updated_vals[c].strip()
                )
                for c in cols_to_update
            ]
            vals.append(selected_magv)

            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            query = f"UPDATE giao_vien SET {set_clause} WHERE magv = %s"
            cur.execute(query, vals)
            conn.commit()
            cur.close()
            conn.close()

            st.success(
                f"Đã cập nhật toàn bộ thông tin cho {selected_magv}!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Lỗi Lưu: {e}")

    else:
      st.info("Chưa có giáo viên nào trong danh sách.")

  except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")