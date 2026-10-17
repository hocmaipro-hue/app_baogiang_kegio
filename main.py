# main.py
import tkinter as tk
from ui_login import LoginWindow


def hien_thiep_an_yen(tengv, callback_tiep_tuc):
    """Cửa sổ thiệp thơ an yên, màu sắc phong cảnh hữu tình, thư thái"""
    thiep = tk.Toplevel()
    thiep.title("🌸 Gửi Chút An Yên Đến Thầy/Cô")
    thiep.geometry("560x370")
    thiep.resizable(False, False)
    thiep.configure(bg="#E8F8F5")  # Màu xanh ngọc pastel êm dịu

    # Căn giữa màn hình máy tính
    thiep.update_idletasks()
    w = thiep.winfo_width()
    h = thiep.winfo_height()
    ws = thiep.winfo_screenwidth()
    hs = thiep.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    thiep.geometry(f"{w}x{h}+{x}+{y}")

    # Đưa lên trên cùng
    thiep.lift()
    thiep.attributes("-topmost", True)
    thiep.focus_force()

    # Khung thiệp bo viền trang nhã
    khung = tk.Frame(
        thiep, bg="#FFFFFF", relief="groove", bd=2, padx=20, pady=15
    )
    khung.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    # Lời đề tặng
    tk.Label(
        khung,
        text=f"🌿 Kính tặng Thầy/Cô: {tengv}",
        font=("Times New Roman", 14, "bold"),
        fg="#117A65",
        bg="#FFFFFF",
    ).pack(pady=(0, 10))

    # 4 Câu thơ an nhiên (Font Times New Roman nghệ thuật)
    tho_text = (
        "“Bụi phấn bay bay mỉm miệng cười,\n"
        "Bảng đen nâng bước tuổi đôi mươi.\n"
        "Rời trang giáo án lòng thanh thản,\n"
        "Một đóa an yên nở giữa đời.”"
    )
    tk.Label(
        khung,
        text=tho_text,
        font=("Times New Roman", 13, "italic"),
        fg="#1A5276",
        bg="#F4F6F6",
        padx=18,
        pady=10,
        relief="ridge",
        bd=1,
        justify="center",
    ).pack(fill=tk.X, pady=5)

    # Lời chúc nhẹ nhàng
    tk.Label(
        khung,
        text="Chúc Thầy/Cô một ngày giảng dạy an vui, nhẹ nhàng và trọn vẹn!",
        font=("Times New Roman", 12),
        fg="#5D6D7E",
        bg="#FFFFFF",
    ).pack(pady=(10, 2))

    # Tên tác giả
    tk.Label(
        khung,
        text="— Thân ái: Tác giả Nguyễn Văn Phong —",
        font=("Times New Roman", 11, "bold italic"),
        fg="#B7950B",
        bg="#FFFFFF",
    ).pack(pady=(0, 12))

    # Nút bấm vào phần mềm
    def tiep_tuc():
        thiep.destroy()
        callback_tiep_tuc()

    btn_ok = tk.Button(
        khung,
        text="🌸 Nhận An Yên & Bắt Đầu 🌸",
        font=("Arial", 10, "bold"),
        bg="#1ABC9C",
        fg="white",
        activebackground="#16A085",
        activeforeground="white",
        padx=15,
        pady=5,
        relief="raised",
        cursor="hand2",
        command=tiep_tuc,
    )
    btn_ok.pack()

    # Bấm phím Enter hoặc phím Space cũng tự vào
    thiep.bind("<Return>", lambda e: tiep_tuc())
    thiep.bind("<space>", lambda e: tiep_tuc())


def launch_app(session):
    role = session.get("role")
    tengv = session.get("tengv", "Thầy/Cô")

    def mo_giao_dien_chinh():
        # NẾU LÀ TỔ TRƯỞNG
        if role == "TO_TRUONG":
            from ui_to_truong_dashboard import ToTruongDashboardWindow

            app = ToTruongDashboardWindow(session)
            app.run()
        # NẾU LÀ ADMIN
        elif role == "ADMIN":
            from ui_admin import AdminWindow

            app = AdminWindow(session)
            app.run()
        # CÒN LẠI (GIÁO VIÊN THƯỜNG)
        else:
            from ui_main import MainWindow

            app = MainWindow(session)
            app.run()

    # Hiện thiệp thơ màu mè phong cảnh hữu tình trước, bấm nút sẽ vào giao diện chính
    hien_thiep_an_yen(tengv, mo_giao_dien_chinh)


if __name__ == "__main__":
    root = tk.Tk()
    login = LoginWindow(root, launch_app)
    root.withdraw()
    root.mainloop()