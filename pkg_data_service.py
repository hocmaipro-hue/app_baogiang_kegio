# pkg_data_service.py
from datetime import date, datetime, timedelta
import re
from config import DB_URI
import psycopg2
import service_so_bao_giang as sbg_service


def rut_gon_phan_cong(ds_mon_lop):
    lop_dict = {}
    for mon, lop in ds_mon_lop:
        if not lop or lop in ['SHDC', 'SHL', 'EMPTY']:
            continue
        m_c = mon.strip()
        if lop not in lop_dict:
            lop_dict[lop] = []
        lop_dict[lop].append(m_c)

    kq = []
    for lop, mons in lop_dict.items():
        co_cd = any('chuyên đề' in m.lower() or 'cđ' in m.lower() for m in mons)
        mon_chinh = next(
            (
                m
                for m in mons
                if 'chuyên đề' not in m.lower() and 'cđ' not in m.lower()
            ),
            'Toán',
        )
        if co_cd and mon_chinh:
            kq.append(f'{mon_chinh} {lop}+CĐ {lop}')
        elif co_cd:
            kq.append(f'CĐ {lop}')
        else:
            kq.append(f'{mon_chinh} {lop}')
    return '; '.join(kq)


def lay_du_lieu_pkg(magv, tu_tuan, den_tuan, extra_info=None):
    if extra_info is None:
        extra_info = {}

    base_monday = sbg_service.get_ngay_bat_dau_nam_hoc(DB_URI)

    # 1. TỰ ĐỘNG TÍNH SỐ TUẦN & KHOẢNG NGÀY CHUẨN XÁC
    if 'tu_ngay' in extra_info and 'den_ngay' in extra_info:
        d_start = datetime.strptime(extra_info['tu_ngay'], '%d/%m/%Y').date()
        d_end = datetime.strptime(extra_info['den_ngay'], '%d/%m/%Y').date()
        if 'so_tuan' in extra_info:
            so_tuan = int(extra_info['so_tuan'])
        else:
            so_ngay = (d_end - d_start).days + 1
            so_tuan = max(1, round(so_ngay / 7))
    else:
        so_tuan = den_tuan - tu_tuan + 1
        d_start = base_monday + timedelta(days=(tu_tuan - 1) * 7)
        d_end = base_monday + timedelta(days=den_tuan * 7 - 2)

    ngay_giua = d_start + (d_end - d_start) / 2

    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COALESCE(dinh_muc_tiet, 17), COALESCE(chuc_vu, 'Giáo viên'), 
               COALESCE(kiem_nhiem, ''), COALESCE(tiet_giam_tru, 0),
               COALESCE(kiem_nhiem_2, ''), COALESCE(giam_tru_kn2, 0),
               COALESCE(con_nho, ''), COALESCE(giam_tru_con_nho, 0),
               COALESCE(hopdong_lan_dau, ''), COALESCE(giam_tru_hopdong_landau, 0),
               to_bo_mon
        FROM giao_vien WHERE magv = %s
    """,
        (magv,),
    )
    row_gv = cur.fetchone() or (
        17,
        'Giáo viên',
        '',
        0,
        '',
        0,
        '',
        0,
        '',
        0,
        'Toán',
    )
    to_bm_gv = row_gv[10]

    cur.execute(
        "SELECT tengv FROM giao_vien WHERE to_bo_mon = %s AND role ="
        " 'TO_TRUONG' LIMIT 1",
        (to_bm_gv,),
    )
    r_tt = cur.fetchone()
    ten_totruong = r_tt[0] if r_tt else 'Tổ trưởng'

    cur.execute(
        "SELECT tengv FROM giao_vien WHERE role = 'ADMIN' OR chuc_vu ILIKE"
        " '%Hiệu trưởng%' LIMIT 1"
    )
    r_ad = cur.fetchone()
    ten_admin = r_ad[0] if r_ad else 'Bùi Duy Minh Trí'

    cur.execute(
        'SELECT DISTINCT mon, lop FROM thoi_khoa_bieu WHERE magv = %s AND lop'
        " NOT IN ('SHDC', 'SHL', 'EMPTY')",
        (magv,),
    )
    str_phan_cong = rut_gon_phan_cong(cur.fetchall())

    cur.execute(
        'SELECT DISTINCT lop FROM thoi_khoa_bieu WHERE magv = %s AND lop NOT IN'
        " ('SHDC', 'SHL', 'EMPTY') ORDER BY lop",
        (magv,),
    )
    danh_sach_lop = [r[0] for r in cur.fetchall()]

    # MA TRẬN MỤC 3
    tkb_matrix = {l: {'weeks': [0] * 5, 'notes': ''} for l in danh_sach_lop}
    ds_ghichu_lop = {l: set() for l in danh_sach_lop}

    for w_idx in range(min(so_tuan, 5)):
        curr_tuan = tu_tuan + w_idx
        rows_data, _ = sbg_service.lay_du_lieu_bao_giang(
            DB_URI, magv, to_bm_gv, curr_tuan
        )
        for row in rows_data:
            lop_r = row.get('lop', '')
            row_type = row.get('row_type', '')
            if lop_r in tkb_matrix:
                if row_type == 'day_chinh':
                    tkb_matrix[lop_r]['weeks'][w_idx] += 1
                elif row_type == 'nghi':
                    ten_bai_nghi = row.get('ten_bai', '')
                    if '[NGHỈ VIỆC RIÊNG]' not in ten_bai_nghi.upper():
                        ly_do_nghi = row.get('ghi_chu', '') or ten_bai_nghi
                        m_ld = re.sub(r'\[.*?\]:?', '', ly_do_nghi).strip()
                        if m_ld and m_ld not in ['EMPTY', '']:
                            ds_ghichu_lop[lop_r].add(m_ld)

    for lop in danh_sach_lop:
        if ds_ghichu_lop[lop]:
            tkb_matrix[lop]['notes'] = '; '.join(sorted(ds_ghichu_lop[lop]))

    # BIẾN ĐỘNG & BDHSG
    cur.execute(
        """
        SELECT loai, ngay, COALESCE(lop, ''), COALESCE(ly_do, ''), COALESCE(gv_day_thay, '')
        FROM bien_dong_lich_day 
        WHERE magv = %s AND ngay BETWEEN %s AND %s AND trang_thai != 'DA_HUY' 
        ORDER BY ngay ASC
    """,
        (magv, d_start, d_end),
    )
    all_bd = cur.fetchall()

    cur.execute(
        'SELECT COALESCE(SUM(bdhsg_quy_doi), 0) FROM kg_hoc_sinh_gioi WHERE'
        ' magv = %s',
        (magv,),
    )
    r_hsg = cur.fetchone()
    # Giữ nguyên số thực float
    tong_hsg = float(r_hsg[0] if r_hsg else 0.0)

    cur.close()
    conn.close()

    raw_day_bu = {}
    raw_nghi_rieng = {}
    raw_day_thay = {}
    raw_nghi_dd = {}

    for b in all_bd:
        loai, ngay, lop, lydo, gv_thay = b[0], b[1], b[2], b[3], b[4]
        if loai == 'Nghỉ theo kế hoạch':
            continue
        elif loai == 'Dạy bù':
            if ngay not in raw_day_bu:
                raw_day_bu[ngay] = {}
            raw_day_bu[ngay][lop] = raw_day_bu[ngay].get(lop, 0) + 1
        elif loai in ['Nghỉ việc riêng', 'Nghỉ dạy']:
            if ngay not in raw_nghi_rieng:
                raw_nghi_rieng[ngay] = {'ly_do': lydo, 'lops': {}}
            if lydo and not raw_nghi_rieng[ngay]['ly_do']:
                raw_nghi_rieng[ngay]['ly_do'] = lydo
            raw_nghi_rieng[ngay]['lops'][lop] = (
                raw_nghi_rieng[ngay]['lops'].get(lop, 0) + 1
            )
        elif loai == 'Dạy thay':
            key_dt = (ngay, gv_thay, lydo or 'Dạy thay', lop)
            raw_day_thay[key_dt] = raw_day_thay.get(key_dt, 0) + 1
        elif loai == 'Nghỉ theo điều động':
            key_dd = (
                ngay,
                lydo if lydo else '- Công văn/Kế hoạch (có đính kèm)',
                lop,
            )
            raw_nghi_dd[key_dd] = raw_nghi_dd.get(key_dd, 0) + 1

    dic_day_bu = {}
    for d, lops_dict in raw_day_bu.items():
        dic_day_bu[d] = {
            'items': [(lp, so_gio) for lp, so_gio in lops_dict.items()]
        }

    dic_nghi_rieng = {}
    for d, info in raw_nghi_rieng.items():
        dic_nghi_rieng[d] = {
            'ly_do': info['ly_do'] if info['ly_do'] else 'Nghỉ việc riêng',
            'items': [(lp, so_gio) for lp, so_gio in info['lops'].items()],
        }

    ds_day_thay = [
        {'ngay': d, 'gv_thay': gv_t, 'ly_do': ld, 'lop': lp, 'tiet': so_gio}
        for (d, gv_t, ld, lp), so_gio in raw_day_thay.items()
    ]
    ds_nghi_dieudong = [
        {'ngay': d, 'ly_do': ld, 'lop': lp, 'tiet': so_gio}
        for (d, ld, lp), so_gio in raw_nghi_dd.items()
    ]

    return {
        'so_tuan': so_tuan,
        'd_start': d_start,
        'd_end': d_end,
        'ngay_giua': ngay_giua,
        'dm_tuan': row_gv[0],
        'chuc_vu': row_gv[1],
        'tong_dm': row_gv[0] * so_tuan,
        'kn1': row_gv[2],
        'gt_kn1': float(row_gv[3] or 0),
        'kn2': row_gv[4],
        'gt_kn2': float(row_gv[5] or 0),
        'gt_khac': float(row_gv[7] or 0) + float(row_gv[9] or 0),
        'str_phan_cong': str_phan_cong,
        'tkb_matrix': tkb_matrix,
        'ds_day_thay': ds_day_thay,
        'dic_nghi_rieng': dic_nghi_rieng,
        'dic_day_bu': dic_day_bu,
        'ds_nghi_dieudong': ds_nghi_dieudong,
        'tong_hsg': tong_hsg,
        'ten_totruong': ten_totruong,
        'ten_admin': ten_admin,
    }