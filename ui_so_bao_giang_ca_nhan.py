# ui_so_bao_giang_ca_nhan.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from config import DB_URI
import service_so_bao_giang as sbg_service
from ui_dieu_chinh_ppct import DieuChinhPPCTWindow

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

C_BORDER      = "#7F8C8D"
C_HEADER_BG   = "#2C3E50"
C_HEADER_FG   = "#FFFFFF"
C_THU_BG      = "#E8F8F5"
C_THU_FG      = "#1A5276"
C_BUOI_BG     = "#FEF9E7"
C_BUOI_FG     = "#7D6608"
C_ROW_EMPTY   = "#FFFFFF"
C_ROW_DAY     = "#F4F6F7"
C_NGHI        = "#FADBD8"
C_NGHI_FG     = "#900C3F"
C_DAY_THAY    = "#FCF3CF"
C_DAY_THAY_FG = "#7D6608"
C_HSG         = "#D4EFDF"
C_HSG_FG      = "#1E8449"

HEADER_HEIGHT = 38
ROW_HEIGHT    = 28

COLUMNS = [
    ("Thứ / Ngày", 115, "center"),
    ("Buổi", 85, "center"),
    ("Tiết", 45, "center"),
    ("Lớp", 65, "center"),
    ("Tiết PPCT", 80, "center"),
    ("Môn học (hoặc PM)", 135, "center"),
    ("Tên bài giảng", 460, "w"),
    ("Trễ / Vượt", 100, "center"),
    ("Ghi chú", 180, "w")
]

class SoBaoGiangCaNhanWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')

        sbg_service.ensure_database_schema(DB_URI)

        self.window = tk.Toplevel()
        self.window.title(f"Sổ Báo Giảng Cá Nhân - {self.tengv}")
        self.window.geometry("1280x720")

        top_frame = tk.Frame(self.window, bg="#F8F9F9", pady=6)
        top_frame.pack(fill=tk.X, padx=15, pady=4)

        tk.Label(top_frame, text="Tuần dạy:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=5)

        self.spn_tuan = ttk.Spinbox(top_frame, from_=1, to=35, width=5, command=self.load_sbg)
        self.spn_tuan.set(1)
        self.spn_tuan.pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="⚙️ ĐIỀU CHỈNH MỐC PPCT (NHẬN LỚP MỚI)", bg="#3498DB", fg="white", 
                  font=("Arial", 9, "bold"), relief="raised", command=self.mo_dieu_chinh_ppct).pack(side=tk.LEFT, padx=10)

        self.lbl_status = tk.Label(top_frame, text="", font=("Arial", 10, "bold"), bg="#F8F9F9")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        table_outer_frame = tk.Frame(self.window)
        table_outer_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.canvas = tk.Canvas(table_outer_frame, bg="white", highlightthickness=0)
        self.v_sb = ttk.Scrollbar(table_outer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_sb = ttk.Scrollbar(table_outer_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(xscrollcommand=self.h_sb.set, yscrollcommand=self.v_sb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_sb.grid(row=0, column=1, sticky="ns")
        self.h_sb.grid(row=1, column=0, sticky="ew")

        table_outer_frame.grid_rowconfigure(0, weight=1)
        table_outer_frame.grid_columnconfigure(0, weight=1)

        self.x_offsets = [0]
        for _, w, _ in COLUMNS:
            self.x_offsets.append(self.x_offsets[-1] + w)
        self.total_table_width = self.x_offsets[-1]
        self.total_table_height = HEADER_HEIGHT + (60 * ROW_HEIGHT)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Double-Button-1>", self._on_double_click_canvas)

        self.current_rows_data = []
        self.load_sbg()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def mo_dieu_chinh_ppct(self):
        DieuChinhPPCTWindow(self.session, callback_refresh=self.load_sbg)

    def load_sbg(self):
        tuan = int(self.spn_tuan.get())
        try:
            # Tính toán hoàn toàn trên bộ nhớ RAM (không gửi request lưu xuống bảng so_bao_giang)
            self.current_rows_data, tong_tiet = sbg_service.lay_du_lieu_bao_giang(
                DB_URI, self.magv, self.to_bm, tuan
            )
            
            # Vẽ lại bảng lên màn hình
            self.render_canvas_table()
            self.lbl_status.config(text=f"Tuần {tuan}: {tong_tiet} tiết", fg="#27AE60")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải Sổ Báo Giảng: {e}")

    def render_canvas_table(self):
        self.canvas.delete("all")
        for c_idx, (col_name, _, _) in enumerate(COLUMNS):
            x1 = self.x_offsets[c_idx]; x2 = self.x_offsets[c_idx + 1]
            self.canvas.create_rectangle(x1, 0, x2, HEADER_HEIGHT, fill=C_HEADER_BG, outline=C_BORDER, width=1)
            self.canvas.create_text((x1 + x2) / 2, HEADER_HEIGHT / 2, text=col_name,
                                    fill=C_HEADER_FG, font=("Arial", 9, "bold"), anchor="center")

        for day_idx in range(6):
            day_start_row = day_idx * 10
            first_item = self.current_rows_data[day_start_row]
            thu_num = first_item['thu_num']
            ngay_str = first_item['ngay'].strftime("%d/%m")

            y_day_top = HEADER_HEIGHT + (day_start_row * ROW_HEIGHT)
            y_day_bottom = y_day_top + (10 * ROW_HEIGHT)

            x_thu1 = self.x_offsets[0]; x_thu2 = self.x_offsets[1]
            self.canvas.create_rectangle(x_thu1, y_day_top, x_thu2, y_day_bottom, fill=C_THU_BG, outline=C_BORDER, width=1)
            mid_y = (y_day_top + y_day_bottom) / 2
            self.canvas.create_text((x_thu1 + x_thu2) / 2, mid_y - 14, text=f"THỨ {thu_num}", fill=C_THU_FG, font=("Arial", 11, "bold"))
            self.canvas.create_line(x_thu1 + 15, mid_y, x_thu2 - 15, mid_y, fill="#A2D9CE", width=1)
            self.canvas.create_text((x_thu1 + x_thu2) / 2, mid_y + 14, text=f"({ngay_str})", fill=C_THU_FG, font=("Arial", 10, "bold"))

            for b_idx, buoi_ten in enumerate(["Buổi sáng", "Buổi chiều"]):
                b_start_row = day_start_row + (b_idx * 5)
                y_b_top = HEADER_HEIGHT + (b_start_row * ROW_HEIGHT)
                y_b_bottom = y_b_top + (5 * ROW_HEIGHT)

                x_b1 = self.x_offsets[1]; x_b2 = self.x_offsets[2]
                self.canvas.create_rectangle(x_b1, y_b_top, x_b2, y_b_bottom, fill=C_BUOI_BG, outline=C_BORDER, width=1)
                self.canvas.create_text((x_b1 + x_b2) / 2, (y_b_top + y_b_bottom) / 2, text=buoi_ten, fill=C_BUOI_FG, font=("Arial", 9, "bold"))

                for t_idx in range(5):
                    data_idx = b_start_row + t_idx
                    r = self.current_rows_data[data_idx]
                    y1 = HEADER_HEIGHT + (data_idx * ROW_HEIGHT)
                    y2 = y1 + ROW_HEIGHT

                    bg_color = C_ROW_EMPTY; fg_color = "#2C3E50"; f_bold = False
                    if r['row_type'] == 'nghi': bg_color = C_NGHI; fg_color = C_NGHI_FG; f_bold = True
                    elif r['row_type'] == 'day_thay': bg_color = C_DAY_THAY; fg_color = C_DAY_THAY_FG; f_bold = True
                    elif r['row_type'] == 'hsg': bg_color = C_HSG; fg_color = C_HSG_FG; f_bold = True
                    elif r['row_type'] in ['day_chinh', 'day_bu']: bg_color = C_ROW_DAY; fg_color = "#000000"; f_bold = True

                    cell_font = ("Arial", 9, "bold") if f_bold else ("Arial", 9)
                    row_values = [
                        (2, r['tiet']), (3, r['lop']), (4, r['tiet_ppct']),
                        (5, r['mon_pm']), (6, r['ten_bai']), (7, r['tre_vuot']), (8, r['chu_y'])
                    ]

                    for col_i, val_text in row_values:
                        cx1 = self.x_offsets[col_i]; cx2 = self.x_offsets[col_i + 1]
                        align = COLUMNS[col_i][2]
                        self.canvas.create_rectangle(cx1, y1, cx2, y2, fill=bg_color, outline=C_BORDER, width=1)
                        if not val_text: continue
                        mid_cell_y = (y1 + y2) / 2
                        cur_fg = fg_color
                        if col_i == 7: cur_fg = "#C0392B" if "Trễ" in val_text else ("#27AE60" if "Vượt" in val_text else fg_color)
                        elif col_i == 8: cur_fg = "#2980B9"

                        if align == "center":
                            self.canvas.create_text((cx1 + cx2) / 2, mid_cell_y, text=val_text, fill=cur_fg, font=cell_font, anchor="center")
                        else:
                            self.canvas.create_text(cx1 + 8, mid_cell_y, text=val_text, fill=cur_fg, font=cell_font, anchor="w")

        self.canvas.configure(scrollregion=(0, 0, self.total_table_width, self.total_table_height))

    def _on_double_click_canvas(self, event):
        canvas_y = self.canvas.canvasy(event.y)
        canvas_x = self.canvas.canvasx(event.x)
        if canvas_y < HEADER_HEIGHT or canvas_y >= self.total_table_height: return
        data_idx = int((canvas_y - HEADER_HEIGHT) // ROW_HEIGHT)
        if 0 <= data_idx < len(self.current_rows_data):
            row_dict = self.current_rows_data[data_idx]
            moi = simpledialog.askstring("Ghi chú", f"Nhập ghi chú:", initialvalue=row_dict['chu_y'])
            if moi is not None:
                row_dict['chu_y'] = moi
                self.render_canvas_table()