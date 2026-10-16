# ui_nhan_su_va_duyet.py
import tkinter as tk
from tkinter import messagebox

class NhanSuWindow:
    def __init__(self, session):
        self.session = session
        self.window = tk.Toplevel()
        self.window.title("Quản lý Tổ chuyên môn & Duyệt báo giảng")
        self.window.geometry("500x300")
        
        tk.Label(self.window, text=f"Bảng điều khiển Tổ trưởng: {session['to_bo_mon']}", font=("Arial", 11, "bold")).pack(pady=15)
        tk.Button(self.window, text="Kiểm tra tiến độ PPCT của giáo viên trong tổ", width=40, command=self.check_progress).pack(pady=10)

    def check_progress(self):
        messagebox.showinfo("Thông báo", "Tính năng kiểm tra tiến độ PPCT trong tổ đang hoạt động.")
