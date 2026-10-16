# calculator.py
def calculate_teaching_hours(dinh_muc, tiet_giam_tru, so_tiet_thuc_te, so_tiet_day_thay, so_tiet_day_bu, so_tiet_bdhsg):
    """Tính toán cân đối giờ dạy và tiết thừa thiếu"""
    dinh_muc_thuc_te = max(0, dinh_muc - tiet_giam_tru)
    tong_thuc_hien = so_tiet_thuc_te + so_tiet_day_thay + so_tiet_day_bu + so_tiet_bdhsg
    tiet_thua_thieu = tong_thuc_hien - dinh_muc_thuc_te
    
    return {
        "dinh_muc_thuc_te": dinh_muc_thuc_te,
        "tong_thuc_hien": tong_thuc_hien,
        "tiet_thua_thieu": tiet_thua_thieu
    }
