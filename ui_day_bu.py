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
    .stTextInput input, .stSelectbox div, .stNumberInput input, .stDateInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_day_bu(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #1E8449;'>Đăng Ký Dạy Bù - GV:"
      f" {tengv}</h4>",
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

  def trich_khoi(ten_lop):
    m = re.search(r"\d+", str(ten_lop))
    return int(m.group()) if m else 10

  def get_ppct_map():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          """
                SELECT DISTINCT khoi, COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE (UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%')
                  AND khoi IS NOT NULL
                ORDER BY khoi, 2 ASC
            """,
          (to_bm, to_bm),
      )
      mapping = {10: [], 11: [], 12: []}
      for kh, pm in cur.fetchall():
        if pm and pm not in mapping.setdefault(kh, []):
          mapping[kh].append(pm)
      cur.close()
      conn.close()
      return mapping
    except Exception:
      return {10: [], 11: [], 12: []}

  def get_lop_ban_than():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          """
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                ORDER BY lop
            """,
          (magv,),
      )
      lops = [r[0].strip() for r in cur.fetchall()]
      cur.close()
      conn.close()
      return lops
    except Exception:
      return []

  ppct_map = get_ppct_map()
  lops_self = get_lop_ban_than()

  # ================= FORM ĐĂNG KÝ =================
  with st.form("form_day_bu"):
    st.markdown("##### 📌 Đăng ký Lịch Dạy Bù (Kiểm tra chống trùng đa tầng)")

    c1, c2, c3 = st.columns(3)
    with c1:
      ngay_str = st.text_input("Ngày dạy bù (VD: 15/09):", value="")
    with c2:
      buoi = st.selectbox("Buổi:", options=["Chiều", "Sáng"], index=0)
    with c3:
      tiet = st.number_input("Tiết dạy:", min_value=1, max_value=5, value=1)

    c4, c5, c6 = st.columns(3)
    with c4:
      lop = st.selectbox("Lớp dạy bù:", options=lops_self if lops_self else [""])
    with c5:
      khoi = trich_khoi(lop) if lop else 10
      ds_pm = ppct_map.get(khoi, ["Toán"])
      pm = st.selectbox("Phân môn:", options=ds_pm if ds_pm else ["Toán"])
    with c6:
      lydo = st.text_input("Lý do / Căn cứ:", value="")

    submitted = st.form_submit_button(
        "➕ GỬI DẠY BÙ", type="primary", use_container_width=True
    )

    if submitted:
      d = chuan_hoa_ngay(ngay_str)
      if not d:
        st.warning("Vui lòng nhập Ngày dạy bù hợp lệ (VD: 15/09)!")
      elif not lop or not pm:
        st.warning("Vui lòng chọn Lớp và Phân môn dạy bù!")
      else:
        thu_so = d.weekday() + 2
        ngay_f = d.strftime("%d/%m/%Y")

        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()

          # TẦNG 1: Kiểm tra bản thân có bận dạy chính khóa không
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
                f"⛔ BẠN ĐANG CÓ TIẾT DẠY! Thứ {thu_so} Tiết {tiet} ({buoi})"
                f" đang có giờ chính khóa ở lớp [{tkb_me[0]}] ({tkb_me[1]})!"
            )
            cur.close()
            conn.close()
          else:
            # TẦNG 2: Kiểm tra bản thân đã đăng ký tiết này cho lớp khác chưa
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
                  f"⛔ BẠN ĐÃ CÓ LỊCH DẠY! Vào Tiết {tiet} ({buoi}) ngày"
                  f" {ngay_f}, bạn đã đăng ký [{bd_me[0]}] cho lớp [{bd_me[1]}]!"
              )
              cur.close()
              conn.close()
            else:
              # TẦNG 3: Kiểm tra lớp có đang học chính khóa theo TKB không
              cur.execute(
                  """
                                SELECT t.mon, COALESCE(g.tengv, t.magv)
                                FROM thoi_khoa_bieu t
                                LEFT JOIN giao_vien g ON t.magv = g.magv
                                WHERE UPPER(TRIM(t.lop)) = %s AND (t.thu = %s OR t.thu = %s) AND t.buoi = %s AND t.tiet = %s
                                  AND t.mon IS NOT NULL AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
                            """,
                  (lop.upper(), str(thu_so), thu_so, buoi, int(tiet)),
              )
              lop_ban = cur.fetchone()
              if lop_ban:
                st.error(
                    f"⛔ LỚP [{lop}] KHÔNG RẢNH! Tiết này lớp đang học môn"
                    f" [{lop_ban[0]}] do GV [{lop_ban[1]}] dạy."
                )
                cur.close()
                conn.close()
              else:
                # TẦNG 4: Chống tranh lớp - đã có GV khác đăng ký dạy bù chưa
                cur.execute(
                    """
                                    SELECT b.magv, COALESCE(g.tengv, b.magv), b.loai, COALESCE(b.phan_mon, '')
                                    FROM bien_dong_lich_day b
                                    LEFT JOIN giao_vien g ON b.magv = g.magv
                                    WHERE UPPER(TRIM(b.lop)) = %s 
                                      AND b.ngay = %s AND b.buoi = %s AND b.tiet_tkb = %s 
                                      AND b.trang_thai != 'DA_HUY' 
                                      AND b.loai IN ('Dạy bù', 'Dạy thay', 'Bồi dưỡng HSG')
                                """,
                    (lop.upper(), d, buoi, int(tiet)),
                )
                gv_da_dk = cur.fetchone()
                if gv_da_dk:
                  st.error(
                      f"⛔ LỚP [{lop}] ĐÃ CÓ GV KHÁC ĐĂNG KÝ TRƯỚC!\n- Tiết"
                      f" {tiet} ({buoi}) ngày {ngay_f}: Thầy/Cô"
                      f" [{gv_da_dk[1]}] đã đăng ký [{gv_da_dk[2]}]"
                      f" ({gv_da_dk[3]})."
                  )
                  cur.close()
                  conn.close()
                else:
                  # Lưu vào CSDL
                  cur.execute(
                      """
                                        INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                        VALUES (%s, 'Dạy bù', %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                    """,
                      (magv, d, buoi, int(tiet), lop, pm, lydo),
                  )
                  conn.commit()
                  cur.close()
                  conn.close()

                  sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d)
                  st.success(
                      f"Đã đăng ký Dạy bù lớp {lop} ngày {ngay_f} thành công!"
                  )
                  st.rerun()
        except Exception as e:
          st.error(f"Lỗi: {e}")

  st.divider()

  # ================= BẢNG LỊCH SỬ =================
  st.markdown("##### 📋 Danh sách các tiết đã đăng ký Dạy Bù")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(ly_do,'')
            FROM bien_dong_lich_day 
            WHERE magv = %s AND loai = 'Dạy bù' AND trang_thai != 'DA_HUY'
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
          columns=["ID", "Ngày", "Buổi", "Tiết", "Lớp", "Phân môn", "Lý do"],
      )
      df_hist["Ngày"] = df_hist["Ngày"].apply(
          lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else str(x)
      )
      st.dataframe(df_hist, use_container_width=True, hide_index=True)

      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        rec_id_huy = st.number_input(
            "Nhập ID tiết cần hủy:", min_value=1, step=1, key="input_huy_day_bu"
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button("❌ Hủy tiết dạy bù", type="primary", use_container_width=True):
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
      st.info("Chưa có lịch sử đăng ký dạy bù nào.")
  except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")