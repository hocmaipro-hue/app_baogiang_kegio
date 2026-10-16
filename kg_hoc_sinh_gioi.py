import psycopg2
from config import DB_URI

def ket_noi_db():
    """Tạo kết nối đến cơ sở dữ liệu Supabase"""
    return psycopg2.connect(DB_URI)

def dong_bo_va_tinh_toan_bdhsg(magv, d_start=None, d_end=None):
    """
    Tự động quét bảng bien_dong_lich_day của giáo viên:
    - Gom nhóm theo từng ngày (nếu cùng ngày có nhiều buổi thì gộp lại, đếm tổng số buổi -> bdhsg_thuc_day)
    - Lấy ngày tương ứng -> ngay_day_hsg (mỗi ngày khác nhau là 1 dòng riêng biệt)
    - Tính số giờ quy đổi = bdhsg_thuc_day * 1.5 -> bdhsg_quy_doi
    - Lưu vào bảng kg_hoc_sinh_gioi
    """
    try:
        conn = ket_noi_db()
        cursor = conn.cursor()
        
        # 1. Truy vấn gom nhóm theo ngày từ bảng bien_dong_lich_day cho phần Bồi dưỡng HSG
        if d_start and d_end:
            query_bd = """
                SELECT TO_CHAR(ngay, 'DD/MM/YYYY') as ngay_str, COUNT(*) as so_buoi
                FROM bien_dong_lich_day 
                WHERE magv = %s AND (loai ILIKE '%%HSG%%' OR loai ILIKE '%%Bồi dưỡng HSG%%') 
                  AND ngay BETWEEN %s AND %s
                GROUP BY ngay
                ORDER BY ngay ASC
            """
            cursor.execute(query_bd, (magv, d_start, d_end))
        else:
            query_bd = """
                SELECT TO_CHAR(ngay, 'DD/MM/YYYY') as ngay_str, COUNT(*) as so_buoi
                FROM bien_dong_lich_day 
                WHERE magv = %s AND (loai ILIKE '%%HSG%%' OR loai ILIKE '%%Bồi dưỡng HSG%%')
                GROUP BY ngay
                ORDER BY ngay ASC
            """
            cursor.execute(query_bd, (magv,))
            
        rows = cursor.fetchall()
        
        # 2. Xóa dữ liệu HSG cũ của giáo viên này trong bảng kg_hoc_sinh_gioi để chuẩn bị nạp dữ liệu mới
        cursor.execute("DELETE FROM kg_hoc_sinh_gioi WHERE magv = %s", (magv,))
        
        # 3. Duyệt qua từng ngày (mỗi ngày khác nhau là một dòng độc lập, ngày trùng đã được gom nhóm COUNT(*))
        tong_so_buoi = 0
        for r in rows:
            ngay_str = r[0]
            thuc_day = float(r[1])
            quy_doi = thuc_day * 1.5
            tong_so_buoi += thuc_day
            
            insert_query = """
                INSERT INTO kg_hoc_sinh_gioi (magv, ngay_day_hsg, bdhsg_thuc_day, bdhsg_quy_doi)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (magv, ngay_str, thuc_day, quy_doi))
            
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Đã đồng bộ HSG cho giáo viên {magv}: Tổng {tong_so_buoi} buổi.")
        return True
        
    except Exception as e:
        print(f"Lỗi đồng bộ BDHSG: {e}")
        return False

def lay_danh_sach_hsg_theo_gv(magv):
    """Lấy danh sách các dòng lịch dạy HSG theo từng ngày của một giáo viên từ bảng kg_hoc_sinh_gioi"""
    try:
        conn = ket_noi_db()
        cursor = conn.cursor()
        
        query = """
            SELECT ngay_day_hsg, bdhsg_thuc_day, bdhsg_quy_doi 
            FROM kg_hoc_sinh_gioi 
            WHERE magv = %s 
            ORDER BY id ASC
        """
        cursor.execute(query, (magv,))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        danh_sach = []
        for r in rows:
            danh_sach.append({
                "ngay_day_hsg": r[0],
                "bdhsg_thuc_day": r[1],
                "bdhsg_quy_doi": r[2]
            })
        return danh_sach
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu HSG: {e}")
        return []

if __name__ == "__main__":
    print("Module quản lý bồi dưỡng học sinh giỏi (kg_hoc_sinh_gioi) đã sẵn sàng.")