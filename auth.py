import psycopg2
from config import DB_URI

def authenticate_user(magv, matkhau):
    """Xác thực đăng nhập trả về session dictionary"""
    print(f"=== BẮT ĐẦU XỬ LÝ ĐĂNG NHẬP CHO: {magv} ===")
    connection = None
    try:
        print("1. Đang tiến hành kết nối tới Supabase...")
        connection = psycopg2.connect(DB_URI, sslmode='require', connect_timeout=5)
        print("2. Kết nối CSDL thành công! Đang truy vấn bảng giao_vien...")
        
        cursor = connection.cursor()
        query = "SELECT magv, tengv, role, to_bo_mon, chuc_vu FROM giao_vien WHERE magv = %s AND matkhau = %s"
        cursor.execute(query, (magv, matkhau))
        row = cursor.fetchone()
        print(f"3. Truy vấn hoàn tất. Dữ liệu tìm thấy: {row is not None}")
        
        if row:
            return {
                "magv": row[0],
                "tengv": row[1],
                "role": row[2],
                "to_bo_mon": row[3],
                "chuc_vu": row[4]
            }
        return None
    except Exception as e:
        print(f"❌ XẢY RA LỖI TRONG QUÁ TRÌNH KẾT NỐI: {str(e)}")
        raise Exception(f"Không thể kết nối CSDL Supabase: {str(e)}")
    finally:
        if connection:
            connection.close()
            print("4. Đã đóng kết nối CSDL an toàn.")

def has_permission(current_session, required_role):
    hierarchy = {"GV": 1, "TO_TRUONG": 2, "ADMIN": 3}
    user_level = hierarchy.get(current_session.get("role", "GV"), 0)
    required_level = hierarchy.get(required_role, 99)
    return user_level >= required_level
