# pkg_excel_helper.py
import openpyxl
from openpyxl.cell.cell import MergedCell
from openpyxl.styles import Font, Alignment, Border, Side
import copy

# Cỡ chữ chuẩn chung cho toàn bộ phiếu kê khai
DEFAULT_FONT_NAME = "Times New Roman"
DEFAULT_FONT_SIZE = 13

font_default_13 = Font(name=DEFAULT_FONT_NAME, size=DEFAULT_FONT_SIZE, bold=False)

def safe_set(ws, row, col, value=None, font=None, align=None):
    """Gán an toàn tuyệt đối: Luôn tìm về ô gốc, không ghi vào MergedCell phụ, chuẩn font 13"""
    cell = ws.cell(row=row, column=col)
    if isinstance(cell, MergedCell):
        for rng in ws.merged_cells.ranges:
            if rng.min_row <= row <= rng.max_row and rng.min_col <= col <= rng.max_col:
                cell = ws.cell(row=rng.min_row, column=rng.min_col)
                break
    
    if not isinstance(cell, MergedCell):
        if value is not None:
            cell.value = value
        # Áp dụng font truyền vào, nếu không có thì đảm bảo Times New Roman 13
        if font: 
            cell.font = font
        elif not cell.font or cell.font.size != DEFAULT_FONT_SIZE:
            # Giữ nguyên in đậm/nghiêng nếu có, chỉ nâng size lên 13
            is_b = cell.font.bold if cell.font else False
            is_i = cell.font.italic if cell.font else False
            cell.font = Font(name=DEFAULT_FONT_NAME, size=DEFAULT_FONT_SIZE, bold=is_b, italic=is_i)

        if align: 
            cell.alignment = align
    return cell

def unmerge_and_merge_exact(ws, cell_range, value, font=None, align=None):
    """Xóa merge cũ, gán giá trị vào ô gốc TRƯỚC RỒI MỚI MERGE (Chống 100% lỗi Read-Only)"""
    min_col, min_row, max_col, max_row = openpyxl.utils.range_boundaries(cell_range)
    
    # 1. Hủy bất kỳ vùng merge nào bị trùng/chồng lấn
    for rng in list(ws.merged_cells.ranges):
        if not (rng.max_row < min_row or rng.min_row > max_row or rng.max_col < min_col or rng.min_col > max_col):
            ws.merged_cells.remove(rng)
            
    # 2. Gán giá trị vào ô đầu tiên TRƯỚC KHI MERGE
    top_cell = ws.cell(row=min_row, column=min_col)
    top_cell.value = value
    
    # Đảm bảo font 13
    if font: 
        top_cell.font = font
    else:
        top_cell.font = font_default_13

    if align: 
        top_cell.alignment = align

    # 3. Tiến hành merge lại
    ws.merge_cells(start_row=min_row, start_column=min_col, end_row=max_row, end_column=max_col)

def clone_row_style(ws, src_row, dest_row, max_col=11):
    """Sao chép style nhưng ép chuẩn chiều cao dòng 22-24 và font chữ 13"""
    if src_row in ws.row_dimensions and ws.row_dimensions[src_row].height:
        ws.row_dimensions[dest_row].height = max(ws.row_dimensions[src_row].height, 22)
    else:
        ws.row_dimensions[dest_row].height = 22

    for c in range(1, max_col + 1):
        src_cell = ws.cell(row=src_row, column=c)
        dest_cell = ws.cell(row=dest_row, column=c)
        if not isinstance(dest_cell, MergedCell) and src_cell.has_style:
            try:
                dest_cell.border = copy.copy(src_cell.border)
                dest_cell.fill = copy.copy(src_cell.fill)
                dest_cell.alignment = copy.copy(src_cell.alignment)
                dest_cell.number_format = src_cell.number_format
                
                # Copy font nhưng ép size thành 13
                is_b = src_cell.font.bold if src_cell.font else False
                is_i = src_cell.font.italic if src_cell.font else False
                dest_cell.font = Font(name=DEFAULT_FONT_NAME, size=DEFAULT_FONT_SIZE, bold=is_b, italic=is_i)
            except Exception:
                pass

def find_row_in_cols(ws, text, cols=('A', 'B'), min_r=1, max_r=300):
    for r in range(min_r, min(ws.max_row + 1, max_r)):
        for c in cols:
            val = str(ws[f'{c}{r}'].value or '').strip()
            if text.lower() in val.lower(): 
                return r
    return None

def find_row_by_marker(ws, marker, col='K', min_r=1, max_r=300):
    for r in range(min_r, min(ws.max_row + 1, max_r)):
        val = str(ws[f'{col}{r}'].value or '').strip()
        if marker.lower() in val.lower(): 
            return r
    return None