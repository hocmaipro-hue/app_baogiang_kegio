# ui_quan_ly_ppct.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class QuanLyPPCTWindow:
    def __init__(self, session):
        self.session = session
        self.mon = get_val(session, 'to_bo_mon', 'Toán')
        self.window = tk.Toplevel()
        self.window.title(f"Quản lý Phân Phối Chương Trình - Môn: {self.mon}")
        self.window.geometry("960x600")

        # --- KHUNG CÔNG CỤ NHẬP EXCEL & THAO TÁC NHANH ---
        tool_frame = tk.LabelFrame(self.window, text=" Nhập dữ liệu tự động ", padx=10, pady=8, font=("Arial", 9, "bold"))
        tool_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(tool_frame, text="📥 NHẬP PPCT TỪ FILE EXCEL (.XLSX)", bg="#2e86c1", fg="white", 
                  font=("Arial", 10, "bold"), height=2, command=self.import_excel).pack(side=tk.LEFT, padx=5)

        tk.Label(tool_frame, text="*(File Excel gồm 5 cột: Phân môn | Khối | Tuần | Tiết PPCT | Tên bài dạy)*", 
                 fg="#555", font=("Arial", 9, "italic")).pack(side=tk.LEFT, padx=10)

        # --- KHUNG NHẬP TAY THỦ CÔNG (KHI CẦN BỔ SUNG LẺ) ---
        form = tk.LabelFrame(self.window, text=" Thêm/Chỉnh sửa lẻ từng bài ", padx=10, pady=5)
        form.pack(fill=tk.X, padx=10, pady=3)

        tk.Label(form, text="Phân môn:").grid(row=0, column=0, sticky="w")
        self.txt_phan_mon = tk.Entry(form, width=15)
        self.txt_phan_mon.grid(row=0, column=1, padx=5, sticky="w")

        tk.Label(form, text="Khối:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.spn_khoi = ttk.Spinbox(form, from_=6, to=12, width=6)
        self.spn_khoi.set(10)
        self.spn_khoi.grid(row=0, column=3, padx=5, sticky="w")

        tk.Label(form, text="Tuần:").grid(row=0, column=4, sticky="w", padx=(10,0))
        self.spn_tuan = ttk.Spinbox(form, from_=1, to=35, width=6)
        self.spn_tuan.set(1)
        self.spn_tuan.grid(row=0, column=5, padx=5, sticky="w")

        tk.Label(form, text="Tiết PPCT:").grid(row=0, column=6, sticky="w", padx=(10,0))
        self.spn_tiet = ttk.Spinbox(form, from_=1, to=150, width=6)
        self.spn_tiet.set(1)
        self.spn_tiet.grid(row=0, column=7, padx=5, sticky="w")

        tk.Label(form, text="Tên bài dạy:").grid(row=1, column=0, sticky="w", pady=4)
        self.txt_ten_bai = tk.Entry(form, width=65)
        self.txt_ten_bai.grid(row=1, column=1, columnspan=6, padx=5, pady=4, sticky="w")

        tk.Button(form, text="➕ Thêm lẻ bài này", bg="#d4efdf", font=("Arial", 9, "bold"),
                  command=self.them_bai).grid(row=1, column=7, padx=5, pady=4)

        # --- BẢNG HIỂN THỊ DANH SÁCH PPCT ---
        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "mon", "phan_mon", "khoi", "tuan", "tiet_ppct", "ten_bai_day")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=13)
        self.tree.heading("id", text="ID")
        self.tree.heading("mon", text="Môn")
        self.tree.heading("phan_mon", text="Phân môn")
        self.tree.heading("khoi", text="Khối")
        self.tree.heading("tuan", text="Tuần")
        self.tree.heading("tiet_ppct", text="Tiết PPCT")
        self.tree.heading("ten_bai_day", text="Tên bài dạy")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("mon", width=80, anchor="center")
        self.tree.column("phan_mon", width=100, anchor="center")
        self.tree.column("khoi", width=60, anchor="center")
        self.tree.column("tuan", width=60, anchor="center")
        self.tree.column("tiet_ppct", width=80, anchor="center")
        self.tree.column("ten_bai_day", width=420, anchor="w")

        sb = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Thanh nút thao tác dưới
        btn_box = tk.Frame(self.window)
        btn_box.pack(pady=6)
        tk.Button(btn_box, text="🔄 Tải lại bảng", width=15, command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_box, text="❌ Xóa bài chọn", width=15, bg="#fadbd8", command=self.xoa_bai).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_box, text="⚠️ Xóa TOÀN BỘ PPCT môn này", width=25, bg="#e74c3c", fg="white", 
                  command=self.xoa_toan_bo).pack(side=tk.LEFT, padx=15)

        self.load_data()

    def import_excel(self):
        """Hàm chọn và đọc file Excel đẩy vào CSDL"""
        file_path = filedialog.askopenfilename(
            title="Chọn file Excel Phân Phối Chương Trình",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        try:
            # Dùng thư viện openpyxl để đọc Excel
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active

            records = []
            # Đọc từ dòng 2 (bỏ qua tiêu đề dòng 1)
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row): continue # Bỏ dòng trống
                
                # 5 cột: Phân môn, Khối, Tuần, Tiết PPCT, Tên bài
                phan_mon = str(row[0]).strip() if row[0] is not None else ""
                khoi = int(row[1]) if row[1] is not None else 10
                tuan = int(row[2]) if row[2] is not None else 1
                tiet = int(row[3]) if row[3] is not None else 1
                ten_bai = str(row[4]).strip() if row[4] is not None else ""

                if ten_bai:
                    records.append((self.mon, phan_mon, khoi, tuan, tiet, ten_bai))

            if not records:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy dữ liệu hợp lệ trong file Excel!")
                return

            # Lưu hàng loạt vào CSDL
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.executemany("""
                INSERT INTO phan_phoi_chuong_trinh (mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, records)
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Thành công", f"Đã nhập thành công {len(records)} tiết bài dạy từ Excel!")
            self.load_data()

        except Exception as e:
            messagebox.showerror("Lỗi Import Excel", f"Không thể đọc file Excel: {e}\n(Hãy đảm bảo máy đã cài thư viện openpyxl: pip install openpyxl)")

    def them_bai(self):
        phan_mon = self.txt_phan_mon.get().strip()
        khoi = self.spn_khoi.get()
        tuan = self.spn_tuan.get()
        tiet = self.spn_tiet.get()
        ten_bai = self.txt_ten_bai.get().strip()

        if not phan_mon or not ten_bai:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập Phân môn và Tên bài dạy!")
            return

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO phan_phoi_chuong_trinh (mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (self.mon, phan_mon, khoi, tuan, tiet, ten_bai))
            conn.commit()
            cur.close()
            conn.close()
            self.txt_ten_bai.delete(0, tk.END)
            self.spn_tiet.set(int(tiet) + 1)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm PPCT: {e}")

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, mon, phan_mon, khoi, tuan, tiet_ppct, ten_bai_day
                FROM phan_phoi_chuong_trinh
                WHERE mon = %s
                ORDER BY khoi, phan_mon, tiet_ppct ASC
            """, (self.mon,))
            for r in cur.fetchall():
                self.tree.insert("", tk.END, values=r)
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải PPCT: {e}")

    def xoa_bai(self):
        sel = self.tree.selection()
        if not sel: return
        rec_id = self.tree.item(sel[0], 'values')[0]
        if messagebox.askyesno("Xác nhận", "Xóa tiết bài dạy này khỏi PPCT?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM phan_phoi_chuong_trinh WHERE id = %s", (rec_id,))
                conn.commit()
                cur.close()
                conn.close()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")

    def xoa_toan_bo(self):
        if messagebox.askyesno("CẢNH BÁO", f"Bạn có chắc muốn xóa TOÀN BỘ dữ liệu PPCT của môn {self.mon}?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM phan_phoi_chuong_trinh WHERE mon = %s", (self.mon,))
                conn.commit()
                cur.close()
                conn.close()
                self.load_data()
                messagebox.showinfo("Đã xóa", "Đã xóa sạch PPCT môn này để bạn nhập lại từ đầu!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")