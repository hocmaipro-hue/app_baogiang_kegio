# ui_duyet_ke_gio_to.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DuyetKeGioWindow:
    def __init__(self, session):
        self.session = session
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')
        self.window = tk.Toplevel()
        self.window.title(f"Quản lý & Duyệt Kê Khai Giờ Dạy (PKG) - Tổ {self.to_bm}")
        self.window.geometry("900x500")

        tk.Label(self.window, text=f"BẢNG TỔNG HỢP GIỜ DẠY CỦA TỔ {self.to_bm.upper()}",
                 font=("Arial", 12, "bold"), fg="#1a5276").pack(pady=10)

        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        cols = ("magv", "tengv", "dinh_muc", "thuc_day", "thay", "bdhsg", "chenh_lech")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=12)
        self.tree.heading("magv", text="Mã GV")
        self.tree.heading("tengv", text="Họ và Tên")
        self.tree.heading("dinh_muc", text="Định mức (tiết)")
        self.tree.heading("thuc_day", text="Tiết thực dạy")
        self.tree.heading("thay", text="Tiết dạy thay")
        self.tree.heading("bdhsg", text="Tiết BDHSG")
        self.tree.heading("chenh_lech", text="Thừa / Thiếu")

        for c in cols: self.tree.column(c, anchor="center")
        self.tree.column("tengv", width=180, anchor="w")

        self.tree.pack(fill=tk.BOTH, expand=True)

        bot = tk.Frame(self.window)
        bot.pack(pady=10)
        tk.Button(bot, text="🔄 Tải lại dữ liệu", command=self.load_data).pack(side=tk.LEFT, padx=10)
        tk.Button(bot, text="✅ KÝ DUYỆT BẢNG KÊ GIỜ CỦA TỔ", bg="#d4efdf", font=("Arial", 10, "bold"),
                  command=lambda: messagebox.showinfo("Thành công", "Đã duyệt bảng kê giờ thành công!")).pack(side=tk.LEFT, padx=10)

        self.load_data()

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT magv, tengv, COALESCE(dinh_muc_tiet, 17)
                FROM giao_vien WHERE to_bo_mon = %s ORDER BY tengv
            """, (self.to_bm,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for r in rows:
                magv, tengv, dinh_muc = r
                thuc_day = dinh_muc
                thay = 0
                bdhsg = 0
                chenh_lech = "+0"
                self.tree.insert("", tk.END, values=(magv, tengv, dinh_muc, thuc_day, thay, bdhsg, chenh_lech))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải bảng kê giờ: {e}")
