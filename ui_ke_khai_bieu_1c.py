import os
import streamlit as st
from xuat_excel_bieu_1c import tao_phieu_ke_khai_1c


def render_ke_khai_bieu_1c(session):
    st.markdown("<h4 style='text-align: center; color: #1a5276;'>📊 Kê Khai Giờ Dạy - Biểu 1C</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        tu_tuan = st.number_input("Từ tuần:", min_value=1, max_value=20, value=1)
    with col2:
        den_tuan = st.number_input("Đến tuần:", min_value=1, max_value=20, value=4)
    
    thang_str = st.text_input("Tháng kê khai:", value="Tháng 9")

    if st.button("📥 Tạo và Tải File Excel Biểu 1C", type="primary", use_container_width=True):
        try:
            with st.spinner("Đang tổng hợp dữ liệu và tạo biểu mẫu Excel..."):
                file_path = tao_phieu_ke_khai_1c(session, int(tu_tuan), int(den_tuan), thang_str)

            if file_path and os.path.exists(file_path):
                st.success("🎉 Tạo file Excel thành công!")
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="💾 Tải xuống File Excel Biểu 1C",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            else:
                st.error("Không thể tạo được tệp Excel. Vui lòng kiểm tra lại dữ liệu.")
        except Exception as e:
            st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
