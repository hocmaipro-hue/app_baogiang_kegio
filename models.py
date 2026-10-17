# models.py
import psycopg2
from config import DB_URI


def create_all_tables():
  """Khởi tạo cấu trúc 8 bảng cơ bản trên CSDL PostgreSQL (Supabase)."""
  try:
    connection = psycopg2.connect(DB_URI)
    cursor = connection.cursor()

    create_queries = """
        -- 1. Bảng Giáo viên & Phân quyền
        CREATE TABLE IF NOT EXISTS giao_vien (
            magv VARCHAR(50) PRIMARY KEY,
            tengv VARCHAR(100) NOT NULL,
            matkhau VARCHAR(100) NOT NULL DEFAULT '123456',
            to_bo_mon VARCHAR(50),
            role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'TO_TRUONG', 'GV')),
            chuc_vu VARCHAR(50),
            kiem_nhiem VARCHAR(100),
            dinh_muc_tiet INT DEFAULT 17,
            tiet_giam_tru INT DEFAULT 0
        );

        -- 2. Bảng Phân phối chương trình
        CREATE TABLE IF NOT EXISTS ppct (
            id SERIAL PRIMARY KEY,
            khoi INT NOT NULL,
            mon_hoc VARCHAR(50) NOT NULL,
            phan_mon VARCHAR(100),
            tuan INT NOT NULL,
            tieu_de_bai_hoc TEXT NOT NULL,
            so_tiet INT NOT NULL,
            to_bo_mon VARCHAR(50)
        );

        -- 3. Bảng Thời khóa biểu
        CREATE TABLE IF NOT EXISTS tkb (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            thu VARCHAR(20) NOT NULL,
            tiet INT NOT NULL,
            lop VARCHAR(20) NOT NULL,
            mon VARCHAR(50) NOT NULL,
            phan_mon VARCHAR(100)
        );

        -- 4. Bảng Sổ báo giảng
        CREATE TABLE IF NOT EXISTS so_bao_giang (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            ngay DATE NOT NULL,
            tuan_hoc INT NOT NULL,
            tiet_thu INT NOT NULL,
            lop VARCHAR(20) NOT NULL,
            mon VARCHAR(50) NOT NULL,
            phan_mon VARCHAR(100),
            ppct_id INT REFERENCES ppct(id) ON DELETE SET NULL,
            trang_thai VARCHAR(50) DEFAULT 'Đã dạy'
        );

        -- 5. Bảng Lịch sử nghỉ
        CREATE TABLE IF NOT EXISTS lich_su_nghi (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            ngay_nghi DATE NOT NULL,
            so_tiet INT NOT NULL,
            loai_nghi VARCHAR(100) NOT NULL,
            ly_do TEXT
        );

        -- 6. Bảng Lịch sử dạy thay
        CREATE TABLE IF NOT EXISTS lich_su_day_thay (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            ngay_day DATE NOT NULL,
            gv_duoc_thay VARCHAR(100) NOT NULL,
            lop VARCHAR(20) NOT NULL,
            so_tiet INT NOT NULL,
            ly_do TEXT
        );

        -- 7. Bảng Lịch sử dạy bù
        CREATE TABLE IF NOT EXISTS lich_su_day_bu (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            ngay_day_bu DATE NOT NULL,
            lop VARCHAR(20) NOT NULL,
            so_tiet INT NOT NULL,
            ly_do TEXT
        );

        -- 8. Bảng Bồi dưỡng HSG
        CREATE TABLE IF NOT EXISTS bdhsg (
            id SERIAL PRIMARY KEY,
            magv VARCHAR(50) REFERENCES giao_vien(magv) ON DELETE CASCADE,
            mon VARCHAR(50) NOT NULL,
            lop VARCHAR(20) NOT NULL,
            so_tiet_tuan INT NOT NULL,
            so_tuan INT NOT NULL
        );
        """
    cursor.execute(create_queries)
    connection.commit()
    print("🎉 Khởi tạo cấu trúc 8 bảng thành công trên Supabase!")
    return True
  except Exception as error:
    print(f"❌ Lỗi khởi tạo bảng: {error}")
    return False
  finally:
    if "connection" in locals() and connection:
      cursor.close()
      connection.close()


if __name__ == "__main__":
  create_all_tables()