# web_app.py - HỆ THỐNG QUẢN LÝ BÁO GIẢNG & KÊ KHAI GIỜ DẠY TRỰC TUYẾN TOÀN DIỆN
import os
import re
from datetime import date, datetime, timedelta
from config import DB_URI
import pandas as pd
import psycopg2
import service_so_bao_giang as sbg_service
import streamlit as st
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c

st.set_page_config(
    page_title="THPT Nguyễn Việt Hồng - Quản Lý Giảng Dạy",
    page_icon="🏫",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
        .header-title { text-align: center; color: #1A5276; font-size: 22px; font-weight: bold; margin-bottom: 2px; }
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
        "<div class='sub-title'>HỆ THỐNG BÁO GIẢNG & KÊ KHAI GIỜ DẠY TRỰC"
        " TUYẾN</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔑 Đăng Nhập Hệ Thống")
            magv = st.text_input(
                "Mã Giáo Viên:", placeholder="VD: PHONGTOAN"
            ).strip()
            mat_khau = st.text_input("Mật Khẩu:", type="password")
            if st.form_submit_button(
                "ĐĂNG NHẬP NGAY", type="primary", use_container_width=True
            ):
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
    # 2. GIAO DIỆN CHÍNH (ĐẦY ĐỦ PHÂN QUYỀN VÀ CÓ KÊ GIỜ)
    # =========================================================================
    user = st.session_state["user"]
    role = str(user["role"]).upper()
    is_admin = role in ["ADMIN", "BGH", "QUẢN TRỊ", "BAN GIÁM HIỆU"]
    is_totruong = role == "TO_TRUONG"

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

    # DANH SÁCH TABS ĐẦY ĐỦ
    tab_titles = [
        "📊 Kê Khai Giờ (Phiếu 1C)",
        "📅 TKB Cá Nhân",
        "📖 Sổ Báo Giảng",
        "⛔ Báo Nghỉ",
        "🟢 Dạy Bù",
        "🟡 Dạy Thay / HSG",
        "📋 Lịch Sử Đơn",
    ]

    if is_totruong:
        tab_titles.extend(["👥 Soi Báo Giảng Tổ", "📝 Đơn Của Tổ"])
    elif is_admin:
        tab_titles.extend([
            "📊 Giám Sát Toàn Trường",
            "📝 Biến Động Toàn Trường",
            "👥 Danh Sách GV",
        ])

    tab_titles.append("⚙️ Đổi Mật Khẩu")

    tabs = st.tabs(tab_titles)

    # -------------------------------------------------------------------------
    # TAB 1: KÊ KHAI GIỜ DẠY (PHIẾU 1C) - ĐẦY ĐỦ TÍNH TOÁN & XUẤT EXCEL
    # -------------------------------------------------------------------------
    with tabs[0]:
        st.subheader("📊 Kê Khai Định Mức Giờ Dạy (Biểu 1C HD)")
        st.caption(
            "Tự động tính số tuần, định mức, bù trừ biến động và xuất file"
            " Excel chuẩn quy cách"
        )

        col_d1, col_d2, col_thang = st.columns([2, 2, 2])
        with col_d1:
            d_tu = st.date_input("Từ ngày:", date(2026, 9, 7), key="pkg_tu_ngay")
        with col_d2:
            d_den = st.date_input(
                "Đến ngày:", date(2026, 10, 3), key="pkg_den_ngay"
            )
        with col_thang:
            thang_str = st.text_input("Tháng kê khai:", value="Tháng 09")

        # Cài đặt kiêm nhiệm trên web
        with st.expander("⚙️ Xem & Cài đặt thông số Kiêm nhiệm / Giảm trừ"):
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT COALESCE(dinh_muc_tiet, 17), COALESCE(kiem_nhiem, ''), COALESCE(tiet_giam_tru, 0),
                           COALESCE(kiem_nhiem_2, ''), COALESCE(giam_tru_kn2, 0)
                    FROM giao_vien WHERE magv = %s
                """,
                    (user["magv"],),
                )
                row_kn = cur.fetchone()
                cur.close()
                conn.close()

                st.write(f"• **Định mức chuẩn:** {row_kn[0]} tiết/tuần")
                st.write(
                    f"• **Kiêm nhiệm 1:** {row_kn[1]} (Giảm {row_kn[2]}"
                    " tiết/tuần)"
                )
                if row_kn[3]:
                    st.write(
                        f"• **Kiêm nhiệm 2:** {row_kn[3]} (Giảm {row_kn[4]}"
                        " tiết/tuần)"
                    )
            except Exception:
                pass

        if st.button("📥 TÍNH TOÁN & TẢI FILE EXCEL PHIẾU 1C", type="primary"):
            if d_tu > d_den:
                st.error("'Từ ngày' không được lớn hơn 'Đến ngày'!")
            else:
                try:
                    with st.spinner("Đang tổng hợp dữ liệu và vẽ file Excel..."):
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
                        den_tuan = max(
                            tu_tuan, (d_den - base_monday).days // 7 + 1
                        )
                        so_ngay = (d_den - d_tu).days + 1
                        so_tuan_thuc_te = max(1, round(so_ngay / 7))

                        extra_info = {
                            "tu_ngay": d_tu.strftime("%d/%m/%Y"),
                            "den_ngay": d_den.strftime("%d/%m/%Y"),
                            "so_tuan": so_tuan_thuc_te,
                        }

                        # Gọi thẳng hàm xuất Excel chuẩn mẫu Biểu 1C
                        file_path = tao_phieu_ke_khai_1c(
                            user, tu_tuan, den_tuan, thang_str, extra_info
                        )

                        with open(file_path, "rb") as f:
                            excel_bytes = f.read()

                        filename = os.path.basename(file_path)

                        st.success(
                            f"Đã tạo thành công Phiếu 1C ({so_tuan_thuc_te}"
                            " tuần)! File đã sẵn sàng để tải về:"
                        )
                        st.download_button(
                            label="📲 BẤM VÀO ĐÂY ĐỂ TẢI FILE EXCEL VỀ MÁY",
                            data=excel_bytes,
                            file_name=filename,
                            mime=(
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            ),
                        )
                except Exception as ex:
                    st.error(f"Lỗi xuất Excel: {ex}")

    # -------------------------------------------------------------------------
    # TAB 2: THỜI KHÓA BIỂU CÁ NHÂN (CÓ LỌC ĐỢT ÁP DỤNG & GÁN PHÂN MÔN)
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.subheader(f"📅 Thời Khóa Biểu & Gán Phân Môn - GV: {user['tengv']}")

        # 1. Lấy danh sách các đợt TKB có trong CSDL
        ds_dot_tkb = []
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ap_dung_tu_tuan, ap_dung_tu_ngay 
                FROM thoi_khoa_bieu 
                WHERE magv = %s AND ap_dung_tu_tuan IS NOT NULL 
                ORDER BY ap_dung_tu_tuan ASC
            """, (user["magv"],))
            ds_dot_raw = cur.fetchall()
            cur.close()
            conn.close()

            if ds_dot_raw:
                for r_dot in ds_dot_raw:
                    t_num = r_dot[0]
                    d_str = r_dot[1].strftime("%d/%m/%Y") if r_dot[1] else ""
                    lbl = f"Tuần {t_num}" + (f" (từ {d_str})" if d_str else "")
                    ds_dot_tkb.append((t_num, lbl))
            else:
                ds_dot_tkb = [(1, "Tuần 1 (Mặc định)")]
        except Exception:
            ds_dot_tkb = [(1, "Tuần 1")]

        dict_dot = {lbl: val for val, lbl in ds_dot_tkb}
        dot_chon_lbl = st.selectbox(
            "📅 Chọn Đợt Áp Dụng TKB:",
            list(dict_dot.keys()),
            index=len(dict_dot) - 1,
        )
        tuan_hieu_luc = dict_dot[dot_chon_lbl]

        # 2. Tải chính xác TKB của đợt đó
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, thu, buoi, tiet, lop, mon, COALESCE(phan_mon, '') 
                FROM thoi_khoa_bieu 
                WHERE magv = %s AND ap_dung_tu_tuan = %s
                ORDER BY thu, buoi DESC, tiet ASC
            """,
                (user["magv"], tuan_hieu_luc),
            )
            rows_tkb = cur.fetchall()
            cur.close()
            conn.close()

            if rows_tkb:
                display_data = []
                map_tiet_gan = {}
                for r in rows_tkb:
                    t_id, t_thu, t_buoi, t_tiet, t_lop, t_mon, t_pm = r
                    pm_hien_thi = (
                        t_pm
                        if t_pm
                        else (
                            ""
                            if t_mon in ["SHDC", "SHL"]
                            else "⚠️ (Chưa gán phân môn)"
                        )
                    )
                    display_data.append({
                        "ID": t_id,
                        "Thứ": t_thu,
                        "Buổi": t_buoi,
                        "Tiết": t_tiet,
                        "Lớp": t_lop,
                        "Môn Học": t_mon,
                        "Phân Môn Hiện Tại": pm_hien_thi,
                    })
                    if t_mon not in ["SHDC", "SHL"]:
                        map_tiet_gan[
                            f"ID {t_id}: Thứ {t_thu} ({t_buoi} - T{t_tiet}) Lớp"
                            f" {t_lop} [{t_mon}]"
                        ] = t_id

                df_tkb = pd.DataFrame(display_data)
                st.dataframe(df_tkb, use_container_width=True)

                # 3. KHUNG GÁN PHÂN MÔN TRỰC TIẾP TRÊN WEB
                st.markdown("#### ⚙️ Gán Phân Môn Cho Tiết Dạy")
                c_tiet, c_pm, c_btn = st.columns([3, 2, 2])
                with c_tiet:
                    tiet_chon_str = st.selectbox(
                        "Chọn tiết cần gán:", list(map_tiet_gan.keys())
                    )
                with c_pm:
                    pm_moi = st.selectbox(
                        "Chọn Phân môn:",
                        [
                            "Đại số",
                            "Giải tích",
                            "Hình học",
                            "Chuyên đề",
                            user["to_bm"],
                        ],
                    )
                with c_btn:
                    st.write("")
                    st.write("")
                    if st.button("💾 LƯU PHÂN MÔN", type="primary"):
                        id_tkb_chon = map_tiet_gan[tiet_chon_str]
                        try:
                            conn = get_db()
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE thoi_khoa_bieu SET phan_mon = %s WHERE"
                                " id = %s",
                                (pm_moi, id_tkb_chon),
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success(
                                f"Đã gán phân môn [{pm_moi}] thành công!"
                            )
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Lỗi: {ex}")
            else:
                st.info(f"Đợt {dot_chon_lbl} không có lịch dạy nào.")
        except Exception as e:
            st.error(f"Lỗi tải TKB: {e}")
    # -------------------------------------------------------------------------
    # TAB 3: SỔ BÁO GIẢNG CÁ NHÂN
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("📖 Tra Cứu Sổ Báo Giảng Tuần")
        tuan_sbg = st.number_input(
            "Chọn Tuần học:", min_value=1, max_value=35, value=1, step=1
        )
        try:
            with st.spinner("Đang tính toán tiến độ Sổ Báo Giảng..."):
                rows_sbg, tong_tiet_sbg = sbg_service.lay_du_lieu_bao_giang(
                    DB_URI, user["magv"], user["to_bm"], int(tuan_sbg)
                )
            st.success(f"Tuần {tuan_sbg}: Tổng cộng {tong_tiet_sbg} tiết thực dạy")

            for r in rows_sbg:
                if r["row_type"] != "empty":
                    c_tag = (
                        "🔴"
                        if r["row_type"] == "nghi"
                        else (
                            "🟡"
                            if r["row_type"] == "day_thay"
                            else (
                                "🔵"
                                if r["row_type"] == "hsg"
                                else "🟢"
                            )
                        )
                    )

                    ngay_str = (
                        r["ngay"].strftime("%d/%m")
                        if hasattr(r["ngay"], "strftime")
                        else str(r["ngay"])
                    )
                    thu_str = f"Thứ {r['thu_num']}"

                    st.markdown(
                        f"""
                    **{c_tag} {thu_str} ({ngay_str}) - Tiết {r['tiet']}**: Lớp **{r['lop']}**  
                    • **Môn/PM:** {r['mon_pm']} | **Tiết PPCT:** {r['tiet_ppct']} | **Bài dạy:** {r['ten_bai']}  
                    • **Tiến độ:** *{r['tre_vuot']}* {f"| Ghi chú: {r['chu_y']}" if r['chu_y'] else ""}
                    """
                    )
                    st.divider()
        except Exception as e:
            st.error(f"Lỗi nạp báo giảng: {e}")
    # -------------------------------------------------------------------------
    # TAB 4: BÁO NGHỈ DẠY
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("⛔ Đăng Ký Báo Nghỉ Giảng Dạy")
        loai_nghi = st.selectbox(
            "Lý do nghỉ:",
            [
                "Nghỉ việc riêng",
                "Nghỉ theo kế hoạch (Họp, Lễ)",
                "Nghỉ theo điều động",
            ],
        )
        ngay_nghi = st.date_input("Ngày nghỉ:", date.today(), key="ngay_nghi_tab")
        thu_so = ngay_nghi.weekday() + 2

        col_b, col_t = st.columns(2)
        with col_b:
            buoi_nghi = st.selectbox(
                "Buổi:", ["Sáng", "Chiều"], key="b_nghi_tab"
            )
        with col_t:
            tiet_nghi = st.selectbox(
                "Tiết TKB:", [1, 2, 3, 4, 5], key="t_nghi_tab"
            )

        lop_tkb, pm_tkb = "", ""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
            """,
                (user["magv"], str(thu_so), thu_so, buoi_nghi, tiet_nghi),
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
                st.warning(
                    f"⚠️ Thứ {thu_so} Tiết {tiet_nghi} không có trên TKB!"
                )
        except Exception:
            pass

        lydo_nghi = st.text_input(
            "Chi tiết lý do (*):", placeholder="Bắt buộc nhập lý do..."
        )
        if st.button("GỬI BÁO NGHỈ", type="primary"):
            if not lydo_nghi.strip():
                st.error("Bắt buộc phải nhập lý do chi tiết!")
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
                            buoi_nghi,
                            tiet_nghi,
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

    # -------------------------------------------------------------------------
    # TAB 5: ĐĂNG KÝ DẠY BÙ (THÔNG MINH: TỰ QUÉT VÀ CHỌN TIẾT ĐÃ NGHỈ)
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("🟢 Đăng Ký Dạy Bù Cho Tiết Đã Nghỉ")

        # 1. TỰ ĐỘNG QUÉT CÁC TIẾT ĐÃ BÁO NGHỈ TRƯỚC ĐÂY
        ds_tiet_nghi_chua_bu = []
        map_tiet_nghi = {}
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, ngay, buoi, tiet_tkb, lop, phan_mon, ly_do 
                FROM bien_dong_lich_day 
                WHERE magv = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC
            """,
                (user["magv"],),
            )
            raw_nghi = cur.fetchall()
            cur.close()
            conn.close()

            if raw_nghi:
                for r in raw_nghi:
                    d_f = r[1].strftime("%d/%m/%Y")
                    label = (
                        f"Nghỉ ngày {d_f} (T{r[3]} {r[2]} - Lớp {r[4]} [{r[5]}])"
                        f" | Lý do: {r[6]}"
                    )
                    ds_tiet_nghi_chua_bu.append(label)
                    map_tiet_nghi[label] = {
                        "lop": r[4],
                        "phan_mon": r[5],
                        "ngay_nghi": d_f,
                        "ly_do_cu": r[6],
                    }
        except Exception:
            pass

        if ds_tiet_nghi_chua_bu:
            tiet_nghi_duoc_chon = st.selectbox(
                "👉 Chọn tiết nghỉ cần dạy bù:", ds_tiet_nghi_chua_bu
            )
            info_nghi = map_tiet_nghi[tiet_nghi_duoc_chon]
            st.info(
                f"✔ Sẽ dạy bù cho: Lớp **{info_nghi['lop']}** - Phân môn:"
                f" **{info_nghi['phan_mon']}**"
            )

            ngay_bu = st.date_input(
                "Chọn Ngày dạy bù thực tế:", date.today(), key="ngay_bu_smart"
            )
            col_bb, col_bt = st.columns(2)
            with col_bb:
                b_bu = st.selectbox(
                    "Buổi dạy bù:", ["Sáng", "Chiều"], key="b_bu_smart"
                )
            with col_bt:
                t_bu = st.selectbox(
                    "Tiết dạy bù:", [1, 2, 3, 4, 5], key="t_bu_smart"
                )

            lydo_bu = (
                f"Dạy bù cho tiết nghỉ ngày {info_nghi['ngay_nghi']}"
                f" ({info_nghi['ly_do_cu']})"
            )
            st.text_input("Ghi chú dạy bù:", value=lydo_bu, disabled=True)

            if st.button("🟢 XÁC NHẬN GỬI ĐĂNG KÝ DẠY BÙ", type="primary"):
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
                            b_bu,
                            t_bu,
                            info_nghi["lop"],
                            info_nghi["phan_mon"],
                            lydo_bu,
                        ),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(
                        f"Đã đăng ký dạy bù thành công cho lớp"
                        f" {info_nghi['lop']} vào ngày"
                        f" {ngay_bu.strftime('%d/%m/%Y')}!"
                    )
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")
        else:
            st.success(
                "🎉 Thầy/Cô hiện tại không có tiết nghỉ nào cần phải dạy bù!"
            )
    # -------------------------------------------------------------------------    
    # TAB 6: DẠY THAY & BDHSG
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.subheader("🟡 Đăng Ký Dạy Thay Hoặc Bồi Dưỡng HSG")
        loai_tt = st.radio(
            "Chọn loại hình:",
            ["Dạy thay đồng nghiệp", "Bồi dưỡng học sinh giỏi (x1.5)"],
            horizontal=True,
        )
        ngay_tt = st.date_input("Ngày thực hiện:", date.today(), key="ngay_tt_tab")
        c_tb, c_tt = st.columns(2)
        with c_tb:
            b_tt = st.selectbox("Buổi:", ["Sáng", "Chiều"], key="b_tt_tab")
        with c_tt:
            t_tt = st.selectbox("Tiết:", [1, 2, 3, 4, 5], key="t_tt_tab")

        lop_tt = st.text_input("Lớp / Đội tuyển:", placeholder="VD: 12A2")
        nd_tt = st.text_input(
            "Chi tiết / Tên GV được dạy thay:", placeholder="Nhập chi tiết..."
        )

        if st.button("GỬI ĐĂNG KÝ BIẾN ĐỘNG", type="primary"):
            loai_db_save = (
                "Dạy thay"
                if "Dạy thay" in loai_tt
                else "Bồi dưỡng HSG"
            )
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
                        loai_db_save,
                        ngay_tt,
                        b_tt,
                        t_tt,
                        lop_tt.strip(),
                        user["to_bm"],
                        nd_tt,
                    ),
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"Đã gửi thành công đơn [{loai_db_save}]!")
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # TAB 7: LỊCH SỬ ĐƠN (CÓ NÚT XÓA)
    # -------------------------------------------------------------------------
    with tabs[6]:
        st.subheader("📋 Lịch Sử Các Đơn Biến Động Đã Gửi")
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, loai, ngay, buoi, tiet_tkb, lop, ly_do, trang_thai 
                FROM bien_dong_lich_day 
                WHERE magv = %s AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC, id DESC LIMIT 15
            """,
                (user["magv"],),
            )
            ls = cur.fetchall()
            cur.close()
            conn.close()

            if ls:
                for row in ls:
                    d_str = row[2].strftime("%d/%m/%Y")
                    col_info, col_del = st.columns([4, 1])
                    with col_info:
                        st.markdown(
                            f"**[{row[1]}]** Ngày {d_str} ({row[3]} - Tiết"
                            f" {row[4]} Lớp {row[5]})  \n*{row[6]}*"
                        )
                    with col_del:
                        if st.button("Xóa", key=f"del_btn_{row[0]}"):
                            c_del = get_db()
                            cur_d = c_del.cursor()
                            cur_d.execute(
                                "DELETE FROM bien_dong_lich_day WHERE id = %s"
                                " AND magv = %s",
                                (row[0], user["magv"]),
                            )
                            c_del.commit()
                            cur_d.close()
                            c_del.close()
                            st.success("Đã xóa đơn!")
                            st.rerun()
                    st.divider()
            else:
                st.info("Chưa có đơn biến động nào.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # -------------------------------------------------------------------------
    # NẾU LÀ TỔ TRƯỞNG: TAB SOI BÁO GIẢNG VÀ ĐƠN TỔ
    # -------------------------------------------------------------------------
    if is_totruong:
        with tabs[7]:
            st.subheader(f"👥 Soi Sổ Báo Giảng Của Tổ {user['to_bm']}")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv FROM giao_vien WHERE to_bo_mon = %s"
                    " ORDER BY tengv",
                    (user["to_bm"],),
                )
                gv_list = cur.fetchall()
                cur.close()
                conn.close()

                gv_dict = {f"{r[1]} ({r[0]})": r[0] for r in gv_list}
                gv_duoc_chon = st.selectbox(
                    "Chọn Giáo viên:", list(gv_dict.keys())
                )
                tuan_soi = st.number_input(
                    "Tuần xem:", min_value=1, max_value=35, value=1, step=1
                )

                if st.button("🔍 XEM BÁO GIẢNG"):
                    magv_soi = gv_dict[gv_duoc_chon]
                    rows_soi, t_soi = sbg_service.lay_du_lieu_bao_giang(
                        DB_URI, magv_soi, user["to_bm"], int(tuan_soi)
                    )
                    st.success(f"Tổng số tiết thực dạy: {t_soi} tiết")
                    for r in rows_soi:
                        if r["row_type"] != "empty":
                            st.markdown(
                                f"**{r['thu_ngay']} ({r['buoi']} - Tiết"
                                f" {r['tiet']})**: Lớp **{r['lop']}** | Môn:"
                                f" {r['mon_pm']} | PPCT: {r['tiet_ppct']} | Bài:"
                                f" {r['ten_bai']} | *{r['tre_vuot']}*"
                            )
                            st.divider()
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

        with tabs[8]:
            st.subheader(f"📝 Đơn Báo Nghỉ / Bù Trong Tổ {user['to_bm']}")
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
                st.dataframe(
                    pd.DataFrame(
                        rows_to,
                        columns=[
                            "ID",
                            "Mã GV",
                            "Họ Tên",
                            "Loại",
                            "Ngày",
                            "Buổi",
                            "Tiết",
                            "Lớp",
                            "Lý Do",
                        ],
                    ),
                    use_container_width=True,
                )
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # NẾU LÀ ADMIN / BGH: TAB ĐIỀU HÀNH TOÀN TRƯỜNG
    # -------------------------------------------------------------------------
    elif is_admin:
        with tabs[7]:
            st.subheader("📊 Giám Sát Tiến Độ & Định Mức Giờ Dạy Toàn Trường")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv, to_bo_mon, COALESCE(dinh_muc_tiet, 17)"
                    " FROM giao_vien ORDER BY to_bo_mon, tengv"
                )
                rows_all_dm = cur.fetchall()
                cur.close()
                conn.close()
                st.dataframe(
                    pd.DataFrame(
                        rows_all_dm,
                        columns=[
                            "Mã GV",
                            "Họ và Tên",
                            "Tổ Bộ Môn",
                            "Định Mức/Tuần",
                        ],
                    ),
                    use_container_width=True,
                )
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

        with tabs[8]:
            st.subheader("📝 Quản Lý Toàn Bộ Biến Động Lịch Dạy Toàn Trường")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, magv, loai, ngay, buoi, tiet_tkb, lop, ly_do, trang_thai 
                    FROM bien_dong_lich_day 
                    ORDER BY ngay DESC LIMIT 50
                """)
                rows_bd_all = cur.fetchall()
                cur.close()
                conn.close()
                st.dataframe(
                    pd.DataFrame(
                        rows_bd_all,
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
                    ),
                    use_container_width=True,
                )
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

        with tabs[9]:
            st.subheader("👥 Danh Sách Toàn Thể Hội Đồng Sư Phạm")
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "SELECT magv, tengv, to_bo_mon, chuc_vu, role FROM"
                    " giao_vien ORDER BY to_bo_mon"
                )
                rows_ns = cur.fetchall()
                cur.close()
                conn.close()
                st.dataframe(
                    pd.DataFrame(
                        rows_ns,
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
            except Exception as ex:
                st.error(f"Lỗi: {ex}")

    # -------------------------------------------------------------------------
    # TAB CUỐI CÙNG: ĐỔI MẬT KHẨU
    # -------------------------------------------------------------------------
    with tabs[-1]:
        st.subheader("🔑 Đổi Mật Khẩu Cá Nhân")
        with st.form("doi_mk_all"):
            mk_cu = st.text_input("Mật khẩu hiện tại:", type="password")
            mk_moi = st.text_input("Mật khẩu mới:", type="password")
            mk_nhap_lai = st.text_input(
                "Nhập lại mật khẩu mới:", type="password"
            )
            if st.form_submit_button("XÁC NHẬN ĐỔI MẬT KHẨU", type="primary"):
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