from datetime import date, datetime
import os
import psycopg2
import streamlit as st
from config import DB_URI
from kg_hoc_sinh_gioi import dong_bo_va_tinh_toan_bdhsg
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
    .stDateInput div, .stTextInput div {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_pkg_module(session):
  inject_custom_css()

  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  st.markdown(
      "<h4 style='text-align: center; color: #1a5276;'>QUẢN LÝ KÊ KHAI ĐỊNH"
      " MỨC GIỜ DẠY (BIỂU 1C HD)</h4>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; font-style: italic; color:"
      f" #555;'>Giáo viên: <b>{tengv}</b> - Tổ bộ môn: <b>{to_bm}</b></p>",
      unsafe_allow_html=True,
  )
  st.divider()

  # Đồng bộ HSG ngầm khi load module
  try:
    dong_bo_va_tinh_toan_bdhsg(magv)
  except Exception:
    pass

  # ================= 1. KHUNG CHỌN THỜI GIAN KÊ KHAI =================
  st.markdown("##### 🕒 Chọn thời gian kê khai")
  c1, c2, c3 = st.columns(3)

  with c1:
    d_tu_ngay = st.date_input(
        "Từ ngày:", value=date(2026, 9, 7), key="pkg_tu_ngay"
    )
  with c2:
    d_den_ngay = st.date_input(
        "Đến ngày:", value=date(2026, 10, 3), key="pkg_den_ngay"
    )
  with c3:
    thang_str = st.text_input(
        "Tháng kê khai:", value="Tháng 09", key="pkg_thang_str"
    )

  st.markdown("---")

  # ================= 2. KHUNG CHỨC NĂNG & THAO TÁC =================
  col_btn1, col_btn2 = st.columns(2)

  with col_btn1:
    st.info(
        "**Bước 1:** Cấu hình và cập nhật giờ giảm trừ kiêm nhiệm trước khi xuất"
        " báo cáo."
    )
    if st.button("⚙️ Cài Đặt Kiêm Nhiệm & Giảm Trừ", use_container_width=True):
      st.session_state["show_kiem_nhiem_modal"] = True

  with col_btn2:
    st.success(
        "**Bước 2:** Tổng hợp dữ liệu tiết dạy, bồi dưỡng HSG và xuất Phiếu Kê"
        " Khai Excel (Biểu 1C)."
    )
    if st.button(
        "📤 Xuất Phiếu Kê Khai Excel (Biểu 1C)",
        type="primary",
        use_container_width=True,
    ):
      if d_tu_ngay > d_den_ngay:
        st.warning("Lỗi ngày: 'Từ ngày' không được lớn hơn 'Đến ngày'!")
        return

      # Lấy ngày khai giảng từ CSDL để tính tuần
      base_monday = date(2026, 9, 7)
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
          base_monday = datetime.strptime(r[0].strip(), "%Y-%m-%d").date()
      except Exception:
        pass

      tu_tuan = max(1, (d_tu_ngay - base_monday).days // 7 + 1)
      den_tuan = max(tu_tuan, (d_den_ngay - base_monday).days // 7 + 1)

      so_ngay = (d_den_ngay - d_tu_ngay).days + 1
      so_tuan_thuc_te = max(1, round(so_ngay / 7))

      extra_info = {
          "tu_ngay": d_tu_ngay.strftime("%d/%m/%Y"),
          "den_ngay": d_den_ngay.strftime("%d/%m/%Y"),
          "so_tuan": so_tuan_thuc_te,
      }

      try:
        # Gọi lại hàm xuất excel backend
        file_path = tao_phieu_ke_khai_1c(
            session, tu_tuan, den_tuan, thang_str, extra_info
        )
        st.success(
            f"Đã tạo xong Phiếu Kê Khai từ {extra_info['tu_ngay']} đến"
            f" {extra_info['den_ngay']} ({so_tuan_thuc_te} tuần) thành công!"
        )

        # Cung cấp nút tải file trực tiếp cho người dùng
        with open(file_path, "rb") as f:
          st.download_button(
              label="⬇️ Tải xuống file Excel Biểu 1C",
              data=f,
              file_name=os.path.basename(file_path),
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              use_container_width=True,
          )
      except Exception as e:
        st.error(f"Không thể tạo file Excel: {e}")

  # Modal hoặc khung phụ hiển thị cài đặt kiêm nhiệm nếu được kích hoạt
  if st.session_state.get("show_kiem_nhiem_modal", False):
    st.markdown("---")
    st.markdown("##### ⚙️ Giao diện Cài đặt Kiêm nhiệm & Giảm trừ")
    # Gọi component cài đặt kiêm nhiệm tương ứng ở đây (hoặc nhúng trực tiếp giao diện cài đặt)
    st.info(
        "Module Cài đặt Kiêm nhiệm & Giảm trừ đang hiển thị. (Bạn có thể tích"
        " hợp giao diện `ui_pkg_kiem_nhiem` tại đây)"
    )
    if st.button("Đóng bảng cài đặt"):
      st.session_state["show_kiem_nhiem_modal"] = False
      st.rerun()