from datetime import datetime, timedelta
import os
import pandas as pd
import psycopg2
import streamlit as st
from config import DB_URI
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c


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
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_ke_khai_bieu_1c(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  # Khởi tạo state cho kiêm nhiệm nếu chưa có
  if "kn_info" not in st.session_state:
    st.session_state.kn_info = {
        "kn1_ten": "GVCN 12A2",
        "kn1_gio": 4,
        "kn2_ten": "",
        "kn2_gio": 0,
        "con_nho": 0,
        "hop_dong": 0,
    }
  if "file_xuat_gan_nhat" not in st.session_state:
    st.session_state.file_xuat_gan_nhat = ""

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>KÊ KHAI THỰC HIỆN ĐỊNH"
      " MỨC GIỜ DẠY (BIỂU 1C HD)</h4>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; color: #555; font-style: italic;'>Giáo"
      f" viên: {tengv} - Tổ bộ môn: {to_bm}</p>",
      unsafe_allow_html=True,
  )

  # ================= KHUNG 1: THỜI GIAN KÊ KHAI =================
  st.markdown("##### ⏱️ Thời gian kê khai thanh toán")
  c1, c2, c3 = st.columns(3)
  with c1:
    thang = st.selectbox(
        "Tháng kê khai:",
        options=[f"Tháng {i:02d}" for i in range(1, 13)],
        index=8,
    )
  with c2:
    tu_tuan = st.number_input("Từ Tuần:", min_value=1, max_value=35, value=1)
  with c3:
    den_tuan = st.number_input("Đến Tuần:", min_value=1, max_value=35, value=4)

  if tu_tuan > den_tuan:
    st.warning("⚠️ Từ tuần phải nhỏ hơn hoặc bằng Đến tuần!")
    return

  # Tính toán ngày bắt đầu & kết thúc tuần
  def get_ngay_bd():
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
        return datetime.strptime(r[0].strip(), "%Y-%m-%d").date()
    except Exception:
      pass
    return datetime.strptime("2026-09-07", "%Y-%m-%d").date()

  so_tuan = den_tuan - tu_tuan + 1
  base_mon = get_ngay_bd()
  d_start = base_mon + timedelta(days=(tu_tuan - 1) * 7)
  d_end = base_mon + timedelta(days=(den_tuan - 1) * 7 + 6)

  st.info(
      f"📅 ({so_tuan} tuần: từ {d_start.strftime('%d/%m/%Y')} đến"
      f" {d_end.strftime('%d/%m/%Y')})"
  )

  st.divider()

  # ================= KHUNG 2: XEM TRƯỚC SỐ LIỆU =================
  st.markdown("##### 📋 Bảng tổng hợp số liệu tính giờ dự kiến")
  try:
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()

    # 1. Định mức
    cur.execute(
        "SELECT COALESCE(dinh_muc_tiet, 17) FROM giao_vien WHERE magv = %s",
        (magv,),
    )
    dm_tuan_row = cur.fetchone()
    dm_tuan = dm_tuan_row[0] if dm_tuan_row else 17
    tong_dm = dm_tuan * so_tuan

    # 2. Phân công TKB
    cur.execute(
        """
            SELECT COUNT(*) FROM thoi_khoa_bieu 
            WHERE magv = %s AND lop NOT IN ('SHDC', 'SHL')
        """,
        (magv,),
    )
    tkb_tuan_row = cur.fetchone()
    tkb_tuan = tkb_tuan_row[0] if tkb_tuan_row else 0
    tong_tkb = tkb_tuan * so_tuan

    # 3. Biến động
    cur.execute(
        """
            SELECT loai, COUNT(*) FROM bien_dong_lich_day 
            WHERE magv = %s AND ngay BETWEEN %s AND %s 
            GROUP BY loai
        """,
        (magv, d_start, d_end),
    )
    bd_dict = dict(cur.fetchall())
    cur.close()
    conn.close()

    day_thay = bd_dict.get("Dạy thay", 0)
    nghi_viec_rieng = bd_dict.get("Nghỉ dạy", 0)
    bdhsg = bd_dict.get("Bồi dưỡng HSG", 0)

    # 4. Kiêm nhiệm
    kn_info = st.session_state.kn_info
    kn1_tong = kn_info["kn1_gio"] * so_tuan
    kn2_tong = kn_info["kn2_gio"] * so_tuan
    giam_kn_tong = (
        kn1_tong
        + kn2_tong
        + (kn_info["con_nho"] + kn_info["hop_dong"]) * so_tuan
    )

    # 5. Tổng thực hiện & Thừa giờ
    tong_thuc_hien = (
        tong_tkb + day_thay - nghi_viec_rieng + bdhsg + giam_kn_tong
    )
    thua_gio = tong_thuc_hien - tong_dm

    str_kn = f"{kn_info['kn1_ten']} ({kn1_tong}h)"
    if kn_info["kn2_ten"]:
      str_kn += f" + {kn_info['kn2_ten']} ({kn2_tong}h)"

    str_cl = f"+{thua_gio}" if thua_gio > 0 else str(thua_gio)

    preview_data = [
        {
            "Mục": "Mục 2",
            "Nội dung kê khai": "Định mức giờ dạy (1)",
            "Số giờ quy đổi": f"{tong_dm} giờ",
            "Chi tiết / Ghi chú": f"{dm_tuan} tiết/tuần x {so_tuan} tuần",
        },
        {
            "Mục": "Mục 3",
            "Nội dung kê khai": "Số giờ theo TKB phân công (2)",
            "Số giờ quy đổi": f"{tong_tkb} giờ",
            "Chi tiết / Ghi chú": f"{tkb_tuan} tiết/tuần x {so_tuan} tuần",
        },
        {
            "Mục": "Mục 4.1",
            "Nội dung kê khai": "Số giờ dạy thay (6)",
            "Số giờ quy đổi": f"{day_thay} giờ",
            "Chi tiết / Ghi chú": "Cộng thêm vào tổng giờ",
        },
        {
            "Mục": "Mục 4.3",
            "Nội dung kê khai": "Nghỉ việc riêng / trừ giờ (5)",
            "Số giờ quy đổi": f"{nghi_viec_rieng} giờ",
            "Chi tiết / Ghi chú": "Trừ khỏi giờ thực hiện",
        },
        {
            "Mục": "Mục 5",
            "Nội dung kê khai": "Hoạt động chuyên môn BDHSG (7)",
            "Số giờ quy đổi": f"{bdhsg} giờ",
            "Chi tiết / Ghi chú": "Cộng vào giờ chuyên môn",
        },
        {
            "Mục": "Mục 6",
            "Nội dung kê khai": "Số giờ giảm do kiêm nhiệm (8)",
            "Số giờ quy đổi": f"{giam_kn_tong} giờ",
            "Chi tiết / Ghi chú": str_kn,
        },
        {
            "Mục": "Mục 7",
            "Nội dung kê khai": "👉 TỔNG SỐ GIỜ THỰC HIỆN (9)",
            "Số giờ quy đổi": f"{tong_thuc_hien} giờ",
            "Chi tiết / Ghi chú": "(2)+(3)-(5)+(6)+(7)+(8)",
        },
        {
            "Mục": "Mục 8",
            "Nội dung kê khai": "💰 SỐ GIỜ DẠY THÊM (9) - (1)",
            "Số giờ quy đổi": f"{str_cl} giờ",
            "Chi tiết / Ghi chú": "Số giờ thanh toán thừa giờ",
        },
    ]

    df_prev = pd.DataFrame(preview_data)
    st.dataframe(df_prev, use_container_width=True, hide_index=True)

  except Exception as e:
    st.error(f"Không thể tải xem trước số liệu: {e}")

  st.divider()

  # ================= KHUNG 3: CÁC NÚT HÀNH ĐỘNG & EXPANDER CÀI ĐẶT =================
  with st.expander("⚙️ Cài đặt Kiêm nhiệm & Giảm trừ định mức", expanded=False):
    c_k1, c_k2 = st.columns(2)
    with c_k1:
      kn1_ten = st.text_input(
          "Kiêm nhiệm 1:", value=st.session_state.kn_info["kn1_ten"]
      )
      kn1_gio = st.number_input(
          "Giảm (h/tuần) KN1:",
          min_value=0,
          max_value=10,
          value=st.session_state.kn_info["kn1_gio"],
      )
      con_nho = st.number_input(
          "Nữ có con nhỏ <12th:",
          min_value=0,
          max_value=5,
          value=st.session_state.kn_info["con_nho"],
      )
    with c_k2:
      kn2_ten = st.text_input(
          "Kiêm nhiệm 2:", value=st.session_state.kn_info["kn2_ten"]
      )
      kn2_gio = st.number_input(
          "Giảm (h/tuần) KN2:",
          min_value=0,
          max_value=10,
          value=st.session_state.kn_info["kn2_gio"],
      )
      hop_dong = st.number_input(
          "Hợp đồng lần đầu:",
          min_value=0,
          max_value=5,
          value=st.session_state.kn_info["hop_dong"],
      )

    if st.button("💾 Lưu cấu hình kiêm nhiệm", use_container_width=True):
      st.session_state.kn_info = {
          "kn1_ten": kn1_ten.strip(),
          "kn1_gio": int(kn1_gio),
          "kn2_ten": kn2_ten.strip(),
          "kn2_gio": int(kn2_gio),
          "con_nho": int(con_nho),
          "hop_dong": int(hop_dong),
      }
      st.success("Đã cập nhật chế độ kiêm nhiệm thành công!")
      st.rerun()

  st.write("")
  b1, b2 = st.columns(2)
  with b1:
    if st.button(
        "📤 XUẤT PHIẾU KÊ KHAI EXCEL (BIỂU 1C)",
        type="primary",
        use_container_width=True,
    ):
      try:
        file_path = tao_phieu_ke_khai_1c(
            session, tu_tuan, den_tuan, thang, st.session_state.kn_info
        )
        st.session_state.file_xuat_gan_nhat = file_path
        st.success(
            "Xuất thành công! Đã tạo xong Phiếu Kê Khai (Biểu 1C HD).\nFile lưu"
            f" tại: {file_path}"
        )
      except Exception as e:
        st.error(f"Không thể tạo file Excel: {e}")

  with b2:
    if st.button("📂 MỞ FILE EXCEL VỪA XUẤT", use_container_width=True):
      f_path = st.session_state.get("file_xuat_gan_nhat", "")
      if not f_path or not os.path.exists(f_path):
        st.warning(
            "Chưa có file Excel nào được xuất hoặc file không tồn tại! Vui lòng"
            " bấm nút xuất trước."
        )
      else:
        try:
          os.startfile(f_path)
          st.success("Đã mở file Excel thành công!")
        except Exception as e:
          st.error(f"Không thể mở file: {e}")