import pandas as pd
import psycopg2
import service_so_bao_giang as sbg_service
import streamlit as st
from config import DB_URI
from ui_dieu_chinh_ppct import render_dieu_chinh_ppct


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
    .stNumberInput input {
        border-radius: 12px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )


def get_val(s, k, d=""):
  return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def render_so_bao_giang_ca_nhan(session):
  inject_custom_css()
  magv = get_val(session, "magv", "")
  tengv = get_val(session, "tengv", "Giáo viên")
  to_bm = get_val(session, "to_bo_mon", "Toán")

  # Tự động khởi tạo schema nếu cần
  sbg_service.ensure_database_schema(DB_URI)

  st.markdown(
      f"<h4 style='text-align: center; color: #1a5276;'>Sổ Báo Giảng Cá Nhân - {tengv}</h4>",
      unsafe_allow_html=True,
  )

  # Thanh công cụ điều khiển tuần & nút mốc PPCT
  c1, c2, c3 = st.columns([1, 2, 1])
  with c1:
    tuan_chon = st.number_input(
        "Tuần dạy:", min_value=1, max_value=35, value=1, step=1
    )

  with c3:
    st.write("")
    st.write("")
    mo_moc_ppct = st.button("⚙️ Cài đặt mốc PPCT", use_container_width=True)

  if mo_moc_ppct:
    with st.expander(
        "⚙️ Bảng Điều Chỉnh Mốc PPCT (Khi Nhận Lớp Mới)", expanded=True
    ):
      render_dieu_chinh_ppct(session)

  st.divider()

  # Tải dữ liệu Sổ báo giảng qua service (tính toán nhanh trên bộ nhớ)
  try:
    current_rows_data, tong_tiet = sbg_service.lay_du_lieu_bao_giang(
        DB_URI, magv, to_bm, int(tuan_chon)
    )

    st.markdown(
        f"<h5 style='color: #27ae60;'>📊 Tuần {tuan_chon}: Tổng số {tong_tiet} tiết</h5>",
        unsafe_allow_html=True,
    )

    if current_rows_data:
      # Định hình dữ liệu thành DataFrame hiển thị
      table_list = []
      for r in current_rows_data:
        ngay_f = (
            r["ngay"].strftime("%d/%m")
            if hasattr(r["ngay"], "strftime")
            else str(r["ngay"])
        )
        table_list.append({
            "Thứ / Ngày": f"Thứ {r['thu_num']} ({ngay_f})",
            "Buổi": r.get("buoi", ""),
            "Tiết": r.get("tiet", ""),
            "Lớp": r.get("lop", ""),
            "Tiết PPCT": r.get("tiet_ppct", ""),
            "Môn / Phân môn": r.get("mon_pm", ""),
            "Tên bài giảng": r.get("ten_bai", ""),
            "Trễ / Vượt": r.get("tre_vuot", ""),
            "Ghi chú": r.get("chu_y", ""),
        })

      df_sbg = pd.DataFrame(table_list)

      # Hiển thị bảng dữ liệu tương tác
      st.dataframe(df_sbg, use_container_width=True, hide_index=True)

    else:
      st.info(f"Không có dữ liệu báo giảng nào cho Tuần {tuan_chon}.")

  except Exception as e:
    st.error(f"Không thể tải Sổ Báo Giảng: {e}")