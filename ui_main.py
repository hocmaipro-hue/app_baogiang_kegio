# ui_main.py - DÀNH RIÊNG CHO GIÁO VIÊN THƯỜNG
import tkinter as tk
from window_manager import open_single_window


class MainWindow:

    def __init__(self, session):
        self.session = session
        self.root = tk.Tk()
        self.root.title(
            f"Quản Lý Báo Giảng - {session.get('tengv')} [GIÁO VIÊN]"
        )
        self.root.geometry("520x530")
        self.root.resizable(False, False)

        # Lời chào
        tk.Label(
            self.root,
            text=f"Phong xin chào Thầy/Cô: {session.get('tengv')}",
            font=("Arial", 13, "bold"),
            fg="#1a5276",
        ).pack(pady=(15, 2))
        tk.Label(
            self.root,
            text=f"Tổ bộ môn: {session.get('to_bo_mon')}",
            font=("Arial", 11, "italic"),
            fg="#555",
        ).pack(pady=(0, 10))

        # Khung chứa các nút chức năng của Giáo viên
        frame_btn = tk.LabelFrame(
            self.root,
            text=" CHỨC NĂNG GIẢNG DẠY ",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=10,
        )
        frame_btn.pack(fill=tk.BOTH, expand=True, padx=25, pady=5)

        # 1. Xem TKB cá nhân
        tk.Button(
            frame_btn,
            text="📅 1. Xem Thời khóa biểu cá nhân",
            font=("Arial", 10),
            height=1,
            command=self.open_tkb,
        ).pack(fill=tk.X, pady=3)

        # 2. BÁO NGHỈ DẠY (CÓ NGHỈ TẾT)
        tk.Button(
            frame_btn,
            text="⛔ 2. Báo Nghỉ dạy (Nghỉ việc riêng / Nghỉ Tết)",
            font=("Arial", 10, "bold"),
            height=1,
            bg="#fadbd8",
            fg="#900c3f",
            relief="groove",
            command=self.open_bao_nghi,
        ).pack(fill=tk.X, pady=3)

        # 3. ĐĂNG KÝ DẠY BÙ
        tk.Button(
            frame_btn,
            text="🟢 3. Đăng ký Dạy Bù",
            font=("Arial", 10, "bold"),
            height=1,
            bg="#d4efdf",
            fg="#1e8449",
            relief="groove",
            command=self.open_day_bu,
        ).pack(fill=tk.X, pady=3)

        # 4. ĐĂNG KÝ DẠY THAY & BDHSG
        tk.Button(
            frame_btn,
            text="🟡 4. Đăng ký Dạy Thay & Bồi Dưỡng HSG",
            font=("Arial", 10, "bold"),
            height=1,
            bg="#fcf3cf",
            fg="#7d6608",
            relief="groove",
            command=self.open_day_thay,
        ).pack(fill=tk.X, pady=3)

        # 5. Sổ báo giảng cá nhân
        tk.Button(
            frame_btn,
            text="📖 5. Quản lý Sổ Báo Giảng cá nhân",
            font=("Arial", 10, "bold"),
            height=1,
            bg="#e8f8f5",
            fg="#1a5276",
            command=self.open_bao_giang,
        ).pack(fill=tk.X, pady=3)

        # 6. Kê khai giờ dạy
        tk.Button(
            frame_btn,
            text="📊 6. Xem Kê khai giờ (PKG cá nhân)",
            font=("Arial", 10),
            height=1,
            command=self.open_pkg,
        ).pack(fill=tk.X, pady=3)

        # Nút Đổi mật khẩu
        tk.Button(
            self.root,
            text="🔑 Đổi mật khẩu",
            bg="#f2f3f4",
            font=("Arial", 9, "bold"),
            command=self.open_doi_mat_khau,
        ).pack(pady=8)

    # =========================================================================
    # CÁC HÀM MỞ CỬA SỔ: CHỐNG MỞ TRÙNG 100% VÀ LUÔN NỔI LÊN TRÊN CÙNG
    # =========================================================================
    def open_tkb(self):
        from ui_xem_tkb import XemTKBWindow

        open_single_window("WIN_TKB", XemTKBWindow, self.session)

    def open_bao_nghi(self):
        from ui_bao_nghi import BaoNghiWindow

        open_single_window("WIN_BAO_NGHI", BaoNghiWindow, self.session)

    def open_day_bu(self):
        from ui_day_bu import DayBuWindow

        open_single_window("WIN_DAY_BU", DayBuWindow, self.session)

    def open_day_thay(self):
        from ui_day_thay_hsg import DayThayHSGWindow

        open_single_window("WIN_DAY_THAY", DayThayHSGWindow, self.session)

    def open_bao_giang(self):
        from ui_so_bao_giang_ca_nhan import SoBaoGiangCaNhanWindow

        open_single_window(
            "WIN_BAO_GIANG", SoBaoGiangCaNhanWindow, self.session
        )

    def open_pkg(self):
        from ui_pkg import PkgWindow

        open_single_window("WIN_PKG", PkgWindow, self.session)

    def open_doi_mat_khau(self):
        from ui_doi_mat_khau import DoiMatKhauWindow

        open_single_window(
            "WIN_DOI_MK", DoiMatKhauWindow, self.session, self.root
        )

    def run(self):
        self.root.mainloop()