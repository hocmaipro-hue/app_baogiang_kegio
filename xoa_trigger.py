import psycopg2
from config import DB_URI

def xoa_trigger_database():
    """Hàm Python thực hiện kết nối và xóa bỏ Trigger ngầm trên cơ sở dữ liệu"""
    try:
        # Kết nối tới cơ sở dữ liệu Supabase PostgreSQL
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        
        print("Đang tiến hành xóa Trigger và Function trên Database...")
        
        # 1. Xóa Trigger gắn trên bảng bien_dong_lich_day
        cursor.execute("DROP TRIGGER IF EXISTS trg_sync_bdhsg ON bien_dong_lich_day;")
        
        # 2. Xóa hàm xử lý ngầm (Function) của trigger đó
        cursor.execute("DROP FUNCTION IF EXISTS trigger_sync_bdhsg();")
        
        # Lưu thay đổi và đóng kết nối
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Đã xóa thành công Trigger SQL khỏi cơ sở dữ liệu!")
        
    except Exception as e:
        print(f"Lỗi khi xóa Trigger: {e}")

if __name__ == "__main__":
    xoa_trigger_database()
