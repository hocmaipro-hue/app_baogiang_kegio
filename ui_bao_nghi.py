# ui_bao_nghi.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime, date, timedelta
import re
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class BaoNghiWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')

        self.window = tk.Toplevel()
        self.window.title(f"Báo Nghỉ Giảng Dạy - GV: {self.tengv}")
        self.window.geometry("1050x640")

        # FORM ĐĂNG KÝ
        frm = tk.LabelFrame(self.window, text=" Đăng ký Báo Nghỉ (Tự động tra cứu TKB) ", 
                            padx=12, pady=10, font=("Arial", 9, "bold"), fg="#900C3F")
        frm.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm, text="Lý do nghỉ:").grid(row=0, column=0, sticky="w", pady=4)
        self.cbo_loai = ttk.Combobox(frm, state="readonly", width=22,
                                     values=["Nghỉ việc riêng", "Nghỉ theo kế hoạch", "Nghỉ theo điều động"])
        self.cbo_loai.current(0)
        self.cbo_loai.grid(row=0, column=1, pady=4, sticky="w")

        tk.Label(frm, text="Từ ngày:").grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        self.txt_ngay = tk.Entry(frm, width=12)
        self.txt_ngay.grid(row=0, column=3, pady=4, sticky="w")
        self.txt_ngay.bind("<KeyRelease>", self.tu_dong_dien_tkb)

        tk.Label(frm, text="Đến ngày (Nghỉ Tết/dài hạn):", fg="#B7950B").grid(row=0, column=4, sticky="w", padx=(10, 0), pady=4)
        self.txt_den_ngay = tk.Entry(frm, width=12)
        self.txt_den_ngay.grid(row=0, column=5, pady=4, sticky="w")
        self.txt_den_ngay.bind("<KeyRelease>", self.tu_dong_dien_tkb)

        tk.Label(frm, text="Buổi:").grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_buoi = ttk.Combobox(frm, state="readonly", width=22, values=["Sáng", "Chiều"])
        self.cbo_buoi.current(0)
        self.cbo_buoi.grid(row=1, column=1, pady=4, sticky="w")
        self.cbo_buoi.bind("<<ComboboxSelected>>", self.tu_dong_dien_tkb)

        tk.Label(frm, text="Tiết TKB:").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)
        self.spn_tiet = ttk.Spinbox(frm, from_=1, to=5, width=10, command=self.tu_dong_dien_tkb)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=1, column=3, pady=4, sticky="w")
        self.spn_tiet.bind("<KeyRelease>", self.tu_dong_dien_tkb)

        tk.Label(frm, text="Lớp:").grid(row=2, column=0, sticky="w", pady=4)
        self.txt_lop = tk.Entry(frm, width=24, state="readonly")
        self.txt_lop.grid(row=2, column=1, pady=4, sticky="w")

        tk.Label(frm, text="Phân môn:").grid(row=2, column=2, sticky="w", padx=(10, 0), pady=4)
        self.txt_pm = tk.Entry(frm, width=20, state="readonly")
        self.txt_pm.grid(row=2, column=3, pady=4, sticky="w")

        # Đánh dấu sao đỏ nhắc nhở bắt buộc nhập lý do
        tk.Label(frm, text="Chi tiết lý do / QĐ (*):", fg="#C0392B", font=("Arial", 9, "bold")).grid(row=2, column=4, sticky="w", padx=(10, 0), pady=4)
        self.txt_lydo = tk.Entry(frm, width=22)
        self.txt_lydo.grid(row=2, column=5, pady=4, sticky="w")

        tk.Button(frm, text="⛔ GỬI BÁO NGHỈ", bg="#C0392B", fg="white", font=("Arial", 9, "bold"),
                  padx=12, relief=tk.RAISED, cursor="hand2", command=self.gui_bao_nghi).grid(row=3, column=5, padx=5, pady=6, sticky="e")

        self.lbl_hint = tk.Label(frm, text="", font=("Arial", 8, "italic"), fg="#7F8C8D")
        self.lbl_hint.grid(row=3, column=0, columnspan=5, sticky="w", pady=(3, 0))

        # BẢNG LỊCH SỬ NGHỈ
        tbl_frm = tk.LabelFrame(self.window, text=" Lịch sử các tiết đã báo nghỉ ", padx=10, pady=5)
        tbl_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "loai", "ngay", "buoi", "tiet", "lop", "pm", "ly_do")
        self.tree = ttk.Treeview(tbl_frm, columns=cols, show="headings", height=12)
        for c, t, w, a in [("id","ID",40,"center"), ("loai","Loại nghỉ",150,"center"), ("ngay","Ngày",90,"center"),
                           ("buoi","Buổi",60,"center"), ("tiet","Tiết",50,"center"), ("lop","Lớp",70,"center"),
                           ("pm","Phân môn",120,"center"), ("ly_do","Lý do chi tiết",350,"w")]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor=a)

        sb = ttk.Scrollbar(tbl_frm, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bot = tk.Frame(self.window)
        bot.pack(pady=6)
        tk.Button(bot, text="❌ Hủy tiết nghỉ đang chọn", bg="#fadbd8", command=self.huy_nghi).pack(side=tk.LEFT, padx=5)
        tk.Button(bot, text="🔄 Tải lại danh sách", command=self.load_data).pack(side=tk.LEFT, padx=5)

        self.load_data()

    def get_nam_hoc(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
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

    def tu_dong_dien_tkb(self, event=None):
        if self.txt_den_ngay.get().strip():
            self.lbl_hint.config(text="ℹ️ Chế độ nghỉ dài hạn/nghỉ Tết: Hệ thống sẽ quét toàn bộ TKB các ngày trong khoảng này.", fg="#7D6608")
            self.txt_lop.config(state="normal"); self.txt_lop.delete(0, tk.END); self.txt_lop.config(state="readonly")
            self.txt_pm.config(state="normal"); self.txt_pm.delete(0, tk.END); self.txt_pm.config(state="readonly")
            return

        d = self.chuan_hoa_ngay(self.txt_ngay.get())
        if not d: return
        thu_so = d.weekday() + 2; buoi = self.cbo_buoi.get()
        try: tiet = int(self.spn_tiet.get())
        except ValueError: return

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT lop, mon, COALESCE(phan_mon, '') FROM thoi_khoa_bieu 
                WHERE magv = %s AND (thu = %s OR thu = %s) AND buoi = %s AND tiet = %s
            """, (self.magv, str(thu_so), thu_so, buoi, tiet))
            r = cur.fetchone(); cur.close(); conn.close()

            self.txt_lop.config(state="normal"); self.txt_lop.delete(0, tk.END)
            self.txt_pm.config(state="normal"); self.txt_pm.delete(0, tk.END)

            if r:
                lop_tkb = r[0].strip()
                pm_tkb = r[2].strip() if r[2].strip() else r[1].strip()
                self.txt_lop.insert(0, lop_tkb)
                self.txt_pm.insert(0, pm_tkb)
                self.lbl_hint.config(text=f"✔ Tìm thấy tiết Thứ {thu_so}: Lớp [{lop_tkb}] - [{pm_tkb}]", fg="#27ae60")
            else:
                self.lbl_hint.config(text=f"⚠️ Thứ {thu_so} Tiết {tiet} ({buoi}): Thầy/Cô KHÔNG CÓ TIẾT DẠY trên TKB!", fg="#c0392b")

            self.txt_lop.config(state="readonly"); self.txt_pm.config(state="readonly")
        except Exception: pass

    def gui_bao_nghi(self):
        loai = self.cbo_loai.get()
        d_tu = self.chuan_hoa_ngay(self.txt_ngay.get())
        raw_den = self.txt_den_ngay.get().strip()
        lydo = self.txt_lydo.get().strip()

        # 👉 1. BẮT BUỘC NHẬP LÝ DO CHI TIẾT
        if not lydo:
            messagebox.showwarning("Thiếu lý do", "Thầy/Cô BẮT BUỘC phải nhập 'Chi tiết lý do / QĐ' để kê khai Phiếu 1C!")
            self.txt_lydo.focus()
            return

        if not d_tu:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Ngày (hoặc Từ ngày) hợp lệ (VD: 15/09)!")
            self.txt_ngay.focus()
            return

        # NGHỈ DÀI HẠN / NGHỈ TẾT
        if raw_den:
            d_den = self.chuan_hoa_ngay(raw_den)
            if not d_den or d_den < d_tu:
                messagebox.showwarning("Lỗi", "Đến ngày không hợp lệ hoặc nhỏ hơn Từ ngày!")
                self.txt_den_ngay.focus()
                return

            so_ngay = (d_den - d_tu).days + 1
            if not messagebox.askyesno("Xác nhận", f"Báo [{loai}] từ {d_tu.strftime('%d/%m/%Y')} đến {d_den.strftime('%d/%m/%Y')} ({so_ngay} ngày)?"):
                return

            try:
                conn = psycopg2.connect(DB_URI); cur = conn.cursor()
                cur.execute("SELECT thu, COALESCE(buoi,'Sáng'), tiet, lop, mon, COALESCE(phan_mon,'') FROM thoi_khoa_bieu WHERE magv = %s", (self.magv,))
                tkb_all = cur.fetchall()

                cur_d = d_tu; count = 0
                while cur_d <= d_den:
                    thu_num = cur_d.weekday() + 2
                    for r in tkb_all:
                        t_thu = int(re.search(r'\d+', str(r[0])).group()) if re.search(r'\d+', str(r[0])) else 2
                        if t_thu == thu_num and r[4].strip() not in ['SHDC', 'SHL']:
                            t_pm = r[5].strip() if r[5].strip() else r[4].strip()
                            cur.execute("""
                                SELECT id FROM bien_dong_lich_day 
                                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                            """, (self.magv, cur_d, r[1], r[2]))
                            if not cur.fetchone():
                                cur.execute("""
                                    INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
                                """, (self.magv, loai, cur_d, r[1], r[2], r[3], t_pm, lydo))
                                count += 1
                    cur_d += timedelta(days=1)
                conn.commit(); cur.close(); conn.close()

                sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_tu)
                if d_den != d_tu: sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_den)

                messagebox.showinfo("Thành công", f"Đã báo nghỉ thành công {count} tiết và tự động bảo lưu PPCT!")
                self.load_data()
                self.txt_lydo.delete(0, tk.END)
                return
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu: {e}"); return

        # NGHỈ 1 TIẾT ĐƠN LẺ
        buoi = self.cbo_buoi.get()
        tiet = int(self.spn_tiet.get())
        lop = self.txt_lop.get().strip()
        pm = self.txt_pm.get().strip()

        if not lop:
            messagebox.showerror("Lỗi", "Tiết này trên TKB bạn không có lịch dạy để báo nghỉ!")
            return

        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT id FROM bien_dong_lich_day 
                WHERE magv = %s AND ngay = %s AND buoi = %s AND tiet_tkb = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
            """, (self.magv, d_tu, buoi, tiet))
            if cur.fetchone():
                messagebox.showwarning("Trùng lặp", "Bạn đã báo nghỉ tiết này rồi!"); cur.close(); conn.close(); return

            cur.execute("""
                INSERT INTO bien_dong_lich_day (magv, loai, ngay, buoi, tiet_tkb, lop, phan_mon, gv_day_thay, ly_do, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, '', %s, 'CHO_DUYET')
            """, (self.magv, loai, d_tu, buoi, tiet, lop, pm, lydo))
            conn.commit(); cur.close(); conn.close()

            sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_tu)
            messagebox.showinfo("Thành công", f"Đã báo nghỉ lớp {lop} ({pm}) ngày {d_tu.strftime('%d/%m/%Y')} thành công!")
            self.load_data()
            self.txt_lydo.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI); cur = conn.cursor()
            cur.execute("""
                SELECT id, loai, ngay, buoi, tiet_tkb, COALESCE(lop,''), COALESCE(phan_mon,''), COALESCE(ly_do,'')
                FROM bien_dong_lich_day 
                WHERE magv = %s AND loai LIKE 'Nghỉ%%' AND trang_thai != 'DA_HUY'
                ORDER BY ngay DESC, tiet_tkb ASC
            """, (self.magv,))
            for r in cur.fetchall():
                ngay_f = r[2].strftime("%d/%m/%Y") if hasattr(r[2], 'strftime') else str(r[2])
                self.tree.insert("", tk.END, values=(r[0], r[1], ngay_f, r[3], r[4], r[5], r[6], r[7]))
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nạp dữ liệu: {e}")

    def huy_nghi(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0], 'values')
        rec_id = item[0]; d_huy = self.chuan_hoa_ngay(item[2])

        if messagebox.askyesno("Xác nhận", f"Hủy báo nghỉ ngày {item[2]} Tiết {item[4]}?"):
            try:
                conn = psycopg2.connect(DB_URI); cur = conn.cursor()
                cur.execute("DELETE FROM bien_dong_lich_day WHERE id = %s AND magv = %s", (rec_id, self.magv))
                conn.commit(); cur.close(); conn.close()
                if d_huy: sbg_service.tu_dong_dong_bo_tuan(DB_URI, self.magv, self.to_bm, d_huy)
                self.load_data()
                messagebox.showinfo("Thành công", "Đã hủy và cập nhật lại Sổ Báo Giảng!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể hủy: {e}")