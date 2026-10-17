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
    .stSelectbox div {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_xem_tkb(session):
  inject_custom_css()
  to_bm = get_val(session, "to_bo_mon", "")
  magv_hien_tai = get_val(session, "magv", "")

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>Thời Khóa Biểu & Gán"
      " Phân Môn</h4>",
      unsafe_allow_html=True,
  )

  # ================= 1. TẢI DỮ LIỆU ĐỢT TUẦN & GIÁO VIÊN =================
  # Tải danh sách đợt TKB (Tuần)
  tuan_dict = {}
  vals_tuan = []
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name ="
        " 'thoi_khoa_bieu';"
    )
    cols = set(r[0] for r in cur.fetchall())
    col_ngay = (
        '"ap_dung_từ_ngay"'
        if "ap_dung_từ_ngay" in cols
        else (
            "ap_dung_tu_ngay"
            if "ap_dung_tu_ngay" in cols
            else "NULL"
        )
    )

    cur.execute(f"""
            SELECT DISTINCT ap_dung_tu_tuan, MIN({col_ngay})
            FROM thoi_khoa_bieu
            WHERE ap_dung_tu_tuan IS NOT NULL
            GROUP BY ap_dung_tu_tuan
            ORDER BY ap_dung_tu_tuan ASC
        """)
    rows_tuan = cur.fetchall()
    cur.close()
    conn.close()

    for r in rows_tuan:
      tuan = r[0]
      ngay = r[1]
      label = (
          f"Tuần {tuan} (từ {ngay.strftime('%d/%m/%Y')})"
          if (ngay and hasattr(ngay, "strftime"))
          else f"Tuần {tuan}"
      )
      tuan_dict[label] = tuan
      vals_tuan.append(label)
  except Exception as e:
    st.error(f"Lỗi tải đợt TKB: {e}")

  # Tải danh sách giáo viên
  gv_dict = {}
  vals_gv = []
  selected_gv_idx = 0
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    if to_bm:
      cur.execute(
          "SELECT magv, tengv FROM giao_vien WHERE to_bo_mon = %s ORDER BY"
          " tengv",
          (to_bm,),
      )
    else:
      cur.execute("SELECT magv, tengv FROM giao_vien ORDER BY to_bo_mon, tengv")
    rows_gv = cur.fetchall()
    cur.close()
    conn.close()

    for idx, (mgv, tgv) in enumerate(rows_gv):
      label = f"{tgv} ({mgv})"
      gv_dict[label] = mgv
      vals_gv.append(label)
      if mgv == magv_hien_tai:
        selected_gv_idx = idx
  except Exception as e:
    st.error(f"Lỗi tải danh sách GV: {e}")

  # Tải toàn bộ phân môn
  all_phan_mon = []
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute("""
            SELECT DISTINCT phan_mon 
            FROM phan_phoi_chuong_trinh 
            WHERE phan_mon IS NOT NULL AND TRIM(phan_mon) != ''
            ORDER BY phan_mon ASC;
        """)
    all_phan_mon = [
        r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()
    ]
    cur.close()
    conn.close()
  except Exception:
    pass

  # ================= 2. THANH CHỌN BỘ LỌC (GIÁO VIÊN & ĐỢT TKB) =================
  c_f1, c_f2 = st.columns(2)
  with c_f1:
    selected_gv_label = st.selectbox(
        "👤 Chọn Giáo viên:",
        options=vals_gv,
        index=selected_gv_idx if vals_gv else 0,
    )
  with c_f2:
    selected_tuan_label = st.selectbox(
        "📅 Chọn Đợt TKB (Tuần):",
        options=vals_tuan,
        index=len(vals_tuan) - 1 if vals_tuan else 0,
    )

  magv = gv_dict.get(selected_gv_label)
  tuan = tuan_dict.get(selected_tuan_label)

  st.divider()

  # ================= 3. TẢI VÀ HIỂN THỊ BẢNG TKB =================
  if not magv:
    st.warning("Vui lòng chọn giáo viên.")
    return

  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    if tuan is not None:
      cur.execute(
          """
                SELECT id, thu, buoi, tiet, lop, mon, COALESCE(phan_mon, '')
                FROM thoi_khoa_bieu 
                WHERE magv = %s AND ap_dung_tu_tuan = %s
                ORDER BY thu ASC, CASE WHEN buoi = 'Sáng' THEN 1 ELSE 2 END ASC,"
          " tiet ASC
            """,
          (magv, tuan),
      )
    else:
      cur.execute(
          """
                SELECT id, thu, buoi, tiet, lop, mon, COALESCE(phan_mon, '')
                FROM thoi_khoa_bieu 
                WHERE magv = %s 
                ORDER BY thu ASC, CASE WHEN buoi = 'Sáng' THEN 1 ELSE 2 END ASC,"
          " tiet ASC
            """,
          (magv,),
      )

    rows_tkb = cur.fetchall()
    cur.close()
    conn.close()

    if rows_tkb:
      df_tkb = pd.DataFrame(
          rows_tkb,
          columns=[
              "ID",
              "Thứ",
              "Buổi",
              "Tiết",
              "Lớp",
              "Môn học",
              "Phân môn",
          ],
      )
      st.markdown(
          "##### 📋 Danh sách tiết dạy (Chọn ID để gán/đổi Phân môn bên dưới)"
      )
      st.dataframe(df_tkb, use_container_width=True, hide_index=True)

      # ================= 4. KHUNG GÁN PHÂN MÔN TRỰC TIẾP =================
      st.markdown("---")
      st.markdown("##### ⚙️ Gán Phân Môn cho tiết dạy")

      c_id, c_pm, c_btn = st.columns([1, 2, 1])
      with c_id:
        record_id = st.number_input(
            "Nhập ID tiết dạy:", min_value=1, step=1, key="input_id_tkb"
        )

      # Lọc phân môn tương ứng theo môn học của dòng ID chọn
      selected_mon = "Toán"
      for r in rows_tkb:
        if r[0] == record_id:
          selected_mon = r[5]
          break

      # Lọc phân môn theo môn
      ds_pm = all_phan_mon
      try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(
            """
                    SELECT DISTINCT phan_mon 
                    FROM phan_phoi_chuong_trinh 
                    WHERE (UPPER(TRIM(mon)) = UPPER(TRIM(%s)) OR %s ILIKE '%' || mon || '%')
                      AND phan_mon IS NOT NULL AND TRIM(phan_mon) != ''
                    ORDER BY phan_mon ASC;
                """,
            (selected_mon, selected_mon),
        )
        filtered_pm = [
            r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()
        ]
        cur.close()
        conn.close()
        if filtered_pm:
          ds_pm = filtered_pm
      except Exception:
        pass

      with c_pm:
        selected_phan_mon = st.selectbox("Chọn Phân môn mới:", options=ds_pm)

      with c_btn:
        st.write("")
        st.write("")
        if st.button("💾 Lưu Phân Môn", type="primary", use_container_width=True):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "UPDATE thoi_khoa_bieu SET phan_mon = %s WHERE id = %s",
                (selected_phan_mon, int(record_id)),
            )
            conn.commit()
            cur.close()
            conn.close()
            st.success(
                f"Đã cập nhật phân môn '{selected_phan_mon}' cho tiết có ID"
                f" {record_id} thành công!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Không thể lưu phân môn: {e}")

    else:
      st.info(
          "Không có tiết dạy nào được tìm thấy cho giáo viên và đợt tuần này."
      )

  except Exception as e:
    st.error(f"Lỗi tải dữ liệu thời khóa biểu: {e}")