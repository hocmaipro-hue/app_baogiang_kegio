# ui_doi_mat_khau.py
import tkinter as tk
from tkinter import messagebox
import psycopg2
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class DoiMatKhauWindow:
    def __init__(self, session, parent=None):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')

        self.window = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.window.title(f"Đổi Mật Khẩu - {self.tengv}")
        self.window.geometry("380x260")
        self.window.resizable(False, False)
        self.window.grab_set()  # Khóa màn hình cha lại khi đang đổi mật khẩu

        # Tiêu đề
        tk.Label(self.window, text="ĐỔI MẬT KHẨU ĐĂNG NHẬP", 
                 font=("Arial", 11, "bold"), fg="#1a5276").pack(pady=(15, 5))
        tk.Label(self.window, text=f"Tài khoản: {self.tengv} ({self.magv})", 
                 font=("Arial", 9, "italic"), fg="#555").pack(pady=(0, 10))

        # Khung nhập liệu
        f = tk.Frame(self.window, padx=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Mật khẩu hiện tại:").grid(row=0, column=0, sticky="w", pady=4)
        self.txt_old = tk.Entry(f, width=22, show="*")
        self.txt_old.grid(row=0, column=1, pady=4)

        tk.Label(f, text="Mật khẩu mới:").grid(row=1, column=0, sticky="w", pady=4)
        self.txt_new = tk.Entry(f, width=22, show="*")
        self.txt_new.grid(row=1, column=1, pady=4)

        tk.Label(f, text="Nhập lại MK mới:").grid(row=2, column=0, sticky="w", pady=4)
        self.txt_confirm = tk.Entry(f, width=22, show="*")
        self.txt_confirm.grid(row=2, column=1, pady=4)

        # Nút bấm lưu
        tk.Button(self.window, text="💾 Lưu Mật Khẩu Mới", bg="#d4efdf", font=("Arial", 9, "bold"), 
                  command=self.xu_ly_doi_mat_khau).pack(pady=(5, 15))

    def xu_ly_doi_mat_khau(self):
        p_old = self.txt_old.get().strip()
        p_new = self.txt_new.get().strip()
        p_conf = self.txt_confirm.get().strip()

        if not p_old or not p_new or not p_conf:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ cả 3 ô mật khẩu!")
            return

        if p_new != p_conf:
            messagebox.showerror("Lỗi xác nhận", "Mật khẩu mới và Nhập lại mật khẩu không khớp nhau!")
            return

        if p_old == p_new:
            messagebox.showwarning("Cảnh báo", "Mật khẩu mới không được trùng với mật khẩu cũ!")
            return

        conn = None
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()

            # 1. Kiểm tra mật khẩu cũ (dùng chính xác tên cột là matkhau)
            cur.execute("SELECT matkhau FROM giao_vien WHERE magv = %s", (self.magv,))
            row = cur.fetchone()

            if not row or (row[0] and str(row[0]).strip() != p_old):
                messagebox.showerror("Sai mật khẩu", "Mật khẩu hiện tại không chính xác!")
                cur.close()
                conn.close()
                return

            # 2. Cập nhật mật khẩu mới vào cột matkhau
            cur.execute("UPDATE giao_vien SET matkhau = %s WHERE magv = %s", (p_new, self.magv))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Thành công", "Đã đổi mật khẩu thành công!\nHãy ghi nhớ mật khẩu mới cho lần đăng nhập sau.")
            self.window.destroy()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Lỗi kết nối", f"Không thể đổi mật khẩu: {e}")