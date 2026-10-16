# service_so_bao_giang.py
from datetime import date, datetime, timedelta
import re
import psycopg2

_SCHEMA_CHECKED = False


def ensure_database_schema(db_uri):
    """Chỉ kiểm tra cấu trúc các bảng cần thiết, bỏ qua so_bao_giang."""
    global _SCHEMA_CHECKED
    if _SCHEMA_CHECKED:
        return
    try:
        conn = psycopg2.connect(db_uri)
        cur = conn.cursor()
        cur.execute(
            "ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS phan_mon"
            " VARCHAR(100);"
        )
        cur.execute(
            "ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS"
            " gv_day_thay VARCHAR(100);"
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cau_hinh_moc_ppct (
                id SERIAL PRIMARY KEY,
                magv VARCHAR(50),
                lop VARCHAR(20),
                phan_mon VARCHAR(100),
                tu_tuan INT,
                tiet_bat_dau INT,
                UNIQUE(magv, lop, phan_mon, tu_tuan)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        _SCHEMA_CHECKED = True
    except Exception as e:
        print(f"Lỗi kiểm tra cấu trúc bảng: {e}")


def get_ngay_bat_dau_nam_hoc(db_uri):
    try:
        conn = psycopg2.connect(db_uri)
        cur = conn.cursor()
        cur.execute(
            "SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'"
        )
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            val = r[0].strip()
            if isinstance(val, (datetime, date)):
                return val if isinstance(val, date) else val.date()
            return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        pass
    return datetime.strptime("2026-09-07", "%Y-%m-%d").date()


def parse_thu(thu_val):
    m = re.search(r"\d+", str(thu_val))
    return int(m.group()) if m else 2


def trich_xuat_khoi(ten_lop):
    m = re.search(r"\d+", str(ten_lop))
    return int(m.group()) if m else 10


def chuan_hoa_phan_mon(mon, phan_mon):
    m_clean = str(mon).strip().lower()
    pm_clean = str(phan_mon).strip()
    if "chuyên đề" in m_clean or "chuyên đề" in pm_clean.lower():
        return "Chuyên đề"
    return pm_clean if pm_clean else str(mon).strip()


def to_date_only(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    return d


def tinh_tuan_tu_ngay(db_uri, ngay_target):
    base_monday = get_ngay_bat_dau_nam_hoc(db_uri)
    ngay_tg = to_date_only(ngay_target)
    delta_days = (ngay_tg - base_monday).days
    if delta_days < 0:
        return 1
    return (delta_days // 7) + 1


def lay_du_lieu_bao_giang(db_uri, magv, to_bm, tuan):
    ensure_database_schema(db_uri)
    base_monday = get_ngay_bat_dau_nam_hoc(db_uri)
    mon_tuan_nay = base_monday + timedelta(days=(tuan - 1) * 7)
    sun_tuan_nay = mon_tuan_nay + timedelta(days=6)

    conn = psycopg2.connect(db_uri)
    cur = conn.cursor()

    # 1. TKB tuần
    cur.execute(
        """
        SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon, COALESCE(phan_mon,''), ap_dung_tu_tuan
        FROM thoi_khoa_bieu 
        WHERE magv = %s AND (ap_dung_tu_tuan IS NULL OR ap_dung_tu_tuan <= %s)
        ORDER BY ap_dung_tu_tuan DESC, thu ASC, tiet ASC
    """,
        (magv, tuan),
    )
    all_tkb_rows = cur.fetchall()

    tkb_rows = []
    seen_slots = set()
    for r in all_tkb_rows:
        slot_key = (r[0], r[1], r[2])
        if slot_key not in seen_slots:
            seen_slots.add(slot_key)
            tkb_rows.append(r[:6])

    # 2. Lấy biến động
    cur.execute(
        """
        SELECT loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(ly_do,''), COALESCE(gv_day_thay,''), COALESCE(phan_mon,'')
        FROM bien_dong_lich_day 
        WHERE magv = %s AND ngay <= %s AND trang_thai != 'DA_HUY'
        ORDER BY ngay, tiet_tkb ASC
    """,
        (magv, sun_tuan_nay),
    )
    all_bd = [
        (b[0], to_date_only(b[1]), b[2], b[3], b[4], b[5], b[6], b[7])
        for b in cur.fetchall()
    ]

    # 3. Lấy PPCT
    cur.execute(
        """
        SELECT id, phan_mon, khoi, tiet_ppct, ten_bai_day, tuan
        FROM phan_phoi_chuong_trinh 
        WHERE (UPPER(mon) = UPPER(%s) OR UPPER(mon) LIKE '%%CHUYÊN ĐỀ%%' OR %s ILIKE '%%' || mon || '%%')
        ORDER BY khoi, phan_mon, tiet_ppct ASC
    """,
        (to_bm, to_bm),
    )
    ppct_map = {}
    ppct_target_map = {}
    for pid, pm, kh, tp, tb, tw in cur.fetchall():
        pm_k = str(pm).strip().lower()
        if "chuyên đề" in pm_k:
            pm_k = "chuyên đề"
        ppct_map[(pm_k, int(kh), int(tp))] = (pid, tb)
        k_target = (pm_k, int(kh), int(tw))
        if k_target not in ppct_target_map or tp > ppct_target_map[k_target]:
            ppct_target_map[k_target] = tp

    # 4. ĐỌC CÁC MỐC KHỞI ĐIỂM
    cur.execute(
        """
        SELECT lop, phan_mon, tu_tuan, tiet_bat_dau 
        FROM cau_hinh_moc_ppct 
        WHERE magv = %s AND tu_tuan <= %s
        ORDER BY tu_tuan ASC
    """,
        (magv, tuan),
    )
    moc_ppct_dict = {}
    for l_m, pm_m, tw_m, tb_m in cur.fetchall():
        pm_k = pm_m.strip().lower()
        if "chuyên đề" in pm_k:
            pm_k = "chuyên đề"
        moc_ppct_dict[(l_m.strip().upper(), pm_k)] = (tw_m, tb_m)

    cur.close()
    conn.close()

    # 5. TÍNH TOÁN LŨY TIẾN TIẾT PPCT
    counter = {}
    start_week_dict = {}
    for (l_key, pm_key), (moc_tuan, moc_tiet) in moc_ppct_dict.items():
        counter[(l_key, pm_key)] = moc_tiet - 1
        start_week_dict[(l_key, pm_key)] = moc_tuan

    for w in range(1, tuan):
        w_mon = base_monday + timedelta(days=(w - 1) * 7)
        w_sun = w_mon + timedelta(days=6)
        w_bd = [b for b in all_bd if w_mon <= b[1] <= w_sun]

        for r in tkb_rows:
            thu_num = parse_thu(r[0])
            tiet_tkb = r[2]
            lop_tkb = r[3]
            mon_tkb = r[4].strip()
            pm_tkb = chuan_hoa_phan_mon(mon_tkb, r[5]).lower()
            if "chuyên đề" in pm_tkb:
                pm_tkb = "chuyên đề"
            if mon_tkb in ["SHDC", "SHL"]:
                continue

            pair = (lop_tkb.upper(), pm_tkb)
            if w < start_week_dict.get(pair, 1):
                continue

            day_of_session = w_mon + timedelta(days=thu_num - 2)
            is_nghi = any(
                b[0].startswith("Nghỉ")
                and b[1] == day_of_session
                and b[3] == tiet_tkb
                for b in w_bd
            )
            if not is_nghi:
                counter[pair] = counter.get(pair, 0) + 1

        for b in w_bd:
            if b[0] == "Dạy bù" and b[4]:
                lop_bu = b[4].upper()
                pm_bu = b[7].strip().lower() if len(b) > 7 and b[7] else ""
                if not pm_bu:
                    pm_bu = (
                        "chuyên đề"
                        if "chuyên đề" in to_bm.lower()
                        else to_bm.lower()
                    )
                pair = (lop_bu, pm_bu)
                if w >= start_week_dict.get(pair, 1):
                    counter[pair] = counter.get(pair, 0) + 1

    # 6. TUẦN HIỆN TẠI
    bd_tuan_nay = [b for b in all_bd if mon_tuan_nay <= b[1] <= sun_tuan_nay]
    active_slots = {}
    for r in tkb_rows:
        thu_num = parse_thu(r[0])
        buoi = r[1]
        tiet = r[2]
        lop = r[3]
        mon = r[4].strip()
        phan_mon = chuan_hoa_phan_mon(mon, r[5])
        ngay_day = mon_tuan_nay + timedelta(days=thu_num - 2)
        active_slots[(thu_num, buoi, tiet)] = {
            "ngay": ngay_day,
            "lop": lop,
            "mon": mon,
            "phan_mon": phan_mon,
            "loai": "TKB",
            "extra": "",
            "gv_thay": "",
        }

    for b in bd_tuan_nay:
        (
            loai_bd,
            ngay_bd,
            buoi_bd,
            tiet_bd,
            lop_bd,
            ly_do,
            gv_thay_bd,
            phan_mon_bd,
        ) = b
        thu_bd = ngay_bd.weekday() + 2
        k = (thu_bd, buoi_bd, tiet_bd)
        if loai_bd.startswith("Nghỉ"):
            if k in active_slots:
                active_slots[k]["loai"] = loai_bd
                active_slots[k]["extra"] = ly_do
        elif loai_bd in ["Dạy bù", "Dạy thay", "Bồi dưỡng HSG"]:
            pm_dang_ky = (
                phan_mon_bd.strip()
                if phan_mon_bd
                else (
                    "BDHSG" if loai_bd == "Bồi dưỡng HSG" else to_bm
                )
            )
            active_slots[k] = {
                "ngay": ngay_bd,
                "lop": lop_bd,
                "mon": to_bm,
                "phan_mon": pm_dang_ky,
                "loai": loai_bd,
                "extra": ly_do,
                "gv_thay": gv_thay_bd,
            }

    # 7. KHUNG 60 TIẾT
    final_rows = []
    tong_tiet_thuc = 0

    for thu in range(2, 8):
        ngay_hien_tai = mon_tuan_nay + timedelta(days=thu - 2)
        ngay_str = ngay_hien_tai.strftime("%d/%m")
        slot_idx_in_day = 0

        for buoi in ["Buổi sáng", "Buổi chiều"]:
            buoi_short = "Sáng" if buoi == "Buổi sáng" else "Chiều"
            slot_idx_in_buoi = 0

            for tiet in range(1, 6):
                slot_idx_in_day += 1
                slot_idx_in_buoi += 1
                col_thu_ngay = (
                    f"THỨ {thu}"
                    if slot_idx_in_day == 1
                    else (f"({ngay_str})" if slot_idx_in_day == 2 else "")
                )
                col_buoi_text = buoi if slot_idx_in_buoi == 1 else ""

                key = (thu, buoi_short, tiet)
                slot = active_slots.get(key)
                lop = ""
                tiet_ppct_str = ""
                mon_pm = ""
                ten_bai = ""
                tre_vuot = ""
                chu_y = ""
                ppct_id = None
                mon_goc = ""
                phan_mon_luu = ""
                row_type = "empty"

                if slot:
                    mon_goc = slot["mon"]
                    lop = slot["lop"]
                    phan_mon = slot["phan_mon"]
                    phan_mon_luu = phan_mon
                    loai = slot["loai"]
                    mon_pm = phan_mon if phan_mon else mon_goc
                    khoi = trich_xuat_khoi(lop)
                    pm_key = phan_mon.strip().lower()
                    if "chuyên đề" in pm_key:
                        pm_key = "chuyên đề"

                    if mon_goc in ["SHDC", "SHL"]:
                        lop = ""
                        mon_pm = ""
                        ten_bai = ""
                        tiet_ppct_str = ""
                        phan_mon_luu = ""
                    elif loai.startswith("Nghỉ"):
                        tiet_ppct_str = "-"
                        ten_bai = f"[{loai.upper()}]: {slot['extra']}"
                        tre_vuot = "Trễ 1 tiết"
                        row_type = "nghi"
                        chu_y = slot["extra"] or loai
                    elif loai == "Bồi dưỡng HSG":
                        lop = lop if lop else ""
                        mon_pm = "BDHSG"
                        tiet_ppct_str = "-"
                        ten_bai = f"[BỒI DƯỠNG HSG]: {slot['extra']}"
                        tong_tiet_thuc += 1
                        row_type = "hsg"
                    elif loai == "Dạy thay":
                        mon_pm = phan_mon if phan_mon else "Dạy thay"
                        tiet_ppct_str = "-"
                        ten_gv_thay = (
                            slot["gv_thay"]
                            if slot["gv_thay"]
                            else "đồng nghiệp"
                        )
                        ten_bai = f"[DẠY THAY {ten_gv_thay}]: {slot['extra']}"
                        tong_tiet_thuc += 1
                        row_type = "day_thay"
                    else:
                        row_type = "day_chinh"
                        pair = (lop.upper(), pm_key)
                        counter[pair] = counter.get(pair, 0) + 1
                        tiet_thuc = counter[pair]
                        tiet_ppct_str = str(tiet_thuc)
                        tong_tiet_thuc += 1

                        ppct_info = ppct_map.get((pm_key, khoi, tiet_thuc))
                        if ppct_info:
                            ppct_id, ten_bai = ppct_info
                        else:
                            ten_bai = f"Bài theo PPCT tiết {tiet_thuc}"

                        if loai == "Dạy bù":
                            ten_bai = f"[DẠY BÙ]: {ten_bai}"
                            row_type = "day_bu"

                        tiet_ke_hoach = ppct_target_map.get(
                            (pm_key, khoi, tuan)
                        )
                        if tiet_ke_hoach:
                            diff = tiet_thuc - tiet_ke_hoach
                            if diff == 0:
                                tre_vuot = "Đúng tiến độ"
                            elif diff < 0:
                                tre_vuot = f"Trễ {abs(diff)} tiết"
                            else:
                                tre_vuot = f"Vượt {diff} tiết"
                        else:
                            tre_vuot = "Đúng tiến độ"

                final_rows.append({
                    "thu_ngay": col_thu_ngay,
                    "buoi": col_buoi_text,
                    "tiet": str(tiet),
                    "lop": lop,
                    "tiet_ppct": tiet_ppct_str,
                    "mon_pm": mon_pm,
                    "ten_bai": ten_bai,
                    "tre_vuot": tre_vuot,
                    "chu_y": chu_y,
                    "thu_num": thu,
                    "row_type": row_type,
                    "ngay": ngay_hien_tai,
                    "mon": mon_goc,
                    "phan_mon": phan_mon_luu,
                    "ppct_id": ppct_id,
                })

    return final_rows, tong_tiet_thuc


# 👉 KHÔNG ĐỒNG BỘ GÌ CẢ ĐỂ TIẾT KIỆM SUPABASE (GIỮ LẠI HÀM RỖNG ĐỂ TRÁNH LỖI GỌI)
def luu_nhanh_so_bao_giang(db_uri, magv, tuan, rows_data):
    pass


def tu_dong_dong_bo_tuan(db_uri, magv, to_bm, ngay_bien_dong):
    pass