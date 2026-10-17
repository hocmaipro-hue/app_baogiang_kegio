from datetime import datetime
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
    .stTextInput input, .stDateInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_cai_dat_kiem_nhiem(
    session, tu_ngay_def="07/09/2026", den_ngay_def="03/10/2026"
):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>QUẢN LÝ & CÀI ĐẶT THÔNG"
      " TIN CỐ ĐỊNH VÀ BDHSG</h4>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; color: #555; font-style: italic;'>Giáo"
      f" viên: {tengv} ({magv})</p>",
      unsafe_allow_html=True,
  )

  # 1. Tải thông tin cố định từ database
  data_gv = {}
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT con_nho, giam_tru_con_nho, hopdong_lan_dau, giam_tru_hopdong_landau, 
                   kiem_nhiem_2, giam_tru_kn2 
            FROM giao_vien WHERE magv = %s
        """,
        (magv,),
    )
    row_gv = cur.fetchone()
    cur.close()
    conn.close()
    if row_gv:
      data_gv = {
          "con_nho": row_gv[0] or "",
          "giam_tru_con_nho": float(row_gv[1] or 0),
          "hopdong_lan_dau": row_gv[2] or "",
          "giam_tru_hopdong_landau": float(row_gv[3] or 0),
          "kiem_nhiem_2": row_gv[4] or "",
          "giam_tru_kn2": float(row_gv[5] or 0),
      }
  except Exception as e:
    st.error(f"Lỗi tải dữ liệu GV: {e}")

  # 2. Lấy sẵn dữ liệu HSG
  hsg_data = {"thuc_day": 0.0, "quy_doi": 0.0}
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT COALESCE(SUM(bdhsg_thuc_day), 0), COALESCE(SUM(bdhsg_quy_doi), 0) 
            FROM kg_hoc_sinh_gioi WHERE magv = %s
        """,
        (magv,),
    )
    r = cur.fetchone()
    if r:
      hsg_data["thuc_day"], hsg_data["quy_doi"] = float(r[0]), float(r[1])
    cur.close()
    conn.close()
  except Exception:
    pass

  # Form cài đặt
  with st.form("form_cai_dat_kiem_nhiem"):
    st.markdown("##### ⚙️ Thông tin Kiêm nhiệm & Giảm trừ")

    con_nho = st.text_input(
        "1. Con nhỏ (Số lượng/Thông tin):",
        value=str(data_gv.get("con_nho", "")),
    )
    giam_tru_con_nho = st.number_input(
        "2. Giảm trừ con nhỏ (Giờ):",
        value=float(data_gv.get("giam_tru_con_nho", 0.0)),
        step=0.5,
    )

    hopdong_lan_dau = st.text_input(
        "3. Hợp đồng lần đầu (Thông tin):",
        value=str(data_gv.get("hopdong_lan_dau", "")),
    )
    giam_tru_hopdong_landau = st.number_input(
        "4. Giảm trừ HĐ lần đầu (Giờ):",
        value=float(data_gv.get("giam_tru_hopdong_landau", 0.0)),
        step=0.5,
    )

    kiem_nhiem_2 = st.text_input(
        "5. Kiêm nhiệm 2 (Tên nhiệm vụ):",
        value=str(data_gv.get("kiem_nhiem_2", "")),
    )
    giam_tru_kn2 = st.number_input(
        "6. Giảm trừ KN2 (Giờ):",
        value=float(data_gv.get("giam_tru_kn2", 0.0)),
        step=0.5,
    )

    st.markdown("---")
    st.markdown("##### 📚 Thống kê BDHSG theo khoảng ngày")

    c_d1, c_d2 = st.columns(2)
    with c_d1:
      txt_tungay = st.text_input("Từ ngày (DD/MM/YYYY):", value=tu_ngay_def)
    with c_d2:
      txt_denngay = st.text_input("Đến ngày (DD/MM/YYYY):", value=den_ngay_def)

    # Nút lọc tính lại
    if st.form_submit_button(
        "🔄 Lọc & Tính lại theo khoảng ngày", use_container_width=True
    ):
      try:
        dt_start = datetime.strptime(txt_tungay.strip(), "%d/%m/%Y").date()
        dt_end = datetime.strptime(txt_denngay.strip(), "%d/%m/%Y").date()

        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(
            """
                    SELECT COUNT(*) FROM bien_dong_lich_day 
                    WHERE magv = %s AND (loai ILIKE '%%HSG%%' OR loai ILIKE '%%Bồi dưỡng HSG%%')
                      AND ngay BETWEEN %s AND %s AND trang_thai != 'DA_HUY'
                """,
            (magv, dt_start, dt_end),
        )
        r = cur.fetchone()
        so_buoi = r[0] if r else 0
        quy_doi = so_buoi * 1.5
        cur.close()
        conn.close()

        hsg_data["thuc_day"] = float(so_buoi)
        hsg_data["quy_doi"] = float(quy_doi)
        st.success(
            f"Đã tính lại thành công: {so_buoi} buổi ({quy_doi} giờ quy đổi)!"
        )
      except Exception as ex:
        st.error(
            f"Lỗi định dạng ngày (vui lòng nhập DD/MM/YYYY): {ex}"
        )

    entry_thucday = st.number_input(
        "7. BDHSG thực dạy (Số buổi):",
        value=float(hsg_data["thuc_day"]),
        step=0.5,
    )
    entry_quydoi = st.number_input(
        "8. BDHSG quy đổi (x 1.5 - Có thể sửa lẻ):",
        value=float(hsg_data["quy_doi"]),
        step=0.5,
    )

    st.write("")
    submitted_save = st.form_submit_button(
        "💾 Lưu cấu hình & Đồng bộ", type="primary", use_container_width=True
    )

    if submitted_save:
      try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(
            """
                    UPDATE giao_vien 
                    SET con_nho = %s, giam_tru_con_nho = %s, 
                        hopdong_lan_dau = %s, giam_tru_hopdong_landau = %s, 
                        kiem_nhiem_2 = %s, giam_tru_kn2 = %s
                    WHERE magv = %s
                """,
            (
                con_nho.strip(),
                giam_tru_con_nho,
                hopdong_lan_dau.strip(),
                giam_tru_hopdong_landau,
                kiem_nhiem_2.strip(),
                giam_tru_kn2,
                magv,
            ),
        )

        cur.execute(
            "DELETE FROM kg_hoc_sinh_gioi WHERE magv = %s", (magv,)
        )
        cur.execute(
            """
                    INSERT INTO kg_hoc_sinh_gioi (magv, ngay_day_hsg, bdhsg_thuc_day, bdhsg_quy_doi)
                    VALUES (%s, %s, %s, %s)
                """,
            (
                magv,
                f"Từ {txt_tungay} đến {txt_denngay}",
                entry_thucday,
                entry_quydoi,
            ),
        )

        conn.commit()
        cur.close()
        conn.close()

        st.success(
            "Đã cập nhật thông tin và thống kê BDHSG thành công!"
        )
        st.rerun()
      except Exception as ex:
        st.error(f"Không thể lưu dữ liệu: {ex}")