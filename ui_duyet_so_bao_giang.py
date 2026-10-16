# ui_duyet_so_bao_giang.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI
import service_so_bao_giang as sbg_service

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DuyetSBGWindow:
    def __init__(self, session):
        self.session = session
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')
        self.window = tk.Toplevel()
        self.window.title(f"Theo Dõi Sổ Báo Giảng - Tổ {self.to_bm}")
        self.window.geometry("1050x560")

        top = tk.Frame(self.window, bg="#F4F6F6", pady=8)
        top.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top, text="Chọn Giáo viên:", font=("Arial", 10, "bold"), bg="#F4F6F6").pack(side=tk.LEFT, padx=5)
        self.cbo_gv = ttk.Combobox(top, width=25, state="readonly")
        self.cbo_gv.pack(side=tk.LEFT, padx=5)
        self.cbo_gv.bind("<<ComboboxSelected>>", lambda e: self.xem_bao_giang())

        tk.Label(top, text="Tuần xem:", font=("Arial", 10, "bold"), bg="#F4F6F6").pack(side=tk.LEFT, padx=(15, 5))
        self.spn_tuan = ttk.Spinbox(top, from_=1, to=45, width=6, command=self.xem_bao_giang)
        self.spn_tuan.set(1)
        self.spn_tuan.pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="🔍 TẢI LẠI", bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
                  padx=12, relief=tk.RAISED, cursor="hand2", command=self.xem_bao_giang).pack(side=tk.LEFT, padx=15)

        self.lbl_thong_tin = tk.Label(top, text="", font=("Arial", 10, "bold"), fg="#27ae60", bg="#F4F6F6")
        self.lbl_thong_tin.pack(side=tk.RIGHT, padx=10)

        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("thu", "buoi", "tiet", "lop", "mon_pm", "tiet_ppct", "ten_bai", "tre_vuot", "chu_y")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=14)
        
        self.tree.heading("thu", text="Thứ")
        self.tree.heading("buoi", text="Buổi")
        self.tree.heading("tiet", text="Tiết")
        self.tree.heading("lop", text="Lớp")
        self.tree.heading("mon_pm", text="Môn/Phân môn")
        self.tree.heading("tiet_ppct", text="Tiết PPCT")
        self.tree.heading("ten_bai", text="Tên bài dạy")
        self.tree.heading("tre_vuot", text="Tiến độ")
        self.tree.heading("chu_y", text="Ghi chú")

        self.tree.column("thu", width=55, anchor="center")
        self.tree.column("buoi", width=55, anchor="center")
        self.tree.column("tiet", width=40, anchor="center")
        self.tree.column("lop", width=65, anchor="center")
        self.tree.column("mon_pm", width=110, anchor="center")
        self.tree.column("tiet_ppct", width=75, anchor="center")
        self.tree.column("ten_bai", width=360, anchor="w")
        self.tree.column("tre_vuot", width=100, anchor="center")
        self.tree.column("chu_y", width=150, anchor="w")

        sb = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_gv_to()

    def load_gv_to(self):
        self.gv_map = {}
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT magv, tengv FROM giao_vien WHERE to_bo_mon = %s ORDER BY tengv", (self.to_bm,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            vals = [f"{r[1]} ({r[0]})" for r in rows]
            for r in rows: self.gv_map[f"{r[1]} ({r[0]})"] = r[0]
            self.cbo_gv['values'] = vals
            if vals: 
                self.cbo_gv.current(0)
                self.xem_bao_giang()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải danh sách GV: {e}")

    def xem_bao_giang(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        selected_gv = self.cbo_gv.get().strip()
        if not selected_gv: return
        magv = self.gv_map.get(selected_gv)
        if not magv: return

        try:
            tuan = int(self.spn_tuan.get())
        except ValueError: return

        try:
            # Lấy trực tiếp dữ liệu chuẩn theo engine đồng bộ thời gian thực
            rows_data, tong_tiet = sbg_service.lay_du_lieu_bao_giang(DB_URI, magv, self.to_bm, tuan)
            
            so_tiet_hien_thi = 0
            for r in rows_data:
                # Chỉ hiển thị các tiết có dạy hoặc có biến động (báo nghỉ, dạy thay, bù...)
                if r['row_type'] != 'empty':
                    so_tiet_hien_thi += 1
                    vals = (
                        f"Thứ {r['thu_num']}",
                        r['buoi'],
                        r['tiet'],
                        r['lop'],
                        r['mon_pm'],
                        r['tiet_ppct'],
                        r['ten_bai'],
                        r['tre_vuot'],
                        r['chu_y']
                    )
                    self.tree.insert("", tk.END, values=vals)

            self.lbl_thong_tin.config(text=f"Tuần {tuan}: {tong_tiet} tiết dạy thực tế (Tự động đồng bộ)")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nạp Sổ Báo Giảng: {e}")