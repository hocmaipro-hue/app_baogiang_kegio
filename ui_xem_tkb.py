# ui_xem_tkb.py
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): 
    return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

# BẢNG MÀU CHUẨN EXCEL - TƯƠNG PHẢN CAO
C_BORDER      = "#7F8C8D"   # Viền ô kẻ bảng xám đậm rõ nét
C_HEADER_BG   = "#2C3E50"   # Nền tiêu đề: Xanh than đậm
C_HEADER_FG   = "#FFFFFF"   # Chữ tiêu đề: Trắng in đậm
C_SELECT_OUT  = "#1B4F72"   # Viền ô khi được chọn: Xanh đậm sắc nét

# PALETTE NỀN PASTEL SÁNG, ĐI KÈM CHỮ ĐEN ĐẬM SẮC NÉT
CLASS_PALETTE = [
    {"bg": "#EBF5FB", "badge": "#AED6F1"},  # Xanh dương pastel
    {"bg": "#E8F8F5", "badge": "#A2D9CE"},  # Xanh ngọc pastel
    {"bg": "#FEF9E7", "badge": "#F9E79F"},  # Vàng kem pastel
    {"bg": "#FDF2E9", "badge": "#F5CBA7"},  # Cam đào pastel
    {"bg": "#F4ECF7", "badge": "#D7BDE2"},  # Tím pastel
    {"bg": "#EAFAF1", "badge": "#A9DFBF"},  # Xanh lá mạ
    {"bg": "#FDEDEC", "badge": "#FADBD8"},  # Hồng phấn
]

HEADER_HEIGHT = 38
ROW_HEIGHT    = 34   # Tăng chiều cao để chữ đậm hiển thị thoáng và đẹp

COLUMNS = [
    ("ID", 65, "center"),
    ("Thứ", 75, "center"),
    ("Buổi", 85, "center"),
    ("Tiết", 60, "center"),
    ("Lớp", 100, "center"),
    ("Môn học", 185, "w"),
    ("Phân môn (Đại số / Hình học / Chuyên đề...)", 325, "w")
]

class XemTKBWindow:
    def __init__(self, session):
        self.session = session
        self.window = tk.Toplevel()
        self.window.title("Thời Khóa Biểu & Gán Phân Môn")
        self.window.geometry("1060x650")
        self.window.configure(bg="#F4F6F9")

        to_bm = get_val(session, 'to_bo_mon', '')
        magv_hien_tai = get_val(session, 'magv', '')

        # ==================== THANH CÔNG CỤ TRÊN CÙNG ====================
        top_frame = tk.Frame(self.window, bg="#FFFFFF", padx=15, pady=10, relief=tk.SOLID, bd=1)
        top_frame.pack(fill=tk.X, padx=15, pady=(10, 6))

        tk.Label(top_frame, text="👤 Giáo viên:", font=("Arial", 10, "bold"), bg="#FFFFFF", fg="#2C3E50").pack(side=tk.LEFT, padx=(5, 4))
        self.cbo_gv = ttk.Combobox(top_frame, width=26, state="readonly", font=("Arial", 9, "bold"))
        self.cbo_gv.pack(side=tk.LEFT, padx=5)
        self.cbo_gv.bind("<<ComboboxSelected>>", lambda e: self.load_tkb())

        tk.Label(top_frame, text="📅 Đợt TKB:", font=("Arial", 10, "bold"), fg="#C0392B", bg="#FFFFFF").pack(side=tk.LEFT, padx=(25, 4))
        self.cbo_tuan = ttk.Combobox(top_frame, width=24, state="readonly", font=("Arial", 9, "bold"))
        self.cbo_tuan.pack(side=tk.LEFT, padx=5)
        self.cbo_tuan.bind("<<ComboboxSelected>>", lambda e: self.load_tkb())

        self.lbl_note = tk.Label(top_frame, text="💡 Nhấp chọn dòng để đổi Phân môn", font=("Arial", 9, "bold", "italic"), fg="#D35400", bg="#FFFFFF")
        self.lbl_note.pack(side=tk.RIGHT, padx=10)

        # ==================== BẢNG LƯỚI EXCEL BẰNG CANVAS ====================
        table_outer = tk.Frame(self.window, bg="#FFFFFF")
        table_outer.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(table_outer, bg="white", highlightthickness=0)
        self.v_sb = ttk.Scrollbar(table_outer, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_sb = ttk.Scrollbar(table_outer, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_sb.set, yscrollcommand=self.v_sb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_sb.grid(row=0, column=1, sticky="ns")
        self.h_sb.grid(row=1, column=0, sticky="ew")

        table_outer.grid_rowconfigure(0, weight=1)
        table_outer.grid_columnconfigure(0, weight=1)

        self.x_offsets = [0]
        for _, w, _ in COLUMNS:
            self.x_offsets.append(self.x_offsets[-1] + w)
        self.total_table_width = self.x_offsets[-1]

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canvas.bind("<Button-1>", self.on_click_canvas)

        # ==================== KHUNG GÁN PHÂN MÔN TRỰC TIẾP ====================
        bottom_frame = tk.LabelFrame(
            self.window, 
            text=" Gán Phân Môn cho tiết đang chọn ", 
            font=("Arial", 10, "bold"), 
            fg="#1A5276",
            bg="#FFFFFF", 
            padx=12, 
            pady=10,
            relief=tk.SOLID,
            bd=1
        )
        bottom_frame.pack(fill=tk.X, padx=15, pady=(6, 12))

        self.lbl_selected = tk.Label(
            bottom_frame, 
            text="👉 Bấm chọn một dòng trên bảng để gán phân môn", 
            fg="#7F8C8D", 
            bg="#FFFFFF", 
            font=("Arial", 9, "bold", "italic")
        )
        self.lbl_selected.pack(side=tk.LEFT, padx=5)

        tk.Label(bottom_frame, text=" | Phân môn: ", font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#2C3E50").pack(side=tk.LEFT, padx=(12, 2))
        
        self.cbo_phan_mon = ttk.Combobox(bottom_frame, width=20, state="readonly", font=("Arial", 9, "bold"))
        self.cbo_phan_mon.pack(side=tk.LEFT, padx=5)

        tk.Button(
            bottom_frame, text="💾 Lưu Phân Môn", bg="#27AE60", fg="white", 
            font=("Arial", 9, "bold"), padx=14, pady=3, relief=tk.RAISED, cursor="hand2",
            activebackground="#219955", activeforeground="white",
            command=self.save_phan_mon
        ).pack(side=tk.LEFT, padx=15)

        self.current_rows = []
        self.selected_idx = None
        self.all_phan_mon = []
        self.lop_color_map = {}

        self.load_tat_ca_phan_mon()
        self.load_danh_sach_dot_tkb()
        self.load_danh_sach_gv(to_bm, magv_hien_tai)

    def load_tat_ca_phan_mon(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT phan_mon 
                FROM phan_phoi_chuong_trinh 
                WHERE phan_mon IS NOT NULL AND TRIM(phan_mon) != ''
                ORDER BY phan_mon ASC;
            """)
            self.all_phan_mon = [r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()]
            cur.close(); conn.close()

            self.cbo_phan_mon['values'] = self.all_phan_mon
            if self.all_phan_mon:
                self.cbo_phan_mon.current(0)
        except Exception as e:
            print("Lỗi tải phân môn:", e)

    def get_phan_mon_theo_mon(self, mon_hoc):
        if not mon_hoc: return self.all_phan_mon
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT phan_mon 
                FROM phan_phoi_chuong_trinh 
                WHERE (UPPER(TRIM(mon)) = UPPER(TRIM(%s)) OR %s ILIKE '%%' || mon || '%%')
                  AND phan_mon IS NOT NULL AND TRIM(phan_mon) != ''
                ORDER BY phan_mon ASC;
            """, (mon_hoc, mon_hoc))
            ds = [r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()]
            cur.close(); conn.close()
            if ds: return ds
        except Exception: pass
        return self.all_phan_mon

    def load_danh_sach_dot_tkb(self):
        self.tuan_dict = {}
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'thoi_khoa_bieu';")
            cols = set(r[0] for r in cur.fetchall())
            col_ngay = '"ap_dung_từ_ngay"' if 'ap_dung_từ_ngay' in cols else ('ap_dung_tu_ngay' if 'ap_dung_tu_ngay' in cols else 'NULL')

            cur.execute(f"""
                SELECT DISTINCT ap_dung_tu_tuan, MIN({col_ngay})
                FROM thoi_khoa_bieu
                WHERE ap_dung_tu_tuan IS NOT NULL
                GROUP BY ap_dung_tu_tuan
                ORDER BY ap_dung_tu_tuan ASC
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()

            vals = []
            for r in rows:
                tuan = r[0]; ngay = r[1]
                label = f"Tuần {tuan} (từ {ngay.strftime('%d/%m/%Y')})" if (ngay and hasattr(ngay, 'strftime')) else f"Tuần {tuan}"
                self.tuan_dict[label] = tuan
                vals.append(label)

            self.cbo_tuan['values'] = vals
            if vals:
                self.cbo_tuan.current(len(vals) - 1)
        except Exception as e:
            print("Lỗi tải đợt TKB:", e)

    def load_danh_sach_gv(self, to_bm, magv_hien_tai):
        self.gv_dict = {}
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            if to_bm:
                cur.execute("SELECT magv, tengv FROM giao_vien WHERE to_bo_mon = %s ORDER BY tengv", (to_bm,))
            else:
                cur.execute("SELECT magv, tengv FROM giao_vien ORDER BY to_bo_mon, tengv")
            rows = cur.fetchall()
            cur.close(); conn.close()

            vals = []
            selected_idx = 0
            for idx, (mgv, tgv) in enumerate(rows):
                label = f"{tgv} ({mgv})"
                self.gv_dict[label] = mgv
                vals.append(label)
                if mgv == magv_hien_tai: selected_idx = idx

            self.cbo_gv['values'] = vals
            if vals:
                self.cbo_gv.current(selected_idx)
                self.load_tkb()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách GV: {e}")

    def load_tkb(self):
        selected_label = self.cbo_gv.get()
        magv = self.gv_dict.get(selected_label)
        if not magv: return

        selected_tuan_label = self.cbo_tuan.get()
        tuan = self.tuan_dict.get(selected_tuan_label)
        self.selected_idx = None

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            if tuan is not None:
                cur.execute("""
                    SELECT id, thu, buoi, tiet, lop, mon, COALESCE(phan_mon, '')
                    FROM thoi_khoa_bieu 
                    WHERE magv = %s AND ap_dung_tu_tuan = %s
                    ORDER BY thu ASC, CASE WHEN buoi = 'Sáng' THEN 1 ELSE 2 END ASC, tiet ASC
                """, (magv, tuan))
            else:
                cur.execute("""
                    SELECT id, thu, buoi, tiet, lop, mon, COALESCE(phan_mon, '')
                    FROM thoi_khoa_bieu 
                    WHERE magv = %s 
                    ORDER BY thu ASC, CASE WHEN buoi = 'Sáng' THEN 1 ELSE 2 END ASC, tiet ASC
                """, (magv,))

            self.current_rows = [list(r) for r in cur.fetchall()]
            cur.close(); conn.close()

            self.lop_color_map.clear()
            unique_classes = []
            for r in self.current_rows:
                lop_name = str(r[4]).strip()
                if lop_name and lop_name not in unique_classes:
                    unique_classes.append(lop_name)

            for idx, c_name in enumerate(unique_classes):
                self.lop_color_map[c_name] = CLASS_PALETTE[idx % len(CLASS_PALETTE)]

            self.render_canvas_table()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải TKB: {e}")

    def render_canvas_table(self):
        """Vẽ toàn bộ bảng với chữ ĐẬM ĐEN TƯƠNG PHẢN CAO"""
        self.canvas.delete("all")

        # 1. Vẽ hàng tiêu đề
        for c_idx, (col_name, _, _) in enumerate(COLUMNS):
            x1 = self.x_offsets[c_idx]
            x2 = self.x_offsets[c_idx + 1]
            self.canvas.create_rectangle(x1, 0, x2, HEADER_HEIGHT, fill=C_HEADER_BG, outline=C_BORDER, width=1)
            self.canvas.create_text((x1 + x2) / 2, HEADER_HEIGHT / 2, text=col_name,
                                    fill=C_HEADER_FG, font=("Arial", 10, "bold"), anchor="center")

        total_rows = len(self.current_rows)
        if total_rows == 0:
            self.canvas.create_text(self.total_table_width / 2, 80, text="Không có tiết dạy nào trong đợt TKB này",
                                    fill="#5D6D7E", font=("Arial", 11, "bold", "italic"))
            self.canvas.configure(scrollregion=(0, 0, self.total_table_width, 150))
            return

        total_h = HEADER_HEIGHT + (total_rows * ROW_HEIGHT)

        # 2. Vẽ từng dòng dữ liệu với chữ ĐẬM
        for r_idx, r in enumerate(self.current_rows):
            y1 = HEADER_HEIGHT + (r_idx * ROW_HEIGHT)
            y2 = y1 + ROW_HEIGHT

            lop_name = str(r[4]).strip()
            mon_val  = str(r[5]).strip()
            pm_val   = str(r[6]).strip()

            if mon_val in ['SHDC', 'SHL']:
                row_bg = "#F2F4F4"
                badge_bg = "#E5E7E9"
                text_fg = "#566573" # Xám đậm cho tiết sinh hoạt
            elif lop_name in self.lop_color_map:
                c_style = self.lop_color_map[lop_name]
                row_bg = c_style["bg"]
                badge_bg = c_style["badge"]
                text_fg = "#17202A" # Đen tuyền sắc nét
            else:
                row_bg = "#FFFFFF"
                badge_bg = "#EAECEE"
                text_fg = "#17202A"

            is_selected = (r_idx == self.selected_idx)

            for col_i, (c_name, _, align) in enumerate(COLUMNS):
                cx1 = self.x_offsets[col_i]
                cx2 = self.x_offsets[col_i + 1]

                cell_bg = badge_bg if col_i == 4 else row_bg
                self.canvas.create_rectangle(cx1, y1, cx2, y2, fill=cell_bg, outline=C_BORDER, width=1)

                val_text = str(r[col_i])
                font_cell = ("Arial", 9, "bold") # TOÀN BỘ CHỮ ĐỀU IN ĐẬM
                cur_fg = text_fg

                # Điểm nhấn cho cột ID, Thứ, Tiết, Lớp
                if col_i == 0:
                    cur_fg = "#566573"
                elif col_i == 4:
                    font_cell = ("Arial", 10, "bold") # Tên lớp to đậm hơn một chút
                    cur_fg = "#0E6251" if lop_name in self.lop_color_map else "#17202A"

                # Điểm nhấn cột Phân môn
                if col_i == 6:
                    if not pm_val and mon_val not in ['SHDC', 'SHL']:
                        val_text = "⚠️ (Chưa gán phân môn)"
                        cur_fg = "#C0392B" # Đỏ tươi đậm nét
                        font_cell = ("Arial", 9, "bold", "italic")
                    else:
                        cur_fg = "#154360" # Xanh than đậm
                        font_cell = ("Arial", 9, "bold")

                mid_y = (y1 + y2) / 2
                if align == "center":
                    self.canvas.create_text((cx1 + cx2) / 2, mid_y, text=val_text, fill=cur_fg, font=font_cell, anchor="center")
                else:
                    self.canvas.create_text(cx1 + 12, mid_y, text=val_text, fill=cur_fg, font=font_cell, anchor="w")

            # Khung viền xanh đậm dày 3px khi được chọn
            if is_selected:
                self.canvas.create_rectangle(self.x_offsets[0] + 1, y1 + 1, self.total_table_width - 1, y2 - 1,
                                             outline=C_SELECT_OUT, width=3)

        self.canvas.configure(scrollregion=(0, 0, self.total_table_width, total_h))

    def on_click_canvas(self, event):
        canvas_y = self.canvas.canvasy(event.y)
        if canvas_y < HEADER_HEIGHT: return

        r_idx = int((canvas_y - HEADER_HEIGHT) // ROW_HEIGHT)
        if 0 <= r_idx < len(self.current_rows):
            self.selected_idx = r_idx
            self.render_canvas_table()
            self.on_select_row_data(self.current_rows[r_idx])

    def on_select_row_data(self, item):
        self.current_id = item[0]
        thu = item[1]
        buoi = item[2]
        tiet = item[3]
        lop = item[4]
        mon = item[5]
        pm_cu = item[6]

        self.lbl_selected.config(
            text=f"👉 Đang chọn: Thứ {thu} ({buoi}) - Tiết {tiet} [Lớp: {lop} | Môn: {mon}]", 
            fg="#1A5276", 
            font=("Arial", 9, "bold")
        )

        ds_phan_mon_theo_mon = self.get_phan_mon_theo_mon(mon)
        self.cbo_phan_mon['values'] = ds_phan_mon_theo_mon

        if pm_cu and pm_cu in ds_phan_mon_theo_mon:
            self.cbo_phan_mon.set(pm_cu)
        elif ds_phan_mon_theo_mon:
            self.cbo_phan_mon.set(ds_phan_mon_theo_mon[0])

    def save_phan_mon(self):
        if self.selected_idx is None or not self.current_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhấp chọn một dòng tiết dạy trên bảng trước!")
            return

        phan_mon_moi = self.cbo_phan_mon.get().strip()
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("UPDATE thoi_khoa_bieu SET phan_mon = %s WHERE id = %s", (phan_mon_moi, self.current_id))
            conn.commit()
            cur.close(); conn.close()

            self.current_rows[self.selected_idx][6] = phan_mon_moi
            self.render_canvas_table()

            messagebox.showinfo("Thành công", f"Đã lưu phân môn: {phan_mon_moi}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu phân môn: {e}")