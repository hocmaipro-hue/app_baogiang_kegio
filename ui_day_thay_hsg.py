from datetime import date, datetime, timedelta
import re
import pandas as pd
import psycopg2
import service_so_bao_giang as sbg_service
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
        border-color: #d4ac0d !important;
        color: #d4ac0d !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #d4ac0d, #b7950b) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #b7950b, #9a7d0a) !important;
        color: white !important;
    }
    .stTextInput input, .stSelectbox div, .stNumberInput input, .stDateInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_day_thay_hsg(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #B7950B;'>Dạy Thay & Bồi Dưỡng"
      f" HSG - GV: {tengv}</h4>",
      unsafe_allow_html=True,
  )

  def get_nam_hoc():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          "SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'"
      )
      r = cur.fetchone()
      cur.close()
      conn.close()
      if r:
        return datetime.strptime(r[0].strip(), "%Y-%m-%d").year
    except Exception:
      pass
    return 2026

  def chuan_hoa_ngay(s):
    s = s.strip()
    nam = get_nam_hoc()
    m1 = re.match(r"^(\d{1,2})[/-](\d{1,2})$", s)
    if m1:
      return date(nam, int(m1.group(2)), int(m1.group(1)))
    m2 = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m2:
      return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
    return None

  def get_gv_toan_truong():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          "SELECT magv, tengv FROM giao_vien WHERE magv != %s ORDER BY tengv",
          (magv,),
      )
      res = {f"{tgv} ({mgv})": mgv for mgv, tgv in cur.fetchall()}
      cur.close()
      conn.close()
      return res
    except Exception:
      return {}

  def get_phan_mon_to():
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

  gv_map = get_gv_toan_truong()
  ds_pms = get_phan_mon_to()

  # ================= FORM ĐĂNG KÝ =================
  with st.form("form_day_thay_hsg"):
    st.markdown("##### 📌 Đăng ký Dạy Thay / Bồi Dưỡng HSG")

    c1, c2, c3 = st.columns(3)
    with c1:
      loai = st.selectbox(
          "Công việc:", options=["Dạy thay", "Bồi dưỡng HSG"], index=0
      )
    with c2:
      ngay_str = st.text_input("Ngày dạy (VD: 15/09):", value="")
    with c3:
      buoi = st.selectbox("Buổi:", options=["Sáng", "Chiều"], index=0)

    c4, c5, c6 = st.columns(3)
    with c4:
      tiet = st.number_input("Tiết dạy:", min_value=1, max_value=5, value=1)
    with c5:
      if loai == "Dạy thay":
        gv_thay_chon = st.selectbox(
            "GV được dạy thay:",
            options=list(gv_map.keys()) if gv_map else [""],
        )
      else:
        gv_thay_chon = st.selectbox(
            "GV được dạy thay:", options=["(Không áp dụng)"], disabled=True
        )
    with c6:
      # Lấy danh sách lớp của GV được dạy thay hoặc nhập tự do nếu HSG
      if loai == "Dạy thay" and gv_thay_chon and gv_thay_chon != "":
        target_magv = gv_map.get(gv_thay_chon, "")
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()
          cur.execute(
              """
                        SELECT DISTINCT lop FROM thoi_khoa_bieu 
                        WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                        ORDER BY lop
                    """,
              (target_magv,),
          )
          lops_target = [r[0].strip() for r in cur.fetchall()]
          cur.close()
          conn.close()
        except Exception:
          lops_target = []
        lop = st.selectbox(
            "Lớp dạy / Đội tuyển:",
            options=lops_target if lops_target else [""],
        )
      else:
        lop = st.text_input(
            "Lớp dạy / Đội tuyển (Nhập tên lớp/đội tuyển):", value=""
        )

    c7, c8 = st.columns(2)
    with c7:
      if loai == "Bồi dưỡng HSG":
        pm = st.text_input("Phân môn:", value="BDHSG")
      else:
        pm = st.selectbox("Phân môn:", options=ds_pms)
    with c8:
      lydo = st.text_input("Tên bài / Lý do:", value="")

    submitted = st.form_submit_button(
        "➕ GỬI ĐĂNG KÝ", type="primary", use_container_width=True
    )

    if submitted:
      d = chuan_hoa_ngay(ngay_str)
      if not d:
        st.warning("Vui lòng nhập Ngày hợp lệ (VD: 15/09)!")
      elif loai == "Dạy thay" and (not gv_thay_chon or not lop):
        st.warning("Vui lòng chọn GV được thay và Lớp dạy!")
      else:
        thu_so = d.weekday() + 2
        ngay_f = d.strftime("%d/%m/%Y")
        gv_thay_val = (
            gv_thay_chon.split(" (")[0]
            if loai == "Dạy thay" and gv_thay_chon
            else ""
        )

        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()

          # 1. Chống trùng lịch TKB chính khóa của bạn
          cur.execute(
              """
                        SELECT lop, mon FROM thoi_khoa_bieu 
                        WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                    """,
              (magv, str(thu_so), thu_so, buoi, int(tiet)),
          )
          tkb_me = cur.fetchone()
          if tkb_me:
            st.error(
                f"⛔ Trùng lịch! Thứ {thu_so} Tiết {tiet} ({buoi}) bạn đang dạy"
                f" lớp [{tkb_me[0]}]!"
            )
            cur.close()
            conn.close()
          else:
            # 2. Chống trùng lịch biến động khác của bản thân
            cur.execute(
                """
                            SELECT loai, lop FROM bien_dong_lich_day 
                            WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND trang_thai != 'DA_HUY'
                        """,
                (magv, d, buoi, int(tiet)),
            )
            bd_me = cur.fetchone()
            if bd_me:
              st.error(
                  f"⛔ Trùng lịch! Tiết {tiet} ({buoi}) ngày {ngay_f} bạn đã có"
                  f" lịch [{bd_me[0]}] lớp [{bd_me[1]}] rồi!"
              )
              cur.close()
              conn.close()
            else:
              # Lưu vào CSDL
              cur.execute(
                  """
                                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
                                """,
                  (
                      magv,
                      loai,
                      d,
                      buoi,
                      int(tiet),
                      lop,
                      pm,
                      gv_thay_val,
                      lydo,
                  ),
              )
              conn.commit()
              cur.close()
              conn.close()

              sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d)
              st.success(
                  f"Đã gửi đăng ký [{loai}] ngày {ngay_f} thành công!"
              )
              st.rerun()
        except Exception as e:
          st.error(f"Lỗi: {e}")

  st.divider()

  # ================= BẢNG LỊCH SỬ =================
  st.markdown("##### 📋 Danh sách tiết Dạy Thay & BDHSG")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(gv_day_thay,''), COALESCE(ly_do,'')
            FROM bien_dong_lich_day 
            WHERE magv = %s AND loai IN ('Dạy thay', 'Bồi dưỡng HSG') AND trang_thai != 'DA_HUY'
            ORDER BY ngay DESC, tiet_tkb ASC
        """,
        (magv,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
      df_hist = pd.DataFrame(
          rows,
          columns=[
              "ID",
              "Loại việc",
              "Ngày",
              "Buổi",
              "Tiết",
              "Lớp",
              "Phân môn",
              "GV được thay",
              "Tên bài / Lý do",
          ],
      )
      df_hist["Ngày"] = df_hist["Ngày"].apply(
          lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else str(x)
      )
      st.dataframe(df_hist, use_container_width=True, hide_index=True)

      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        rec_id_huy = st.number_input(
            "Nhập ID dòng cần hủy:", min_value=1, step=1, key="input_huy_thay_hsg"
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button(
            "❌ Hủy đăng ký này", type="primary", use_container_width=True
        ):
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "SELECT ngay FROM bien_dong_lich_day WHERE id = %s AND magv ="
                " %s",
                (int(rec_id_huy), magv),
            )
            r_ngay = cur.fetchone()

            cur.execute(
                "DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s",
                (int(rec_id_huy), magv),
            )
            conn.commit()
            cur.close()
            conn.close()

            if r_ngay and r_ngay[0]:
              sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, r_ngay[0])

            st.success("Đã hủy và cập nhật lại Sổ Báo Giảng!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể hủy: {e}")
    else:
      st.info("Chưa có lịch sử đăng ký Dạy thay hoặc Bồi dưỡng HSG nào.")
  except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")