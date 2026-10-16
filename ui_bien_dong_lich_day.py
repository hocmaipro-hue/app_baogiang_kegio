import streamlit as st
import psycopg2
from datetime import datetime, date, timedelta
import re
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_nam_hoc():
    try:
        conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'")
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            return datetime.strptime(r[0].strip(), "%Y-%m-%d").year
    except Exception:
        pass
    return 2026

def chuan_hoa_ngay(s):
    if isinstance(s, (date, datetime)):
        return s if isinstance(s, date) and not isinstance(s, datetime) else s.date()
    s = str(s).strip()
    nam = get_nam_hoc()
    m1 = re.match(r'^(\d{1,2})[/-](\d{1,2})$', s)
    if m1:
        try:
            return date(nam, int(m1.group(2)), int(m1.group(1)))
        except ValueError:
            return None
    m2 = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', s)
    if m2:
        try:
            return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
        except ValueError:
            return None
    return None

def trich_khoi(ten_lop):
    m = re.search(r'\d+', str(ten_lop))
    return int(m.group()) if m else 10

def run_bien_dong_lich_day_dashboard(current_session):
    magv = current_session.get("magv")
    tengv = current_session.get("tengv")
    to_bm = current_session.get("to_bo_mon", "Toán")

    st.title("🔄 Quản Lý Biến Động Lịch Dạy")
    st.write(f"Giáo viên thực hiện: **{tengv}** (Tổ: {to_bm})")

    # Tạo các tab con phân chia nghiệp vụ rõ ràng
    tab_nghi, tab_bu, tab_thay_hsg, tab_lich_su = st.tabs([
        "⛔ Đăng Ký Báo Nghỉ", 
        "➕ Đăng Ký Dạy Bù", 
        "⭐ Dạy Thay & BD HSG", 
        "📋 Lịch Sử Biến Động"
    ])

    # ================= TAB 1: BÁO NGHỈ =================
    with tab_nghi:
        st.subheader("Đăng ký Báo Nghỉ Giảng Dạy")
        st.info("Hệ thống tự động tra cứu TKB cá nhân khi bạn chọn ngày và tiết nghỉ.")

        with st.form("form_bao_nghi"):
            col1, col2 = st.columns(2)
            with col1:
                loai_nghi = st.selectbox("Lý do nghỉ chung", ["Nghỉ việc riêng", "Nghỉ theo kế hoạch", "Nghỉ theo điều động"])
                ngay_str = st.text_input("Từ ngày (VD: 15/09 hoặc 15/09/2026)", value=datetime.now().strftime("%d/%m/%Y"))
                buoi_nghi = st.selectbox("Buổi nghỉ", ["Sáng", "Chiều"])
            with col2:
                den_ngay_str = st.text_input("Đến ngày (Dành cho nghỉ dài hạn / nghỉ Tết - nếu có)", placeholder="Bỏ trống nếu nghỉ 1 ngày")
                tiet_nghi = st.selectbox("Tiết TKB bắt đầu", [1, 2, 3, 4, 5])
                ly_do_chi_tiet = st.text_input("Chi tiết lý do / Quyết định số (* Bắt buộc để kê Phiếu 1C)")

            submitted_nghi = st.form_submit_button("⛔ Gửi Đăng Ký Báo Nghỉ", use_container_width=True)

            if submitted_nghi:
                if not ly_do_chi_tiet.strip():
                    st.warning("⚠️ Thầy/Cô BẮT BUỘC phải nhập 'Chi tiết lý do / QĐ' để kê khai Phiếu 1C!")
                else:
                    d_tu = chuan_hoa_ngay(ngay_str)
                    if not d_tu:
                        st.error("❌ Ngày bắt đầu không hợp lệ!")
                    else:
                        try:
                            conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
                            cur = conn.cursor()

                            # Trường hợp nghỉ dài hạn / nghỉ khoảng ngày
                            if den_ngay_str.strip():
                                d_den = chuan_hoa_ngay(den_ngay_str)
                                if not d_den or d_den < d_tu:
                                    st.error("❌ 'Đến ngày' không hợp lệ hoặc nhỏ hơn 'Từ ngày'!")
                                else:
                                    cur.execute("SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon, COALESCE(phan_mon,'') FROM thoi_khoa_bieu WHERE magv = %s", (magv,))
                                    tkb_all = cur.fetchall()

                                    cur_d = d_tu
                                    count = 0
                                    while cur_d <= d_den:
                                        thu_num = cur_d.weekday() + 2
                                        for r in tkb_all:
                                            t_thu = int(re.search(r'\d+', str(r[0])).group()) if re.search(r'\d+', str(r[0])) else 2
                                            if t_thu == thu_num and r[4].strip() not in ['SHDC', 'SHL']:
                                                t_pm = r[5].strip() if r[5].strip() else r[4].strip()
                                                cur.execute("""
                                                    SELECT id FROM bien_dong_lich_day 
                                                    WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                                                """, (magv, cur_d, r[1], r[2]))
                                                if not cur.fetchone():
                                                    cur.execute("""
                                                        INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                                        VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                                    """, (magv, loai_nghi, cur_d, r[1], r[2], r[3], t_pm, ly_do_chi_tiet))
                                                    count += 1
                                        cur_d += timedelta(days=1)
                                    conn.commit()
                                    cur.close()
                                    conn.close()

                                    sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_tu)
                                    if d_den != d_tu:
                                        sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_den)

                                    st.success(f"✅ Đã báo nghỉ thành công {count} tiết trong khoảng thời gian trên và đồng bộ Sổ báo giảng!")
                            else:
                                # Nghỉ 1 tiết đơn lẻ
                                thu_so = d_tu.weekday() + 2
                                cur.execute("""
                                    SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                                    WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                                """, (magv, str(thu_so), thu_so, buoi_nghi, tiet_nghi))
                                r_tkb = cur.fetchone()

                                if not r_tkb:
                                    st.error(f"⚠️ Vào Thứ {thu_so} Tiết {tiet_nghi} ({buoi_nghi}), thầy/cô không có tiết dạy trên TKB!")
                                else:
                                    lop_tkb = r_tkb[0].strip()
                                    pm_tkb = r_tkb[2].strip() if r_tkb[2].strip() else r_tkb[1].strip()

                                    cur.execute("""
                                        SELECT id FROM bien_dong_lich_day 
                                        WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                                    """, (magv, d_tu, buoi_nghi, tiet_nghi))
                                    if cur.fetchone():
                                        st.warning("⚠️ Thầy/Cô đã báo nghỉ tiết này rồi!")
                                    else:
                                        cur.execute("""
                                            INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                        """, (magv, loai_nghi, d_tu, buoi_nghi, tiet_nghi, lop_tkb, pm_tkb, ly_do_chi_tiet))
                                        conn.commit()
                                        cur.close()
                                        conn.close()

                                        sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_tu)
                                        st.success(f"✅ Đã báo nghỉ lớp {lop_tkb} ({pm_tkb}) ngày {d_tu.strftime('%d/%m/%Y')} thành công!")
                        except Exception as e:
                            st.error(f"❌ Lỗi kết nối CSDL: {e}")

    # ================= TAB 2: DẠY BÙ =================
    ্সে = tab_bu
    with tab_bu:
        st.subheader("Đăng ký Lịch Dạy Bù")
        st.info("Hệ thống tự động kiểm tra chống trùng đa tầng (lịch bản thân, lịch của lớp, và lịch giáo viên khác đã đăng ký).")

        # Lấy danh sách lớp của giáo viên để chọn dạy bù
        try:
            conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                ORDER BY lop
            """, (magv,))
            ds_lop = [r[0].strip() for r in cur.fetchall()]

            # Lấy danh sách phân phối chương trình theo khối
            cur.execute("""
                SELECT DISTINCT khoi, COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE (UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%')
                  AND khoi IS NOT NULL
                ORDER BY khoi, 2 ASC
            """, (to_bm, to_bm))
            ppct_data = cur.fetchall()
            cur.close()
            conn.close()
        except Exception:
            ds_lop = []
            ppct_data = []

        ppct_map = {10: [], 11: [], 12: []}
        for kh, pm in ppct_data:
            if pm and pm not in ppct_map.setdefault(kh, []):
                ppct_map[kh].append(pm)

        with st.form("form_day_bu"):
            c1, c2, c3 = st.columns(3)
            with c1:
                ngay_bu_str = st.text_input("Ngày dạy bù (VD: 18/09/2026)", value=datetime.now().strftime("%d/%m/%Y"))
                buoi_bu = st.selectbox("Buổi dạy bù", ["Chiều", "Sáng"])
            with c2:
                tiet_bu = st.selectbox("Tiết dạy bù", [1, 2, 3, 4, 5])
                lop_bu = st.selectbox("Lớp dạy bù", ds_lop if ds_lop else ["10A1", "11A1", "12A1"])
            with c3:
                # Xác định phân môn theo khối lớp chọn
                khoi_chon = trich_khoi(lop_bu)
                ds_pm_khoi = ppct_map.get(khoi_chon, ["Đại số và Giải tích", "Hình học"])
                pm_bu = st.selectbox("Phân môn", ds_pm_khoi if ds_pm_khoi else ["Môn học"])
                lydo_bu = st.text_input("Lý do / Căn cứ dạy bù")

            submitted_bu = st.form_submit_button("➕ Gửi Đăng Ký Dạy Bù", use_container_width=True)

            if submitted_bu:
                d_bu = chuan_hoa_ngay(ngay_bu_str)
                if not d_bu:
                    st.error("❌ Ngày dạy bù không hợp lệ!")
                else:
                    thu_so = d_bu.weekday() + 2
                    ngay_f = d_bu.strftime("%d/%m/%Y")
                    try:
                        conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
                        cur = conn.cursor()

                        # Tầng 1: Kiểm tra bản thân có bận dạy chính khóa không
                        cur.execute("""
                            SELECT lop, mon FROM thoi_khoa_bieu 
                            WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                        """, (magv, str(thu_so), thu_so, buoi_bu, tiet_bu))
                        if cur.fetchone():
                            st.error(f"⛔ Bạn đang có tiết chính khóa vào Thứ {thu_so} Tiết {tiet_bu} ({buoi_bu})! Không thể dạy bù.")
                        else:
                            # Tầng 2: Kiểm tra bản thân đã đăng ký tiết này cho lớp khác chưa
                            cur.execute("""
                                SELECT loai, lop FROM bien_dong_lich_day 
                                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND trang_thai != 'DA_HUY'
                            """, (magv, d_bu, buoi_bu, tiet_bu))
                            bd_me = cur.fetchone()
                            if bd_me:
                                st.error(f"⛔ Bạn đã đăng ký lịch [{bd_me[0]}] cho lớp [{bd_me[1]}] vào thời gian này rồi!")
                            else:
                                # Tầng 3: Kiểm tra lớp có đang học chính khóa theo TKB không
                                cur.execute("""
                                    SELECT t.mon, COALESCE(g.tengv, t.magv)
                                    FROM thoi_khoa_bieu t
                                    LEFT JOIN giao_vien g ON t.magv = g.magv
                                    WHERE UPPER(TRIM(t.lop)) = %s AND (t.thu = %s OR t.thu = %s) AND t.buoi = %s AND t.tiet = %s
                                      AND t.mon IS NOT NULL AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
                                """, (lop_bu.upper(), str(thu_so), thu_so, buoi_bu, tiet_bu))
                                lop_ban = cur.fetchone()
                                if lop_ban:
                                    st.error(f"⛔ Lớp [{lop_bu}] đang bận học môn [{lop_ban[0]}] do GV [{lop_ban[1]}] dạy vào tiết này!")
                                else:
                                    # Tầng 4: Kiểm tra GV khác đã đăng ký dạy bù/thay cho lớp này chưa
                                    cur.execute("""
                                        SELECT b.magv, COALESCE(g.tengv, b.magv), b.loai, COALESCE(b.phan_mon, '')
                                        FROM bien_dong_lich_day b
                                        LEFT JOIN giao_vien g ON b.magv = g.magv
                                        WHERE UPPER(TRIM(b.lop)) = %s AND b.ngay = %s AND b.buoi = %s AND b.tiet_tkb = %s 
                                          AND b.trang_thai != 'DA_HUY' AND b.loai IN ('Dạy bù', 'Dạy thay', 'Bồi dưỡng HSG')
                                    """, (lop_bu.upper(), d_bu, buoi_bu, tiet_bu))
                                    gv_trung = cur.fetchone()
                                    if gv_trung:
                                        st.error(f"⛔ Lớp [{lop_bu}] đã được GV [{gv_trung[1]}] đăng ký [{gv_trung[2]}] vào tiết này!")
                                    else:
                                        cur.execute("""
                                            INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                            VALUES (%s, 'Dạy bù', %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                        """, (magv, d_bu, buoi_bu, tiet_bu, lop_bu, pm_bu, lydo_bu))
                                        conn.commit()
                                        cur.close()
                                        conn.close()

                                        sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_bu)
                                        st.success(f"✅ Đăng ký dạy bù lớp {lop_bu} ngày {ngay_f} thành công!")
                    except Exception as e:
                        st.error(f"❌ Lỗi hệ thống: {e}")

    # ================= TAB 3: DẠY THAY & BỒI DƯỠNG HSG =================
    with tab_thay_hsg:
        st.subheader("Đăng ký Dạy Thay / Bồi Dưỡng HSG")
        
        try:
            conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT magv, tengv FROM giao_vien ORDER BY tengv")
            ds_gv = cur.fetchall()
            cur.close()
            conn.close()
        except Exception:
            ds_gv = []

        map_gv = {f"{g[1]} ({g[0]})": g[0] for g in ds_gv}

        with st.form("form_thay_hsg"):
            c1, c2 = st.columns(2)
            with c1:
                loai_cv = st.selectbox("Loại công việc", ["Dạy thay", "Bồi dưỡng HSG"])
                ngay_cv_str = st.text_input("Ngày thực hiện", value=datetime.now().strftime("%d/%m/%Y"))
                buoi_cv = st.selectbox("Buổi", ["Sáng", "Chiều"], key="buoi_thay")
            with c2:
                tiet_cv = st.selectbox("Tiết", [1, 2, 3, 4, 5], key="tiet_thay")
                gv_duoc_thay_label = st.selectbox("Giáo viên được dạy thay (nếu có)", list(map_gv.keys()) if map_gv else [])
                lop_hsg = st.text_input("Lớp / Đội tuyển HSG", placeholder="VD: 10 Toán hoặc 12A1")
                lydo_cv = st.text_input("Lý do chi tiết")

            submitted_thay = st.form_submit_button("⭐ Gửi Đăng Ký Dạy Thay / HSG", use_container_width=True)
            if submitted_thay:
                d_cv = chuan_hoa_ngay(ngay_cv_str)
                if not d_cv:
                    st.error("❌ Ngày không hợp lệ!")
                else:
                    magv_thay = map_gv.get(gv_duoc_thay_label, "")
                    try:
                        conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
                        """, (magv, loai_cv, d_cv, buoi_cv, tiet_cv, lop_hsg, to_bm, magv_thay, lydo_cv))
                        conn.commit()
                        cur.close()
                        conn.close()

                        sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_cv)
                        st.success(f"✅ Đăng ký thành công [{loai_cv}] ngày {d_cv.strftime('%d/%m/%Y')}!")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")

    # ================= TAB 4: LỊCH SỬ BIẾN ĐỘNG & HỦY =================
    with tab_lich_su:
        st.subheader("📋 Lịch sử các tiết đã đăng ký biến động lịch dạy")
        if st.button("🔄 Tải lại danh sách"):
            st.rerun()

        try:
            conn = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(ly_do,''), trang_thai
                FROM bien_dong_lich_day 
                WHERE magv = %s AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC, tiet_tkb ASC
            """, (magv,))
            records = cur.fetchall()
            cur.close()
            conn.close()

            if records:
                for r in records:
                    rec_id, loai, ngay, buoi, tiet, lop, pm, lydo, trang_thai = r
                    ngay_f = ngay.strftime("%d/%m/%Y") if hasattr(ngay, 'strftime') else str(ngay)
                    
                    with st.expander(f"[{loai}] Ngày {ngay_f} - Buổi {buoi} - Tiết {tiet} - Lớp {lop}"):
                        st.write(- **Phân môn:** {pm})
                        st.write(- **Lý do:** {lydo if lydo else '(Không có)'})
                        st.write(- **Trạng thái duyệt:** {trang_thai})
                        
                        if st.button(f"❌ Hủy đăng ký này (ID: {rec_id})", key=f"huy_{rec_id}"):
                            try:
                                conn_del = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
                                cur_del = conn_del.cursor()
                                cur_del.execute("DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s", (rec_id, magv))
                                conn_del.commit()
                                cur_del.close()
                                conn_del.close()

                                d_huy = chuan_hoa_ngay(ngay)
                                if d_huy:
                                    sbg_service.tu_dong_dong_bo_tuan(DB_URI, magv, to_bm, d_huy)
                                st.success("✅ Đã hủy thành công và cập nhật lại sổ báo giảng!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Không thể hủy: {e}")
            else:
                st.info("Chưa có lịch sử biến động nào được ghi nhận.")
        except Exception as e:
            st.error(f"❌ Lỗi tải dữ liệu: {e}")
