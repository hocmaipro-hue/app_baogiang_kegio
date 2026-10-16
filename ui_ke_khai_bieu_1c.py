# ui_ke_khai_bieu_1c.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime, timedelta
import psycopg2
from config import DB_URI
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class KeKhaiBieu1CWindow:
    def __init__(self, session):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')
        self.to_bm = get_val(session, 'to_bo_mon', 'Toán')
        
        self.window = tk.Toplevel()
        self.window.title(f"Phiếu Kê Khai Định Mức Giờ Dạy (Biểu 1C HD) - {self.tengv}")
        self.window.geometry("900x620")

        # Cấu hình kiêm nhiệm mặc định (2 kiêm nhiệm)
        self.kn_info = {
            'kn1_ten': 'GVCN 12A2', 'kn1_gio': 4,
            'kn2_ten': '', 'kn2_gio': 0,
            'con_nho': 0, 'hop_dong': 0
        }
        self.file_xuat_gan_nhat = ""

        # Tiêu đề
        tk.Label(self.window, text="KÊ KHAI THỰC HIỆN ĐỊNH MỨC GIỜ DẠY (BIỂU 1C HD)", 
                 font=("Arial", 13, "bold"), fg="#1a5276").pack(pady=(12, 2))
        tk.Label(self.window, text=f"Giáo viên: {self.tengv} - Tổ bộ môn: {self.to_bm}", 
                 font=("Arial", 10, "italic"), fg="#555").pack(pady=(0, 8))

        # --- KHUNG 1: CHỌN THÁNG VÀ KHOẢNG TUẦN ---
        fr_top = tk.LabelFrame(self.window, text=" Thời gian kê khai thanh toán ", padx=10, pady=8, font=("Arial", 9, "bold"))
        fr_top.pack(fill=tk.X, padx=15, pady=4)

        tk.Label(fr_top, text="Tháng kê khai:").grid(row=0, column=0, sticky="w", padx=5)
        self.cbo_thang = ttk.Combobox(fr_top, width=12, state="readonly", 
                                      values=[f"Tháng {i:02d}" for i in range(1, 13)])
        self.cbo_thang.set("Tháng 09")
        self.cbo_thang.grid(row=0, column=1, padx=5)

        tk.Label(fr_top, text="Từ Tuần:").grid(row=0, column=2, padx=(15, 2))
        self.spn_tu = ttk.Spinbox(fr_top, from_=1, to=35, width=5)
        self.spn_tu.set(1)
        self.spn_tu.grid(row=0, column=3, padx=2)

        tk.Label(fr_top, text="Đến Tuần:").grid(row=0, column=4, padx=(10, 2))
        self.spn_den = ttk.Spinbox(fr_top, from_=1, to=35, width=5)
        self.spn_den.set(4)
        self.spn_den.grid(row=0, column=5, padx=2)

        self.lbl_info_tuan = tk.Label(fr_top, text="(4 tuần: từ 09/09/2026 đến 03/10/2026)", fg="#2980b9", font=("Arial", 9, "italic"))
        self.lbl_info_tuan.grid(row=0, column=6, padx=(15, 5))

        # --- KHUNG 2: BẢNG XEM TRƯỚC SỐ LIỆU ĐỐI CHIẾU ---
        fr_preview = tk.LabelFrame(self.window, text=" Bảng tổng hợp số liệu tính giờ dự kiến ", padx=10, pady=8, font=("Arial", 9, "bold"))
        fr_preview.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        cols = ("muc", "noi_dung", "so_gio", "ghi_chu")
        self.tree = ttk.Treeview(fr_preview, columns=cols, show="headings", height=9)
        self.tree.heading("muc", text="Mục")
        self.tree.heading("noi_dung", text="Nội dung kê khai")
        self.tree.heading("so_gio", text="Số giờ quy đổi")
        self.tree.heading("ghi_chu", text="Chi tiết / Ghi chú")

        self.tree.column("muc", width=60, anchor="center")
        self.tree.column("noi_dung", width=260, anchor="w")
        self.tree.column("so_gio", width=110, anchor="center")
        self.tree.column("ghi_chu", width=420, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- KHUNG 3: 4 NÚT HÀNH ĐỘNG CHÍNH ---
        fr_btn = tk.Frame(self.window)
        fr_btn.pack(pady=10)

        # Nút 1
        tk.Button(fr_btn, text="🔄 1. TẢI & XEM TRƯỚC SỐ LIỆU", font=("Arial", 9, "bold"), bg="#ebf5fb",
                  command=self.load_preview).pack(side=tk.LEFT, padx=6)

        # Nút 2
        tk.Button(fr_btn, text="⚙️ 2. CÀI ĐẶT 2 KIÊM NHIỆM", font=("Arial", 9, "bold"), bg="#fef9e7",
                  command=self.cai_dat_kiem_nhiem).pack(side=tk.LEFT, padx=6)

        # Nút 3
        tk.Button(fr_btn, text="📤 3. XUẤT PHIẾU KÊ KHAI EXCEL (BIỂU 1C)", font=("Arial", 9, "bold"), bg="#27ae60", fg="white",
                  command=self.xuat_excel).pack(side=tk.LEFT, padx=6)

        # Nút 4
        tk.Button(fr_btn, text="📂 4. MỞ FILE EXCEL VỪA XUẤT", font=("Arial", 9, "bold"), bg="#2980b9", fg="white",
                  command=self.mo_file_excel).pack(side=tk.LEFT, padx=6)

        self.load_preview()

    def get_ngay_bd(self):
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT gia_tri FROM cau_hinh WHERE khoa = 'ngay_bat_dau_nam_hoc'")
            r = cur.fetchone()
            cur.close(); conn.close()
            if r: return datetime.strptime(r[0].strip(), "%Y-%m-%d").date()
        except Exception: pass
        return datetime.strptime("2026-09-07", "%Y-%m-%d").date()

    def load_preview(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        tu_tuan = int(self.spn_tu.get())
        den_tuan = int(self.spn_den.get())
        if tu_tuan > den_tuan:
            messagebox.showwarning("Cảnh báo", "Từ tuần phải nhỏ hơn hoặc bằng Đến tuần!")
            return

        so_tuan = den_tuan - tu_tuan + 1
        base_mon = self.get_ngay_bd()
        d_start = base_mon + timedelta(days=(tu_tuan - 1) * 7)
        d_end = base_mon + timedelta(days=(den_tuan - 1) * 7 + 6)
        self.lbl_info_tuan.config(text=f"({so_tuan} tuần: từ {d_start.strftime('%d/%m/%Y')} đến {d_end.strftime('%d/%m/%Y')})")

        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            # 1. Định mức
            cur.execute("SELECT COALESCE(dinh_muc_tiet, 17) FROM giao_vien WHERE magv = %s", (self.magv,))
            dm_tuan = cur.fetchone()[0]
            tong_dm = dm_tuan * so_tuan

            # 2. Phân công TKB
            cur.execute("SELECT COUNT(*) FROM thoi_khoa_bieu WHERE magv = %s AND lop NOT IN ('SHDC', 'SHL')", (self.magv,))
            tkb_tuan = cur.fetchone()[0]
            tong_tkb = tkb_tuan * so_tuan

            # 3. Biến động
            cur.execute("""
                SELECT loai, COUNT(*) FROM bien_dong_lich_day 
                WHERE magv = %s AND ngay BETWEEN %s AND %s 
                GROUP BY loai
            """, (self.magv, d_start, d_end))
            bd_dict = dict(cur.fetchall())
            cur.close(); conn.close()

            day_thay = bd_dict.get('Dạy thay', 0)
            nghi_viec_rieng = bd_dict.get('Nghỉ dạy', 0) # có thể trừ
            bdhsg = bd_dict.get('Bồi dưỡng HSG', 0)

            # 4. Kiêm nhiệm
            kn1_tong = self.kn_info['kn1_gio'] * so_tuan
            kn2_tong = self.kn_info['kn2_gio'] * so_tuan
            giam_kn_tong = kn1_tong + kn2_tong + (self.kn_info['con_nho'] + self.kn_info['hop_dong']) * so_tuan

            # 5. Tổng thực hiện & Thừa giờ (công thức dòng 73)
            tong_thuc_hien = tong_tkb + day_thay - nghi_viec_rieng + bdhsg + giam_kn_tong
            thua_gio = tong_thuc_hien - tong_dm

            # Hiển thị lên bảng xem trước
            self.tree.insert("", tk.END, values=("Mục 2", "Định mức giờ dạy (1)", f"{tong_dm} giờ", f"{dm_tuan} tiết/tuần x {so_tuan} tuần"))
            self.tree.insert("", tk.END, values=("Mục 3", "Số giờ theo TKB phân công (2)", f"{tong_tkb} giờ", f"{tkb_tuan} tiết/tuần x {so_tuan} tuần"))
            self.tree.insert("", tk.END, values=("Mục 4.1", "Số giờ dạy thay (6)", f"{day_thay} giờ", "Cộng thêm vào tổng giờ"))
            self.tree.insert("", tk.END, values=("Mục 4.3", "Nghỉ việc riêng / trừ giờ (5)", f"{nghi_viec_rieng} giờ", "Trừ khỏi giờ thực hiện"))
            self.tree.insert("", tk.END, values=("Mục 5", "Hoạt động chuyên môn BDHSG (7)", f"{bdhsg} giờ", "Cộng vào giờ chuyên môn"))
            
            str_kn = f"{self.kn_info['kn1_ten']} ({kn1_tong}h)"
            if self.kn_info['kn2_ten']: str_kn += f" + {self.kn_info['kn2_ten']} ({kn2_tong}h)"
            self.tree.insert("", tk.END, values=("Mục 6", "Số giờ giảm do kiêm nhiệm (8)", f"{giam_kn_tong} giờ", str_kn))

            str_cl = f"+{thua_gio}" if thua_gio > 0 else str(thua_gio)
            self.tree.insert("", tk.END, values=("Mục 7", "👉 TỔNG SỐ GIỜ THỰC HIỆN (9)", f"{tong_thuc_hien} giờ", "(2)+(3)-(5)+(6)+(7)+(8)"))
            self.tree.insert("", tk.END, values=("Mục 8", "💰 SỐ GIỜ DẠY THÊM (9) - (1)", f"{str_cl} giờ", "Số giờ thanh toán thừa giờ"))

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải xem trước: {e}")

    def cai_dat_kiem_nhiem(self):
        """Hộp thoại cài đặt linh hoạt 2 kiêm nhiệm"""
        dlg = tk.Toplevel(self.window)
        dlg.title("Cài đặt Kiêm nhiệm & Giảm trừ định mức")
        dlg.geometry("450x320")
        dlg.grab_set()

        tk.Label(dlg, text="CÀI ĐẶT CÔNG TÁC KIÊM NHIỆM", font=("Arial", 11, "bold"), fg="#1a5276").pack(pady=10)

        f = tk.Frame(dlg, padx=15, pady=5)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Kiêm nhiệm 1:").grid(row=0, column=0, sticky="w", pady=4)
        txt_kn1 = tk.Entry(f, width=20)
        txt_kn1.insert(0, self.kn_info['kn1_ten'])
        txt_kn1.grid(row=0, column=1, pady=4)
        tk.Label(f, text="Giảm (h/tuần):").grid(row=0, column=2, padx=(8, 2))
        spn_kn1 = ttk.Spinbox(f, from_=0, to=10, width=5)
        spn_kn1.set(self.kn_info['kn1_gio'])
        spn_kn1.grid(row=0, column=3)

        tk.Label(f, text="Kiêm nhiệm 2:").grid(row=1, column=0, sticky="w", pady=4)
        txt_kn2 = tk.Entry(f, width=20)
        txt_kn2.insert(0, self.kn_info['kn2_ten'])
        txt_kn2.grid(row=1, column=1, pady=4)
        tk.Label(f, text="Giảm (h/tuần):").grid(row=1, column=2, padx=(8, 2))
        spn_kn2 = ttk.Spinbox(f, from_=0, to=10, width=5)
        spn_kn2.set(self.kn_info['kn2_gio'])
        spn_kn2.grid(row=1, column=3)

        tk.Label(f, text="Nữ có con nhỏ <12th:").grid(row=2, column=0, sticky="w", pady=4)
        spn_con = ttk.Spinbox(f, from_=0, to=5, width=5)
        spn_con.set(self.kn_info['con_nho'])
        spn_con.grid(row=2, column=1, sticky="w", pady=4)

        tk.Label(f, text="Hợp đồng lần đầu:").grid(row=3, column=0, sticky="w", pady=4)
        spn_hd = ttk.Spinbox(f, from_=0, to=5, width=5)
        spn_hd.set(self.kn_info['hop_dong'])
        spn_hd.grid(row=3, column=1, sticky="w", pady=4)

        def save_kn():
            self.kn_info['kn1_ten'] = txt_kn1.get().strip()
            self.kn_info['kn1_gio'] = int(spn_kn1.get())
            self.kn_info['kn2_ten'] = txt_kn2.get().strip()
            self.kn_info['kn2_gio'] = int(spn_kn2.get())
            self.kn_info['con_nho'] = int(spn_con.get())
            self.kn_info['hop_dong'] = int(spn_hd.get())
            dlg.destroy()
            self.load_preview()
            messagebox.showinfo("Thành công", "Đã cập nhật chế độ kiêm nhiệm!")

        tk.Button(dlg, text="💾 Lưu cấu hình", bg="#d4efdf", font=("Arial", 9, "bold"), command=save_kn).pack(pady=10)

    def xuat_excel(self):
        tu_tuan = int(self.spn_tu.get())
        den_tuan = int(self.spn_den.get())
        thang = self.cbo_thang.get()

        try:
            file_path = tao_phieu_ke_khai_1c(self.session, tu_tuan, den_tuan, thang, self.kn_info)
            self.file_xuat_gan_nhat = file_path
            messagebox.showinfo("Xuất thành công!", f"Đã tạo xong Phiếu Kê Khai (Biểu 1C HD)!\n\nFile lưu tại:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi xuất Excel", f"Không thể tạo file: {e}")

    def mo_file_excel(self):
        if not self.file_xuat_gan_nhat or not os.path.exists(self.file_xuat_gan_nhat):
            messagebox.showwarning("Cảnh báo", "Chưa có file Excel nào được xuất hoặc file không tồn tại!\nVui lòng bấm nút số 3 để xuất trước.")
            return
        os.startfile(self.file_xuat_gan_nhat)
