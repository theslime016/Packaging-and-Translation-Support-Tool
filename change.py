import os
import re

# Đường dẫn thư mục cần đổi tên
folder_path = r"sources\ODSEPUB"

# Lấy danh sách file
files = os.listdir(folder_path)

# Sắp xếp theo số trong tên file (nếu có)
def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    else:
        return float('inf')

files = sorted(files, key=extract_number)

# Đổi tên thành 1, 2, 3, ...
for idx, old_name in enumerate(files, 1):
    old_path = os.path.join(folder_path, old_name)
    
    # Giữ đuôi file cũ
    ext = os.path.splitext(old_name)[1]
    
    new_name = f"{idx}{ext}"
    new_path = os.path.join(folder_path, new_name)
    
    print(f"Đổi {old_name} -> {new_name}")
    os.rename(old_path, new_path)