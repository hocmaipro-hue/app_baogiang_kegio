# web_app.py - CỔNG THÔNG TIN TOÀN TRƯỜNG THUẦN WEB (KHÔNG DÙNG TKINTER)
from datetime import date, datetime, timedelta
import os
import re
from config import DB_URI
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Quản Lý Giảng Dạy - THPT Nguyễn Việt Hồng",
    page_icon="🏫",
    layout="wide",
)


def get_db():
    return psycopg2.connect(DB_URI)


if "user" not in st.session_state:
    st.session_state["user"] = None

# =============================================================================
# 1. MÀN HÌNH ĐĂNG NHẬP
# =============================================================================
if not st.session_state["user"]:
    st.markdown(
        "<h2 style='text-align: center; color: #1A5276;'>TRƯỜNG THPT NGUYỄN"
        " VIỆT HỒNG</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #555;'>HỆ THỐNG QUẢN LÝ BÁO GIẢNG"
        " & THEO DÕI GIỜ DẠY TRỰC TUYẾN</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔑 Đăng Nhập Hệ Thống")
            magv = st.text_input("Mã Giáo Viên:", placeholder="VD: PHONGTOAN").strip()
            mat_khau = st.text_input("Mật Khẩu:", type="password")
            btn_login = st.form_submit_button(
                "ĐĂNG NHẬP NGAY", type="primary", use_container_width=True
            )

            if btn_login:
                if not magv or not mat_khau:
                    st.warning("Vui lòng nhập đầy đủ thông tin!")
                else:
                    try:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            """
                            SELECT magv, tengv, to_bo_mon, role 
                            FROM giao_vien 
                            WHERE UPPER(TRIM(magv)) = UPPER(TRIM(%s)) AND matkhau = %s
                        """,
                            (magv, mat_khau),
                        )
                        user = cur.fetchone()
                        cur.close()
                        conn.close()

                        if user:
                            st.session_state["user"] = {
                                "magv": user[0],
                                "tengv": user[1],
                                "to_bm": user[2],
                                "role": user[3],
                            }
                            st.rerun()
                        else:
                            st.error("Sai Mã giáo viên hoặc Mật khẩu!")
                    except Exception as e:
                        st.error(f"Lỗi kết nối CSDL: {e}")

else:
    # =========================================================================
    # 2. GIAO DIỆN CHÍNH (PHÂN QUYỀN TỰ ĐỘNG)
    # =========================================================================
    user = st.session_state["user"]
    role = str(user["role"]).upper()
    is_admin = role in ["ADMIN", "BGH", "QUẢN TRỊ", "BAN GIÁM HIỆU"]
    is_totruong = role == "TO_TRUONG"

    # Header
    chuc_danh = (
        "BAN GIÁM HIỆU"
        if is_admin
        else (f"TỔ TRƯỞNG {user['to_bm']}" if is_totruong else "GIÁO VIÊN")
    )
    c_info, c_logout = st.columns([4, 1])
    with c_info:
        st.markdown(
            f"👤 **{user['tengv']}** ({user['magv']}) | Chức vụ: **{chuc_danh}**"
            f" | Tổ: **{user['to_bm']}**"
        )
    with c_logout:
        if st.button("Đăng Xuất", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

    st.divider()

    # -------------------------------------------------------------------------
    # GIAO DIỆN DÀNH CHO ADMIN / BAN GIÁM HIỆU
    # -------------------------------------------------------------------------
    if is_admin:
        st.subheader("🏢 TRUNG TÂM ĐIỀU HÀNH & GIÁM SÁT TOÀN TRƯỜNG")
        tab_ad1, tab_ad2, tab_ad3 = st.tabs([
            "📊 Giám Sát Giờ Dạy Toàn Trường",
            "📝 Giám Sát Đơn Nghỉ / Bù",
            "👥 Danh Sách Giáo Viên",
        ])

        with tab_ad1:
            st.markdown("#### Bảng Đối Chiếu Tiến Độ Giờ Dạy")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv, to_bo_mon, COALESCE(dinh_muc_tiet, 17)"
                    " FROM giao_vien ORDER BY to_bo_mon, tengv"
                )
                rows = cur.fetchall()
                cur.close()
                conn.close()

                df_gv = pd.DataFrame(
                    rows,
                    columns=["Mã GV", "Họ và Tên", "Tổ Bộ Môn", "Định Mức/Tuần"],
                )
                st.dataframe(df_gv, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi tải dữ liệu: {e}")

        with tab_ad2:
            st.markdown("#### Toàn Bộ Đơn Báo Nghỉ / Dạy Bù Toàn Trường")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, magv, loai, ngay, buoi, tiet_tkb, lop, ly_do, trang_thai 
                    FROM bien_dong_lich_day 
                    ORDER BY ngay DESC LIMIT 50
                """)
                rows_bd = cur.fetchall()
                cur.close()
                conn.close()

                df_bd = pd.DataFrame(
                    rows_bd,
                    columns=[
                        "ID",
                        "Mã GV",
                        "Loại",
                        "Ngày",
                        "Buổi",
                        "Tiết",
                        "Lớp",
                        "Lý Do",
                        "Trạng Thái",
                    ],
                )
                st.dataframe(df_bd, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi: {e}")

        with tab_ad3:
            st.markdown("#### Danh Mục Nhân Sự Toàn Trường")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv, to_bo_mon, chuc_vu, role FROM"
                    " giao_vien ORDER BY to_bo_mon"
                )
                ds_all_gv = cur.fetchall()
                cur.close()
                conn.close()
                st.dataframe(
                    pd.DataFrame(
                        ds_all_gv,
                        columns=[
                            "Mã GV",
                            "Họ Tên",
                            "Tổ",
                            "Chức Vụ",
                            "Quyền Hạn",
                        ],
                    ),
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # -------------------------------------------------------------------------
    # GIAO DIỆN DÀNH CHO TỔ TRƯỞNG CHUYÊN MÔN
    # -------------------------------------------------------------------------
    elif is_totruong:
        st.subheader(f"👥 QUẢN LÝ CHUYÊN MÔN - TỔ {user['to_bm'].upper()}")
        tab_tt1, tab_tt2 = st.tabs(
            ["📝 Duyệt Báo Nghỉ / Bù Của Tổ", "👥 Giáo Viên Trong Tổ"]
        )

        with tab_tt1:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT b.id, b.magv, g.tengv, b.loai, b.ngay, b.buoi, b.tiet_tkb, b.lop, b.ly_do 
                    FROM bien_dong_lich_day b 
                    JOIN giao_vien g ON b.magv = g.magv 
                    WHERE g.to_bo_mon = %s 
                    ORDER BY b.ngay DESC LIMIT 30
                """,
                    (user["to_bm"],),
                )
                rows_to = cur.fetchall()
                cur.close()
                conn.close()

                if rows_to:
                    df_to = pd.DataFrame(
                        rows_to,
                        columns=[
                            "ID",
                            "Mã GV",
                            "Giáo Viên",
                            "Loại",
                            "Ngày",
                            "Buổi",
                            "Tiết",
                            "Lớp",
                            "Lý Do",
                        ],
                    )
                    st.dataframe(df_to, use_container_width=True)
                else:
                    st.info("Hiện không có đơn báo nghỉ nào trong tổ.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

        with tab_tt2:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv, chuc_vu, COALESCE(dinh_muc_tiet, 17)"
                    " FROM giao_vien WHERE to_bo_mon = %s ORDER BY tengv",
                    (user["to_bm"],),
                )
                rows_gv_to = cur.fetchall()
                cur.close()
                conn.close()
                st.dataframe(
                    pd.DataFrame(
                        rows_gv_to,
                        columns=["Mã GV", "Họ Tên", "Chức Vụ", "Định Mức/Tuần"],
                    ),
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # -------------------------------------------------------------------------
    # GIAO DIỆN DÀNH CHO GIÁO VIÊN BỘ MÔN
    # -------------------------------------------------------------------------
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "⛔ Báo Nghỉ",
            "🟢 Dạy Bù",
            "🟡 Dạy Thay / HSG",
            "📅 Hôm Nay",
        ])

        with tab1:
            st.subheader("⛔ Đăng Ký Báo Nghỉ Giảng Dạy")
            loai_nghi = st.selectbox(
                "Lý do nghỉ:",
                [
                    "Nghỉ việc riêng",
                    "Nghỉ theo kế hoạch (Họp, Lễ)",
                    "Nghỉ theo điều động",
                ],
            )
            ngay_nghi = st.date_input("Ngày nghỉ:", date.today())
            thu_so = ngay_nghi.weekday() + 2

            col_b, col_t = st.columns(2)
            with col_b:
                buoi = st.selectbox("Buổi:", ["Sáng", "Chiều"])
            with col_t:
                tiet = st.selectbox("Tiết TKB:", [1, 2, 3, 4, 5])

            lop_tkb, pm_tkb = "", ""
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                    WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                """,
                    (user["magv"], str(thu_so), thu_so, buoi, tiet),
                )
                r = cur.fetchone()
                cur.close()
                conn.close()
                if r:
                    lop_tkb = r[0].strip()
                    pm_tkb = r[2].strip() if r[2].strip() else r[1].strip()
                    st.info(
                        f"✔ TKB Thứ {thu_so}: Lớp **{lop_tkb}** - Môn: {pm_tkb}"
                    )
                else:
                    st.warning(f"⚠️ Thứ {thu_so} Tiết {tiet} không có trên TKB!")
            except Exception:
                pass

            lydo_nghi = st.text_input(
                "Chi tiết lý do (*):", placeholder="Bắt buộc nhập lý do..."
            )
            if st.button("GỬI BÁO NGHỈ", type="primary"):
                if not lydo_nghi.strip():
                    st.error("Bắt buộc phải nhập lý do!")
                elif not lop_tkb:
                    st.error("Tiết này không có lịch dạy trên TKB!")
                else:
                    try:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            """
                            INSERT INTO bien_dong_lich_day 
                            (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                        """,
                            (
                                user["magv"],
                                loai_nghi,
                                ngay_nghi,
                                buoi,
                                tiet,
                                lop_tkb,
                                pm_tkb,
                                lydo_nghi,
                            ),
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(
                            f"Đã báo nghỉ thành công lớp {lop_tkb} ngày"
                            f" {ngay_nghi.strftime('%d/%m/%Y')}!"
                        )
                    except Exception as ex:
                        st.error(f"Lỗi: {ex}")

        with tab2:
            st.subheader("🟢 Đăng Ký Dạy Bù")
            ngay_bu = st.date_input(
                "Ngày dạy bù:", date.today(), key="ngay_bu_gv"
            )
            col_bb, col_bt = st.columns(2)
            with col_bb:
                buoi_bu = st.selectbox("Buổi:", ["Sáng", "Chiều"], key="b_bu_gv")
            with col_bt:
                tiet_bu = st.selectbox(
                    "Tiết:", [1, 2, 3, 4, 5], key="t_bu_gv"
                )

            lop_bu = st.text_input("Lớp dạy bù:", placeholder="VD: 11A1")
            lydo_bu = st.text_input(
                "Lý do dạy bù:", placeholder="VD: Bù cho tiết nghỉ..."
            )

            if st.button("GỬI ĐĂNG KÝ DẠY BÙ", type="primary"):
                if not lop_bu.strip():
                    st.error("Vui lòng nhập tên lớp!")
                else:
                    try:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            """
                            INSERT INTO bien_dong_lich_day 
                            (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                            VALUES (%s, 'Dạy bù', %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                        """,
                            (
                                user["magv"],
                                ngay_bu,
                                buoi_bu,
                                tiet_bu,
                                lop_bu.strip(),
                                user["to_bm"],
                                lydo_bu or "Dạy bù",
                            ),
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"Đã đăng ký dạy bù lớp {lop_bu} thành công!")
                    except Exception as ex:
                        st.error(f"Lỗi: {ex}")

        with tab3:
            st.subheader("🟡 Đăng Ký Dạy Thay / BDHSG")
            loai_chon = st.radio(
                "Chọn loại biến động:",
                ["Dạy thay đồng nghiệp", "Bồi dưỡng học sinh giỏi"],
                horizontal=True,
            )
            ngay_tt = st.date_input("Ngày thực hiện:", date.today())
            lop_tt = st.text_input("Lớp / Đội tuyển:", placeholder="VD: 12A2")
            noi_dung_tt = st.text_input(
                "Chi tiết / Lý do / GV được dạy thay:",
                placeholder="Nhập chi tiết...",
            )

            if st.button("GỬI ĐĂNG KÝ NGAY", type="primary"):
                loai_luu = (
                    "Dạy thay"
                    if "Dạy thay" in loai_chon
                    else "Bồi dưỡng HSG"
                )
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO bien_dong_lich_day 
                        (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                        VALUES (%s, %s, %s, 'Sáng', 1, %s, %s, '', %s, 'CHO_DUYET')
                    """,
                        (
                            user["magv"],
                            loai_luu,
                            ngay_tt,
                            lop_tt,
                            user["to_bm"],
                            noi_dung_tt,
                        ),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"Đã ghi nhận thành công đơn [{loai_luu}]!")
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

        with tab4:
            st.subheader("📅 Lịch Dạy Hôm Nay")
            hom_nay = date.today()
            thu_hn = hom_nay.weekday() + 2
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT buoi, tiet, lop, mon, COALESCE(phan_mon, '') 
                    FROM thoi_khoa_bieu 
                    WHERE magv = %s AND (thu = %s OR thu = %s)
                    ORDER BY buoi DESC, tiet ASC
                """,
                    (user["magv"], str(thu_hn), thu_hn),
                )
                ds = cur.fetchall()
                cur.close()
                conn.close()
                if ds:
                    for t in ds:
                        pm_str = f"({t[4]})" if t[4] else ""
                        st.write(
                            f"🔹 **{t[0]} - Tiết {t[1]}**: Lớp **{t[2]}** - Môn"
                            f" {t[3]} {pm_str}"
                        )
                else:
                    st.info("Hôm nay Thầy/Cô không có tiết dạy trên TKB.")
            except Exception as e:
                st.error(f"Lỗi: {e}")