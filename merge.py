import os
import re

# ===== CẤU HÌNH TÙY CHỌN =====
ADD_CHAP_NUMBER = False        # Bật/Tắt thêm "Chap + số"
ADD_CHAP_TITLE  = False        # Bật/Tắt thêm "Tên chap"
REMOVE_DAI_WA   = False        # Bỏ phần "第〇〇話" nếu có
# ==============================

# Đường dẫn thư mục chứa các file cần gộp
folder_path = r"sources\Maou"

# Tên file đầu ra
output_file = os.path.join(r"sources", "MaouA.txt")

def extract_chapter_info(filename):
    # Tách phần tên không có đuôi
    base_name = os.path.splitext(filename)[0]

    # Mặc định nếu không có số thì gán giá trị 99999 để sort cuối
    chapter_num = 99999
    cleaned_title = base_name

    # Ưu tiên nếu có dạng: 第001話～森での発見～
    m = re.match(r'^第(\d+)話[～~]?(.*)$', base_name)
    if m:
        chapter_num = int(m.group(1).lstrip('0') or '0')
        cleaned_title = m.group(2).strip()
    else:
        # Nếu có dạng "001-Tên chương"
        m = re.match(r'^(\d+)[\-_ ]+(.*)$', base_name)
        if m:
            chapter_num = int(m.group(1).lstrip('0') or '0')
            cleaned_title = m.group(2).strip()
        else:
            # Nếu có số ở đầu không theo định dạng cố định
            m = re.match(r'^(\d+)', base_name)
            if m:
                chapter_num = int(m.group(1).lstrip('0') or '0')
                cleaned_title = base_name[len(m.group(0)):].strip()

    # Xử lý bỏ "第xx話" nếu bật flag
    if REMOVE_DAI_WA:
        tokens = re.split(r'\s|　', cleaned_title, maxsplit=1)
        if len(tokens) > 1 and re.match(r'^第.+話$', tokens[0]):
            cleaned_title = tokens[1].strip()

    return chapter_num, cleaned_title, filename

# Lấy danh sách file .txt và phân tích
txt_files = [
    extract_chapter_info(f)
    for f in os.listdir(folder_path)
    if f.endswith(".txt") and f != "merged.txt"
]

def natural_key(text):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', text)]

# Sắp xếp theo natural order theo tên file gốc
txt_files.sort(key=lambda x: natural_key(x[2]))

# Gộp các file
with open(output_file, 'w', encoding='utf-16') as outfile:
    for chapter_num, cleaned_title, filename in txt_files:
        file_path = os.path.join(folder_path, filename)
        print(f"Đang thêm file: {filename}")

        # Tạo tiêu đề nếu được bật
        header_parts = []
        if ADD_CHAP_NUMBER and chapter_num != 99999:
            header_parts.append(f"Chap {chapter_num}")
        if ADD_CHAP_TITLE and cleaned_title:
            header_parts.append(cleaned_title)

        if header_parts:
            header_line = ": ".join(header_parts)
            outfile.write(header_line + "\n\n")

        # Ghi nội dung
        def read_file_safely(file_path):
            encodings_to_try = ['utf-16', 'utf-8-sig', 'utf-8', 'shift_jis']
            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError(f"Không thể đọc file {file_path} với các encoding phổ biến.")
        contents = read_file_safely(file_path)
        outfile.write(contents)
        outfile.write("\n\n")