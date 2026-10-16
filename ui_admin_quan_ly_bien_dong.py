# ui_admin_quan_ly_bien_dong.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI

class AdminQuanLyBienDongWindow:
    def __init__(self, session):
        self.session = session
        self.window = tk.Toplevel()
        self.window.title("Giám Sát & Quản Lý Lịch Nghỉ / Dạy Bù Toàn Trường - BGH")
        self.window.geometry("1060x580")

        self.ensure_column_gv_day_thay()

        tk.Label(self.window, text="DANH SÁCH BÁO NGHỈ, DẠY BÙ, DẠY THAY TOÀN TRƯỜNG", 
                 font=("Arial", 12, "bold"), fg="#1a5276").pack(pady=8)

        # Khung lọc tìm kiếm
        filter_frame = tk.Frame(self.window)
        filter_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(filter_frame, text="Tổ bộ môn:").pack(side=tk.LEFT, padx=5)
        self.cbo_to = ttk.Combobox(filter_frame, width=15, state="readonly", values=["Tất cả"])
        self.cbo_to.set("Tất cả")
        self.cbo_to.pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="Loại việc:").pack(side=tk.LEFT, padx=(15, 5))
        self.cbo_loai = ttk.Combobox(filter_frame, width=15, state="readonly", 
                                     values=["Tất cả", "Nghỉ dạy", "Dạy bù", "Dạy thay", "Bồi dưỡng HSG"])
        self.cbo_loai.set("Tất cả")
        self.cbo_loai.pack(side=tk.LEFT, padx=5)

        tk.Button(filter_frame, text="🔍 Lọc danh sách", bg="#d4efdf", font=("Arial", 9, "bold"),
                  command=self.load_data).pack(side=tk.LEFT, padx=15)

        # Bảng dữ liệu (ĐÃ TĂNG LÊN 12 CỘT)
        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        cols = ("id", "magv", "tengv", "to_bm", "loai", "ngay", "buoi", "tiet", "lop", "gv_day_thay", "ly_do", "trang_thai")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("magv", text="Mã GV")
        self.tree.heading("tengv", text="Họ và Tên")
        self.tree.heading("to_bm", text="Tổ")
        self.tree.heading("loai", text="Loại việc")
        self.tree.heading("ngay", text="Ngày")
        self.tree.heading("buoi", text="Buổi")
        self.tree.heading("tiet", text="Tiết")
        self.tree.heading("lop", text="Lớp")
        self.tree.heading("gv_day_thay", text="GV dạy thay / được thay")  # <-- CỘT MỚI THÊM
        self.tree.heading("ly_do", text="Lý do / Chuyên đề")
        self.tree.heading("trang_thai", text="Trạng thái")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("magv", width=65, anchor="center")
        self.tree.column("tengv", width=140, anchor="w")
        self.tree.column("to_bm", width=65, anchor="center")
        self.tree.column("loai", width=95, anchor="center")
        self.tree.column("ngay", width=85, anchor="center")
        self.tree.column("buoi", width=50, anchor="center")
        self.tree.column("tiet", width=45, anchor="center")
        self.tree.column("lop", width=60, anchor="center")
        self.tree.column("gv_day_thay", width=150, anchor="w")  # <-- ĐỘ RỘNG CỘT MỚI
        self.tree.column("ly_do", width=160, anchor="w")
        self.tree.column("trang_thai", width=85, anchor="center")

        sb = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Nút hành động
        btn_box = tk.Frame(self.window)
        btn_box.pack(pady=8)
        tk.Button(btn_box, text="❌ XÓA DÒNG BÁO CÁO ĐANG CHỌN", bg="#fadbd8", fg="#c0392b", font=("Arial", 9, "bold"),
                  command=self.xoa_don_sai).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_box, text="🔄 Tải lại toàn bộ", width=15, command=self.load_data).pack(side=tk.LEFT, padx=10)

        self.load_to_bo_mon()
        self.load_data()

    def ensure_column_gv_day_thay(self):
        """Tự động thêm cột gv_day_thay vào CSDL Supabase nếu chưa có"""
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("ALTER TABLE bien_dong_lich_day ADD COLUMN IF NOT EXISTS gv_day_thay VARCHAR(100);")
            conn.commit()
            cur.close()
            conn.close()
        except Exception: pass

    def load_to_bo_mon(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT to_bo_mon FROM giao_vien WHERE to_bo_mon IS NOT NULL")
            tos = ["Tất cả"] + [r[0] for r in cur.fetchall()]
            self.cbo_to['values'] = tos
            cur.close()
            conn.close()
        except Exception: pass

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        to_sel = self.cbo_to.get()
        loai_sel = self.cbo_loai.get()

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            sql = """
                SELECT b.id, b.magv, g.tengv, g.to_bo_mon, b.loai, b.ngay, b.buoi, 
                       b.tiet_tkb, COALESCE(b.lop,''), COALESCE(b.gv_day_thay,''), 
                       COALESCE(b.ly_do,''), b.trang_thai
                FROM bien_dong_lich_day b
                LEFT JOIN giao_vien g ON b.magv = g.magv
                WHERE 1=1
            """
            params = []
            if to_sel != "Tất cả":
                sql += " AND g.to_bo_mon = %s"
                params.append(to_sel)
            if loai_sel != "Tất cả":
                sql += " AND b.loai = %s"
                params.append(loai_sel)

            sql += " ORDER BY b.ngay DESC, b.tiet_tkb ASC"
            cur.execute(sql, params)
            for r in cur.fetchall():
                ngay_f = r[5].strftime("%d/%m/%Y") if hasattr(r[5], 'strftime') else str(r[5])
                vals = (r[0], r[1], r[2], r[3], r[4], ngay_f, r[6], r[7], r[8], r[9], r[10], r[11])
                self.tree.insert("", tk.END, values=vals)
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải biến động: {e}")

    def xoa_don_sai(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn 1 dòng báo cáo cần xóa!")
            return
        item = self.tree.item(sel[0], 'values')
        rec_id, tengv, loai, ngay = item[0], item[2], item[4], item[5]

        if messagebox.askyesno("Xác nhận BGH", f"Xóa báo cáo '{loai}' ngày {ngay} của giáo viên {tengv}?\n(Sau khi xóa, Sổ Báo Giảng của GV sẽ tự động phục hồi)"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM bien_dong_lich_day WHERE id = %s", (rec_id,))
                conn.commit()
                cur.close()
                conn.close()
                self.tree.delete(sel[0])
                messagebox.showinfo("Thành công", "Đã xóa báo cáo sai thành công!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")