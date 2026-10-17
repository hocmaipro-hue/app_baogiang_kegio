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
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def ensure_table_exists():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS cau_hinh_moc_ppct (
                id SERIAL PRIMARY KEY,
                magv VARCHAR(50),
                lop VARCHAR(20),
                phan_mon VARCHAR(100),
                tu_tuan INT,
                tiet_bat_dau INT,
                UNIQUE(magv, lop, phan_mon, tu_tuan)
            );
        """)
    conn.commit()
    cur.close()
    conn.close()
  except Exception as e:
    print("Lỗi tạo bảng mốc PPCT:", e)


def render_dieu_chinh_ppct(session):
  inject_custom_css()
  ensure_table_exists()

  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #27ae60;'>Cài đặt mốc khởi điểm"
      f" PPCT - {tengv}</h4>",
      unsafe_allow_html=True,
  )

  # Lấy danh sách lớp của giáo viên
  def get_lops():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          "SELECT DISTINCT lop FROM thoi_khoa_bieu WHERE magv = %s ORDER BY lop",
          (magv,),
      )
      lops = [r[0].strip() for r in cur.fetchall() if r[0]]
      cur.close()
      conn.close()
      return lops if lops else [""]
    except Exception:
      return [""]

  # Lấy danh sách phân môn
  def get_pms():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          """
                SELECT DISTINCT COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%'
                ORDER BY 1 ASC;
            """,
          (to_bm, to_bm),
      )
      pms = [r[0].strip() for r in cur.fetchall() if r[0]]
      cur.close()
      conn.close()
      return pms if pms else ["Toán"]
    except Exception:
      return ["Toán"]

  lops = get_lops()
  pms = get_pms()

  # ================= FORM THIẾT LẬP MỐC =================
  with st.form("form_moc_ppct"):
    st.markdown("##### 📌 Thiết lập mốc bài dạy khi nhận lớp mới")

    c1, c2 = st.columns(2)
    with c1:
      lop_chon = st.selectbox("Lớp dạy:", options=lops)
    with c2:
      pm_chon = st.selectbox("Phân môn:", options=pms)

    c3, c4 = st.columns(2)
    with c3:
      tuan_val = st.number_input("Từ Tuần:", min_value=1, max_value=40, value=20)
    with c4:
      tiet_val = st.number_input(
          "Bắt đầu từ Tiết PPCT:", min_value=1, max_value=200, value=1
      )

    submitted = st.form_submit_button(
        "💾 LƯU THIẾT LẬP", type="primary", use_container_width=True
    )

    if submitted:
      if not lop_chon or not pm_chon:
        st.warning("Vui lòng chọn Lớp và Phân môn!")
      else:
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()
          cur.execute(
              """
                        INSERT INTO cau_hinh_moc_ppct (magv, lop, phan_mon, tu_tuan, tiet_bat_dau)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (magv, lop, phan_mon, tu_tuan)
                        DO UPDATE SET tiet_bat_dau = EXCLUDED.tiet_bat_dau;
                    """,
              (magv, lop_chon, pm_chon, int(tuan_val), int(tiet_val)),
          )
          conn.commit()
          cur.close()
          conn.close()
          st.success(
              f"Đã lưu mốc: Lớp {lop_chon} ({pm_chon}) từ Tuần {tuan_val} bắt"
              f" đầu từ Tiết {tiet_val}!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Không thể lưu mốc: {e}")

  st.divider()

  # ================= BẢNG DANH SÁCH MỐC ĐÃ THIẾT LẬP =================
  st.markdown("##### 📋 Danh sách các mốc PPCT đã thiết lập")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, lop, phan_mon, tu_tuan, tiet_bat_dau 
            FROM cau_hinh_moc_ppct WHERE magv = %s 
            ORDER BY lop, phan_mon, tu_tuan ASC
        """,
        (magv,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
      df_moc = pd.DataFrame(
          rows,
          columns=[
              "ID",
              "Lớp",
              "Phân môn",
              "Áp dụng từ Tuần",
              "Tiết PPCT bắt đầu",
          ],
      )
      st.dataframe(df_moc, use_container_width=True, hide_index=True)

      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        rec_id_xoa = st.number_input(
            "Nhập ID mốc cần xóa:", min_value=1, step=1, key="input_xoa_moc"
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button("❌ Xóa mốc này", type="primary", use_container_width=True):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM cau_hinh_moc_ppct WHERE id = %s AND magv = %s",
                (int(rec_id_xoa), magv),
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success("Đã xóa thiết lập mốc thành công!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể xóa: {e}")
    else:
      st.info("Chưa có thiết lập mốc PPCT nào.")
  except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")