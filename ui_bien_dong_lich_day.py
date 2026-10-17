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


def render_bien_dong_lich_day(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>Đăng ký Biến động Lịch"
      f" dạy - {tengv} (Tổ: {to_bm})</h4>",
      unsafe_allow_html=True,
  )

  # Hàm kiểm tra cột CSDL
  def ensure_columns_exist():
    try:
      conn = psycopg2.connect(DB_URI)
      cur = conn.cursor()
      cur.execute(
          "ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS gv_day_thay"
          " VARCHAR(100);"
      )
      cur.execute(
          "ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS phan_mon"
          " VARCHAR(100);"
      )
      conn.commit()
      cur.close()
      conn.close()
    except Exception:
      pass

  ensure_columns_exist()

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

  def chuan_hoa_ngay(text_input):
    s = text_input.strip()
    nam = get_nam_hoc()
    m1 = re.match(r"^(\d{1,2})[/-](\d{1,2})$", s)
    if m1:
      return date(nam, int(m1.group(2)), int(m1.group(1)))
    m2 = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m2:
      return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
    m3 = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", s)
    if m3:
      return date(int(m3.group(1)), int(m3.group(2)), int(m3.group(3)))
    return None

  def trich_khoi(ten_lop):
    m = re.search(r"\d+", str(ten_lop))
    return int(m.group()) if m else 10

  # Tải danh sách lớp bản thân
  def get_lops_ban_than():
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

  # Tải danh sách GV toàn trường
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

  # Tải phân môn theo khối từ PPCT
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

  ppct_map = get_ppct_map()
  gv_map = get_gv_toan_truong()
  lops_self = get_lops_ban_than()

  # ================= FORM ĐĂNG KÝ =================
  with st.form("form_bien_dong"):
    st.markdown("##### 📌 Đăng ký biến động mới")

    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
      loai = st.selectbox(
          "Loại biến động:",
          options=[
              "Nghỉ theo kế hoạch",
              "Nghỉ theo điều động",
              "Nghỉ việc riêng",
              "Dạy bù",
              "Dạy thay",
              "Bồi dưỡng HSG",
          ],
      )
    with r1_c2:
      ngay_str = st.text_input("Từ Ngày (VD: 15/09):", value="")
    with r1_c3:
      den_ngay_str = st.text_input(
          "Đến Ngày (Nghỉ dài hạn - tùy chọn):", value=""
      )

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
      buoi = st.selectbox("Buổi:", options=["Sáng", "Chiều"])
    with r2_c2:
      tiet = st.number_input("Tiết TKB:", min_value=1, max_value=5, value=1)
    with r2_c3:
      if loai == "Dạy thay":
        gv_thay_chon = st.selectbox(
            "GV được dạy thay:", options=list(gv_map.keys())
        )
      else:
        gv_thay_chon = st.selectbox(
            "GV được dạy thay:", options=["(Không áp dụng)"], disabled=True
        )

    r3_c1, r3_c2, r3_c3 = st.columns(3)
    with r3_c1:
      # Xử lý danh sách lớp tùy thuộc vào loại biến động
      if loai == "Dạy thay" and gv_thay_chon and gv_thay_chon != "(Không áp dụng)":
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
          lops_target = lops_self
        lop_chon = st.selectbox("Lớp dạy:", options=lops_target)
      elif loai == "Bồi dưỡng HSG":
        lop_chon = st.text_input("Lớp dạy (Nhập tên lớp HSG):", value="")
      else:
        lop_chon = st.selectbox("Lớp dạy:", options=lops_self)

    with r3_c2:
      if loai == "Bồi dưỡng HSG":
        phan_mon_chon = st.text_input("Phân môn:", value="BDHSG")
      else:
        khoi_val = trich_khoi(lop_chon) if lop_chon else 10
        ds_pm = ppct_map.get(khoi_val, ["Toán"])
        phan_mon_chon = st.selectbox(
            "Phân môn:", options=ds_pm if ds_pm else ["Toán"]
        )

    with r3_c3:
      lydo = st.text_input("Lý do / QĐ:", value="")

    submitted = st.form_submit_button(
        "➕ GỬI ĐĂNG KÝ", type="primary", use_container_width=True
    )

    if submitted:
      tu_ngay = chuan_hoa_ngay(ngay_str)
      if not tu_ngay:
        st.warning("Vui lòng nhập Ngày (hoặc Từ ngày) hợp lệ!")
      else:
        # 1. NGHỈ DÀI HẠN
        if loai.startswith("Nghỉ") and den_ngay_str.strip():
          den_ngay = chuan_hoa_ngay(den_ngay_str)
          if not den_ngay or den_ngay < tu_ngay:
            st.warning("Đến ngày không hợp lệ hoặc nhỏ hơn Từ ngày!")
          else:
            try:
              conn = psycopg2.connect(DB_URI)
              cur = conn.cursor()
              cur.execute(
                  "SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon,"
                  " COALESCE(phan_mon,'') FROM thoi_khoa_bieu WHERE magv = %s",
                  (magv,),
              )
              tkb_all = cur.fetchall()

              cur_d = tu_ngay
              count_added = 0
              while cur_d <= den_ngay:
                thu_num = cur_d.weekday() + 2
                for r in tkb_all:
                  t_thu = (
                      int(re.search(r"\d+", str(r[0])).group())
                      if re.search(r"\d+", str(r[0]))
                      else 2
                  )
                  if t_thu == thu_num and r[4].strip() not in ["SHDC", "SHL"]:
                    t_buoi, t_tiet, t_lop = r[1], r[2], r[3]
                    t_pm = r[5].strip() if r[5].strip() else r[4].strip()

                    cur.execute(
                        """
                                        SELECT id FROM bien_dong_lich_day 
                                        WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                                    """,
                        (magv, cur_d, t_buoi, t_tiet),
                    )
                    if not cur.fetchone():
                      cur.execute(
                          """
                                            INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                        """,
                          (
                              magv,
                              loai,
                              cur_d,
                              t_buoi,
                              t_tiet,
                              t_lop,
                              t_pm,
                              lydo or "Nghỉ dài hạn/Nghỉ Tết",
                          ),
                      )
                      count_added += 1
                cur_d += timedelta(days=1)

              conn.commit()
              cur.close()
              conn.close()

              sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, tu_ngay)
              if den_ngay != tu_ngay:
                sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, den_ngay)

              st.success(f"Đã tự động tạo {count_added} tiết nghỉ thành công!")
              st.rerun()
            except Exception as e:
              st.error(f"Không thể lưu nghỉ dài hạn: {e}")
        else:
          # 2. NGHỈ ĐƠN LẺ HOẶC DẠY BÙ / DẠY THAY / HSG
          thu_so = tu_ngay.weekday() + 2
          try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            if loai.startswith("Nghỉ"):
              cur.execute(
                  """
                                SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                            """,
                  (magv, str(thu_so), thu_so, buoi, int(tiet)),
              )
              tkb_slot = cur.fetchone()
              if not tkb_slot:
                st.error(
                    f"Thứ {thu_so} Tiết {tiet} ({buoi}) không có trên TKB!"
                )
                cur.close()
                conn.close()
              else:
                lop_tkb = tkb_slot[0].strip()
                pm_tkb = (
                    tkb_slot[2].strip()
                    if tkb_slot[2].strip()
                    else tkb_slot[1].strip()
                )

                cur.execute(
                    """
                                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                """,
                    (
                        magv,
                        loai,
                        tu_ngay,
                        buoi,
                        int(tiet),
                        lop_tkb,
                        pm_tkb,
                        lydo,
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()

                sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, tu_ngay)
                st.success("Đã báo nghỉ thành công!")
                st.rerun()
            else:
              # Kiểm tra trùng lịch bản thân
              cur.execute(
                  """
                                SELECT lop, mon FROM thoi_khoa_bieu 
                                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                            """,
                  (magv, str(thu_so), thu_so, buoi, int(tiet)),
              )
              tkb_self = cur.fetchone()
              if tkb_self:
                st.error(
                    f"⛔ Trùng giờ của bạn ở lớp [{tkb_self[0]}]"
                    f" ({tkb_self[1]})!"
                )
                cur.close()
                conn.close()
              else:
                # Kiểm tra lớp có đang học chính khóa khi Dạy bù
                if loai == "Dạy bù":
                  cur.execute(
                      """
                                        SELECT t.mon, COALESCE(g.tengv, t.magv) FROM thoi_khoa_bieu t
                                        LEFT JOIN giao_vien g ON t.magv = g.magv
                                        WHERE UPPER(TRIM(t.lop)) = %s AND (t.thu = %s OR t.thu = %s) AND t.buoi = %s AND t.tiet = %s
                                          AND t.mon IS NOT NULL AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
                                    """,
                      (
                          lop_chon.upper(),
                          str(thu_so),
                          thu_so,
                          buoi,
                          int(tiet),
                      ),
                  )
                  lich_lop = cur.fetchone()
                  if lich_lop:
                    st.error(
                        f"⛔ Lớp [{lop_chon}] vào tiết này đang học môn"
                        f" [{lich_lop[0]}] ({lich_lop[1]})!"
                    )
                    cur.close()
                    conn.close()
                    return

                gv_thay_val = (
                    gv_thay_chon.split(" (")[0]
                    if loai == "Dạy thay" and gv_thay_chon
                    else ""
                )
                cur.execute(
                    """
                                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
                                """,
                    (
                        magv,
                        loai,
                        tu_ngay,
                        buoi,
                        int(tiet),
                        lop_chon,
                        phan_mon_chon,
                        gv_thay_val,
                        lydo,
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()

                sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, tu_ngay)
                st.success(f"Đã lưu '{loai}' thành công!")
                st.rerun()
          except Exception as e:
            st.error(f"Lỗi: {e}")

  st.divider()

  # ================= BẢNG LỊCH SỬ =================
  st.markdown("##### 📋 Lịch sử biến động đã gửi")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop, ''), COALESCE(phan_mon, ''), COALESCE(gv_day_thay, ''), COALESCE(ly_do, ''), trang_thai
            FROM bien_dong_lich_day WHERE magv = %s ORDER BY ngay DESC, tiet_tkb ASC
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
              "Môn/PM",
              "GV thay",
              "Lý do",
              "Trạng thái",
          ],
      )
      df_hist["Ngày"] = df_hist["Ngày"].apply(
          lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else str(x)
      )
      st.dataframe(df_hist, use_container_width=True, hide_index=True)

      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        rec_id_huy = st.number_input(
            "Nhập ID dòng cần hủy:", min_value=1, step=1, key="input_huy_bd"
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

            st.success("Đã hủy thành công và đồng bộ lại Sổ Báo Giảng!")
            st.rerun()
          except Exception as e:
            st.error(f"Không thể hủy: {e}")
    else:
      st.info("Chưa có lịch sử biến động nào.")
  except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")