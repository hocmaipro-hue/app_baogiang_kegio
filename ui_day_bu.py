# ui_day_bu.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime, date
import re
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DayBuWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')

        self.window = tk.Toplevel()
        self.window.title(f"Đăng Ký Dạy Bù - GV: {self.tengv}")
        self.window.geometry("1080x640")

        self.ppct_mon_khoi_map = {}

        # FORM ĐĂNG KÝ
        frm = tk.LabelFrame(self.window, text=" Đăng ký Lịch Dạy Bù (Kiểm tra chống trùng đa tầng) ", 
                            padx=12, pady=10, font=("Arial", 9, "bold"), fg="#1E8449")
        frm.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm, text="Ngày dạy bù:").grid(row=0, column=0, sticky="w", pady=4)
        self.txt_ngay = tk.Entry(frm, width=14)
        self.txt_ngay.grid(row=0, column=1, pady=4, sticky="w")

        tk.Label(frm, text="Buổi:").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.cbo_buoi = ttk.Combobox(frm, state="readonly", width=10, values=["Sáng", "Chiều"])
        self.cbo_buoi.current(1) # Mặc định thường dạy bù vào buổi chiều
        self.cbo_buoi.grid(row=0, column=3, pady=4, sticky="w")

        tk.Label(frm, text="Tiết dạy:").grid(row=0, column=4, sticky="w", padx=(10, 0), pady=4)
        self.spn_tiet = ttk.Spinbox(frm, from_=1, to=5, width=8)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=0, column=5, pady=4, sticky="w")

        tk.Label(frm, text="Lớp dạy bù:").grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_lop = ttk.Combobox(frm, state="readonly", width=14)
        self.cbo_lop.grid(row=1, column=1, pady=4, sticky="w")
        self.cbo_lop.bind("<<ComboboxSelected>>", self.on_select_lop)

        tk.Label(frm, text="Phân môn:").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)
        self.cbo_pm = ttk.Combobox(frm, state="readonly", width=14, font=("Arial", 9, "bold"))
        self.cbo_pm.grid(row=1, column=3, pady=4, sticky="w")

        tk.Label(frm, text="Lý do / Căn cứ:").grid(row=1, column=4, sticky="w", padx=(10, 0), pady=4)
        self.txt_lydo = tk.Entry(frm, width=22)
        self.txt_lydo.grid(row=1, column=5, pady=4, sticky="w")

        tk.Button(frm, text="➕ GỬI DẠY BÙ", bg="#27AE60", fg="white", font=("Arial", 9, "bold"),
                  padx=12, relief=tk.RAISED, cursor="hand2", command=self.gui_day_bu).grid(row=2, column=5, padx=5, pady=6, sticky="e")

        self.lbl_hint = tk.Label(frm, text="* Hệ thống tự động kiểm tra: Chống trùng lịch bản thân, Lịch chính khóa của Lớp và Giáo viên khác đăng ký trước.", 
                                 font=("Arial", 8, "italic"), fg="#7F8C8D")
        self.lbl_hint.grid(row=2, column=0, columnspan=5, sticky="w", pady=(3, 0))

        # BẢNG LỊCH SỬ DẠY BÙ
        tbl_frm = tk.LabelFrame(self.window, text=" Danh sách các tiết đã đăng ký Dạy Bù ", padx=10, pady=5)
        tbl_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "ngay", "buoi", "tiet", "lop", "pm", "ly_do")
        self.tree = ttk.Treeview(tbl_frm, columns=cols, show="headings", height=12)
        for c, t, w, a in [("id","ID",40,"center"), ("ngay","Ngày",90,"center"),
                           ("buoi","Buổi",60,"center"), ("tiet","Tiết",50,"center"), ("lop","Lớp",70,"center"),
                           ("pm","Phân môn",120,"center"), ("ly_do","Lý do chi tiết",350,"w")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor=a)

        sb = ttk.Scrollbar(tbl_frm, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bot = tk.Frame(self.window)
        bot.pack(pady=6)
        tk.Button(bot, text="❌ Hủy tiết dạy bù đang chọn", bg="#fadbd8", command=self.huy_day_bu).pack(side=tk.LEFT, padx=5)
        tk.Button(bot, text="🔄 Tải lại danh sách", command=self.load_data).pack(side=tk.LEFT, padx=5)

        self.load_ppct_theo_khoi()
        self.load_lop_ban_than()
        self.load_data()

    def get_nam_hoc(self):
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'")
            r = cur.fetchone(); cur.close(); conn.close()
            if r: return datetime.strptime(r[0].strip(), "%Y-%m-%d").year
        except Exception: pass
        return 2026

    def chuan_hoa_ngay(self, s):
        s = s.strip(); nam = self.get_nam_hoc()
        m1 = re.match(r'^(\d{1,2})[/-](\d{1,2})$', s)
        if m1: return date(nam, int(m1.group(2)), int(m1.group(1)))
        m2 = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', s)
        if m2: return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
        return None

    def trich_khoi(self, ten_lop):
        m = re.search(r'\d+', str(ten_lop))
        return int(m.group()) if m else 10

    def load_ppct_theo_khoi(self):
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
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

    def load_lop_ban_than(self):
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
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

    def on_select_lop(self, event=None):
        lop = self.cbo_lop.get().strip()
        if not lop: return
        khoi = self.trich_khoi(lop)
        ds_pm = self.ppct_mon_khoi_map.get(khoi, [])
        if ds_pm:
            self.cbo_pm['values'] = ds_pm
            self.cbo_pm.set(ds_pm[0])

    def gui_day_bu(self):
        d = self.chuan_hoa_ngay(self.txt_ngay.get())
        if not d:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Ngày dạy bù hợp lệ (VD: 15/09 hoặc 15/09/2026)!")
            return

        buoi = self.cbo_buoi.get()
        try:
            tiet = int(self.spn_tiet.get())
        except ValueError:
            messagebox.showwarning("Lỗi", "Tiết dạy phải là số nguyên!")
            return

        lop = self.cbo_lop.get().strip()
        pm = self.cbo_pm.get().strip()
        lydo = self.txt_lydo.get().strip()

        if not lop or not pm:
            messagebox.showwarning("Lỗi", "Vui lòng chọn Lớp và Phân môn dạy bù!")
            return

        thu_so = d.weekday() + 2
        ngay_f = d.strftime("%d/%m/%Y")

        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()

            # -----------------------------------------------------------------
            # TẦNG 1: KIỂM TRA BẢN THÂN CÓ BẬN DẠY CHÍNH KHÓA KHÔNG
            # -----------------------------------------------------------------
            cur.execute("""
                SELECT lop, mon FROM thoi_khoa_bieu 
                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
            """, (self.magv, str(thu_so), thu_so, buoi, tiet))
            tkb_me = cur.fetchone()
            if tkb_me:
                messagebox.showerror("Trùng lịch của bạn", 
                    f"⛔ BẠN ĐANG CÓ TIẾT DẠY!\n\n"
                    f"Thứ {thu_so} Tiết {tiet} ({buoi}) bạn đang có tiết chính khóa ở lớp [{tkb_me[0]}] (Môn: {tkb_me[1]})!\n"
                    f"Không thể dạy bù vào tiết này!")
                cur.close(); conn.close(); return

            # -----------------------------------------------------------------
            # TẦNG 2: KIỂM TRA BẢN THÂN ĐÃ ĐĂNG KÝ TIẾT NÀY CHO LỚP KHÁC CHƯA
            # -----------------------------------------------------------------
            cur.execute("""
                SELECT loai, lop FROM bien_dong_lich_day 
                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND trang_thai != 'DA_HUY'
            """, (self.magv, d, buoi, tiet))
            bd_me = cur.fetchone()
            if bd_me:
                messagebox.showerror("Trùng lịch của bạn", 
                    f"⛔ BẠN ĐÃ CÓ LỊCH DẠY RỒI!\n\n"
                    f"Vào Tiết {tiet} ({buoi}) ngày {ngay_f}, bạn ĐÃ ĐĂNG KÝ [{bd_me[0]}] cho lớp [{bd_me[1]}]!\n"
                    f"Một giáo viên không thể phân thân dạy 2 lớp cùng một giờ!")
                cur.close(); conn.close(); return

            # -----------------------------------------------------------------
            # TẦNG 3: KIỂM TRA LỚP CÓ ĐANG HỌC TIẾT CHÍNH KHÓA THEO TKB KHÔNG
            # -----------------------------------------------------------------
            cur.execute("""
                SELECT t.mon, COALESCE(g.tengv, t.magv)
                FROM thoi_khoa_bieu t
                LEFT JOIN giao_vien g ON t.magv = g.magv
                WHERE UPPER(TRIM(t.lop)) = %s AND (t.thu = %s OR t.thu = %s) AND t.buoi = %s AND t.tiet = %s
                  AND t.mon IS NOT NULL AND UPPER(TRIM(t.mon)) NOT IN ('', 'EMPTY', 'SHDC', 'SHL')
            """, (lop.upper(), str(thu_so), thu_so, buoi, tiet))
            lop_ban = cur.fetchone()
            if lop_ban:
                messagebox.showerror("Lớp đang có tiết học", 
                    f"⛔ LỚP [{lop}] KHÔNG RẢNH TIẾT NÀY!\n\n"
                    f"Vào Thứ {thu_so} Tiết {tiet} ({buoi}), lớp [{lop}] đang có giờ học chính khóa:\n"
                    f"- Môn học: [{lop_ban[0]}]\n"
                    f"- Giáo viên dạy: [{lop_ban[1]}]\n\n"
                    f"👉 Dạy bù bắt buộc phải xếp vào TIẾT TRỐNG của lớp học sinh!")
                cur.close(); conn.close(); return

            # -----------------------------------------------------------------
            # TẦNG 4 (MỚI NHẤT): CHỐNG TRANH LỚP - ĐÃ CÓ GV KHÁC XÍ CHỖ DẠY BÙ CHƯA?
            # -----------------------------------------------------------------
            cur.execute("""
                SELECT b.magv, COALESCE(g.tengv, b.magv), b.loai, COALESCE(b.phan_mon, '')
                FROM bien_dong_lich_day b
                LEFT JOIN giao_vien g ON b.magv = g.magv
                WHERE UPPER(TRIM(b.lop)) = %s 
                  AND b.ngay = %s AND b.buoi = %s AND b.tiet_tkb = %s 
                  AND b.trang_thai != 'DA_HUY' 
                  AND b.loai IN ('Dạy bù', 'Dạy thay', 'Bồi dưỡng HSG')
            """, (lop.upper(), d, buoi, tiet))
            gv_da_dang_ky = cur.fetchone()

            if gv_da_dang_ky:
                ten_gv_trung = gv_da_dang_ky[1]
                loai_trung = gv_da_dang_ky[2]
                pm_trung = gv_da_dang_ky[3]
                messagebox.showerror("Trùng lịch dạy bù của Lớp!", 
                    f"⛔ LỚP [{lop}] ĐÃ CÓ GIÁO VIÊN KHÁC ĐĂNG KÝ TRƯỚC!\n\n"
                    f"- Vào Tiết {tiet} ({buoi}) ngày {ngay_f}:\n"
                    f"  + Thầy/Cô: [{ten_gv_trung}]\n"
                    f"  + Đã đăng ký: [{loai_trung}] ({pm_trung})\n\n"
                    f"👉 Hai giáo viên không thể cùng vào dạy một lớp ở cùng một thời điểm. Vui lòng chọn tiết khác!")
                cur.close(); conn.close(); return

            # LƯU VÀO CSDL
            cur.execute("""
                INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                VALUES (%s, 'Dạy bù', %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
            """, (self.magv, d, buoi, tiet, lop, pm, lydo))
            conn.commit(); cur.close(); conn.close()

            # Tự động đồng bộ sang Sổ báo giảng
            sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d)
            messagebox.showinfo("Thành công", f"Đã đăng ký Dạy bù lớp {lop} ngày {ngay_f} thành công!")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT id, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(ly_do,'')
                FROM bien_dong_lich_day 
                WHERE magv = %s AND loai = 'Dạy bù' AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC, tiet_tkb ASC
            """, (self.magv,))
            for r in cur.fetchall():
                ngay_f = r[1].strftime("%d/%m/%Y") if hasattr(r[1], 'strftime') else str(r[1])
                self.tree.insert("", tk.END, values=(r[0], ngay_f, r[2], r[3], r[4], r[5], r[6]))
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nạp dữ liệu: {e}")

    def huy_day_bu(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0], 'values')
        rec_id = item[0]; d_huy = self.chuan_hoa_ngay(item[1])

        if messagebox.askyesno("Xác nhận", f"Hủy lịch dạy bù ngày {item[1]} Tiết {item[3]} lớp {item[4]}?"):
            try:
                conn = psycopg2.connect(DB_URI); cur = conn.cursor()
                cur.execute("DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s", (rec_id, self.magv))
                conn.commit(); cur.close(); conn.close()
                if d_huy: sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_huy)
                self.load_data()
                messagebox.showinfo("Thành công", "Đã hủy và cập nhật lại Sổ Báo Giảng!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể hủy: {e}")