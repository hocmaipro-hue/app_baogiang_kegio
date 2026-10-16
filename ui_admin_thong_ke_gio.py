# ui_admin_thong_ke_gio.py
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk
from config import DB_URI
import psycopg2
from window_manager import open_single_window


def get_val(s, k, d=""):
    return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


def fmt_num(val):
    if val is None:
        return "0"
    try:
        v = float(val)
        return str(int(v)) if v.is_integer() else f"{v:.1f}"
    except (ValueError, TypeError):
        return "0"


def to_float(val, default=0.0):
    if val is None:
        return default
    try:
        s = str(val).strip().replace(",", ".")
        return float(s) if s else default
    except (ValueError, TypeError):
        return default


class AdminThongKeGioWindow:

    def __init__(self, session):
        self.session = session
        self.role = get_val(session, "role", "GV")
        self.to_bm = get_val(session, "to_bo_mon", "")
        self.is_admin = str(self.role).upper() in [
            "ADMIN",
            "BGH",
            "QUẢN TRỊ",
            "BAN GIÁM HIỆU",
        ]

        self.window = tk.Toplevel()
        phan_cap = (
            "TOÀN TRƯỜNG - BGH" if self.is_admin else f"TỔ {self.to_bm.upper()}"
        )
        self.window.title(
            f"Bảng Thống Kê & Giám Sát Giờ Dạy Theo Giai Đoạn - {phan_cap}"
        )
        self.window.geometry("1220x680")
        self.window.configure(bg="#f4f6f9")

        self.ensure_database_schema()

        tieu_de_text = (
            "BẢNG TỔNG HỢP & ĐỐI CHIẾU TIẾT DẠY TOÀN TRƯỜNG THEO GIAI ĐOẠN"
            if self.is_admin
            else f"BẢNG TỔNG HỢP & ĐỐI CHIẾU TIẾT DẠY - TỔ {self.to_bm.upper()}"
        )
        tk.Label(
            self.window,
            text=tieu_de_text,
            font=("Arial", 13, "bold"),
            fg="#1a5276",
            bg="#f4f6f9",
        ).pack(pady=(10, 6))

        filter_frame = tk.LabelFrame(
            self.window,
            text=" Chọn khoảng thời gian thống kê ",
            padx=12,
            pady=8,
            font=("Arial", 9, "bold"),
            fg="#1b4f72",
            bg="#ffffff",
        )
        filter_frame.pack(fill=tk.X, padx=15, pady=4)

        tk.Label(
            filter_frame,
            text="Từ Tuần:",
            font=("Arial", 9, "bold"),
            bg="#ffffff",
        ).pack(side=tk.LEFT, padx=5)
        self.spn_tu_tuan = ttk.Spinbox(
            filter_frame,
            from_=1,
            to=45,
            width=5,
            font=("Arial", 9, "bold"),
            justify="center",
        )
        self.spn_tu_tuan.set(1)
        self.spn_tu_tuan.pack(side=tk.LEFT, padx=5)

        tk.Label(
            filter_frame,
            text="Đến Tuần:",
            font=("Arial", 9, "bold"),
            bg="#ffffff",
        ).pack(side=tk.LEFT, padx=(15, 5))
        self.spn_den_tuan = ttk.Spinbox(
            filter_frame,
            from_=1,
            to=45,
            width=5,
            font=("Arial", 9, "bold"),
            justify="center",
        )
        self.spn_den_tuan.set(4)
        self.spn_den_tuan.pack(side=tk.LEFT, padx=5)

        tk.Button(
            filter_frame,
            text="📊 XEM THỐNG KÊ ĐỢT NÀY",
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.load_thong_ke,
        ).pack(side=tk.LEFT, padx=20)

        self.lbl_info_dot = tk.Label(
            filter_frame,
            text="",
            font=("Arial", 9, "italic"),
            fg="#b03a2e",
            bg="#ffffff",
        )
        self.lbl_info_dot.pack(side=tk.LEFT, padx=5)

        frame_table = tk.Frame(self.window, bg="#ffffff")
        frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=6)

        cols = (
            "magv",
            "tengv",
            "to_bm",
            "dm_dot",
            "tiet_tkb_dot",
            "tbg_tkb",
            "tiet_bd",
            "giam_tru",
            "thuc_day",
            "chenh_lech",
            "ket_luan",
        )
        self.tree = ttk.Treeview(
            frame_table, columns=cols, show="headings", height=15
        )

        self.tree.heading("magv", text="Mã GV")
        self.tree.heading("tengv", text="Họ và Tên")
        self.tree.heading("to_bm", text="Tổ")
        self.tree.heading("dm_dot", text="Định mức đợt")
        self.tree.heading("tiet_tkb_dot", text="Tiết TKB đợt")
        self.tree.heading("tbg_tkb", text="TBG / TKB")
        self.tree.heading("tiet_bd", text="Tiết biến động")
        self.tree.heading("giam_tru", text="Kiêm nhiệm / Giảm trừ")
        self.tree.heading("thuc_day", text="Tổng số tiết đợt")
        self.tree.heading("chenh_lech", text="Thừa/Thiếu")
        self.tree.heading("ket_luan", text="Kết luận")

        self.tree.column("magv", width=70, anchor="center")
        self.tree.column("tengv", width=150, anchor="w")
        self.tree.column("to_bm", width=80, anchor="center")
        self.tree.column("dm_dot", width=85, anchor="center")
        self.tree.column("tiet_tkb_dot", width=85, anchor="center")
        self.tree.column("tbg_tkb", width=95, anchor="center")
        self.tree.column("tiet_bd", width=95, anchor="center")
        self.tree.column("giam_tru", width=150, anchor="center")
        self.tree.column("thuc_day", width=105, anchor="center")
        self.tree.column("chenh_lech", width=85, anchor="center")
        self.tree.column("ket_luan", width=125, anchor="center")

        self.tree.tag_configure("thua", foreground="#1e8449")
        self.tree.tag_configure("thieu", foreground="#c0392b")
        self.tree.tag_configure("du", foreground="#2c3e50")

        sb = ttk.Scrollbar(
            frame_table, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_box = tk.Frame(self.window, bg="#f4f6f9")
        btn_box.pack(pady=(4, 10))

        tk.Button(
            btn_box,
            text="📅 1. Xem TKB của GV này",
            bg="#ebf5fb",
            fg="#1b4f72",
            font=("Arial", 9, "bold"),
            padx=10,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.xem_tkb_gv,
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            btn_box,
            text="📖 2. Soi Sổ Báo Giảng của GV này",
            bg="#e8f8f5",
            fg="#117864",
            font=("Arial", 9, "bold"),
            padx=10,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.xem_sbg_gv,
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            btn_box,
            text="📋 3. Soi Kê Giờ (Phiếu 1C) của GV này",
            bg="#fef9e7",
            fg="#b7950b",
            font=("Arial", 9, "bold"),
            padx=10,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.xem_ke_gio_1c,
        ).pack(side=tk.LEFT, padx=8)

        self.load_thong_ke()

    def ensure_database_schema(self):
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

    def get_ngay_bat_dau_nam_hoc(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "SELECT gia_tri FROM cau_hinh WHERE khoa ="
                " 'ngay_bat_dau_nam_hoc'"
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
        except Exception:
            pass
        return datetime.strptime("2026-09-07", "%Y-%m-%d").date()

    def load_thong_ke(self):
        try:
            tu_tuan = int(self.spn_tu_tuan.get())
            den_tuan = int(self.spn_den_tuan.get())
        except ValueError:
            messagebox.showwarning(
                "Cảnh báo", "Tuần nhập vào phải là số nguyên!"
            )
            return

        if tu_tuan > den_tuan:
            messagebox.showwarning(
                "Cảnh báo", "Từ Tuần phải nhỏ hơn hoặc bằng Đến Tuần!"
            )
            return

        so_tuan = den_tuan - tu_tuan + 1
        base_monday = self.get_ngay_bat_dau_nam_hoc()

        ngay_bat_dau_dot = base_monday + timedelta(days=(tu_tuan - 1) * 7)
        ngay_ket_thuc_dot = base_monday + timedelta(days=(den_tuan - 1) * 7 + 6)

        self.lbl_info_dot.config(
            text=(
                f"👉 Đợt kiểm tra gồm {so_tuan} tuần (Từ"
                f" {ngay_bat_dau_dot.strftime('%d/%m/%Y')} đến"
                f" {ngay_ket_thuc_dot.strftime('%d/%m/%Y')})"
            )
        )

        for r in self.tree.get_children():
            self.tree.delete(r)

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE"
                " table_name = 'giao_vien';"
            )
            gv_cols = set(r[0] for r in cur.fetchall())

            def col_safe(col_name):
                return (
                    f"COALESCE({col_name}::text, '0')"
                    if col_name in gv_cols
                    else "'0'"
                )

            base_sql = f"""
                SELECT magv, tengv, to_bo_mon, 
                       {col_safe('dinh_muc_tiet')},
                       {col_safe('tiet_giam_tru')},
                       {col_safe('giam_tru_con_nho')},
                       {col_safe('giam_tru_hopdong_landau')},
                       {col_safe('giam_tru_kn2')}
                FROM giao_vien
            """
            if self.is_admin:
                cur.execute(base_sql + " ORDER BY to_bo_mon, tengv")
            else:
                cur.execute(
                    base_sql + " WHERE to_bo_mon = %s ORDER BY tengv",
                    (self.to_bm,),
                )
            danh_sach_gv = cur.fetchall()

            cur.execute(
                "SELECT DISTINCT ap_dung_tu_tuan FROM thoi_khoa_bieu ORDER BY"
                " ap_dung_tu_tuan ASC"
            )
            cac_moc_tuan = [r[0] for r in cur.fetchall() if r[0] is not None]

            cur.execute("""
                SELECT magv, ap_dung_tu_tuan, COUNT(*) 
                FROM thoi_khoa_bieu 
                WHERE UPPER(TRIM(mon)) NOT IN ('SHDC', 'SHL', 'SINH HOẠT LỚP', 'CHÀO CỜ', 'SINH HOẠT DƯỚI CỜ')
                GROUP BY magv, ap_dung_tu_tuan
            """)
            tkb_map = {}
            for mgv, tuan_ad, cnt in cur.fetchall():
                tkb_map[(mgv, tuan_ad)] = cnt

            cur.execute(
                """
                SELECT magv, loai, COUNT(*) 
                FROM bien_dong_lich_day 
                WHERE ngay BETWEEN %s AND %s AND trang_thai != 'DA_HUY'
                GROUP BY magv, loai
            """,
                (ngay_bat_dau_dot, ngay_ket_thuc_dot),
            )
            raw_bd = cur.fetchall()

            cur.execute(
                "SELECT magv, COALESCE(SUM(bdhsg_quy_doi), 0) FROM"
                " kg_hoc_sinh_gioi GROUP BY magv"
            )
            hsg_map = dict(cur.fetchall())

            cur.close()
            conn.close()

            nghi_map = {}
            day_thay_map = {}
            day_bu_map = {}

            for mgv, loai, cnt in raw_bd:
                loai_str = str(loai).strip()
                if loai_str.startswith("Nghỉ"):
                    nghi_map[mgv] = nghi_map.get(mgv, 0) + cnt
                elif loai_str == "Dạy thay":
                    day_thay_map[mgv] = day_thay_map.get(mgv, 0) + cnt
                elif loai_str == "Dạy bù":
                    day_bu_map[mgv] = day_bu_map.get(mgv, 0) + cnt

            def lay_moc_tkb_hieu_luc(w):
                if not cac_moc_tuan:
                    return 1
                phu_hop = [m for m in cac_moc_tuan if m <= w]
                return max(phu_hop) if phu_hop else min(cac_moc_tuan)

            for g in danh_sach_gv:
                (
                    mgv,
                    tgv,
                    to_bm,
                    raw_dm,
                    raw_tiet_gt,
                    raw_gt_con_nho,
                    raw_gt_hd_landau,
                    raw_gt_kn2,
                ) = g

                dm_tuan = to_float(raw_dm, 17.0)
                dm_dot = dm_tuan * so_tuan

                tiet_tkb_dot = 0
                for w in range(tu_tuan, den_tuan + 1):
                    moc_hieu_luc = lay_moc_tkb_hieu_luc(w)
                    tiet_tkb_dot += tkb_map.get((mgv, moc_hieu_luc), 0)

                so_tiet_nghi = nghi_map.get(mgv, 0)
                tiet_tbg = max(0, tiet_tkb_dot - so_tiet_nghi)
                str_tbg_tkb = (
                    f"{tiet_tbg}/{tiet_tkb_dot}"
                    if so_tiet_nghi > 0
                    else f"{tiet_tbg}"
                )

                hsg_qd = float(hsg_map.get(mgv, 0.0))
                day_thay = float(day_thay_map.get(mgv, 0))
                day_bu = float(day_bu_map.get(mgv, 0))
                tiet_bien_dong = hsg_qd + day_thay + day_bu

                giam_tru_1_tuan = (
                    to_float(raw_tiet_gt)
                    + to_float(raw_gt_con_nho)
                    + to_float(raw_gt_hd_landau)
                    + to_float(raw_gt_kn2)
                )
                tiet_giam_tru_tong = giam_tru_1_tuan * so_tuan

                tong_so_tiet_dot = (
                    float(tiet_tbg)
                    + float(tiet_bien_dong)
                    + float(tiet_giam_tru_tong)
                )
                chenh_lech = tong_so_tiet_dot - float(dm_dot)

                if chenh_lech == 0:
                    ket_luan = "Đủ tiết đợt này"
                    str_cl = "0"
                    tag = "du"
                elif chenh_lech < 0:
                    ket_luan = f"Thiếu {fmt_num(abs(chenh_lech))} tiết"
                    str_cl = f"-{fmt_num(abs(chenh_lech))}"
                    tag = "thieu"
                else:
                    ket_luan = f"Thừa {fmt_num(chenh_lech)} tiết"
                    str_cl = f"+{fmt_num(chenh_lech)}"
                    tag = "thua"

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        mgv,
                        tgv,
                        to_bm,
                        fmt_num(dm_dot),
                        tiet_tkb_dot,
                        str_tbg_tkb,
                        fmt_num(tiet_bien_dong),
                        fmt_num(tiet_giam_tru_tong),
                        fmt_num(tong_so_tiet_dot),
                        str_cl,
                        ket_luan,
                    ),
                    tags=(tag,),
                )

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải thống kê: {e}")

    def xem_tkb_gv(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn 1 giáo viên trên bảng!"
            )
            return
        item = self.tree.item(sel[0], "values")
        magv = item[0]
        dummy_session = {
            "magv": magv,
            "tengv": item[1],
            "to_bo_mon": item[2],
            "role": "GV",
        }
        from ui_xem_tkb import XemTKBWindow

        open_single_window(f"WIN_TKB_{magv}", XemTKBWindow, dummy_session)

    def xem_sbg_gv(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn 1 giáo viên trên bảng!"
            )
            return
        item = self.tree.item(sel[0], "values")
        magv = item[0]
        dummy_session = {
            "magv": magv,
            "tengv": item[1],
            "to_bo_mon": item[2],
            "role": "GV",
        }
        from ui_so_bao_giang_ca_nhan import SoBaoGiangCaNhanWindow

        open_single_window(
            f"WIN_SBG_{magv}", SoBaoGiangCaNhanWindow, dummy_session
        )

    def xem_ke_gio_1c(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn 1 giáo viên trên bảng để soi kê giờ!"
            )
            return
        item = self.tree.item(sel[0], "values")
        magv = item[0]
        dummy_session = {
            "magv": magv,
            "tengv": item[1],
            "to_bo_mon": item[2],
            "role": "GV",
        }

        # 👉 CHỐNG MỞ TRÙNG 100%: DÙNG KEY f"WIN_PKG_{magv}"
        from ui_pkg import PkgWindow

        open_single_window(f"WIN_PKG_{magv}", PkgWindow, dummy_session)