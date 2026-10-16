# web_app.py - HỆ THỐNG QUẢN LÝ BÁO GIẢNG & KÊ KHAI GIỜ DẠY MOBILE TOÀN DIỆN
import io
import os
import re
from datetime import date, datetime, timedelta
from config import DB_URI
import psycopg2
import service_so_bao_giang as sbg_service
import streamlit as st
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c

st.set_page_config(
    page_title="Sổ Báo Giảng & Kê Giờ THPT Nguyễn Việt Hồng",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
        .header-title { text-align: center; color: #1A5276; font-size: 20px; font-weight: bold; margin-bottom: 2px; }
        .sub-title { text-align: center; color: #555; font-size: 13px; margin-bottom: 12px; }
    </style>
""",
    unsafe_allow_html=True,
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
        "<div class='header-title'>TRƯỜNG THPT NGUYỄN VIỆT HỒNG</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-title'>HỆ THỐNG QUẢN LÝ BÁO GIẢNG & KÊ KHAI GIỜ DẠY TRÊN"
        " DI ĐỘNG</div>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        st.subheader("🔑 Đăng Nhập Hệ Thống")
        magv = st.text_input(
            "Tên đăng nhập (Mã GV):", placeholder="VD: PHONGTOAN"
        ).strip()
        mat_khau = st.text_input("Mật khẩu:", type="password")
        if st.form_submit_button("ĐĂNG NHẬP NGAY", type="primary"):
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
    # 2. GIAO DIỆN CHÍNH TRÊN ĐIỆN THOẠI (TRỌN VẸN 8 CHỨC NĂNG)
    # =========================================================================
    user = st.session_state["user"]

    # Header người dùng & Đăng xuất
    c_info, c_logout = st.columns([3, 1])
    with c_info:
        st.markdown(
            f"👤 **{user['tengv']}** ({user['magv']}) - Tổ {user['to_bm']}"
        )
    with c_logout:
        if st.button("Thoát"):
            st.session_state["user"] = None
            st.rerun()

    # Toàn bộ danh mục nghiệp vụ của giáo viên
    tabs = st.tabs([
        "📖 Báo Giảng",
        "📊 Kê Giờ 1C",
        "⛔ Báo Nghỉ",
        "🟢 Dạy Bù",
        "🟡 Dạy Thay",
        "🔵 BDHSG",
        "📅 Hôm Nay",
        "⚙️ Đổi MK",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SỔ BÁO GIẢNG CHI TIẾT (TỰ TÍNH TIẾN ĐỘ THEO TUẦN)
    # -------------------------------------------------------------------------
    with tabs[0]:
        st.subheader("📖 Tra Cứu Sổ Báo Giảng")
        tuan_chon = st.number_input(
            "Chọn Tuần học:", min_value=1, max_value=35, value=1, step=1
        )

        try:
            with st.spinner("Đang tính toán tiến độ Sổ Báo Giảng..."):
                rows_data, tong_tiet = sbg_service.lay_du_lieu_bao_giang(
                    DB_URI, user["magv"], user["to_bm"], int(tuan_chon)
                )

            st.success(f"Tuần {tuan_chon}: Tổng cộng {tong_tiet} tiết thực dạy")

            # Hiển thị các tiết có dạy trong tuần
            co_tiet = False
            for r in rows_data:
                if r["row_type"] != "empty":
                    co_tiet = True
                    color_tag = "🟢"
                    if r["row_type"] == "nghi":
                        color_tag = "🔴"
                    elif r["row_type"] == "day_thay":
                        color_tag = "🟡"
                    elif r["row_type"] == "hsg":
                        color_tag = "🔵"

                    st.markdown(
                        f"""
                    **{color_tag} {r['thu_ngay']} ({r['buoi']} - Tiết {r['tiet']})**: Lớp **{r['lop']}**  
                    • **Môn/PM:** {r['mon_pm']} | **Tiết PPCT:** {r['tiet_ppct']}  
                    • **Bài dạy:** {r['ten_bai']}  
                    • **Tiến độ:** *{r['tre_vuot']}* {f"| Ghi chú: {r['chu_y']}" if r['chu_y'] else ""}
                    """
                    )
                    st.divider()

            if not co_tiet:
                st.info(f"Tuần {tuan_chon} Thầy/Cô không có lịch dạy!")
        except Exception as e:
            st.error(f"Lỗi nạp sổ báo giảng: {e}")

    # -------------------------------------------------------------------------
    # TAB 2: KÊ KHAI GIỜ DẠY & TẢI FILE EXCEL PHIẾU 1C VỀ ĐIỆN THOẠI
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.subheader("📊 Kê Khai Giờ Dạy (Phiếu 1C)")
        st.caption("Xuất và tải trực tiếp file Excel Phiếu 1C về máy điện thoại")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_tu = st.date_input("Từ ngày:", date(2026, 9, 7), key="pkg_d_tu")
        with col_d2:
            d_den = st.date_input("Đến ngày:", date(2026, 10, 3), key="pkg_d_den")

        thang_kkhai = st.text_input("Tháng kê khai:", value="Tháng 09")

        if st.button("📥 XUẤT VÀ TẢI PHIẾU 1C EXCEL", type="primary"):
            if d_tu > d_den:
                st.error("'Từ ngày' không được lớn hơn 'Đến ngày'!")
            else:
                try:
                    with st.spinner("Đang tính toán và vẽ file Excel 1C..."):
                        base_monday = date(2026, 9, 7)
                        try:
                            conn = get_db()
                            cur = conn.cursor()
                            cur.execute(
                                "SELECT gia_tri FROM cau_hinh WHERE khoa ="
                                " 'ngay_bat_dau_nam_hoc'"
                            )
                            r_c = cur.fetchone()
                            cur.close()
                            conn.close()
                            if r_c:
                                base_monday = datetime.strptime(
                                    r_c[0].strip(), "%Y-%m-%d"
                                ).date()
                        except Exception:
                            pass

                        tu_tuan = max(1, (d_tu - base_monday).days // 7 + 1)
                        den_tuan = max(tu_tuan, (d_den - base_monday).days // 7 + 1)
                        so_ngay = (d_den - d_tu).days + 1
                        so_tuan_thuc_te = max(1, round(so_ngay / 7))

                        extra_info = {
                            "tu_ngay": d_tu.strftime("%d/%m/%Y"),
                            "den_ngay": d_den.strftime("%d/%m/%Y"),
                            "so_tuan": so_tuan_thuc_te,
                        }

                        # Gọi hàm xuất Excel chuẩn
                        file_path = tao_phieu_ke_khai_1c(
                            user, tu_tuan, den_tuan, thang_kkhai, extra_info
                        )

                        # Đọc file nhị phân để cho tải về điện thoại
                        with open(file_path, "rb") as f:
                            excel_bytes = f.read()

                        filename = os.path.basename(file_path)

                        st.success(
                            f"Đã tạo xong Phiếu 1C ({so_tuan_thuc_te} tuần)!"
                        )
                        st.download_button(
                            label="📲 BẤM VÀO ĐÂY ĐỂ TẢI FILE EXCEL VỀ MÁY",
                            data=excel_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                except Exception as ex:
                    st.error(f"Lỗi xuất Excel: {ex}")

    # -------------------------------------------------------------------------
    # TAB 3: BÁO NGHỈ DẠY
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("⛔ Đăng Ký Báo Nghỉ Giảng Dạy")
        loai_nghi = st.selectbox(
            "Lý do nghỉ:",
            [
                "Nghỉ việc riêng",
                "Nghỉ theo kế hoạch (Họp, Lễ)",
                "Nghỉ theo điều động",
            ],
        )

        ngay_nghi = st.date_input("Ngày nghỉ:", date.today(), key="ngay_nghi")
        thu_so = ngay_nghi.weekday() + 2

        col_b, col_t = st.columns(2)
        with col_b:
            buoi = st.selectbox("Buổi:", ["Sáng", "Chiều"], key="buoi_nghi")
        with col_t:
            tiet = st.selectbox("Tiết TKB:", [1, 2, 3, 4, 5], key="tiet_nghi")

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
                    f"✔ TKB Thứ {thu_so}: Lớp **{lop_tkb}** - Phân môn:"
                    f" {pm_tkb}"
                )
            else:
                st.warning(
                    f"⚠️ Thứ {thu_so} Tiết {tiet} ({buoi}): Thầy/Cô không có"
                    " lịch dạy!"
                )
        except Exception:
            pass

        lydo_nghi = st.text_input(
            "Chi tiết lý do / QĐ (*):",
            placeholder="Bắt buộc nhập lý do (VD: Con ốm, Đi công tác...)",
            key="lydo_nghi",
        )

        if st.button("⛔ GỬI BÁO NGHỈ NGAY", type="primary"):
            if not lydo_nghi.strip():
                st.error("Thầy/Cô BẮT BUỘC phải nhập lý do chi tiết!")
            elif not lop_tkb:
                st.error(
                    "Tiết này trên TKB không có lịch dạy nên không thể báo nghỉ!"
                )
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
                    st.error(f"Lỗi lưu dữ liệu: {ex}")

    # -------------------------------------------------------------------------
    # TAB 4: ĐĂNG KÝ DẠY BÙ
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("🟢 Đăng Ký Lịch Dạy Bù")
        ds_lop_gv = []
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop NOT IN ('SHDC', 'SHL', 'EMPTY') ORDER BY lop
            """,
                (user["magv"],),
            )
            ds_lop_gv = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
        except Exception:
            pass

        ngay_bu = st.date_input(
            "Ngày dạy bù:", date.today(), key="ngay_day_bu"
        )
        col_bu_b, col_bu_t = st.columns(2)
        with col_bu_b:
            buoi_bu = st.selectbox(
                "Buổi dạy bù:", ["Sáng", "Chiều"], key="buoi_bu"
            )
        with col_bu_t:
            tiet_bu = st.selectbox(
                "Tiết dạy bù:", [1, 2, 3, 4, 5], key="tiet_bu"
            )

        col_l, col_pm = st.columns(2)
        with col_l:
            lop_bu = st.selectbox(
                "Lớp dạy bù:", ds_lop_gv if ds_lop_gv else ["11A1", "12A2"]
            )
        with col_pm:
            pm_bu = st.selectbox(
                "Phân môn:",
                [
                    "Đại số",
                    "Giải tích",
                    "Hình học",
                    "Chuyên đề",
                    user["to_bm"],
                ],
            )

        lydo_bu = st.text_input(
            "Lý do dạy bù:",
            placeholder="VD: Dạy bù cho tiết nghỉ ngày...",
            key="lydo_bu",
        )

        if st.button("🟢 GỬI ĐĂNG KÝ DẠY BÙ", type="primary"):
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
                        lop_bu,
                        pm_bu,
                        lydo_bu or "Dạy bù",
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(
                    f"Đã đăng ký dạy bù lớp {lop_bu} ngày"
                    f" {ngay_bu.strftime('%d/%m/%Y')}!"
                )
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # TAB 5: ĐĂNG KÝ DẠY THAY
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.subheader("🟡 Đăng Ký Dạy Thay Đồng Nghiệp")
        ds_gv_dong_nghiep = []
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT tengv FROM giao_vien WHERE magv != %s ORDER BY tengv",
                (user["magv"],),
            )
            ds_gv_dong_nghiep = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
        except Exception:
            pass

        gv_duoc_thay = st.selectbox(
            "Dạy thay cho Thầy/Cô nào:", ds_gv_dong_nghiep
        )
        ngay_thay = st.date_input(
            "Ngày dạy thay:", date.today(), key="ngay_thay"
        )

        col_dt_b, col_dt_t = st.columns(2)
        with col_dt_b:
            buoi_thay = st.selectbox(
                "Buổi:", ["Sáng", "Chiều"], key="buoi_thay"
            )
        with col_dt_t:
            tiet_thay = st.selectbox(
                "Tiết:", [1, 2, 3, 4, 5], key="tiet_thay"
            )

        col_dt_l, col_dt_pm = st.columns(2)
        with col_dt_l:
            lop_thay = st.text_input("Dạy thay tại Lớp:", placeholder="VD: 12A1")
        with col_dt_pm:
            pm_thay = st.text_input(
                "Môn/Phân môn dạy thay:", placeholder="VD: Toán"
            )

        lydo_thay = st.text_input(
            "Lý do dạy thay:", placeholder="VD: Đi tập huấn, ốm..."
        )

        if st.button("🟡 GỬI BÁO DẠY THAY", type="primary"):
            if not lop_thay.strip():
                st.error("Vui lòng nhập tên lớp dạy thay!")
            else:
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO bien_dong_lich_day 
                        (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                        VALUES (%s, 'Dạy thay', %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
                    """,
                        (
                            user["magv"],
                            ngay_thay,
                            buoi_thay,
                            tiet_thay,
                            lop_thay.strip(),
                            pm_thay.strip() or user["to_bm"],
                            gv_duoc_thay,
                            lydo_thay or f"Dạy thay {gv_duoc_thay}",
                        ),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"Đã ghi nhận dạy thay cho Thầy/Cô {gv_duoc_thay}!")
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # TAB 6: BỒI DƯỠNG HỌC SINH GIỎI (BDHSG)
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.subheader("🔵 Đăng Ký Buổi Bồi Dưỡng Học Sinh Giỏi")
        st.caption("ℹ️ Mỗi buổi bồi dưỡng HSG sẽ được tự động quy đổi x 1.5 giờ")

        ngay_hsg = st.date_input(
            "Ngày bồi dưỡng HSG:", date.today(), key="ngay_hsg"
        )
        col_hsg_b, col_hsg_t = st.columns(2)
        with col_hsg_b:
            buoi_hsg = st.selectbox("Buổi:", ["Sáng", "Chiều"], key="buoi_hsg")
        with col_hsg_t:
            so_tiet_hsg = st.selectbox(
                "Số tiết bồi dưỡng:", [1, 2, 3, 4], index=2
            )

        lop_doi_tuyen = st.text_input(
            "Đội tuyển bồi dưỡng:",
            placeholder=f"VD: Đội tuyển HSG {user['to_bm']} 12",
        )
        noi_dung_hsg = st.text_input(
            "Nội dung chuyên đề:", placeholder="VD: Bồi dưỡng chuyên đề Số học..."
        )

        if st.button("🔵 GỬI ĐĂNG KÝ BDHSG", type="primary"):
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO bien_dong_lich_day 
                    (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                    VALUES (%s, 'Bồi dưỡng HSG', %s, %s, %s, %s, 'BDHSG', '', %s, 'CHO_DUYET')
                """,
                    (
                        user["magv"],
                        ngay_hsg,
                        buoi_hsg,
                        so_tiet_hsg,
                        lop_doi_tuyen or "Đội tuyển HSG",
                        noi_dung_hsg or "Bồi dưỡng HSG",
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(
                    f"Đã lưu buổi bồi dưỡng HSG ngày"
                    f" {ngay_hsg.strftime('%d/%m/%Y')}!"
                )
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # TAB 7: LỊCH DẠY HÔM NAY (TRA CỨU NHANH)
    # -------------------------------------------------------------------------
    with tabs[6]:
        hom_nay = date.today()
        thu_hn = hom_nay.weekday() + 2
        st.subheader(
            f"📅 Hôm nay: Thứ {thu_hn} ({hom_nay.strftime('%d/%m/%Y')})"
        )

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
            ds_tiet = cur.fetchall()
            cur.close()
            conn.close()

            if ds_tiet:
                for t in ds_tiet:
                    pm_str = f"({t[4]})" if t[4] else ""
                    st.write(
                        f"🔹 **{t[0]} - Tiết {t[1]}**: Lớp **{t[2]}** - Môn"
                        f" {t[3]} {pm_str}"
                    )
            else:
                st.info("Hôm nay Thầy/Cô không có tiết dạy trên TKB!")
        except Exception as e:
            st.error(f"Lỗi tải lịch: {e}")

    # -------------------------------------------------------------------------
    # TAB 8: ĐỔI MẬT KHẨU CÁ NHÂN
    # -------------------------------------------------------------------------
    with tabs[7]:
        st.subheader("🔑 Đổi Mật Khẩu Đăng Nhập")
        with st.form("doi_mk_form"):
            mk_cu = st.text_input("Mật khẩu hiện tại:", type="password")
            mk_moi = st.text_input("Mật khẩu mới:", type="password")
            mk_nhap_lai = st.text_input("Nhập lại mật khẩu mới:", type="password")
            btn_dmk = st.form_submit_button("XÁC NHẬN ĐỔI MẬT KHẨU")

            if btn_dmk:
                if not mk_cu or not mk_moi:
                    st.warning("Vui lòng điền đầy đủ các ô!")
                elif mk_moi != mk_nhap_lai:
                    st.error("Mật khẩu nhập lại không khớp!")
                else:
                    try:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT matkhau FROM giao_vien WHERE magv = %s",
                            (user["magv"],),
                        )
                        mk_that = cur.fetchone()[0]
                        if mk_cu != mk_that:
                            st.error("Mật khẩu hiện tại không đúng!")
                        else:
                            cur.execute(
                                "UPDATE giao_vien SET matkhau = %s WHERE magv"
                                " = %s",
                                (mk_moi, user["magv"]),
                            )
                            conn.commit()
                            st.success("Đổi mật khẩu thành công!")
                        cur.close()
                        conn.close()
                    except Exception as ex:
                        st.error(f"Lỗi: {ex}")