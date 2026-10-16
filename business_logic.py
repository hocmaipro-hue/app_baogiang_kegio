# business_logic.py
import psycopg2
from config import DB_URI

def create_bao_giang_record(magv, ngay, tuan_hoc, tiet_thu, lop, mon, phan_mon, ppct_id):
    """Thêm mới một dòng sổ báo giảng"""
    try:
        connection = psycopg2.connect(DB_URI)
        cursor = connection.cursor()
        sql = """
            INSERT INTO so_bao_giang (magv, ngay, tuan_hoc, tiet_thu, lop, mon, phan_mon, ppct_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (magv, ngay, tuan_hoc, tiet_thu, lop, mon, phan_mon, ppct_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Lỗi thêm sổ báo giảng: {e}")
        return False
    finally:
        if 'connection' in locals() and connection:
            connection.close()
