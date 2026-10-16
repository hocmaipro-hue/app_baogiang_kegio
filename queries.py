# queries.py
import psycopg2
from config import DB_URI

def get_bao_giang_by_role(session):
    """Lấy danh sách sổ báo giảng tự động phân quyền theo session"""
    try:
        connection = psycopg2.connect(DB_URI)
        cursor = connection.cursor()
        
        role = session["role"]
        magv = session["magv"]
        to_bo_mon = session["to_bo_mon"]
        
        if role == "ADMIN":
            sql = "SELECT s.*, g.tengv FROM so_bao_giang s JOIN giao_vien g ON s.magv = g.magv ORDER BY s.ngay DESC"
            cursor.execute(sql)
        elif role == "TO_TRUONG":
            sql = "SELECT s.*, g.tengv FROM so_bao_giang s JOIN giao_vien g ON s.magv = g.magv WHERE g.to_bo_mon = %s ORDER BY s.ngay DESC"
            cursor.execute(sql, (to_bo_mon,))
        else:
            sql = "SELECT s.*, g.tengv FROM so_bao_giang s JOIN giao_vien g ON s.magv = g.magv WHERE s.magv = %s ORDER BY s.ngay DESC"
            cursor.execute(sql, (magv,))
            
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Lỗi truy vấn: {e}")
        return []
    finally:
        if 'connection' in locals() and connection:
            connection.close()
