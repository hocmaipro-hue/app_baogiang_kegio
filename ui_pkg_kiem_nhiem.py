# ui_pkg_kiem_nhiem.py
import tkinter as tk
from tkinter import messagebox
import psycopg2
from datetime import datetime
from config import DB_URI

def get_val(s, k, d=""): return s.get(k, d) if isinstance(s, dict) else getattr(s, k, d)

class CaiDatKiemNhiemWindow:
    def __init__(self, session, parent=None, tu_ngay_def="07/09/2026", den_ngay_def="03/10/2026"):
        self.session = session
        self.magv = get_val(session, 'magv', '')
        self.tengv = get_val(session, 'tengv', 'Giáo viên')

        self.dlg = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.dlg.title(f"Cài đặt Kiêm nhiệm & Giảm trừ định mức - {self.tengv}")
        self.dlg.geometry("620x580")
        self.dlg.grab_set()

        tk.Label(self.dlg, text="QUẢN LÝ & CÀI ĐẶT THÔNG TIN CỐ ĐỊNH VÀ BDHSG", 
                 font=("Arial", 11, "bold"), fg="#1a5276").pack(pady=10)

        f = tk.Frame(self.dlg, padx=15, pady=5)
        f.pack(fill=tk.BOTH, expand=True)

        # 1. Tải thông tin cố định từ database
        data_gv = {}
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT con_nho, giam_tru_con_nho, hopdong_lan_dau, giam_tru_hopdong_landau, 
                       kiem_nhiem_2, giam_tru_kn2 
                FROM giao_vien WHERE magv = %s
            """, (self.magv,))
            row_gv = cur.fetchone()
            cur.close()
            conn.close()
            if row_gv:
                data_gv = {
                    "con_nho": row_gv[0] or "",
                    "giam_tru_con_nho": row_gv[1] or 0,
                    "hopdong_lan_dau": row_gv[2] or "",
                    "giam_tru_hopdong_landau": row_gv[3] or 0,
                    "kiem_nhiem_2": row_gv[4] or "",
                    "giam_tru_kn2": row_gv[5] or 0,
                }
        except Exception as e:
            print(f"Lỗi tải dữ liệu GV: {e}")

        # 2. Tạo các ô nhập từ 1 đến 6
        self.entries = {}
        fields_info = [
            ("con_nho", "1. Con nhỏ (Số lượng/Thông tin):"),
            ("giam_tru_con_nho", "2. Giảm trừ con nhỏ (Giờ):"),
            ("hopdong_lan_dau", "3. Hợp đồng lần đầu (Thông tin):"),
            ("giam_tru_hopdong_landau", "4. Giảm trừ HĐ lần đầu (Giờ):"),
            ("kiem_nhiem_2", "5. Kiêm nhiệm 2 (Tên nhiệm vụ):"),
            ("giam_tru_kn2", "6. Giảm trừ KN2 (Giờ):"),
        ]

        row_idx = 0
        for field_key, label_text in fields_info:
            tk.Label(f, text=label_text, font=("Arial", 9, "bold")).grid(row=row_idx, column=0, sticky="w", pady=4)
            txt_entry = tk.Entry(f, width=32, font=("Arial", 9))
            txt_entry.insert(0, str(data_gv.get(field_key, "")))
            txt_entry.grid(row=row_idx, column=1, columnspan=3, pady=4, padx=5, sticky="w")
            self.entries[field_key] = txt_entry
            row_idx += 1

        # 3. Dòng 7 & 8: Thống kê BDHSG theo khoảng ngày
        tk.Label(f, text="7. Thống kê BDHSG (Từ ngày - Đến ngày):", 
                 font=("Arial", 9, "bold"), fg="#1a5276").grid(row=row_idx, column=0, sticky="w", pady=(10, 4))
        
        fr_date = tk.Frame(f)
        fr_date.grid(row=row_idx, column=1, columnspan=3, sticky="w", pady=(10, 4))
        
        tk.Label(fr_date, text="Từ:", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.txt_tungay = tk.Entry(fr_date, width=11, font=("Arial", 9))
        self.txt_tungay.insert(0, tu_ngay_def)
        self.txt_tungay.pack(side=tk.LEFT, padx=2)

        tk.Label(fr_date, text="Đến:", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.txt_denngay = tk.Entry(fr_date, width=11, font=("Arial", 9))
        self.txt_denngay.insert(0, den_ngay_def)
        self.txt_denngay.pack(side=tk.LEFT, padx=2)
        row_idx += 1

        # Lấy sẵn dữ liệu HSG
        hsg_data = {"thuc_day": 0, "quy_doi": 0}
        try:
            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(SUM(bdhsg_thuc_day), 0), COALESCE(SUM(bdhsg_quy_doi), 0) FROM kg_hoc_sinh_gioi WHERE magv = %s", (self.magv,))
            r = cur.fetchone()
            if r: hsg_data["thuc_day"], hsg_data["quy_doi"] = r[0], r[1]
            cur.close(); conn.close()
        except Exception: pass

        tk.Label(f, text="   + BDHSG thực dạy (Số buổi):", font=("Arial", 9)).grid(row=row_idx, column=0, sticky="w", pady=4)
        self.entry_thucday = tk.Entry(f, width=32, font=("Arial", 9))
        self.entry_thucday.insert(0, str(hsg_data["thuc_day"]))
        self.entry_thucday.grid(row=row_idx, column=1, columnspan=3, pady=4, padx=5, sticky="w")
        row_idx += 1

        tk.Label(f, text="   + BDHSG quy đổi (x 1.5 - Có thể sửa lẻ):", font=("Arial", 9)).grid(row=row_idx, column=0, sticky="w", pady=4)
        self.entry_quydoi = tk.Entry(f, width=32, font=("Arial", 9))
        self.entry_quydoi.insert(0, str(hsg_data["quy_doi"]))
        self.entry_quydoi.grid(row=row_idx, column=1, columnspan=3, pady=4, padx=5, sticky="w")
        row_idx += 1

        btn_tinh = tk.Button(f, text="🔄 Lọc & Tính lại theo khoảng ngày", bg="#ebf5fb", 
                             font=("Arial", 8, "bold"), command=self.tinh_lai_theo_khoang_ngay)
        btn_tinh.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)

        tk.Button(self.dlg, text="💾 Lưu cấu hình & Đồng bộ", bg="#d4efdf", 
                  font=("Arial", 9, "bold"), command=self.save_kn).pack(pady=10)

    def tinh_lai_theo_khoang_ngay(self):
        try:
            dt_start = datetime.strptime(self.txt_tungay.get().strip(), "%d/%m/%Y").date()
            dt_end = datetime.strptime(self.txt_denngay.get().strip(), "%d/%m/%Y").date()

            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM bien_dong_lich_day 
                WHERE magv = %s AND (loai ILIKE '%%HSG%%' OR loai ILIKE '%%Bồi dưỡng HSG%%')
                  AND ngay BETWEEN %s AND %s AND trang_thai != 'DA_HUY'
            """, (self.magv, dt_start, dt_end))
            r = cur.fetchone()
            so_buoi = r[0] if r else 0
            quy_doi = so_buoi * 1.5
            cur.close(); conn.close()

            self.entry_thucday.delete(0, tk.END)
            self.entry_thucday.insert(0, str(so_buoi))
            self.entry_quydoi.delete(0, tk.END)
            self.entry_quydoi.insert(0, str(quy_doi))
            messagebox.showinfo("Thành công", f"Đã tính lại: {so_buoi} buổi ({quy_doi} giờ quy đổi)!", parent=self.dlg)
        except Exception as ex:
            messagebox.showerror("Lỗi", f"Vui lòng kiểm tra định dạng DD/MM/YYYY: {ex}", parent=self.dlg)

    def save_kn(self):
        try:
            con_nho = self.entries['con_nho'].get().strip()
            gt_cn = float(self.entries['giam_tru_con_nho'].get().strip() or 0)
            hd_dau = self.entries['hopdong_lan_dau'].get().strip()
            gt_hd = float(self.entries['giam_tru_hopdong_landau'].get().strip() or 0)
            kn_2 = self.entries['kiem_nhiem_2'].get().strip()
            gt_kn2 = float(self.entries['giam_tru_kn2'].get().strip() or 0)
            
            bdhsg_thuc = float(self.entry_thucday.get().strip() or 0)
            bdhsg_qd = float(self.entry_quydoi.get().strip() or 0)

            conn = psycopg2.connect(DB_URI)
            cur = conn.cursor()
            cur.execute("""
                UPDATE giao_vien 
                SET con_nho = %s, giam_tru_con_nho = %s, 
                    hopdong_lan_dau = %s, giam_tru_hopdong_landau = %s, 
                    kiem_nhiem_2 = %s, giam_tru_kn2 = %s
                WHERE magv = %s
            """, (con_nho, gt_cn, hd_dau, gt_hd, kn_2, gt_kn2, self.magv))
            
            cur.execute("DELETE FROM kg_hoc_sinh_gioi WHERE magv = %s", (self.magv,))
            cur.execute("""
                INSERT INTO kg_hoc_sinh_gioi (magv, ngay_day_hsg, bdhsg_thuc_day, bdhsg_quy_doi)
                VALUES (%s, %s, %s, %s)
            """, (self.magv, f"Từ {self.txt_tungay.get()} đến {self.txt_denngay.get()}", bdhsg_thuc, bdhsg_qd))
            
            conn.commit()
            cur.close(); conn.close()

            self.dlg.destroy()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin và thống kê BDHSG thành công!")
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Vui lòng nhập đúng định dạng số vào các ô giờ và số buổi!", parent=self.dlg)
        except Exception as ex:
            messagebox.showerror("Lỗi cơ sở dữ liệu", f"Không thể lưu dữ liệu: {ex}", parent=self.dlg)
