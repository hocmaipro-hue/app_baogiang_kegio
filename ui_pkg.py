# ui_pkg.py
from datetime import date, datetime
import os
import re
import subprocess
import tkinter as tk
from tkinter import messagebox
from config import DB_URI
from kg_hoc_sinh_gioi import dong_bo_va_tinh_toan_bdhsg
import psycopg2
from ui_pkg_kiem_nhiem import CaiDatKiemNhiemWindow
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c


def get_val(s, k, d=""):
    return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)


class PkgWindow:

    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, "magv", "")
        self.tengv = get_val(session, "tengv", "Giáo viên")
        self.to_bm = get_val(session, "to_bo_mon", "Toán")

        self.window = tk.Toplevel()
        self.window.title(
            f"Phiếu Kê Khai Định Mức Giờ Dạy (Biểu 1C HD) - {self.tengv}"
        )
        self.window.geometry("780x480")

        self.file_xuat_gan_nhat = ""

        # Tiêu đề giao diện
        tk.Label(
            self.window,
            text="QUẢN LÝ KÊ KHAI ĐỊNH MỨC GIỜ DẠY (BIỂU 1C HD)",
            font=("Arial", 13, "bold"),
            fg="#1a5276",
        ).pack(pady=(15, 5))
        tk.Label(
            self.window,
            text=f"Giáo viên: {self.tengv} - Tổ bộ môn: {self.to_bm}",
            font=("Arial", 10, "italic"),
            fg="#555",
        ).pack(pady=(0, 10))

        # Khung chọn thời gian: Từ ngày -> Đến ngày
        fr_time = tk.LabelFrame(
            self.window,
            text=" 🕒 Chọn thời gian kê khai (Từ ngày - Đến ngày) ",
            font=("Arial", 9, "bold"),
            fg="#1a5276",
            padx=10,
            pady=8,
        )
        fr_time.pack(pady=5, padx=20, fill=tk.X)

        tk.Label(fr_time, text="Từ ngày:", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w", padx=3
        )
        self.txt_tu_ngay = tk.Entry(fr_time, width=13, font=("Arial", 9))
        self.txt_tu_ngay.insert(0, "07/09/2026")
        self.txt_tu_ngay.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(fr_time, text="Đến ngày:", font=("Arial", 9)).grid(
            row=0, column=2, sticky="w", padx=3
        )
        self.txt_den_ngay = tk.Entry(fr_time, width=13, font=("Arial", 9))
        self.txt_den_ngay.insert(0, "03/10/2026")
        self.txt_den_ngay.grid(row=0, column=3, sticky="w", padx=5)

        tk.Label(fr_time, text="Tháng kê khai:", font=("Arial", 9)).grid(
            row=0, column=4, sticky="w", padx=3
        )
        self.txt_thang = tk.Entry(fr_time, width=13, font=("Arial", 9))
        self.txt_thang.insert(0, "Tháng 09")
        self.txt_thang.grid(row=0, column=5, sticky="w", padx=5)

        # Đồng bộ HSG ngầm
        dong_bo_va_tinh_toan_bdhsg(self.magv)

        # 3 Nút chức năng chính
        fr_btn = tk.Frame(self.window)
        fr_btn.pack(pady=10)

        tk.Button(
            fr_btn,
            text="⚙️ 1. CÀI ĐẶT KIÊM NHIỆM & GIẢM TRỪ",
            font=("Arial", 10, "bold"),
            bg="#fef9e7",
            width=38,
            pady=6,
            command=self.mo_cai_dat_kiem_nhiem,
        ).pack(pady=5)

        tk.Button(
            fr_btn,
            text="📤 2. XUẤT PHIẾU KÊ KHAI EXCEL (BIỂU 1C)",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            width=38,
            pady=6,
            command=self.xuat_excel,
        ).pack(pady=5)

        tk.Button(
            fr_btn,
            text="📂 3. MỞ FILE EXCEL VỪA XUẤT",
            font=("Arial", 10, "bold"),
            bg="#2980b9",
            fg="white",
            width=38,
            pady=6,
            command=self.mo_file_excel,
        ).pack(pady=5)

    def mo_cai_dat_kiem_nhiem(self):
        CaiDatKiemNhiemWindow(
            self.session,
            self.window,
            self.txt_tu_ngay.get(),
            self.txt_den_ngay.get(),
        )

    def parse_ngay(self, s):
        s = s.strip()
        nam_nay = 2026
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "SELECT gia_tri FROM cau_hinh WHERE khoa ="
                " 'ngay_bat_dau_nam_hoc'"
            )
            r = cur.fetchone()
            cur.close()
            conn.close()
            if r:
                nam_nay = datetime.strptime(r[0].strip(), "%Y-%m-%d").year
        except Exception:
            pass

        m1 = re.match(r"^(\d{1,2})[/-](\d{1,2})$", s)
        if m1:
            return date(nam_nay, int(m1.group(2)), int(m1.group(1)))
        m2 = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
        if m2:
            return date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
        return None

    def xuat_excel(self):
        dong_bo_va_tinh_toan_bdhsg(self.magv)

        d_from = self.parse_ngay(self.txt_tu_ngay.get())
        d_to = self.parse_ngay(self.txt_den_ngay.get())
        thang_str = self.txt_thang.get().strip() or "Tháng 09"

        if not d_from or not d_to:
            messagebox.showwarning(
                "Sai định dạng ngày",
                "Vui lòng nhập ngày dạng DD/MM/YYYY (VD: 07/09/2026)",
            )
            return
        if d_from > d_to:
            messagebox.showwarning(
                "Lỗi ngày", "'Từ ngày' không được lớn hơn 'Đến ngày'!"
            )
            return

        # 👉 LẤY NGÀY KHAI GIẢNG TỪ CSDL ĐỂ TÍNH TUẦN
        base_monday = date(2026, 9, 7)
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute(
                "SELECT gia_tri FROM cau_hinh WHERE khoa ="
                " 'ngay_bat_dau_nam_hoc'"
            )
            r = cur.fetchone()
            cur.close()
            conn.close()
            if r:
                base_monday = datetime.strptime(
                    r[0].strip(), "%Y-%m-%d"
                ).date()
        except Exception:
            pass

        tu_tuan = max(1, (d_from - base_monday).days // 7 + 1)
        den_tuan = max(tu_tuan, (d_to - base_monday).days // 7 + 1)

        # 👉 TỰ ĐỘNG TÍNH SỐ TUẦN THỰC TẾ DỰA THEO SỐ NGÀY ĐƯỢC CHỌN
        so_ngay = (d_to - d_from).days + 1
        so_tuan_thuc_te = max(1, round(so_ngay / 7))

        extra_info = {
            "tu_ngay": d_from.strftime("%d/%m/%Y"),
            "den_ngay": d_to.strftime("%d/%m/%Y"),
            "so_tuan": so_tuan_thuc_te,  # Truyền số tuần tự tính
        }

        try:
            file_path = tao_phieu_ke_khai_1c(
                self.session, tu_tuan, den_tuan, thang_str, extra_info
            )
            self.file_xuat_gan_nhat = file_path
            messagebox.showinfo(
                "Xuất thành công!",
                f"Đã tạo xong Phiếu Kê Khai!\nTừ {extra_info['tu_ngay']} đến"
                f" {extra_info['den_ngay']} ({so_tuan_thuc_te} tuần)\n\nLưu"
                f" tại:\n{file_path}",
            )
        except Exception as e:
            messagebox.showerror("Lỗi xuất Excel", f"Không thể tạo file: {e}")

    def mo_file_excel(self):
        if not self.file_xuat_gan_nhat or not os.path.exists(
            self.file_xuat_gan_nhat
        ):
            messagebox.showwarning(
                "Cảnh báo",
                "Chưa có file Excel nào được xuất!\nVui lòng bấm nút số 2 để"
                " xuất trước.",
            )
            return
        try:
            os.startfile(os.path.abspath(self.file_xuat_gan_nhat))
        except Exception:
            try:
                subprocess.Popen(
                    ["start", os.path.abspath(self.file_xuat_gan_nhat)],
                    shell=True,
                )
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở file: {e}")