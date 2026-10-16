# ui_ds_giao_vien_to.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DSGiaoVienToWindow:
    def __init__(self, session):
        self.session = session
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')
        self.window = tk.Toplevel()
        self.window.title(f"Danh sách Giáo viên trong Tổ {self.to_bm}")
        self.window.geometry("750x420")

        tk.Label(self.window, text=f"DANH SÁCH GIÁO VIÊN - TỔ: {self.to_bm.upper()}",
                 font=("Arial", 12, "bold"), fg="#1c2833").pack(pady=10)

        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        cols = ("magv", "tengv", "role", "chuc_vu", "dinh_muc")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=10)
        self.tree.heading("magv", text="Mã GV")
        self.tree.heading("tengv", text="Họ và Tên")
        self.tree.heading("role", text="Vai trò")
        self.tree.heading("chuc_vu", text="Chức vụ")
        self.tree.heading("dinh_muc", text="Định mức tiết")

        self.tree.column("magv", width=90, anchor="center")
        self.tree.column("tengv", width=200, anchor="w")
        self.tree.column("role", width=110, anchor="center")
        self.tree.column("chuc_vu", width=140, anchor="w")
        self.tree.column("dinh_muc", width=90, anchor="center")

        sb = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.window, text="🔄 Tải lại", command=self.load_data).pack(pady=10)
        self.load_data()

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT magv, tengv, role, COALESCE(chuc_vu, ''), COALESCE(dinh_muc_tiet, 0)
                FROM giao_vien 
                WHERE to_bo_mon = %s 
                ORDER BY magv ASC
            """, (self.to_bm,))
            for r in cur.fetchall():
                self.tree.insert("", tk.END, values=r)
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách GV tổ: {e}")
