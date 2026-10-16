# ui_admin.py
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from config import DB_URI
from doc_tkb import nap_tkb_tu_excel, xoa_toan_bo_tkb
import psycopg2
from window_manager import open_single_window


def get_val(s, k, d=""):
    return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


class AdminWindow:

    def __init__(self, session):
        self.session = session
        self.window = tk.Tk() if not tk._default_root else tk.Toplevel()
        tengv = get_val(session, "tengv", "Quản trị viên")
        self.window.title(
            f"Hệ Thống Quản Trị & Điều Hành - {tengv} [BGH/ADMIN]"
        )
        self.window.geometry("890x750")
        self.window.configure(bg="#f4f6f9")

        self.ensure_cau_hinh_table()

        # ==================== BANNER TIÊU ĐỀ ====================
        f_header = tk.Frame(self.window, bg="#ffffff", relief=tk.RIDGE, bd=1)
        f_header.pack(fill=tk.X, padx=14, pady=(10, 6))

        tk.Label(
            f_header,
            text="TRUNG TÂM QUẢN TRỊ TOÀN TRƯỜNG - BAN GIÁM HIỆU",
            font=("Arial", 14, "bold"),
            fg="#b03a2e",
            bg="#ffffff",
        ).pack(pady=(10, 3))

        tk.Label(
            f_header,
            text=f"Xin chào: {tengv}   |   Quyền hạn: BGH/ADMIN",
            font=("Arial", 10, "italic"),
            fg="#5d6d7e",
            bg="#ffffff",
        ).pack(pady=(0, 9))

        # ==================== KHỐI 1: CÔNG VIỆC CÁ NHÂN ====================
        gr_ca_nhan = tk.LabelFrame(
            self.window,
            text="  📌 Công Việc Giảng Dạy Cá Nhân (Nghĩa vụ BGH)  ",
            font=("Arial", 10, "bold"),
            fg="#1b4f72",
            bg="#ffffff",
            padx=10,
            pady=8,
            relief=tk.GROOVE,
        )
        gr_ca_nhan.pack(fill=tk.X, padx=14, pady=4)

        tk.Button(
            gr_ca_nhan,
            text="📅 1. TKB Cá Nhân",
            width=13,
            height=1,
            bg="#ebf5fb",
            fg="#1b4f72",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_tkb_ca_nhan,
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            gr_ca_nhan,
            text="📖 2. Sổ Báo Giảng",
            width=14,
            height=1,
            bg="#e8f8f5",
            fg="#117864",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_sbg_ca_nhan,
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            gr_ca_nhan,
            text="📊 3. Kê Khai Giờ",
            width=13,
            height=1,
            bg="#fef5e7",
            fg="#b9770e",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_pkg_ca_nhan,
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            gr_ca_nhan,
            text="📝 4. Biến Động Lịch Dạy",
            width=17,
            height=1,
            bg="#fef9e7",
            fg="#7d6608",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_bien_dong_ca_nhan,
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            gr_ca_nhan,
            text="🔑 Đổi Mật Khẩu",
            width=13,
            height=1,
            bg="#fdfefe",
            fg="#784212",
            font=("Arial", 9, "bold"),
            relief=tk.GROOVE,
            cursor="hand2",
            command=self.open_doi_mat_khau,
        ).pack(side=tk.RIGHT, padx=3)

        # ==================== KHỐI 2: CẤU HÌNH NĂM HỌC ====================
        gr_cau_hinh = tk.LabelFrame(
            self.window,
            text="  ⚙️ Cài Đặt Thông Số Năm Học (Chỉ cài 1 lần đầu năm)  ",
            font=("Arial", 10, "bold"),
            fg="#4a235a",
            bg="#ffffff",
            padx=12,
            pady=8,
            relief=tk.GROOVE,
        )
        gr_cau_hinh.pack(fill=tk.X, padx=14, pady=4)

        tk.Label(
            gr_cau_hinh,
            text="Ngày bắt đầu năm học (Thứ 2 Tuần 1 - YYYY-MM-DD):",
            font=("Arial", 9),
            bg="#ffffff",
        ).pack(side=tk.LEFT, padx=5)

        self.txt_ngay_bd = tk.Entry(
            gr_cau_hinh,
            width=14,
            font=("Consolas", 10, "bold"),
            justify="center",
        )
        self.txt_ngay_bd.pack(side=tk.LEFT, padx=6)

        tk.Button(
            gr_cau_hinh,
            text="💾 Lưu Cài Đặt",
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.luu_ngay_bat_dau,
        ).pack(side=tk.LEFT, padx=8)

        self.load_ngay_bat_dau()

        # ==================== KHỐI 3: QUẢN TRỊ NHÂN SỰ ====================
        gr_quan_tri = tk.LabelFrame(
            self.window,
            text="  👥 Quản Lý Nhân Sự & Giám Sát Chuyên Môn Toàn Trường  ",
            font=("Arial", 10, "bold"),
            fg="#117864",
            bg="#ffffff",
            padx=10,
            pady=8,
            relief=tk.GROOVE,
        )
        gr_quan_tri.pack(fill=tk.X, padx=14, pady=4)

        tk.Button(
            gr_quan_tri,
            text="👥 4. Quản lý Danh sách Giáo viên (Thêm / Xóa / Excel)",
            width=45,
            height=2,
            bg="#ebf5fb",
            fg="#1b4f72",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_quan_ly_gv,
        ).grid(row=0, column=0, padx=6, pady=4)

        tk.Button(
            gr_quan_tri,
            text="📝 5. Giám sát & Xóa đơn Nghỉ / Dạy bù Toàn trường",
            width=45,
            height=2,
            bg="#fef9e7",
            fg="#7d6608",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_quan_ly_bien_dong,
        ).grid(row=0, column=1, padx=6, pady=4)

        tk.Button(
            gr_quan_tri,
            text="📈 6. Bảng Thống Kê & Đối Chiếu Giờ Dạy Toàn Trường",
            width=94,
            height=2,
            bg="#e8f8f5",
            fg="#0e6251",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.open_thong_ke_gio,
        ).grid(row=1, column=0, columnspan=2, padx=6, pady=4)

        # ==================== KHỐI 4: NHẬP VÀ XÓA TKB ====================
        gr_tkb = tk.LabelFrame(
            self.window,
            text="  📅 Quản Lý & Nhập Thời Khóa Biểu Toàn Trường Từ Excel  ",
            font=("Arial", 10, "bold"),
            fg="#b03a2e",
            bg="#ffffff",
            padx=12,
            pady=8,
            relief=tk.GROOVE,
        )
        gr_tkb.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        f_tkb_top = tk.Frame(gr_tkb, bg="#ffffff")
        f_tkb_top.pack(fill=tk.X, pady=(2, 6))

        tk.Button(
            f_tkb_top,
            text="🗑️ XÓA SẠCH TOÀN BỘ TKB TRÊN SERVER",
            bg="#c0392b",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.xoa_sach_tkb,
        ).pack(fill=tk.X)

        f_tkb_mid = tk.Frame(
            gr_tkb, bg="#f8f9f9", relief=tk.SOLID, bd=1, padx=8, pady=8
        )
        f_tkb_mid.pack(fill=tk.X, pady=4)

        tk.Button(
            f_tkb_mid,
            text="📁 Chọn file Excel...",
            bg="#2980b9",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            cursor="hand2",
            command=self.chon_file_tkb,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_file = tk.Label(
            f_tkb_mid,
            text="(Chưa chọn file)",
            fg="#7f8c8d",
            bg="#f8f9f9",
            font=("Arial", 9, "italic"),
            width=22,
            anchor="w",
        )
        self.lbl_file.pack(side=tk.LEFT, padx=2)

        tk.Button(
            f_tkb_mid,
            text="📥 Tiến hành Import",
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.import_tkb,
        ).pack(side=tk.RIGHT, padx=4)

        self.txt_ngay_ad = tk.Entry(
            f_tkb_mid, width=12, font=("Consolas", 9, "bold"), justify="center"
        )
        self.txt_ngay_ad.pack(side=tk.RIGHT, padx=6)
        tk.Label(
            f_tkb_mid,
            text="Từ Ngày:",
            font=("Arial", 9, "bold"),
            fg="#2c3e50",
            bg="#f8f9f9",
        ).pack(side=tk.RIGHT, padx=2)

        self.spn_tuan = ttk.Spinbox(
            f_tkb_mid,
            from_=1,
            to=45,
            width=4,
            font=("Arial", 9, "bold"),
            justify="center",
            command=self.on_change_tuan,
        )
        self.spn_tuan.set(1)
        self.spn_tuan.bind("<KeyRelease>", lambda e: self.on_change_tuan())
        self.spn_tuan.pack(side=tk.RIGHT, padx=6)
        tk.Label(
            f_tkb_mid,
            text="Áp dụng Tuần:",
            font=("Arial", 9, "bold"),
            fg="#c0392b",
            bg="#f8f9f9",
        ).pack(side=tk.RIGHT, padx=2)

        self.txt_log = tk.Text(
            gr_tkb,
            height=5,
            font=("Consolas", 9),
            bg="#1c2833",
            fg="#58d68d",
            insertbackground="white",
            relief=tk.SUNKEN,
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=(5, 2))
        self.txt_log.insert(tk.END, ">>> Sẵn sàng nhập Thời khóa biểu...\n")

        self.selected_tkb_file = ""
        self.on_change_tuan()

    def on_change_tuan(self):
        try:
            tuan = int(self.spn_tuan.get())
            ngay_bd_str = self.txt_ngay_bd.get().strip()
            base_date = datetime.strptime(ngay_bd_str, "%Y-%m-%d").date()
            ngay_ad = base_date + timedelta(days=(tuan - 1) * 7)
            self.txt_ngay_ad.delete(0, tk.END)
            self.txt_ngay_ad.insert(0, ngay_ad.strftime("%Y-%m-%d"))
        except Exception:
            pass

    def ensure_cau_hinh_table(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS cau_hinh (khoa VARCHAR(50) PRIMARY"
                " KEY, gia_tri TEXT);"
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass

    def load_ngay_bat_dau(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "SELECT gia_tri FROM cau_hinh WHERE khoa ="
                " 'ngay_bat_dau_nam_hoc'"
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                self.txt_ngay_bd.insert(0, row[0])
            else:
                self.txt_ngay_bd.insert(0, "2026-09-07")
        except Exception:
            self.txt_ngay_bd.delete(0, tk.END)
            self.txt_ngay_bd.insert(0, "2026-09-07")

    def luu_ngay_bat_dau(self):
        ngay = self.txt_ngay_bd.get().strip()
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO cau_hinh (khoa, gia_tri) VALUES ('ngay_bat_dau_nam_hoc', %s)
                ON CONFLICT (khoa) DO UPDATE SET gia_tri = EXCLUDED.gia_tri
            """,
                (ngay,),
            )
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo(
                "Thành công", f"Đã lưu ngày bắt đầu năm học: {ngay}"
            )
            self.on_change_tuan()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")

    # =========================================================================
    # CÁC HÀM MỞ CỬA SỔ CỦA ADMIN: CHỐNG MỞ TRÙNG 100%
    # =========================================================================
    def open_tkb_ca_nhan(self):
        from ui_xem_tkb import XemTKBWindow

        open_single_window("WIN_TKB", XemTKBWindow, self.session)

    def open_sbg_ca_nhan(self):
        from ui_so_bao_giang_ca_nhan import SoBaoGiangCaNhanWindow

        open_single_window(
            "WIN_BAO_GIANG", SoBaoGiangCaNhanWindow, self.session
        )

    def open_pkg_ca_nhan(self):
        from ui_pkg import PkgWindow

        open_single_window("WIN_PKG", PkgWindow, self.session)

    def open_bien_dong_ca_nhan(self):
        from ui_bien_dong_lich_day import BienDongLichDayWindow

        open_single_window("WIN_BIEN_DONG", BienDongLichDayWindow, self.session)

    def open_doi_mat_khau(self):
        from ui_doi_mat_khau import DoiMatKhauWindow

        open_single_window(
            "WIN_ADMIN_DOI_MK", DoiMatKhauWindow, self.session, self.window
        )

    def open_quan_ly_gv(self):
        from ui_quan_ly_giao_vien import QuanLyGiaoVienWindow

        open_single_window("WIN_QUAN_LY_GV", QuanLyGiaoVienWindow, self.session)

    def open_quan_ly_bien_dong(self):
        from ui_admin_quan_ly_bien_dong import AdminQuanLyBienDongWindow

        open_single_window(
            "WIN_QUAN_LY_BIEN_DONG", AdminQuanLyBienDongWindow, self.session
        )

    def open_thong_ke_gio(self):
        from ui_admin_thong_ke_gio import AdminThongKeGioWindow

        open_single_window(
            "WIN_ADMIN_THONG_KE_GIO", AdminThongKeGioWindow, self.session
        )

    def chon_file_tkb(self):
        fp = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if fp:
            self.selected_tkb_file = fp
            filename = fp.replace("\\", "/").split("/")[-1]
            self.lbl_file.config(
                text=filename, fg="#1b4f72", font=("Arial", 9, "bold")
            )
            self.txt_log.insert(tk.END, f"📁 Đã chọn file: {filename}\n")
            self.txt_log.see(tk.END)

    def import_tkb(self):
        from doc_tkb import kiem_tra_tuan_ton_tai

        if not self.selected_tkb_file:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn file Excel TKB trước khi import!"
            )
            return

        try:
            tuan_val = int(self.spn_tuan.get().strip())
        except ValueError:
            messagebox.showwarning(
                "Cảnh báo", "Số tuần áp dụng phải là một số nguyên hợp lệ!"
            )
            return

        ngay_val = self.txt_ngay_ad.get().strip()
        if not ngay_val:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng nhập ngày áp dụng (YYYY-MM-DD)!"
            )
            return

        so_tiet_cu = kiem_tra_tuan_ton_tai(tuan_val)
        if so_tiet_cu > 0:
            tra_loi = messagebox.askyesno(
                "Xác nhận ghi đè",
                f"⚠️ CẢNH BÁO: Tuần {tuan_val} hiện đã có {so_tiet_cu} tiết học"
                " trong cơ sở dữ liệu!\n\nBạn có muốn XÓA BẢN CŨ VÀ DÁN ĐÈ bản"
                f" mới này lên Tuần {tuan_val} không?",
            )
            if not tra_loi:
                self.txt_log.insert(
                    tk.END,
                    f"⛔ Đã hủy Import Tuần {tuan_val} (Giữ nguyên dữ liệu"
                    " cũ).\n",
                )
                self.txt_log.see(tk.END)
                return

        try:
            self.txt_log.insert(
                tk.END,
                f"⏳ Đang xử lý bóc tách TKB áp dụng từ Tuần {tuan_val} (Ngày:"
                f" {ngay_val})...\n",
            )
            self.window.update_idletasks()

            kq = nap_tkb_tu_excel(
                self.selected_tkb_file,
                ap_dung_tu_tuan=tuan_val,
                ap_dung_tu_ngay=ngay_val,
            )

            if isinstance(kq, tuple):
                success, msg = kq
            else:
                success, msg = (
                    True,
                    f"Bóc tách thành công (Áp dụng từ Tuần {tuan_val})!",
                )

            if success:
                messagebox.showinfo("Thành công", msg)
                self.txt_log.insert(tk.END, f"✅ {msg}\n")
            else:
                messagebox.showerror("Lỗi", msg)
                self.txt_log.insert(tk.END, f"❌ {msg}\n")

            self.txt_log.see(tk.END)
        except Exception as e:
            messagebox.showerror("Lỗi Import", f"Lỗi thực thi: {e}")
            self.txt_log.insert(tk.END, f"❌ Ngoại lệ: {e}\n")
            self.txt_log.see(tk.END)

    def xoa_sach_tkb(self):
        if messagebox.askyesno(
            "CẢNH BÁO",
            "Bạn có chắc chắn muốn XÓA SẠCH toàn bộ Thời khóa biểu trên server?",
        ):
            try:
                success, msg = xoa_toan_bo_tkb()
                if success:
                    messagebox.showinfo("Đã xóa", msg)
                    self.txt_log.insert(tk.END, f"⚠️ {msg}\n")
                else:
                    messagebox.showerror("Lỗi", msg)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa TKB: {e}")

    def run(self):
        self.window.mainloop()