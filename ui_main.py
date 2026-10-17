import streamlit as st

try:
    from ui_bien_dong_lich_day import render_bien_dong_lich_day
except ImportError:
    render_bien_dong_lich_day = None

try:
    from ui_day_bu import render_day_bu
except ImportError:
    render_day_bu = None

try:
    from ui_day_thay_hsg import render_day_thay_hsg
except ImportError:
    render_day_thay_hsg = None

try:
    from ui_doi_mat_khau import render_doi_mat_khau
except ImportError:
    render_doi_mat_khau = None

try:
    from ui_ke_khai_bieu_1c import render_ke_khai_bieu_1c
except ImportError:
    render_ke_khai_bieu_1c = None

try:
    from ui_xem_tkb import render_xem_tkb
except ImportError:
    render_xem_tkb = None

try:
    from ui_so_bao_giang_ca_nhan import render_so_bao_giang_ca_nhan
except ImportError:
    render_so_bao_giang_ca_nhan = None


def render_user_dashboard(session):
    tengv = session.get("tengv", "Giáo viên")
    to_bm = session.get("to_bo_mon", "Toán")

    with st.sidebar:
        st.markdown(f"<h3 style='color: #1a5276;'>Xin chào,</h3><h4>{tengv}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #555; font-style: italic;'>Tổ bộ môn: {to_bm}</p>", unsafe_allow_html=True)
        st.divider()

        menu_chon = st.radio(
            "CHỨC NĂNG GIẢNG DẠY",
            options=[
                "📅 Xem TKB cá nhân",
                "⛔ Báo Nghỉ dạy",
                "🟢 Đăng ký Dạy Bù",
                "🟡 Đăng ký Dạy Thay & HSG",
                "📖 Sổ Báo Giảng cá nhân",
                "📊 Xem Kê khai giờ (PKG)",
                "🔑 Đổi mật khẩu",
            ],
        )

        st.divider()
        if st.button("🚪 Đăng xuất", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if menu_chon == "📅 Xem TKB cá nhân":
        if render_xem_tkb:
            render_xem_tkb(session)
    elif menu_chon == "⛔ Báo Nghỉ dạy":
        if render_bien_dong_lich_day:
            render_bien_dong_lich_day(session)
    elif menu_chon == "🟢 Đăng ký Dạy Bù":
        if render_day_bu:
            render_day_bu(session)
    elif menu_chon == "🟡 Đăng ký Dạy Thay & HSG":
        if render_day_thay_hsg:
            render_day_thay_hsg(session)
    elif menu_chon == "📖 Sổ Báo Giảng cá nhân":
        if render_so_bao_giang_ca_nhan:
            render_so_bao_giang_ca_nhan(session)
    elif menu_chon == "📊 Xem Kê khai giờ (PKG)":
        if render_ke_khai_bieu_1c:
            render_ke_khai_bieu_1c(session)
    elif menu_chon == "🔑 Đổi mật khẩu":
        if render_doi_mat_khau:
            render_doi_mat_khau(session)
