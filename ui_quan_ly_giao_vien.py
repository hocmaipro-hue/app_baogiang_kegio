# ui_quan_ly_giao_vien.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

def safe_int(val, default=17):
    if val is None: return default
    s = str(val).strip()
    if s.lower() in ['không', 'khong', '-', '', 'none', 'null']: return default
    try: return int(float(s))
    except Exception: return default

class QuanLyGiaoVienWindow:
    def __init__(self, session):
        self.session = session
        self.user_role = str(get_val(session, 'role', '')).upper()
        self.user_to = get_val(session, 'to_bo_mon', '')

        self.window = tk.Toplevel()
        tieude = "QUẢN LÝ TẤT CẢ CÁC CỘT GIÁO VIÊN [ADMIN]" if self.user_role in ['ADMIN', 'BGH'] else f"DANH SÁCH GIÁO VIÊN - TỔ {self.user_to.upper()}"
        self.window.title(tieude)
        self.window.geometry("1120x660")
        
        tk.Label(self.window, text=tieude, font=("Arial", 13, "bold"), fg="#1a5276").pack(pady=6)
        
        # --- KHUNG 1: THÊM LẺ (CƠ BẢN) ---
        frame_add = tk.LabelFrame(self.window, text=" Thêm 1 Giáo viên mới (Cơ bản) ", padx=10, pady=5)
        frame_add.pack(fill=tk.X, padx=10, pady=3)

        tk.Label(frame_add, text="Mã GV:").grid(row=0, column=0, sticky="w")
        self.txt_magv = tk.Entry(frame_add, width=10)
        self.txt_magv.grid(row=0, column=1, padx=3, sticky="w")

        tk.Label(frame_add, text="Họ tên:").grid(row=0, column=2, padx=(8,0), sticky="w")
        self.txt_tengv = tk.Entry(frame_add, width=18)
        self.txt_tengv.grid(row=0, column=3, padx=3, sticky="w")

        tk.Label(frame_add, text="Tổ:").grid(row=0, column=4, padx=(8,0), sticky="w")
        self.txt_to = tk.Entry(frame_add, width=10)
        if self.user_role not in ['ADMIN', 'BGH']:
            self.txt_to.insert(0, self.user_to)
            self.txt_to.config(state="readonly")
        self.txt_to.grid(row=0, column=5, padx=3, sticky="w")

        tk.Label(frame_add, text="Vai trò:").grid(row=0, column=6, padx=(8,0), sticky="w")
        self.cbo_role = ttk.Combobox(frame_add, width=10, state="readonly", values=["GV", "TO_TRUONG", "ADMIN"])
        self.cbo_role.set("GV")
        self.cbo_role.grid(row=0, column=7, padx=3, sticky="w")

        tk.Button(frame_add, text="➕ Thêm nhanh GV", bg="#d4efdf", font=("Arial", 9, "bold"),
                  command=self.them_gv_le).grid(row=0, column=8, padx=15, sticky="w")

        # --- KHUNG 2: BẢNG DỮ LIỆU TỰ ĐỘNG (KHÓA CO ÉP CỘT) ---
        frame_table = tk.Frame(self.window)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(frame_table, show="headings", height=14)
        
        # Thanh cuộn dọc & ngang
        sb_y = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame_table, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        frame_table.grid_rowconfigure(0, weight=1)
        frame_table.grid_columnconfigure(0, weight=1)
        
        # Click đúp để sửa
        self.tree.bind("<Double-1>", lambda event: self.mo_cua_so_sua_tat_ca_cot())

        # --- KHUNG 3: CÁC NÚT HÀNH ĐỘNG ---
        frame_btn = tk.Frame(self.window)
        frame_btn.pack(pady=8)
        
        if self.user_role in ['ADMIN', 'BGH']:
            tk.Button(frame_btn, text="📥 NHẬP TỪ EXCEL", bg="#2980b9", fg="white", 
                      font=("Arial", 9, "bold"), command=self.import_excel_dsgv).grid(row=0, column=0, padx=5)
        
        tk.Button(frame_btn, text="🔄 Tải lại", width=9, command=self.load_data).grid(row=0, column=1, padx=5)
        
        tk.Button(frame_btn, text="✏️ Sửa tất cả các cột", bg="#d6eaf8", font=("Arial", 9, "bold"),
                  command=self.mo_cua_so_sua_tat_ca_cot).grid(row=0, column=2, padx=5)

        tk.Button(frame_btn, text="🔑 Reset MK (123456)", bg="#fcf3cf", font=("Arial", 9, "bold"),
                  command=self.reset_mat_khau).grid(row=0, column=3, padx=5)

        tk.Button(frame_btn, text="❌ Xóa dòng chọn", width=13, bg="#fadbd8", command=self.delete_selected_row).grid(row=0, column=4, padx=5)
        
        if self.user_role in ['ADMIN', 'BGH']:
            tk.Button(frame_btn, text="⚠️ Xóa TOÀN BỘ danh sách", width=20, bg="#e74c3c", fg="white", 
                      command=self.delete_all_rows).grid(row=0, column=5, padx=8)
        
        self.all_columns = []
        self.load_data()

    def load_data(self):
        """Tự động quét cấu trúc cơ sở dữ liệu và giữ thanh trượt vĩnh viễn không bị mất"""
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            if self.user_role in ['ADMIN', 'BGH']:
                cur.execute("SELECT * FROM giao_vien ORDER BY magv ASC")
            else:
                cur.execute("SELECT * FROM giao_vien WHERE to_bo_mon = %s ORDER BY magv ASC", (self.user_to,))

            self.all_columns = [desc[0] for desc in cur.description]

            # Thiết lập lại cột cho Treeview
            self.tree["columns"] = self.all_columns
            for col in self.all_columns:
                self.tree.heading(col, text=col)
                
                # Định độ rộng cố định cho từng loại cột
                w = 130
                if col in ['magv', 'matkhau', 'role']: w = 110
                elif col in ['tengv', 'to_bo_mon', 'chuc_vu']: w = 170
                
                # 👉 CỰC KỲ QUAN TRỌNG: stretch=False để CHỐNG CO ÉP CỘT & GIỮ THANH CUỘN NGANG
                self.tree.column(col, width=w, minwidth=100, stretch=False, 
                                 anchor="center" if col not in ['tengv', 'chuc_vu'] else "w")

            # Đổ dữ liệu vào bảng
            for r in cur.fetchall():
                row_vals = ["" if x is None else str(x) for x in r]
                self.tree.insert("", tk.END, values=row_vals)

            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu", f"Không thể lấy danh sách: {e}")

    # ================= CỬA SỔ SỬA ĐẦY ĐỦ TẤT CẢ CÁC CỘT (DYNAMIC) =================
    def mo_cua_so_sua_tat_ca_cot(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn 1 giáo viên trên bảng để sửa!")
            return

        item_vals = self.tree.item(sel[0], "values")
        data_dict = dict(zip(self.all_columns, item_vals))
        magv = data_dict.get('magv', '')

        edit_win = tk.Toplevel(self.window)
        edit_win.title(f"Sửa Toàn Bộ Cột - Mã GV: {magv}")
        edit_win.geometry("520x620")
        edit_win.grab_set()

        tk.Label(edit_win, text=f"CHỈNH SỬA TẤT CẢ CỘT CỦA GIÁO VIÊN: {magv}", 
                 font=("Arial", 11, "bold"), fg="#1a5276").pack(pady=10)

        canvas = tk.Canvas(edit_win)
        scrollbar = ttk.Scrollbar(edit_win, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, padx=15, pady=5)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        entries = {}
        row_idx = 0

        for col in self.all_columns:
            tk.Label(scrollable_frame, text=f"{col}:", font=("Arial", 9, "bold"), anchor="w").grid(
                row=row_idx, column=0, sticky="w", pady=4, padx=5
            )
            
            ent = tk.Entry(scrollable_frame, width=32)
            ent.insert(0, data_dict.get(col, ""))
            
            if col == 'magv':
                ent.config(state="readonly", fg="#555")

            ent.grid(row=row_idx, column=1, pady=4, padx=5)
            entries[col] = ent
            row_idx += 1

        def luu_tat_ca():
            cols_to_update = [c for c in self.all_columns if c != 'magv']
            set_clause = ", ".join([f"{c} = %s" for c in cols_to_update])
            
            vals = []
            for c in cols_to_update:
                v = entries[c].get().strip()
                vals.append(None if v == "" else v)
            vals.append(magv)

            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                query = f"UPDATE giao_vien SET {set_clause} WHERE magv = %s"
                cur.execute(query, vals)
                conn.commit()
                cur.close()
                conn.close()

                messagebox.showinfo("Thành công", f"Đã cập nhật toàn bộ thông tin cho {magv}!", parent=edit_win)
                edit_win.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Lỗi Lưu", f"Lỗi thực thi: {e}", parent=edit_win)

        btn_save = tk.Button(scrollable_frame, text="💾 LƯU THAY ĐỔI TẤT CẢ CỘT", 
                             bg="#d4efdf", font=("Arial", 10, "bold"), command=luu_tat_ca)
        btn_save.grid(row=row_idx, column=0, columnspan=2, pady=15)

    # ================= CÁC TÍNH NĂNG KHÁC =================
    def them_gv_le(self):
        mgv = self.txt_magv.get().strip().upper()
        tgv = self.txt_tengv.get().strip()
        to_bm = self.txt_to.get().strip()
        role = self.cbo_role.get()

        if not mgv or not tgv:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập ít nhất Mã GV và Họ tên!")
            return
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO giao_vien (magv, tengv, to_bo_mon, role, matkhau)
                VALUES (%s, %s, %s, %s, '123456')
                ON CONFLICT (magv) DO NOTHING;
            """, (mgv, tgv, to_bm, role))
            conn.commit()
            cur.close()
            conn.close()
            self.txt_magv.delete(0, tk.END)
            self.txt_tengv.delete(0, tk.END)
            self.load_data()
            messagebox.showinfo("Thành công", f"Đã thêm giáo viên: {tgv} (Mật khẩu mặc định: 123456)")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm GV: {e}")

    def reset_mat_khau(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn 1 giáo viên để đặt lại mật khẩu!")
            return
        item_vals = self.tree.item(sel[0], "values")
        magv = item_vals[self.all_columns.index('magv')] if 'magv' in self.all_columns else item_vals[0]

        if messagebox.askyesno("Xác nhận", f"Đặt lại mật khẩu cho ({magv}) về '123456'?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("UPDATE giao_vien SET matkhau = '123456' WHERE magv = %s", (magv,))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("Thành công", f"Đã đặt lại mật khẩu của {magv} về 123456!")
                self.load_data()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đổi mật khẩu: {e}")

    def import_excel_dsgv(self):
        fp = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if not fp: return
        try:
            import openpyxl
            wb = openpyxl.load_workbook(fp)
            ws = wb.active
            records = []
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row): continue
                mgv = str(row[0]).strip() if row[0] is not None else ""
                if mgv.lower() in ['mã', 'magv', 'ma gv', 'stt', 'mã giáo viên', 'mã gv']: continue
                tgv = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
                to_bm = str(row[2]).strip() if len(row) > 2 and row[2] is not None else "Toán"
                role = str(row[3]).strip() if len(row) > 3 and row[3] is not None else "GV"
                chuc_vu = str(row[4]).strip() if len(row) > 4 and row[4] is not None else role
                dm = safe_int(row[5] if len(row) > 5 else None, default=17)

                if mgv and tgv:
                    records.append((mgv, tgv, to_bm, role, chuc_vu, dm, '123456'))

            if not records:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy dữ liệu hợp lệ trong Excel!")
                return

            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.executemany("""
                INSERT INTO giao_vien (magv, tengv, to_bo_mon, role, chuc_vu, dinh_muc_tiet, matkhau)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (magv) DO UPDATE SET 
                    tengv = EXCLUDED.tengv, to_bo_mon = EXCLUDED.to_bo_mon,
                    role = EXCLUDED.role, chuc_vu = EXCLUDED.chuc_vu, dinh_muc_tiet = EXCLUDED.dinh_muc_tiet
            """, records)
            conn.commit()
            cur.close()
            conn.close()
            self.load_data()
            messagebox.showinfo("Thành công", f"Đã nạp thành công {len(records)} giáo viên từ Excel!")
        except Exception as e:
            messagebox.showerror("Lỗi Import Excel", f"Không thể nạp file: {e}")

    def delete_selected_row(self):
        sel = self.tree.selection()
        if not sel: return
        item_vals = self.tree.item(sel[0], "values")
        magv = item_vals[self.all_columns.index('magv')] if 'magv' in self.all_columns else item_vals[0]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa giáo viên mã: {magv}?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM giao_vien WHERE magv = %s", (magv,))
                conn.commit()
                cur.close()
                conn.close()
                self.tree.delete(sel[0])
                messagebox.showinfo("Đã xóa", f"Đã xóa thành công giáo viên {magv}!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")

    def delete_all_rows(self):
        if messagebox.askyesno("CẢNH BÁO", "Hành động này sẽ XÓA SẠCH danh sách giáo viên toàn trường! Tiếp tục?"):
            try:
                conn = psycopg2.connect(DB_URI)
                cur = conn.cursor()
                cur.execute("DELETE FROM giao_vien;")
                conn.commit()
                cur.close()
                conn.close()
                self.load_data()
                messagebox.showinfo("Thành công", "Đã xóa toàn bộ danh sách giáo viên!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi xóa toàn bộ: {e}")