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
    div.stButton > button {
        border-radius: 24px !important;
        border: 1px solid #d0d7de !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #c0392b, #e74c3c) !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_bao_nghi(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      f"<h4 style='text-align: center; color: #900C3F;'>Báo Nghỉ Giảng Dạy - GV:"
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

  with st.form("form_bao_nghi"):
    st.markdown("##### 📌 Đăng ký Báo Nghỉ")
    f1, f2, f3 = st.columns(3)
    with f1:
      loai = st.selectbox(
          "Lý do nghỉ:",
          options=[
              "Nghỉ việc riêng",
              "Nghỉ theo kế hoạch",
              "Nghỉ theo điều động",
          ],
      )
    with f2:
      ngay_str = st.text_input("Từ ngày (VD: 15/09):", value="")
    with f3:
      den_ngay_str = st.text_input(
          "Đến ngày (Dài hạn/Nghỉ Tết):", value=""
      )

    f4, f5, f6 = st.columns(3)
    with f4:
      buoi = st.selectbox("Buổi:", options=["Sáng", "Chiều"])
    with f5:
      tiet = st.number_input("Tiết TKB:", min_value=1, max_value=5, value=1)
    with f6:
      lydo = st.text_input("Chi tiết lý do / QĐ (*):", value="")

    submitted = st.form_submit_button(
        "⛔ GỬI BÁO NGHỈ", type="primary", use_container_width=True
    )

    if submitted:
      if not lydo.strip():
        st.warning("Thầy/Cô BẮT BUỘC nhập lý do chi tiết!")
      else:
        d_tu = chuan_hoa_ngay(ngay_str)
        if not d_tu:
          st.warning("Nhập ngày không hợp lệ!")
        else:
          if den_ngay_str.strip():
            d_den = chuan_hoa_ngay(den_ngay_str)
            if not d_den or d_den < d_tu:
              st.warning("Đến ngày không hợp lệ!")
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

                cur_d = d_tu
                count = 0
                while cur_d <= d_den:
                  thu_num = cur_d.weekday() + 2
                  for r in tkb_all:
                    t_thu = (
                        int(re.search(r"\d+", str(r[0])).group())
                        if re.search(r"\d+", str(r[0]))
                        else 2
                    )
                    if t_thu == thu_num and r[4].strip() not in [
                        "SHDC",
                        "SHL",
                    ]:
                      t_pm = r[5].strip() if r[5].strip() else r[4].strip()
                      cur.execute(
                          """
                                                SELECT id FROM bien_dong_lich_day 
                                                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                                            """,
                          (magv, cur_d, r[1], r[2]),
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
                                r[1],
                                r[2],
                                r[3],
                                t_pm,
                                lydo,
                            ),
                        )
                        count += 1
                  cur_d += timedelta(days=1)
                conn.commit()
                cur.close()
                conn.close()

                sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_tu)
                if d_den != d_tu:
                  sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_den)

                st.success(f"Đã báo nghỉ thành công {count} tiết!")
                st.rerun()
              except Exception as e:
                st.error(f"Lỗi: {e}")
          else:
            thu_so = d_tu.weekday() + 2
            try:
              conn = psycopg2.connect(DB_URI)
              cur = conn.cursor()
              cur.execute(
                  """
                                SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                            """,
                  (magv, str(thu_so), thu_so, buoi, int(tiet)),
              )
              r_tkb = cur.fetchone()
              if not r_tkb:
                st.error("Tiết này bạn không có lịch dạy trên TKB!")
                cur.close()
                conn.close()
              else:
                lop_tkb = r_tkb[0].strip()
                pm_tkb = (
                    r_tkb[2].strip() if r_tkb[2].strip() else r_tkb[1].strip()
                )

                cur.execute(
                    """
                                    SELECT id FROM bien_dong_lich_day 
                                    WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                                """,
                    (magv, d_tu, buoi, int(tiet)),
                )
                if cur.fetchone():
                  st.warning("Bạn đã báo nghỉ tiết này rồi!")
                  cur.close()
                  conn.close()
                else:
                  cur.execute(
                      """
                                        INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                    """,
                      (magv, loai, d_tu, buoi, int(tiet), lop_tkb, pm_tkb, lydo),
                  )
                  conn.commit()
                  cur.close()
                  conn.close()

                  sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_tu)
                  st.success(f"Đã báo nghỉ lớp {lop_tkb} ({pm_tkb})!")
                  st.rerun()
            except Exception as e:
              st.error(f"Lỗi: {e}")

  st.divider()
  st.markdown("##### 📋 Lịch sử báo nghỉ")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(ly_do,'')
            FROM bien_dong_lich_day 
            WHERE magv = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
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
              "Loại nghỉ",
              "Ngày",
              "Buổi",
              "Tiết",
              "Lớp",
              "Phân môn",
              "Lý do",
          ],
      )
      df_hist["Ngày"] = df_hist["Ngày"].apply(
          lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else str(x)
      )
      st.dataframe(df_hist, use_container_width=True, hide_index=True)

      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        rec_id_huy = st.number_input(
            "Nhập ID cần hủy:", min_value=1, step=1, key="input_huy_nghi"
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button("❌ Hủy báo nghỉ", type="primary", use_container_width=True):
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

            st.success("Đã hủy thành công!")
            st.rerun()
          except Exception as e:
            st.error(f"Lỗi: {e}")
    else:
      st.info("Chưa có lịch sử báo nghỉ.")
  except Exception as e:
    st.error(f"Lỗi nạp dữ liệu: {e}")