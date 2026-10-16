# ui_login.py
import tkinter as tk
from tkinter import messagebox
from auth import authenticate_user

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.root.title("Đăng nhập - Quản Lý Báo Giảng")
        self.root.geometry("350x220")
        self.on_success = on_success
        
        tk.Label(root, text="HỆ THỐNG QUẢN LÝ BÁO GIẢNG", font=("Arial", 11, "bold")).pack(pady=10)
        
        tk.Label(root, text="Mã giáo viên (MAGV):").pack()
        self.entry_magv = tk.Entry(root, width=30)
        self.entry_magv.pack(pady=5)
        
        tk.Label(root, text="Mật khẩu:").pack()
        self.entry_pass = tk.Entry(root, width=30, show="*")
        self.entry_pass.pack(pady=5)
        
        tk.Button(root, text="Đăng nhập", bg="green", fg="white", command=self.handle_login).pack(pady=10)

    def handle_login(self):
        magv = self.entry_magv.get().strip()
        pwd = self.entry_pass.get().strip()
        session = authenticate_user(magv, pwd)
        if session:
            messagebox.showinfo("Thành công", f"Chào mừng {session['tengv']} ({session['role']})")
            self.root.destroy()
            self.on_success(session)
        else:
            messagebox.showerror("Lỗi", "Mã giáo viên hoặc mật khẩu không đúng!")
