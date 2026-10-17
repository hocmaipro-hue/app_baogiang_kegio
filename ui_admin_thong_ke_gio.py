from datetime import datetime, timedelta
import pandas as pd
import psycopg2
import streamlit as st
from config import DB_URI


def inject_custom_css():
  st.markdown(
      """
    <style>
    div.stButton > button {
        border-radius: 22px !important;
        border: 1px solid #d0d7de !important;
        padding: 6px 14px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 3px 8px rgba(0,0,0,0.1) !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def fmt_num(val):
  if val is None:
    return "0"
  try:
    v = float(val)
    return str(int(v)) if v.is_integer() else f"{v:.1f}"
  except Exception:
    return "0"


def to_float(val, default=0.0):
  if val is None:
    return default
  try:
    s = str(val).strip().replace(",", ".")
    return float(s) if s else default
  except Exception:
    return default


def ensure_database_schema():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "ALTER TABLE thoi_khoa_bieu ADD COLUMN IF NOT EXISTS phan_mon"
        " VARCHAR(100);"
    )
    conn.commit()
    cur.close()
    conn.close()
  except Exception:
    pass


def get_ngay_bat_dau_nam_hoc():
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    cur.execute(
        "SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'"
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
      return datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
  except Exception:
    pass
  return datetime.strptime("2026-09-07", "%Y-%m-%d").date()


def render_admin_thong_ke_gio(session):
  inject_custom_css()
  ensure_database_schema()

  role = get_val(session, "role", "GV")
  to_bm = get_val(session, "to_bo_mon", "")
  is_admin = str(role).upper() in ["ADMIN", "BGH", "QUẢN TRỊ", "BAN GIÁM HIỆU"]

  tieu_de = (
      "BẢNG TỔNG HỢP & ĐỐI CHIẾU TIẾT DẠY TOÀN TRƯỜNG"
      if is_admin
      else f"BẢNG TỔNG HỢP TIẾT DẠY - TỔ {to_bm.upper()}"
  )
  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>{tieu_de}</h4>",
      unsafe_allow_html=True,
  )

  c1, c2, c3 = st.columns([1, 1, 2])
  with c1:
    tu_tuan = st.number_input("Từ Tuần:", min_value=1, max_value=45, value=1)
  with c2:
    den_tuan = st.number_input("Đến Tuần:", min_value=1, max_value=45, value=4)

  so_tuan = den_tuan - tu_tuan + 1
  base_monday = get_ngay_bat_dau_nam_hoc()
  ngay_bd_dot = base_monday + timedelta(days=(int(tu_tuan) - 1) * 7)
  ngay_kt_dot = base_monday + timedelta(days=(int(den_tuan) - 1) * 7 + 6)

  with c3:
    st.write("")
    st.caption(
        f"👉 Đợt kiểm tra: {so_tuan} tuần ({ngay_bd_dot.strftime('%d/%m')} -"
        f" {ngay_kt_dot.strftime('%d/%m/%Y')})"
    )

  st.divider()

  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()

    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name"
        " = 'giao_vien';"
    )
    gv_cols = set(r[0] for r in cur.fetchall())

    def col_safe(col_name):
      return f"COALESCE({col_name}::text, '0')" if col_name in gv_cols else "'0'"

    base_sql = f"""
            SELECT magv, tengv, to_bo_mon, {col_safe('dinh_muc_tiet')}, {col_safe('tiet_giam_tru')},
                   {col_safe('giam_tru_con_nho')}, {col_safe('giam_tru_hopdong_landau')}, {col_safe('giam_tru_kn2')}
            FROM giao_vien
        """
    if is_admin:
      cur.execute(base_sql + " ORDER BY to_bo_mon, tengv")
    else:
      cur.execute(base_sql + " WHERE to_bo_mon = %s ORDER BY tengv", (to_bm,))
    danh_sach_gv = cur.fetchall()

    cur.execute(
        "SELECT DISTINCT ap_dung_tu_tuan FROM thoi_khoa_bieu ORDER BY"
        " ap_dung_tu_tuan ASC"
    )
    cac_moc_tuan = [r[0] for r in cur.fetchall() if r[0] is not None]

    cur.execute("""
            SELECT magv, ap_dung_tu_tuan, COUNT(*) FROM thoi_khoa_bieu 
            WHERE UPPER(TRIM(mon)) NOT IN ('SHDC', 'SHL', 'SINH HOẠT LỚP', 'CHÀO CỜ', 'SINH HOẠT DƯỚI CỜ')
            GROUP BY magv, ap_dung_tu_tuan
        """)
    tkb_map = {(mgv, tuan_ad): cnt for mgv, tuan_ad, cnt in cur.fetchall()}

    cur.execute(
        """
            SELECT magv, loai, COUNT(*) FROM bien_dong_lich_day 
            WHERE ngay BETWEEN %s AND %s AND trang_thai != 'DA_HUY'
            GROUP BY magv, loai
        """,
        (ngay_bd_dot, ngay_kt_dot),
    )
    raw_bd = cur.fetchall()

    cur.execute(
        "SELECT magv, COALESCE(SUM(bdhsg_quy_doi), 0) FROM kg_hoc_sinh_gioi"
        " GROUP BY magv"
    )
    hsg_map = dict(cur.fetchall())
    cur.close()
    conn.close()

    nghi_map, day_thay_map, day_bu_map = {}, {}, {}
    for mgv, loai, cnt in raw_bd:
      l_str = str(loai).strip()
      if l_str.startswith("Nghỉ"):
        nghi_map[mgv] = nghi_map.get(mgv, 0) + cnt
      elif l_str == "Dạy thay":
        day_thay_map[mgv] = day_thay_map.get(mgv, 0) + cnt
      elif l_str == "Dạy bù":
        day_bu_map[mgv] = day_bu_map.get(mgv, 0) + cnt

    def lay_moc_hieu_luc(w):
      if not cac_moc_tuan:
        return 1
      p = [m for m in cac_moc_tuan if m <= w]
      return max(p) if p else min(cac_moc_tuan)

    rows = []
    for g in danh_sach_gv:
      (
          mgv,
          tgv,
          to_bm_gv,
          raw_dm,
          raw_tiet_gt,
          raw_gt_cn,
          raw_gt_hd,
          raw_gt_kn2,
      ) = g
      dm_dot = to_float(raw_dm, 17.0) * so_tuan

      tiet_tkb_dot = sum(
          tkb_map.get((mgv, lay_moc_hieu_luc(w)), 0)
          for w in range(int(tu_tuan), int(den_tuan) + 1)
      )
      so_tiet_nghi = nghi_map.get(mgv, 0)
      tiet_tbg = max(0, tiet_tkb_dot - so_tiet_nghi)
      str_tbg_tkb = (
          f"{tiet_tbg}/{tiet_tkb_dot}" if so_tiet_nghi > 0 else f"{tiet_tbg}"
      )

      tiet_bd = (
          float(hsg_map.get(mgv, 0))
          + float(day_thay_map.get(mgv, 0))
          + float(day_bu_map.get(mgv, 0))
      )
      tiet_gt = (
          to_float(raw_tiet_gt)
          + to_float(raw_gt_cn)
          + to_float(raw_gt_hd)
          + to_float(raw_gt_kn2)
      ) * so_tuan
      tong_tiet = float(tiet_tbg) + tiet_bd + tiet_gt
      chenh_lech = tong_tiet - dm_dot

      ket_luan = (
          "Đủ tiết"
          if chenh_lech == 0
          else (
              f"Thiếu {fmt_num(abs(chenh_lech))}"
              if chenh_lech < 0
              else f"Thừa {fmt_num(chenh_lech)}"
          )
      )
      str_cl = (
          "0"
          if chenh_lech == 0
          else (
              f"-{fmt_num(abs(chenh_lech))}"
              if chenh_lech < 0
              else f"+{fmt_num(chenh_lech)}"
          )
      )

      rows.append({
          "Mã GV": mgv,
          "Họ và Tên": tgv,
          "Tổ": to_bm_gv,
          "Định mức đợt": fmt_num(dm_dot),
          "Tiết TKB": tiet_tkb_dot,
          "TBG/TKB": str_tbg_tkb,
          "Biến động": fmt_num(tiet_bd),
          "Giảm trừ": fmt_num(tiet_gt),
          "Tổng tiết": fmt_num(tong_tiet),
          "Thừa/Thiếu": str_cl,
          "Kết luận": ket_luan,
      })

    df = pd.DataFrame(rows)
    if not df.empty:
      st.dataframe(df, use_container_width=True, hide_index=True)
  except Exception as e:
    st.error(f"Không thể tải thống kê: {e}")