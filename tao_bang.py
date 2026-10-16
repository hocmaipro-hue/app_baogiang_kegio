# tao_bang.py
import psycopg2
from config import DB_URI

def khoi_tao_he_thong():
    print("⏳ Đang kết nối tới Supabase để tạo bảng...")
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()

        # 1. Bảng Phân phối chương trình (PPCT)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS phan_phoi_chuong_trinh (
                id SERIAL PRIMARY KEY,
                mon VARCHAR(50),
                phan_mon VARCHAR(50),
                khoi INT,
                tuan INT NOT NULL,
                tiet_ppct INT NOT NULL,
                ten_bai_day TEXT NOT NULL
            );
        """)

        # 2. Bảng Biến động lịch dạy (Nghỉ/Bù/Thay/BDHSG)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bien_dong_lich_day (
                id SERIAL PRIMARY KEY,
                magv VARCHAR(20) NOT NULL,
                loai VARCHAR(50) NOT NULL,
                ngay DATE NOT NULL,
                buoi VARCHAR(10),
                tiet_tkb INT NOT NULL,
                lop VARCHAR(20),
                ly_do TEXT,
                trang_thai VARCHAR(20) DEFAULT 'CHO_DUYET'
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ THÀNH CÔNG! Đã tạo xong tất cả các bảng trên CSDL mà không tốn dung lượng!")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    khoi_tao_he_thong()
