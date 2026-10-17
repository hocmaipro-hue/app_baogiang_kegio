# BỘ QUẢN LÝ TRẠNG THÁI & ĐIỀU HƯỚNG TOÀN HỆ THỐNG (STREAMLIT STATE MANAGER)


def init_session_state(default_session=None):
  """Khởi tạo các biến trạng thái cần thiết trong st.session_state nếu chưa có."""
  if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
  if "user_session" not in st.session_state:
    st.session_state.user_session = default_session or {}
  if "current_tab" not in st.session_state:
    st.session_state.current_tab = ""


def get_current_user_session():
  """Lấy thông tin session của người dùng đang đăng nhập."""
  return st.session_state.get("user_session", {})


def set_current_user_session(session_data):
  """Thiết lập session cho người dùng sau khi đăng nhập thành công."""
  st.session_state.authenticated = True
  st.session_state.user_session = session_data


def clear_user_session():
  """Xóa sạch session khi đăng xuất."""
  st.session_state.clear()
  init_session_state()


# Hàm tương thích ngược giả lập open_single_window cho các module cũ nếu cần gọi
def open_single_window(window_key, window_class, *args, **kwargs):
  """Hàm hỗ trợ tương thích: Chuyển hướng xử lý sang state hoặc render trực tiếp

  trong môi trường Streamlit.
  """
  # Trên Streamlit, các module được quản lý trực tiếp qua sidebar radio hoặc tab,
  # hàm này ghi nhận key đang hoạt động vào session_state.
  st.session_state[f"active_window_{window_key}"] = True
  return None