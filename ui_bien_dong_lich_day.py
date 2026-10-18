from datetime import date, datetime, timedelta
import re
import psycopg2
import streamlit as st
from config import DB_URI


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def trich_khoi(ten_lop):
  m = re.search(r"\d+", str(ten_lop))
  return int(m.group()) if m else 10


def chuan_hoa_ngay(text_input):
  s = text_input.strip()
  nam = 2026
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


def render_bien_dong_lich_day(session):
  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>⛔ Đăng Ký Biến Động Lịch"
      " Dạy & Báo Nghỉ</h4>",
      unsafe_allow_html=True,
  )

  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  # Đảm bảo cấu trúc cột CSDL
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

  # Lấy danh sách lớp bản thân từ TKB
  ds_lop_self = []
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
    ds_lop_self = [r[0].strip() for r in cur.fetchall()]
    cur.close()
    conn.close()
  except Exception:
    pass

  # Lấy danh sách giáo viên toàn trường
  map_gv_toan_truong = {}
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "SELECT magv, tengv FROM giao_vien WHERE magv != %s ORDER BY tengv",
        (magv,),
    )
    map_gv_toan_truong = {
        f"{tgv} ({mgv})": mgv for mgv, tgv in cur.fetchall()
    }
    cur.close()
    conn.close()
  except Exception:
    pass

  # Lấy phân môn theo PPCT
  ppct_mon_khoi_map = {10: [], 11: [], 12: []}
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
    for kh, pm in cur.fetchall():
      if pm and pm not in ppct_mon_khoi_map.setdefault(kh, []):
        ppct_mon_khoi_map[kh].append(pm)
    cur.close()
    conn.close()
  except Exception:
    pass

  with st.form("form_bien_dong"):
    st.markdown(f"**📝 Đăng ký biến động mới (Tổ: {to_bm})**")

    c1, c2, c3 = st.columns(3)
    with c1:
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
    with c2:
      raw_tu_ngay = st.text_input(
          "Từ Ngày (VD: 15/09 hoặc 15/09/2026):",
          value=datetime.now().strftime("%d/%m/%Y"),
      )
    with c3:
      raw_den_ngay = st.text_input(
          "Đến Ngày (Nghỉ dài hạn - tùy chọn):", value=""
      )

    c4, c5, c6 = st.columns(3)
    with c4:
      buoi = st.selectbox("Buổi:", options=["Sáng", "Chiều"])
    with c5:
      tiet = st.number_input("Tiết TKB:", min_value=1, max_value=5, value=1)
    with c6:
      gv_thay_label = st.selectbox(
          "GV được dạy thay:",
          options=["(Không áp dụng)"] + list(map_gv_toan_truong.keys()),
      )

    # Auto-fill TKB chuẩn từ CSDL
    auto_lop = ""
    auto_pm = ""
    co_tiets_tkb = False
    tu_ngay_obj = chuan_hoa_ngay(raw_tu_ngay)

    if tu_ngay_obj and not raw_den_ngay.strip():
      thu_so = tu_ngay_obj.weekday() + 2
      try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(
            """
                    SELECT lop, mon, COALESCE(phan_mon, '') 
                    FROM thoi_khoa_bieu 
                    WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                """,
            (magv, str(thu_so), thu_so, buoi, int(tiet)),
        )
        r_tkb = cur.fetchone()
        cur.close()
        conn.close()
        if r_tkb:
          auto_lop = r_tkb[0].strip()
          auto_pm = r_tkb[2].strip() if r_tkb[2].strip() else r_tkb[1].strip()
          co_tiets_tkb = True
          st.success(
              f"✔ Khớp TKB Thứ {thu_so} Tiết {tiet} ({buoi}): [{auto_lop}] -"
              f" [{auto_pm}]"
          )
        else:
          st.error(
              f"⚠️ Thứ {thu_so} Tiết {tiet} ({buoi}): KHÔNG CÓ TIẾT TRÊN TKB!"
          )
      except Exception:
        pass

    c7, c8, c9 = st.columns(3)
    with c7:
      if loai.startswith("Nghỉ"):
        # Báo nghỉ: Khóa chặt lớp theo TKB, không cho người dùng sửa
        lop = st.text_input(
            "Lớp dạy (Tự động từ TKB):", value=auto_lop, disabled=True
        )
      elif loai == "Bồi dưỡng HSG":
        lop = st.text_input("Lớp dạy:", value="")
      else:
        lop = st.selectbox(
            "Lớp dạy:", options=ds_lop_self if ds_lop_self else [""]
        )

    with c8:
      if loai.startswith("Nghỉ"):
        # Báo nghỉ: Khóa chặt phân môn theo TKB, không cho người dùng sửa
        phan_mon = st.text_input(
            "Phân môn (Tự động từ TKB):", value=auto_pm, disabled=True
        )
      elif loai == "Bồi dưỡng HSG":
        phan_mon = st.text_input("Phân môn:", value="BDHSG")
      else:
        khoi_chon = trich_khoi(lop) if lop else 10
        ds_pm_khoi = ppct_mon_khoi_map.get(khoi_chon, [to_bm])
        phan_mon = st.selectbox(
            "Phân môn:", options=ds_pm_khoi if ds_pm_khoi else [to_bm]
        )

    with c9:
      lydo = st.text_input("Lý do / QĐ:", value="")

    submitted = st.form_submit_button(
        "➕ GỬI ĐĂNG KÝ BIẾN ĐỘNG", type="primary", use_container_width=True
    )

    if submitted:
      if not tu_ngay_obj:
        st.error("Vui lòng nhập Ngày hợp lệ!")
        return

      try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()

        # 1. BÁO NGHỈ DÀI HẠN (Nghỉ Tết, nghỉ hè...)
        if loai.startswith("Nghỉ") and raw_den_ngay.strip():
          den_ngay_obj = chuan_hoa_ngay(raw_den_ngay)
          if not den_ngay_obj or den_ngay_obj < tu_ngay_obj:
            st.error("Đến ngày không hợp lệ hoặc nhỏ hơn Từ ngày!")
            cur.close()
            conn.close()
            return

          cur.execute(
              "SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon,"
              " COALESCE(phan_mon,'') FROM thoi_khoa_bieu WHERE magv = %s",
              (magv,),
          )
          tkb_all = cur.fetchall()

          cur_d = tu_ngay_obj
          count_added = 0
          while cur_d <= den_ngay_obj:
            thu_num = cur_d.weekday() + 2
            for r in tkb_all:
              t_thu = (
                  int(re.search(r"\d+", str(r[0])).group())
                  if re.search(r"\d+", str(r[0]))
                  else 2
              )
              if t_thu == thu_num and r[4].strip() not in ["SHDC", "SHL"]:
                t_buoi = r[1]
                t_tiet = r[2]
                t_lop = r[3]
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
                          lydo or "Nghỉ dài hạn",
                      ),
                  )
                  count_added += 1
            cur_d += timedelta(days=1)

          conn.commit()
          cur.close()
          conn.close()
          st.success(f"Đã tự động tạo {count_added} tiết nghỉ thành công!")
          st.rerun()

        # 2. BÁO NGHỈ ĐƠN LẺ HOẶC DẠY BÙ / DẠY THAY
        else:
          thu_so = tu_ngay_obj.weekday() + 2

          # Chống ghi sai dữ liệu khi Báo nghỉ đơn lẻ
          if loai.startswith("Nghỉ"):
            if not co_tiets_tkb:
              st.error(
                  f"⛔ KHÔNG THỂ BÁO NGHỈ! Vào Thứ {thu_so} Tiết {tiet}"
                  f" ({buoi}) thầy/cô KHÔNG CÓ TIẾT TRÊN TKB!"
              )
              cur.close()
              conn.close()
              return
            lop = auto_lop
            phan_mon = auto_pm

          elif loai in ["Dạy bù", "Dạy thay"]:
            if not lop:
              st.error(f"Vui lòng chọn Lớp {loai}!")
              cur.close()
              conn.close()
              return

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
                  f"⛔ TRÙNG GIỜ CỦA BẠN!\n\nVào Thứ {thu_so} Tiết {tiet}"
                  f" ({buoi}), bạn đang dạy lớp [{tkb_self[0]}] (Môn:"
                  f" {tkb_self[1]})!"
              )
              cur.close()
              conn.close()
              return

            # Kiểm tra trùng lịch của lớp khi dạy bù
            if loai == "Dạy bù":
              cur.execute(
                  """
                            SELECT t.mon, COALESCE(g.tengv, t.magv)
                            FROM thoi_khoa_bieu t
                            LEFT JOIN giao_vien g ON t.magv = g.magv
                            WHERE UPPER(TRIM(t.lop)) = %s 
                              AND (t.thu = %s OR t.thu = %s) 
                              AND t.buoi = %s 
                              AND t.tiet = %s
                              AND t.mon IS NOT NULL 
                              AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
                        """,
                  (lop.upper(), str(thu_so), thu_so, buoi, int(tiet)),
              )
              lich_lop = cur.fetchone()
              if lich_lop:
                st.error(
                    f"⛔ Lớp [{lop}] vào Thứ {thu_so} Tiết {tiet} ({buoi}) đang"
                    f" có tiết chính khóa môn [{lich_lop[0]}] giáo viên"
                    f" [{lich_lop[1]}]!"
                )
                cur.close()
                conn.close()
                return

          gv_thay_str = (
              map_gv_toan_truong.get(gv_thay_label, "")
              if gv_thay_label != "(Không áp dụng)"
              else ""
          )
          if loai == "Dạy thay" and not gv_thay_str:
            st.error("Vui lòng chọn GV được dạy thay!")
            cur.close()
            conn.close()
            return

          cur.execute(
              """
                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
                """,
              (
                  magv,
                  loai,
                  tu_ngay_obj,
                  buoi,
                  int(tiet),
                  lop,
                  phan_mon,
                  gv_thay_str,
                  lydo,
              ),
          )
          conn.commit()
          cur.close()
          conn.close()
          st.success(
              f"Đã lưu thành công đăng ký '{loai}' ngày"
              f" {tu_ngay_obj.strftime('%d/%m/%Y')}!"
          )
          st.rerun()

      except Exception as e:
        st.error(f"Không thể lưu: {e}")

  # Lịch sử biến động
  st.divider()
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
      data_list = []
      for r in rows:
        ngay_f = (
            r[2].strftime("%d/%m/%Y")
            if hasattr(r[2], "strftime")
            else str(r[2])
        )
        data_list.append(
            {
                "ID": r[0],
                "Loại việc": r[1],
                "Ngày": ngay_f,
                "Buổi": r[3],
                "Tiết": r[4],
                "Lớp": r[5],
                "Môn/PM": r[6],
                "GV Thay": r[7],
                "Lý do": r[8],
                "Trạng thái": r[9],
            }
        )
      st.dataframe(data_list, use_container_width=True, hide_index=True)

      selected_id = st.number_input(
          "Nhập ID biến động muốn hủy:", min_value=1, step=1, key="huy_id"
      )
      if st.button(
          "❌ Hủy Đăng Ký Theo ID", type="secondary", use_container_width=True
      ):
        try:
          conn = psycopg2.connect(DB_URI)
          cur = conn.cursor()
          cur.execute(
              "DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s",
              (int(selected_id), magv),
          )
          conn.commit()
          cur.close()
          conn.close()
          st.success(f"Đã hủy thành công bản ghi ID {selected_id}!")
          st.rerun()
        except Exception as e:
          st.error(f"Không thể hủy: {e}")
    else:
      st.info("Chưa có lịch sử đăng ký biến động nào.")
  except Exception as e:
    st.error(f"Lỗi tải lịch sử: {e}")
