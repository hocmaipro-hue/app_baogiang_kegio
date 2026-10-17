# auth.py
import psycopg2
from config import DB_URI

def authenticate_user(magv, matkhau):
    """Xác thực đăng nhập trả về session dictionary"""
    try:
        connection = psycopg2.connect(DB_URI)
        cursor = connection.cursor()
        query = "SELECT magv, tengv, role, to_bo_mon, chuc_vu FROM giao_vien WHERE magv = %s AND matkhau = %s"
        cursor.execute(query, (magv, matkhau))
        row = cursor.fetchone()
        
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
        print(f"Lỗi đăng nhập: {e}")
        return None
    finally:
        if 'connection' in locals() and connection:
            connection.close()

def has_permission(current_session, required_role):
    """Kiểm tra ma trận phân quyền thừa kế cấp bậc (Admin > Tổ trưởng > GV)"""
    hierarchy = {"GV": 1, "TO_TRUONG": 2, "ADMIN": 3}
    user_level = hierarchy.get(current_session.get("role", "GV"), 0)
    required_level = hierarchy.get(required_role, 99)
    return user_level >= required_level