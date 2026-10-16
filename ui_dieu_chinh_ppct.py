# ui_dieu_chinh_ppct.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DieuChinhPPCTWindow:
    def __init__(self, session, callback_refresh=None):
        self.session = session
        self.callback_refresh = callback_refresh
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')

        self.window = tk.Toplevel()
        self.window.title(f"Cài đặt mốc khởi điểm PPCT - {self.tengv}")
        self.window.geometry("750x450")
        self.window.grab_set() # Giữ focus

        self.ensure_table_exists()

        # FORM NHẬP LIỆU
        frm_input = tk.LabelFrame(self.window, text=" Thiết lập mốc bài dạy khi nhận lớp mới ", 
                                  padx=10, pady=10, font=("Arial", 9, "bold"))
        frm_input.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm_input, text="Lớp dạy:").grid(row=0, column=0, sticky="w", pady=4)
        self.cbo_lop = ttk.Combobox(frm_input, width=10, state="readonly")
        self.cbo_lop.grid(row=0, column=1, sticky="w", pady=4, padx=5)

        tk.Label(frm_input, text="Phân môn:").grid(row=0, column=2, sticky="w", pady=4, padx=(10, 0))
        self.cbo_pm = ttk.Combobox(frm_input, width=18, state="readonly")
        self.cbo_pm.grid(row=0, column=3, sticky="w", pady=4, padx=5)

        tk.Label(frm_input, text="Từ Tuần:").grid(row=1, column=0, sticky="w", pady=4)
        self.spn_tuan = ttk.Spinbox(frm_input, from_=1, to=40, width=8)
        self.spn_tuan.set(20)
        self.spn_tuan.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        tk.Label(frm_input, text="Bắt đầu từ Tiết PPCT:").grid(row=1, column=2, sticky="w", pady=4, padx=(10, 0))
        self.spn_tiet = ttk.Spinbox(frm_input, from_=1, to=200, width=10)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=1, column=3, sticky="w", pady=4, padx=5)

        tk.Button(frm_input, text="💾 LƯU THIẾT LẬP", bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                  padx=10, command=self.luu_moc).grid(row=1, column=4, padx=15, pady=4)

        # BẢNG DANH SÁCH MỐC ĐÃ THIẾT LẬP
        frm_table = tk.Frame(self.window)
        frm_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "lop", "phan_mon", "tu_tuan", "tiet_bat_dau")
        self.tree = ttk.Treeview(frm_table, columns=cols, show="headings", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("lop", text="Lớp")
        self.tree.heading("phan_mon", text="Phân môn")
        self.tree.heading("tu_tuan", text="Áp dụng từ Tuần")
        self.tree.heading("tiet_bat_dau", text="Tiết PPCT bắt đầu")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("lop", width=80, anchor="center")
        self.tree.column("phan_mon", width=160, anchor="center")
        self.tree.column("tu_tuan", width=120, anchor="center")
        self.tree.column("tiet_bat_dau", width=120, anchor="center")

        sb = ttk.Scrollbar(frm_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bot = tk.Frame(self.window)
        bot.pack(pady=6)
        tk.Button(bot, text="❌ Xóa mốc đang chọn", bg="#fadbd8", command=self.xoa_moc).pack(side=tk.LEFT, padx=5)
        tk.Button(bot, text="Đóng", width=10, command=self.window.destroy).pack(side=tk.LEFT, padx=5)

        self.load_lop_va_mon()
        self.load_data()

    def ensure_table_exists(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
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
            cur.close(); conn.close()
        except Exception as e:
            print("Lỗi tạo bảng mốc PPCT:", e)

    def load_lop_va_mon(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT lop FROM thoi_khoa_bieu WHERE magv = %s ORDER BY lop", (self.magv,))
            lops = [r[0].strip() for r in cur.fetchall() if r[0]]
            self.cbo_lop['values'] = lops
            if lops: self.cbo_lop.current(0)

            cur.execute("""
                SELECT DISTINCT COALESCE(NULLIF(TRIM(phan_mon), ''), mon)
                FROM phan_phoi_chuong_trinh
                WHERE UPPER(mon) = UPPER(%s) OR %s ILIKE '%%' || mon || '%%' OR UPPER(mon) LIKE '%%TOÁN%%'
                ORDER BY 1 ASC;
            """, (self.to_bm, self.to_bm))
            pms = [r[0].strip() for r in cur.fetchall() if r[0]]
            self.cbo_pm['values'] = pms
            if pms: self.cbo_pm.current(0)
            cur.close(); conn.close()
        except Exception: pass

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, lop, phan_mon, tu_tuan, tiet_bat_dau 
                FROM cau_hinh_moc_ppct WHERE magv = %s 
                ORDER BY lop, phan_mon, tu_tuan ASC
            """, (self.magv,))
            for r in cur.fetchall():
                self.tree.insert("", tk.END, values=r)
            cur.close(); conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách mốc: {e}")

    def luu_moc(self):
        lop = self.cbo_lop.get().strip()
        pm = self.cbo_pm.get().strip()
        try:
            tuan = int(self.spn_tuan.get())
            tiet = int(self.spn_tiet.get())
        except ValueError:
            messagebox.showwarning("Lỗi", "Tuần và Tiết bắt đầu phải là số nguyên!")
            return

        if not lop or not pm:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Lớp và Phân môn!")
            return

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cau_hinh_moc_ppct (magv, lop, phan_mon, tu_tuan, tiet_bat_dau)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (magv, lop, phan_mon, tu_tuan)
                DO UPDATE SET tiet_bat_dau = EXCLUDED.tiet_bat_dau;
            """, (self.magv, lop, pm, tuan, tiet))
            conn.commit()
            cur.close(); conn.close()
            messagebox.showinfo("Thành công", f"Đã lưu mốc: Lớp {lop} ({pm}) từ Tuần {tuan} sẽ bắt đầu từ Tiết {tiet}!")
            self.load_data()
            if self.callback_refresh: self.callback_refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu mốc: {e}")

    def xoa_moc(self):
        sel = self.tree.selection()
        if not sel: return
        rec_id = self.tree.item(sel[0], 'values')[0]
        if messagebox.askyesno("Xác nhận", "Xóa thiết lập mốc này?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM cau_hinh_moc_ppct WHERE id = %s AND magv = %s", (rec_id, self.magv))
                conn.commit()
                cur.close(); conn.close()
                self.load_data()
                if self.callback_refresh: self.callback_refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
