# ui_bien_dong_lich_day.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime, date, timedelta
import re
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class BienDongLichDayWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')
        self.window = tk.Toplevel()
        self.window.title(f"Đăng ký Biến động Lịch dạy - {self.tengv}")
        self.window.geometry("1180x680")

        self.map_gv_toan_truong = {}
        self.ppct_mon_khoi_map = {}

        self.ensure_columns_exist()

        form_frame = tk.LabelFrame(self.window, text=f" Đăng ký biến động mới (Tổ: {self.to_bm}) ", 
                                   padx=12, pady=10, font=("Arial", 9, "bold"))
        form_frame.pack(fill=tk.X, padx=10, pady=5)

        # DÒNG 0: Loại biến động, Từ ngày, Đến ngày (nghỉ dài hạn)
        tk.Label(form_frame, text="Loại biến động:").grid(row=0, column=0, sticky="w", pady=4)
        self.cbo_loai = ttk.Combobox(form_frame, state="readonly", width=18,
                                     values=["Nghỉ theo kế hoạch", "Nghỉ theo điều động", "Nghỉ việc riêng", "Dạy bù", "Dạy thay", "Bồi dưỡng HSG"])
        self.cbo_loai.current(0)
        self.cbo_loai.grid(row=0, column=1, pady=4, sticky="w")
        self.cbo_loai.bind("<<ComboboxSelected>>", self.on_change_loai)

        tk.Label(form_frame, text="Từ Ngày:").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.txt_ngay = tk.Entry(form_frame, width=12)
        self.txt_ngay.grid(row=0, column=3, pady=4, sticky="w")
        self.txt_ngay.bind("<KeyRelease>", self.tu_dong_dien_thong_tin_tkb)

        self.lbl_den_ngay = tk.Label(form_frame, text="Đến Ngày (Nghỉ dài):", fg="#7D6608")
        self.lbl_den_ngay.grid(row=0, column=4, sticky="w", padx=(10, 0), pady=4)
        self.txt_den_ngay = tk.Entry(form_frame, width=12)
        self.txt_den_ngay.grid(row=0, column=5, pady=4, sticky="w")

        # DÒNG 1: Buổi, Tiết, GV dạy thay
        tk.Label(form_frame, text="Buổi:").grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_buoi = ttk.Combobox(form_frame, state="readonly", width=18, values=["Sáng", "Chiều"])
        self.cbo_buoi.current(0)
        self.cbo_buoi.grid(row=1, column=1, pady=4, sticky="w")
        self.cbo_buoi.bind("<<ComboboxSelected>>", self.tu_dong_dien_thong_tin_tkb)

        tk.Label(form_frame, text="Tiết TKB:").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)
        self.spn_tiet = ttk.Spinbox(form_frame, from_=1, to=5, width=10, command=self.tu_dong_dien_thong_tin_tkb)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=1, column=3, pady=4, sticky="w")
        self.spn_tiet.bind("<KeyRelease>", self.tu_dong_dien_thong_tin_tkb)

        self.lbl_gv_thay = tk.Label(form_frame, text="GV được dạy thay:")
        self.lbl_gv_thay.grid(row=1, column=4, sticky="w", padx=(10, 0), pady=4)
        self.cbo_gv_thay = ttk.Combobox(form_frame, width=18, state="disabled")
        self.cbo_gv_thay.grid(row=1, column=5, pady=4, sticky="w")
        self.cbo_gv_thay.bind("<<ComboboxSelected>>", self.on_select_gv_thay)

        # DÒNG 2: Lớp, Phân môn, Lý do
        tk.Label(form_frame, text="Lớp dạy:").grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_lop = ttk.Combobox(form_frame, width=18, state="readonly")
        self.cbo_lop.grid(row=2, column=1, pady=4, sticky="w")
        self.cbo_lop.bind("<<ComboboxSelected>>", self.on_select_lop)

        tk.Label(form_frame, text=f"Phân môn:").grid(row=2, column=2, sticky="w", padx=(10, 0), pady=4)
        self.cbo_phan_mon = ttk.Combobox(form_frame, state="readonly", width=15, font=("Arial", 9, "bold"))
        self.cbo_phan_mon.grid(row=2, column=3, pady=4, sticky="w")

        tk.Label(form_frame, text="Lý do / QĐ:").grid(row=2, column=4, sticky="w", padx=(10, 0), pady=4)
        self.txt_lydo = tk.Entry(form_frame, width=22)
        self.txt_lydo.grid(row=2, column=5, pady=4, sticky="w")

        tk.Button(form_frame, text="➕ GỬI ĐĂNG KÝ", bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  padx=12, relief=tk.RAISED, cursor="hand2",
                  command=self.gui_dang_ky).grid(row=3, column=5, padx=5, pady=6, sticky="e")

        self.lbl_tkb_hint = tk.Label(form_frame, text="", font=("Arial", 8, "italic"), fg="#7F8C8D")
        self.lbl_tkb_hint.grid(row=3, column=0, columnspan=5, sticky="w", pady=(3, 0))

        # BẢNG LỊCH SỬ
        table_frame = tk.LabelFrame(self.window, text=" Lịch sử biến động đã gửi ", padx=10, pady=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "loai", "ngay", "buoi", "tiet_tkb", "lop", "phan_mon", "gv_day_thay", "ly_do", "trang_thai")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, t, w, a in [("id","ID",35,"center"), ("loai","Loại việc",130,"center"), ("ngay","Ngày",85,"center"),
                           ("buoi","Buổi",55,"center"), ("tiet_tkb","Tiết",45,"center"), ("lop","Lớp",65,"center"),
                           ("phan_mon","Môn/PM",110,"center"), ("gv_day_thay","GV thay",120,"w"),
                           ("ly_do","Lý do",220,"w"), ("trang_thai","Trạng thái",90,"center")]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="❌ Hủy dòng đang chọn", bg="#fadbd8", command=self.huy_dang_ky).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Tải lại danh sách", command=self.load_data).pack(side=tk.LEFT, padx=5)

        self.load_danh_sach_gv_toan_truong()
        self.load_phan_mon_theo_khoi_ppct()
        self.load_danh_sach_lop_ban_than()
        self.load_data()
        self.on_change_loai(None)

    def ensure_columns_exist(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS gv_day_thay VARCHAR(100);")
            cur.execute("ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS phan_mon VARCHAR(100);")
            conn.commit()
            cur.close(); conn.close()
        except Exception: pass

    def trich_khoi(self, ten_lop):
        m = re.search(r'\d+', str(ten_lop))
        return int(m.group()) if m else 10

    def load_phan_mon_theo_khoi_ppct(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT khoi, COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE (UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%')
                  AND khoi IS NOT NULL
                ORDER BY khoi, 2 ASC
            """, (self.to_bm, self.to_bm))
            self.ppct_mon_khoi_map = {10: [], 11: [], 12: []}
            for kh, pm in cur.fetchall():
                if pm and pm not in self.ppct_mon_khoi_map.setdefault(kh, []):
                    self.ppct_mon_khoi_map[kh].append(pm)
            cur.close(); conn.close()
        except Exception: pass

    def on_select_lop(self, event=None):
        if self.cbo_loai.get().startswith("Nghỉ"): return
        lop = self.cbo_lop.get().strip()
        if not lop: return
        khoi = self.trich_khoi(lop)
        ds_pm = self.ppct_mon_khoi_map.get(khoi, [])
        if ds_pm:
            self.cbo_phan_mon['values'] = ds_pm
            self.cbo_phan_mon.set(ds_pm[0])

    def load_danh_sach_lop_ban_than(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                ORDER BY lop
            """, (self.magv,))
            lops = [r[0].strip() for r in cur.fetchall()]
            cur.close(); conn.close()
            self.cbo_lop['values'] = lops
            if lops: 
                self.cbo_lop.current(0)
                self.on_select_lop()
        except Exception: pass

    def load_danh_sach_gv_toan_truong(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT magv, tengv FROM giao_vien WHERE magv != %s ORDER BY tengv", (self.magv,))
            self.map_gv_toan_truong = {f"{tgv} ({mgv})": mgv for mgv, tgv in cur.fetchall()}
            cur.close(); conn.close()
            self.cbo_gv_thay['values'] = list(self.map_gv_toan_truong.keys())
        except Exception: pass

    def on_select_gv_thay(self, event=None):
        target_magv = self.map_gv_toan_truong.get(self.cbo_gv_thay.get().strip(), "")
        if not target_magv: return
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                ORDER BY lop
            """, (target_magv,))
            lops = [r[0].strip() for r in cur.fetchall()]
            cur.close(); conn.close()
            self.cbo_lop['values'] = lops
            if lops: 
                self.cbo_lop.current(0)
                self.on_select_lop()
            else: self.cbo_lop.set("")
        except Exception: pass

    def on_change_loai(self, event=None):
        loai = self.cbo_loai.get()
        if loai.startswith("Nghỉ"):
            self.cbo_gv_thay.config(state="disabled")
            self.txt_den_ngay.config(state="normal")
            self.tu_dong_dien_thong_tin_tkb()
        elif loai == "Dạy thay":
            self.txt_den_ngay.config(state="disabled")
            self.cbo_gv_thay.config(state="readonly")
            self.cbo_lop.config(state="readonly")
            self.cbo_phan_mon.config(state="readonly")
            self.on_select_gv_thay()
        elif loai == "Bồi dưỡng HSG":
            self.txt_den_ngay.config(state="disabled")
            self.cbo_gv_thay.config(state="disabled")
            self.cbo_lop.config(state="normal"); self.cbo_lop.set("")
            self.cbo_phan_mon.config(state="normal")
            self.cbo_phan_mon['values'] = ["BDHSG"]; self.cbo_phan_mon.set("BDHSG")
        else: # Dạy bù
            self.txt_den_ngay.config(state="disabled")
            self.cbo_gv_thay.config(state="disabled")
            self.cbo_lop.config(state="readonly")
            self.cbo_phan_mon.config(state="readonly")
            self.load_danh_sach_lop_ban_than()

    def get_nam_hoc(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'")
            r = cur.fetchone()
            cur.close(); conn.close()
            if r: return datetime.strptime(r[0].strip(), "%Y-%m-%d").year
        except Exception: pass
        return 2026

    def chuan_hoa_ngay(self, text_input):
        s = text_input.strip()
        nam = self.get_nam_hoc()
        m1 = re.match(r'^(\d{1,2})[/-](\d{1,2})$', s)
        if m1: return date(nam, int(m1.group(2)), int(m1.group(1)))
        m2 = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', s)
        if m2: return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
        m3 = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', s)
        if m3: return date(int(m3.group(1)), int(m3.group(2)), int(m3.group(3)))
        return None

    def tu_dong_dien_thong_tin_tkb(self, event=None):
        loai = self.cbo_loai.get()
        if not loai.startswith("Nghỉ"): return

        if self.txt_den_ngay.get().strip():
            self.lbl_tkb_hint.config(text="ℹ️ Chế độ nghỉ dài ngày: Toàn bộ tiết TKB trong khoảng ngày sẽ được đánh dấu nghỉ.", fg="#7D6608")
            return

        ngay_chuan = self.chuan_hoa_ngay(self.txt_ngay.get().strip())
        if not ngay_chuan: return
        thu_so = ngay_chuan.weekday() + 2
        buoi = self.cbo_buoi.get()
        try: tiet = int(self.spn_tiet.get())
        except ValueError: return

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT lop, mon, COALESCE(phan_mon, '') 
                FROM thoi_khoa_bieu 
                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
            """, (self.magv, str(thu_so), thu_so, buoi, tiet))
            r = cur.fetchone()
            cur.close(); conn.close()

            if r:
                lop_tkb = r[0].strip()
                pm_tkb = r[2].strip() if r[2].strip() else r[1].strip()
                self.cbo_lop.config(state="normal"); self.cbo_lop.set(lop_tkb); self.cbo_lop.config(state="disabled")
                self.cbo_phan_mon.config(state="normal"); self.cbo_phan_mon.set(pm_tkb); self.cbo_phan_mon.config(state="disabled")
                self.lbl_tkb_hint.config(text=f"✔ Khớp TKB Thứ {thu_so}: [{lop_tkb}] - [{pm_tkb}]", fg="#27ae60")
            else:
                self.cbo_lop.config(state="normal"); self.cbo_lop.set("")
                self.cbo_phan_mon.config(state="normal"); self.cbo_phan_mon.set("")
                self.lbl_tkb_hint.config(text=f"⚠️ Thứ {thu_so} Tiết {tiet} ({buoi}): KHÔNG CÓ TIẾT!", fg="#c0392b")
        except Exception: pass

    def gui_dang_ky(self):
        loai = self.cbo_loai.get()
        raw_tu_ngay = self.txt_ngay.get().strip()
        raw_den_ngay = self.txt_den_ngay.get().strip()
        buoi = self.cbo_buoi.get()
        tiet = int(self.spn_tiet.get())
        lop = self.cbo_lop.get().strip()
        phan_mon = self.cbo_phan_mon.get().strip()
        gv_thay = self.cbo_gv_thay.get().strip().split(" (")[0]
        lydo = self.txt_lydo.get().strip()

        tu_ngay = self.chuan_hoa_ngay(raw_tu_ngay)
        if not tu_ngay:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Ngày (hoặc Từ ngày) hợp lệ!")
            return

        # =========================================================================
        # 1. BÁO NGHỈ DÀI NGÀY (NGHỈ TẾT, NGHỈ HÈ...)
        # =========================================================================
        if loai.startswith("Nghỉ") and raw_den_ngay:
            den_ngay = self.chuan_hoa_ngay(raw_den_ngay)
            if not den_ngay or den_ngay < tu_ngay:
                messagebox.showwarning("Lỗi", "Đến ngày không hợp lệ hoặc nhỏ hơn Từ ngày!")
                return

            so_ngay = (den_ngay - tu_ngay).days + 1
            if not messagebox.askyesno("Xác nhận nghỉ dài ngày", 
                f"Báo [{loai}] từ {tu_ngay.strftime('%d/%m/%Y')} đến {den_ngay.strftime('%d/%m/%Y')} ({so_ngay} ngày)?\n"
                f"Hệ thống sẽ tự động quét toàn bộ TKB và cho nghỉ tất cả các tiết trong thời gian này."):
                return

            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon, COALESCE(phan_mon,'') FROM thoi_khoa_bieu WHERE magv = %s", (self.magv,))
                tkb_all = cur.fetchall()

                cur_d = tu_ngay
                count_added = 0
                while cur_d <= den_ngay:
                    thu_num = cur_d.weekday() + 2
                    for r in tkb_all:
                        t_thu = int(re.search(r'\d+', str(r[0])).group()) if re.search(r'\d+', str(r[0])) else 2
                        if t_thu == thu_num and r[4].strip() not in ['SHDC', 'SHL']:
                            t_buoi = r[1]; t_tiet = r[2]; t_lop = r[3]
                            t_pm = r[5].strip() if r[5].strip() else r[4].strip()
                            
                            cur.execute("""
                                SELECT id FROM bien_dong_lich_day 
                                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                            """, (self.magv, cur_d, t_buoi, t_tiet))
                            if not cur.fetchone():
                                cur.execute("""
                                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                """, (self.magv, loai, cur_d, t_buoi, t_tiet, t_lop, t_pm, lydo or "Nghỉ dài hạn/Nghỉ Tết"))
                                count_added += 1
                    cur_d += timedelta(days=1)

                conn.commit()
                cur.close(); conn.close()

                sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, tu_ngay)
                if den_ngay != tu_ngay:
                    sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, den_ngay)

                messagebox.showinfo("Thành công", f"Đã tự động tạo {count_added} tiết nghỉ trong khoảng thời gian trên!")
                self.load_data()
                return
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu nghỉ dài hạn: {e}")
                return

        # =========================================================================
        # 2. BÁO NGHỈ ĐƠN LẺ HOẶC DẠY BÙ / DẠY THAY
        # =========================================================================
        thu_so = tu_ngay.weekday() + 2
        ngay_f = tu_ngay.strftime("%d/%m/%Y")

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            # A. BÁO NGHỈ ĐƠN LẺ
            if loai.startswith('Nghỉ'):
                cur.execute("""
                    SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                    WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                """, (self.magv, str(thu_so), thu_so, buoi, tiet))
                tkb_slot = cur.fetchone()
                if not tkb_slot:
                    messagebox.showerror("Sai lịch", f"Thứ {thu_so} Tiết {tiet} ({buoi}) không có trên TKB!")
                    cur.close(); conn.close(); return

            # B. DẠY BÙ, DẠY THAY, BỒI DƯỠNG HSG
            elif loai in ['Dạy bù', 'Dạy thay', 'Bồi dưỡng HSG']:
                if loai in ['Dạy bù', 'Dạy thay'] and not lop:
                    messagebox.showwarning("Thiếu dữ liệu", f"Vui lòng chọn Lớp {loai}!")
                    cur.close(); conn.close(); return
                
                # Kiểm tra chống lệch khối
                if loai in ['Dạy bù', 'Dạy thay']:
                    khoi = self.trich_khoi(lop)
                    ds_pm_khoi = self.ppct_mon_khoi_map.get(khoi, [])
                    if ds_pm_khoi and phan_mon not in ds_pm_khoi:
                        messagebox.showerror("Sai Khối", f"Lớp {lop} (Khối {khoi}) không có phân môn [{phan_mon}]!")
                        cur.close(); conn.close(); return

                # Kiểm tra trùng lịch bản thân GV
                cur.execute("""
                    SELECT lop, mon FROM thoi_khoa_bieu 
                    WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
                """, (self.magv, str(thu_so), thu_so, buoi, tiet))
                tkb_ban_than = cur.fetchone()
                if tkb_ban_than:
                    messagebox.showerror("Trùng lịch của bạn", 
                        f"⛔ TRÙNG GIỜ CỦA BẠN!\n\n"
                        f"Vào Thứ {thu_so} Tiết {tiet} ({buoi}), thầy/cô đang có giờ dạy chính khóa ở lớp [{tkb_ban_than[0]}] (Môn: {tkb_ban_than[1]})!\n"
                        f"Không thể đi {loai} vào giờ này!")
                    cur.close(); conn.close(); return

                # KIỂM TRA TRÙNG LỊCH CHÍNH KHÓA CỦA LỚP HỌC KHI DẠY BÙ
                if loai == 'Dạy bù':
                    cur.execute("""
                        SELECT t.mon, COALESCE(g.tengv, t.magv)
                        FROM thoi_khoa_bieu t
                        LEFT JOIN giao_vien g ON t.magv = g.magv
                        WHERE UPPER(TRIM(t.lop)) = %s 
                          AND (t.thu = %s OR t.thu = %s) 
                          AND t.buoi = %s 
                          AND t.tiet = %s
                          AND t.mon IS NOT NULL 
                          AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
                    """, (lop.upper(), str(thu_so), thu_so, buoi, tiet))
                    lich_lop = cur.fetchone()

                    if lich_lop:
                        mon_trung = lich_lop[0].strip()
                        gv_trung = lich_lop[1].strip()
                        messagebox.showerror("Lớp đang có tiết học!", 
                            f"⛔ KHÔNG THỂ DẠY BÙ VÀO TIẾT NÀY!\n\n"
                            f"- Lớp [{lop}] vào Thứ {thu_so} Tiết {tiet} ({buoi}) ĐANG CÓ TIẾT CHÍNH KHÓA:\n"
                            f"  + Môn: [{mon_trung}]\n"
                            f"  + Giáo viên: [{gv_trung}]\n\n"
                            f"👉 Dạy bù chỉ được xếp vào TIẾT TRỐNG của lớp, không thể dạy chen vào giờ của môn học khác!")
                        cur.close(); conn.close(); return

                if loai == 'Dạy thay' and not gv_thay:
                    messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn GV được dạy thay!")
                    cur.close(); conn.close(); return

            cur.execute("""
                INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
            """, (self.magv, loai, tu_ngay, buoi, tiet, lop, phan_mon, gv_thay, lydo))
            conn.commit()
            cur.close(); conn.close()

            sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, tu_ngay)
            messagebox.showinfo("Thành công", f"Đã lưu '{loai}' ngày {ngay_f} và TỰ ĐỘNG CẬP NHẬT SỔ BÁO GIẢNG!")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop, ''), COALESCE(phan_mon, ''), COALESCE(gv_day_thay, ''), COALESCE(ly_do, ''), trang_thai
                FROM bien_dong_lich_day WHERE magv = %s ORDER BY ngay DESC, tiet_tkb ASC
            """, (self.magv,))
            for r in cur.fetchall():
                ngay_f = r[2].strftime("%d/%m/%Y") if hasattr(r[2], 'strftime') else str(r[2])
                self.tree.insert("", tk.END, values=(r[0], r[1], ngay_f, r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải dữ liệu: {e}")

    def huy_dang_ky(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0], 'values')
        rec_id = item[0]
        ngay_huy = self.chuan_hoa_ngay(item[2])

        if messagebox.askyesno("Xác nhận", "Hủy đăng ký này? Sổ báo giảng tuần này sẽ được cập nhật lại tự động."):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s", (rec_id, self.magv))
                conn.commit()
                cur.close(); conn.close()
                if ngay_huy:
                    sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, ngay_huy)
                self.load_data()
                messagebox.showinfo("Đã hủy", "Đã hủy thành công và đồng bộ lại Sổ Báo Giảng!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể hủy: {e}")