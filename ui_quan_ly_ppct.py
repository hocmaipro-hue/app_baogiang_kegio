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
        border-color: #2e86c1 !important;
        color: #2e86c1 !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2e86c1, #2980b9) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #21618c, #2e86c1) !important;
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


def render_quan_ly_ppct(session):
  inject_custom_css()
  mon = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #2e86c1;'>Quản lý Phân Phối"
      f" Chương Trình - Môn: {mon}</h4>",
      unsafe_allow_html=True,
  )

  # ================= KHUNG CÔNG CỤ NHẬP EXCEL =================
  with st.expander("📥 Nhập dữ liệu tự động từ file Excel", expanded=False):
    st.info(
        "📌 *Cấu trúc file Excel gồm 5 cột: Phân môn | Khối | Tuần | Tiết PPCT"
        " | Tên bài dạy*"
    )
    uploaded_file = st.file_uploader(
        "Chọn file Excel (.xlsx, .xls)", type=["xlsx", "xls"]
    )

    if uploaded_file is not None:
      if st.button("🚀 Nạp PPCT từ file Excel này", type="primary"):
        try:
          import openpyxl

          wb = openpyxl.load_workbook(uploaded_file)
          sheet = wb.active

          records = []
          for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
              continue  # Bỏ qua dòng trống

            phan_mon = str(row[0]).strip() if row[0] is not None else ""
            khoi = int(row[1]) if row[1] is not None else 10
            tuan = int(row[2]) if row[2] is not None else 1
            tiet = int(row[3]) if row[3] is not None else 1
            ten_bai = str(row[4]).strip() if row[4] is not None else ""

            if ten_bai:
              records.append((mon, phan_mon, khoi, tuan, tiet, ten_bai))

          if not records:
            st.warning("Không tìm thấy dữ liệu hợp lệ trong file Excel!")
          else:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.executemany(
                """
                            INSERT INTO phan_phoi_chuong_trinh (mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                records,
            )
            conn.commit()
            cur.close()
            conn.close()

            st.success(
                f"Đã nhập thành công {len(records)} tiết bài dạy từ Excel!"
            )
            st.rerun()

        except Exception as e:
          st.error(f"Lỗi đọc file Excel: {e}")

  st.divider()

  # ================= KHUNG NHẬP TAY THỦ CÔNG =================
  with st.expander("➕ Thêm / Chỉnh sửa lẻ từng bài", expanded=False):
    with st.form("form_them_ppct_le"):
      c1, c2, c3, c4 = st.columns(4)
      with c1:
        txt_phan_mon = st.text_input("Phân môn:", value="Đại số")
      with c2:
        spn_khoi = st.number_input(
            "Khối:", min_value=6, max_value=12, value=10
        )
      with c3:
        spn_tuan = st.number_input("Tuần:", min_value=1, max_value=35, value=1)
      with c4:
        spn_tiet = st.number_input(
            "Tiết PPCT:", min_value=1, max_value=150, value=1
        )

      txt_ten_bai = st.text_input("Tên bài dạy:", value="")

      submitted_add = st.form_submit_button(
          "Thêm lẻ bài này", type="primary", use_container_width=True
      )

      if submitted_add:
        phan_mon_val = txt_phan_mon.strip()
        ten_bai_val = txt_ten_bai.strip()

        if not phan_mon_val or not ten_bai_val:
          st.warning("Vui lòng nhập Phân môn và Tên bài dạy!")
        else:
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                """
                            INSERT INTO phan_phoi_chuong_trinh (mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                (
                    mon,
                    phan_mon_val,
                    int(spn_khoi),
                    int(spn_tuan),
                    int(spn_tiet),
                    ten_bai_val,
                ),
            )
            conn.commit()
            cur.close()
            conn.close()

            st.success(f"Đã thêm thành công bài: '{ten_bai_val}'!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể thêm PPCT: {e}")

  st.divider()

  # ================= BẢNG HIỂN THỊ DANH SÁCH PPCT =================
  st.markdown("##### 📋 Danh sách Phân Phối Chương Trình")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day
            FROM phan_phoi_chuong_trinh
            WHERE mon = %s
            ORDER BY khoi, phan_mon, tiet_ppct ASC
        """,
        (mon,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
      df_ppct = pd.DataFrame(
          rows,
          columns=[
              "ID",
              "Môn",
              "Phân môn",
              "Khối",
              "Tuần",
              "Tiết PPCT",
              "Tên bài dạy",
          ],
      )
      st.dataframe(df_ppct, use_container_width=True, hide_index=True)

      c_act1, c_act2 = st.columns([2, 1])
      with c_act1:
        rec_id_xoa = st.number_input(
            "Nhập ID bài dạy cần xóa:", min_value=1, step=1, key="input_xoa_ppct"
        )
      with c_act2:
        st.write("")
        st.write("")
        if st.button("❌ Xóa bài này", type="primary", use_container_width=True):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM phan_phoi_chuong_trinh WHERE id = %s",
                (int(rec_id_xoa),),
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success("Đã xóa tiết bài dạy thành công!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể xóa: {e}")

      st.write("")
      if st.button(
          f"⚠️ Xóa TOÀN BỘ PPCT môn {mon}", use_container_width=True
      ):
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()
          cur.execute(
              "DELETE FROM phan_phoi_chuong_trinh WHERE mon = %s", (mon,)
          )
          conn.commit()
          cur.close()
          conn.close()
          st.success("Đã xóa sạch PPCT môn này để bạn nhập lại từ đầu!")
          st.rerun()
        except Exception as e:
          st.error(f"Không thể xóa toàn bộ: {e}")

    else:
      st.info(f"Chưa có dữ liệu PPCT nào cho môn {mon}.")

  except Exception as e:
    st.error(f"Lỗi tải danh sách PPCT: {e}")