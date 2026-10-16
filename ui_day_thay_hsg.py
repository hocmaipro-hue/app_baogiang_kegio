# ui_day_thay_hsg.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime, date
import re
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DayThayHSGWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')

        self.window = tk.Toplevel()
        self.window.title(f"Dạy Thay & Bồi Dưỡng HSG - GV: {self.tengv}")
        self.window.geometry("1080x640")

        self.map_gv_toan_truong = {}

        # FORM ĐĂNG KÝ
        frm = tk.LabelFrame(self.window, text=" Đăng ký Dạy Thay / Bồi Dưỡng HSG ", 
                            padx=12, pady=10, font=("Arial", 9, "bold"), fg="#B7950B")
        frm.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm, text="Công việc:").grid(row=0, column=0, sticky="w", pady=4)
        self.cbo_loai = ttk.Combobox(frm, state="readonly", width=18, values=["Dạy thay", "Bồi dưỡng HSG"])
        self.cbo_loai.current(0)
        self.cbo_loai.grid(row=0, column=1, pady=4, sticky="w")
        self.cbo_loai.bind("<<ComboboxSelected>>", self.on_change_loai)

        tk.Label(frm, text="Ngày dạy:").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.txt_ngay = tk.Entry(frm, width=12)
        self.txt_ngay.grid(row=0, column=3, pady=4, sticky="w")

        tk.Label(frm, text="Buổi:").grid(row=0, column=4, sticky="w", padx=(10, 0), pady=4)
        self.cbo_buoi = ttk.Combobox(frm, state="readonly", width=10, values=["Sáng", "Chiều"])
        self.cbo_buoi.current(0)
        self.cbo_buoi.grid(row=0, column=5, pady=4, sticky="w")

        tk.Label(frm, text="Tiết dạy:").grid(row=1, column=0, sticky="w", pady=4)
        self.spn_tiet = ttk.Spinbox(frm, from_=1, to=5, width=8)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=1, column=1, pady=4, sticky="w")

        self.lbl_gv_thay = tk.Label(frm, text="GV được dạy thay:", fg="blue", font=("Arial", 9, "bold"))
        self.lbl_gv_thay.grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)
        self.cbo_gv_thay = ttk.Combobox(frm, width=20, state="readonly")
        self.cbo_gv_thay.grid(row=1, column=3, pady=4, sticky="w")
        self.cbo_gv_thay.bind("<<ComboboxSelected>>", self.on_select_gv_thay)

        tk.Label(frm, text="Lớp dạy / Đội tuyển:").grid(row=1, column=4, sticky="w", padx=(10, 0), pady=4)
        self.cbo_lop = ttk.Combobox(frm, width=14, state="readonly")
        self.cbo_lop.grid(row=1, column=5, pady=4, sticky="w")

        tk.Label(frm, text="Phân môn:").grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_pm = ttk.Combobox(frm, state="readonly", width=18)
        self.cbo_pm.grid(row=2, column=1, pady=4, sticky="w")

        tk.Label(frm, text="Tên bài / Lý do:").grid(row=2, column=2, sticky="w", padx=(10, 0), pady=4)
        self.txt_lydo = tk.Entry(frm, width=22)
        self.txt_lydo.grid(row=2, column=3, pady=4, sticky="w")

        tk.Button(frm, text="➕ GỬI ĐĂNG KÝ", bg="#D4AC0D", fg="white", font=("Arial", 9, "bold"),
                  padx=12, relief=tk.RAISED, cursor="hand2", command=self.gui_dang_ky).grid(row=2, column=5, padx=5, pady=6, sticky="e")

        # BẢNG LỊCH SỬ
        tbl_frm = tk.LabelFrame(self.window, text=" Danh sách tiết Dạy Thay & BDHSG ", padx=10, pady=5)
        tbl_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "loai", "ngay", "buoi", "tiet", "lop", "pm", "gv_thay", "ly_do")
        self.tree = ttk.Treeview(tbl_frm, columns=cols, show="headings", height=12)
        for c, t, w, a in [("id","ID",40,"center"), ("loai","Loại việc",100,"center"), ("ngay","Ngày",90,"center"),
                           ("buoi","Buổi",60,"center"), ("tiet","Tiết",50,"center"), ("lop","Lớp",70,"center"),
                           ("pm","Phân môn",100,"center"), ("gv_thay","GV được thay",140,"w"), ("ly_do","Tên bài / Lý do",280,"w")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor=a)

        sb = ttk.Scrollbar(tbl_frm, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bot = tk.Frame(self.window)
        bot.pack(pady=6)
        tk.Button(bot, text="❌ Hủy dòng đang chọn", bg="#fadbd8", command=self.huy_dang_ky).pack(side=tk.LEFT, padx=5)
        tk.Button(bot, text="🔄 Tải lại danh sách", command=self.load_data).pack(side=tk.LEFT, padx=5)

        self.load_gv_toan_truong()
        self.load_phan_mon_to()
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

    def load_gv_toan_truong(self):
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("SELECT magv, tengv FROM giao_vien WHERE magv != %s ORDER BY tengv", (self.magv,))
            self.map_gv_toan_truong = {f"{tgv} ({mgv})": mgv for mgv, tgv in cur.fetchall()}
            cur.close(); conn.close()
            self.cbo_gv_thay['values'] = list(self.map_gv_toan_truong.keys())
            if self.cbo_gv_thay['values']:
                self.cbo_gv_thay.current(0)
                self.on_select_gv_thay()
        except Exception: pass

    def load_phan_mon_to(self):
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%'
                ORDER BY 1 ASC;
            """, (self.to_bm, self.to_bm))
            pms = [r[0].strip() for r in cur.fetchall() if r[0]]
            cur.close(); conn.close()
            self.cbo_pm['values'] = pms
            if pms: self.cbo_pm.current(0)
        except Exception: pass

    def on_select_gv_thay(self, event=None):
        target_magv = self.map_gv_toan_truong.get(self.cbo_gv_thay.get().strip(), "")
        if not target_magv: return
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT lop FROM thoi_khoa_bieu 
                WHERE magv = %s AND lop IS NOT NULL AND lop != '' AND UPPER(TRIM(lop)) NOT IN ('SHDC', 'SHL') 
                ORDER BY lop
            """, (target_magv,))
            lops = [r[0].strip() for r in cur.fetchall()]
            cur.close(); conn.close()
            self.cbo_lop['values'] = lops
            if lops: self.cbo_lop.current(0)
            else: self.cbo_lop.set("")
        except Exception: pass

    def on_change_loai(self, event=None):
        loai = self.cbo_loai.get()
        if loai == "Dạy thay":
            self.cbo_gv_thay.config(state="readonly")
            self.lbl_gv_thay.config(fg="blue", font=("Arial", 9, "bold"))
            self.cbo_lop.config(state="readonly")
            self.cbo_pm.config(state="readonly")
            self.load_phan_mon_to()
            self.on_select_gv_thay()
        else: # Bồi dưỡng HSG
            self.cbo_gv_thay.config(state="disabled")
            self.lbl_gv_thay.config(fg="black", font=("Arial", 9))
            self.cbo_lop.config(state="normal"); self.cbo_lop.set("")
            self.cbo_pm.config(state="normal")
            self.cbo_pm['values'] = ["BDHSG"]; self.cbo_pm.set("BDHSG")

    def gui_dang_ky(self):
        loai = self.cbo_loai.get()
        d = self.chuan_hoa_ngay(self.txt_ngay.get())
        if not d:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Ngày hợp lệ (VD: 15/09)!")
            return

        buoi = self.cbo_buoi.get()
        tiet = int(self.spn_tiet.get())
        lop = self.cbo_lop.get().strip()
        pm = self.cbo_pm.get().strip()
        gv_thay = self.cbo_gv_thay.get().strip().split(" (")[0] if loai == "Dạy thay" else ""
        lydo = self.txt_lydo.get().strip()

        if loai == "Dạy thay" and (not gv_thay or not lop):
            messagebox.showwarning("Lỗi", "Vui lòng chọn GV được thay và Lớp dạy!")
            return

        thu_so = d.weekday() + 2
        ngay_f = d.strftime("%d/%m/%Y")

        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()

            # 1. Chống trùng lịch TKB chính khóa của bạn
            cur.execute("""
                SELECT lop, mon FROM thoi_khoa_bieu 
                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
            """, (self.magv, str(thu_so), thu_so, buoi, tiet))
            tkb_me = cur.fetchone()
            if tkb_me:
                messagebox.showerror("Trùng lịch", f"Thứ {thu_so} Tiết {tiet} ({buoi}) bạn đang dạy lớp [{tkb_me[0]}]!")
                cur.close(); conn.close(); return

            # 2. Chống trùng lịch biến động khác của bản thân
            cur.execute("""
                SELECT loai, lop FROM bien_dong_lich_day 
                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND trang_thai != 'DA_HUY'
            """, (self.magv, d, buoi, tiet))
            bd_me = cur.fetchone()
            if bd_me:
                messagebox.showerror("Trùng lịch", f"Tiết {tiet} ({buoi}) ngày {ngay_f} bạn đã có lịch [{bd_me[0]}] lớp [{bd_me[1]}] rồi!")
                cur.close(); conn.close(); return

            # LƯU VÀO CSDL
            cur.execute("""
                INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CHO_DUYET')
            """, (self.magv, loai, d, buoi, tiet, lop, pm, gv_thay, lydo))
            conn.commit(); cur.close(); conn.close()

            sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d)
            messagebox.showinfo("Thành công", f"Đã gửi đăng ký [{loai}] ngày {ngay_f} thành công!")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(gv_day_thay,''), COALESCE(ly_do,'')
                FROM bien_dong_lich_day 
                WHERE magv = %s AND loai IN ('Dạy thay', 'Bồi dưỡng HSG') AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC, tiet_tkb ASC
            """, (self.magv,))
            for r in cur.fetchall():
                ngay_f = r[2].strftime("%d/%m/%Y") if hasattr(r[2], 'strftime') else str(r[2])
                self.tree.insert("", tk.END, values=(r[0], r[1], ngay_f, r[3], r[4], r[5], r[6], r[7], r[8]))
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nạp dữ liệu: {e}")

    def huy_dang_ky(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0], 'values')
        rec_id = item[0]; d_huy = self.chuan_hoa_ngay(item[2])

        if messagebox.askyesno("Xác nhận", f"Hủy đăng ký [{item[1]}] ngày {item[2]} Tiết {item[4]}?"):
            try:
                conn = psycopg2.connect(DB_URI); cur = conn.cursor()
                cur.execute("DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s", (rec_id, self.magv))
                conn.commit(); cur.close(); conn.close()
                if d_huy: sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_huy)
                self.load_data()
                messagebox.showinfo("Thành công", "Đã hủy và cập nhật lại Sổ Báo Giảng!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể hủy: {e}")
