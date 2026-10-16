# window_manager.py
# BỘ QUẢN LÝ CỬA SỔ DUY NHẤT TOÀN HỆ THỐNG (SINGLETON WINDOW MANAGER)

_OPEN_WINDOWS = {}


def _tim_tk_window(instance):
    """Tự động dò tìm đối tượng Tk/Toplevel bên trong instance của class."""
    if instance is None:
        return None
    # Nếu bản thân instance là cửa sổ Tkinter
    if hasattr(instance, "winfo_exists"):
        return instance
    # Dò tìm các thuộc tính phổ biến trong dự án
    for attr in ["window", "root", "dlg", "top"]:
        if hasattr(instance, attr):
            obj = getattr(instance, attr)
            if obj is not None and hasattr(obj, "winfo_exists"):
                return obj
    return None


def open_single_window(window_key, window_class, *args, **kwargs):
    """HÀM DÙNG CHUNG CHO MƯỜI MẤY NÚT CON:

    - Nếu cửa sổ chưa mở: Khởi tạo mới và hiển thị lên. - Nếu cửa sổ đang mở:
    Tự động kéo nổi lên trước màn hình chính, chống đẻ thêm cửa sổ.
    """
    global _OPEN_WINDOWS

    # 1. KIỂM TRA XEM CỬA SỔ ĐÃ TỒN TẠI TRÊN MÀN HÌNH CHƯA
    if window_key in _OPEN_WINDOWS:
        existing_instance = _OPEN_WINDOWS[window_key]
        tk_win = _tim_tk_window(existing_instance)

        if tk_win is not None:
            try:
                # Kiểm tra cửa sổ còn sống hay đã bị đóng
                if tk_win.winfo_exists():
                    tk_win.deiconify()  # Phục hồi nếu bị thu nhỏ
                    tk_win.lift()  # Kéo lên trên cửa sổ chính

                    # Ép Windows phải đưa cửa sổ này lên trên cùng
                    tk_win.attributes("-topmost", True)
                    tk_win.after_idle(tk_win.attributes, "-topmost", False)

                    tk_win.focus_force()  # Chiếm tiêu điểm
                    return existing_instance
            except Exception:
                pass

        # Nếu cửa sổ đã bị đóng thì xóa khỏi bộ nhớ theo dõi
        del _OPEN_WINDOWS[window_key]

    # 2. CHƯA CÓ THÌ TIẾN HÀNH KHỞI TẠO MỚI
    try:
        new_instance = window_class(*args, **kwargs)
    except Exception as e:
        print(f"Lỗi khởi tạo cửa sổ {window_key}: {e}")
        raise e

    _OPEN_WINDOWS[window_key] = new_instance

    # 3. TỰ ĐỘNG GẮN BỘ THEO DÕI: KHI BẤM NÚT [X] TẮT THÌ GIẢI PHÓNG
    tk_win = _tim_tk_window(new_instance)
    if tk_win is not None:
        try:
            # Đảm bảo cửa sổ mới luôn nổi lên trên cùng lúc vừa bật
            tk_win.lift()
            tk_win.focus_force()

            def on_close_cleanup(event=None):
                if event is None or event.widget == tk_win:
                    if window_key in _OPEN_WINDOWS:
                        del _OPEN_WINDOWS[window_key]

            tk_win.bind("<Destroy>", on_close_cleanup, add="+")
        except Exception:
            pass

    return new_instance