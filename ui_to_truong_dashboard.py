# ui_to_truong_dashboard.py
import tkinter as tk
from window_manager import open_single_window

# Import các chức năng con
from ui_admin_thong_ke_gio import AdminThongKeGioWindow
from ui_bien_dong_lich_day import BienDongLichDayWindow
from ui_doi_mat_khau import DoiMatKhauWindow
from ui_duyet_so_bao_giang import DuyetSBGWindow
from ui_quan_ly_giao_vien import QuanLyGiaoVienWindow
from ui_quan_ly_ppct import QuanLyPPCTWindow
from ui_so_bao_giang_ca_nhan import SoBaoGiangCaNhanWindow
from ui_xem_tkb import XemTKBWindow


def get_val(session, key, default=""):
    return (
        session.get(key, default)
        if isinstance(session, dict)
        else getattr(session, key, default)
    )


class ToTruongDashboardWindow:

    def __init__(self, session):
        self.session = session
        self.root = tk.Tk() if not tk._default_root else tk.Toplevel()

        tengv = get_val(session, "tengv", "Giáo viên")
        to_bm = get_val(session, "to_bo_mon", "Chuyên môn")

        self.root.title(f"Quản Lý Báo Giảng - {tengv} [TỔ TRƯỞNG]")
        self.root.geometry("520x620")
        self.root.resizable(False, False)

        # Tiêu đề lời chào
        tk.Label(
            self.root,
            text=f"Xin chào: {tengv}",
            font=("Arial", 14, "bold"),
            fg="#1a5276",
        ).pack(pady=(15, 2))
        tk.Label(
            self.root,
            text=f"Tổ bộ môn: {to_bm}",
            font=("Arial", 11, "italic"),
            fg="#555",
        ).pack(pady=(0, 5))

        # Nút Đổi mật khẩu cá nhân
        tk.Button(
            self.root,
            text="🔑 Đổi mật khẩu cá nhân",
            bg="#fcf3cf",
            font=("Arial", 9, "bold"),
            command=lambda: open_single_window(
                "WIN_TT_DOI_MK", DoiMatKhauWindow, self.session, self.root
            ),
        ).pack(pady=5)

        # --- NHÓM 1: CÔNG VIỆC CÁ NHÂN ---
        lbl_gr1 = tk.LabelFrame(
            self.root,
            text=" 📖 CÔNG VIỆC GIẢNG DẠY CÁ NHÂN ",
            font=("Arial", 10, "bold"),
            fg="#2e4053",
            padx=15,
            pady=8,
        )
        lbl_gr1.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(
            lbl_gr1,
            text="📅 1. Xem Thời khóa biểu",
            font=("Arial", 10),
            height=2,
            command=lambda: open_single_window(
                "WIN_TKB", XemTKBWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            lbl_gr1,
            text="📝 2. Đăng ký Biến động (Nghỉ / Bù / Thay / BDHSG)",
            font=("Arial", 10),
            height=2,
            command=lambda: open_single_window(
                "WIN_BIEN_DONG", BienDongLichDayWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            lbl_gr1,
            text="📖 3. Quản lý Sổ Báo Giảng cá nhân",
            font=("Arial", 10),
            height=2,
            bg="#e8f8f5",
            command=lambda: open_single_window(
                "WIN_BAO_GIANG", SoBaoGiangCaNhanWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        # --- NHÓM 2: QUẢN LÝ CHUYÊN MÔN CỦA TỔ ---
        lbl_gr2 = tk.LabelFrame(
            self.root,
            text=" 👥 QUẢN LÝ CHUYÊN MÔN CỦA TỔ ",
            font=("Arial", 10, "bold"),
            fg="#784212",
            padx=15,
            pady=8,
        )
        lbl_gr2.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(
            lbl_gr2,
            text="📚 4. Quản lý Phân phối chương trình (PPCT)",
            font=("Arial", 10),
            height=2,
            command=lambda: open_single_window(
                "WIN_QUAN_LY_PPCT", QuanLyPPCTWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            lbl_gr2,
            text="👥 5. Duyệt Sổ Báo Giảng & Nghỉ bù của Tổ",
            font=("Arial", 10, "bold"),
            height=2,
            bg="#fef9e7",
            command=lambda: open_single_window(
                "WIN_DUYET_SBG", DuyetSBGWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            lbl_gr2,
            text="📊 6. Thống Kê & Đối Chiếu Giờ Dạy Của Tổ",
            font=("Arial", 10, "bold"),
            height=2,
            bg="#ebf5fb",
            fg="#1b4f72",
            command=lambda: open_single_window(
                "WIN_ADMIN_THONG_KE_GIO", AdminThongKeGioWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            lbl_gr2,
            text="👥 7. Quản lý DS Giáo viên trong Tổ (Xem MK & Sửa cột)",
            font=("Arial", 10, "bold"),
            height=2,
            bg="#d4efdf",
            command=lambda: open_single_window(
                "WIN_QUAN_LY_GV", QuanLyGiaoVienWindow, self.session
            ),
        ).pack(fill=tk.X, pady=3)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    demo_session = {
        "magv": "GV01",
        "tengv": "TUYÊN",
        "to_bo_mon": "Toán",
        "role": "TO_TRUONG",
    }
    app = ToTruongDashboardWindow(demo_session)
    app.run()