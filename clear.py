import os
import re

# ========== CẤU HÌNH ==========  
input_folder = r"sources\HTML"
output_folder = r"sources"
output_filename = "MaouA V11.txt"

# ✅ Bật/tắt tiêu đề "Chap n:"
ENABLE_CHAPTER_TITLES = True
CHAPTER_PREFIX = "Chap"
CHAPTER_SEPARATOR = ""
# ==============================

os.makedirs(output_folder, exist_ok=True)

def convert_html_to_text(html_content):
    # ❌ Xóa luôn phần <title>...</title>
    html_content = re.sub(r'<title>.*?</title>', '', html_content, flags=re.IGNORECASE | re.DOTALL)

    # ✅ Thay <img ... src="..."> → [IMAGE: ...]
    html_content = re.sub(
        r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>',
        r'\n[IMAGE: \1]\n',
        html_content, flags=re.IGNORECASE
    )
    # ✅ Thay <image ... xlink:href="..."> → [IMAGE: ...]
    html_content = re.sub(
        r'<image[^>]*(?:xlink:href|href)=["\']([^"\']+)["\'][^>]*>',
        r'\n[IMAGE: \1]\n',
        html_content, flags=re.IGNORECASE
    )
    # ✅ Xuống dòng với <br> và </p>
    html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'</p>', '\n', html_content, flags=re.IGNORECASE)
    # ✅ Xóa tag HTML khác
    html_content = re.sub(r'<[^>]+>', '', html_content)
    # ✅ Dọn khoảng trắng dư
    html_content = re.sub(r'\n\s*\n+', '\n\n', html_content)
    return html_content.strip()


def get_title(html_content):
    match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

def is_text_only_images(text):
    cleaned = re.sub(r'\[IMAGE: [^\]]+\]', '', text)
    cleaned = re.sub(r'\s+', '', cleaned)
    return not cleaned

def get_all_html_files(folder):
    def extract_numbers(filename):
        # Trích tất cả các số trong tên file để sắp xếp đúng thứ tự
        return [int(num) for num in re.findall(r'\d+', filename)]

    html_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".html") or file.endswith(".xhtml"):
                full_path = os.path.join(root, file)
                html_files.append(full_path)

    return sorted(html_files, key=lambda x: extract_numbers(os.path.basename(x)))

# ✅ Gộp toàn bộ nội dung
all_text = ""
all_files = get_all_html_files(input_folder)

if not all_files:
    print("⚠️ Không tìm thấy file HTML hoặc XHTML nào trong thư mục.")
else:
    chapter_count = 0
    title_used = False

    for index, file_path in enumerate(all_files):
        print(f"▶ Đang ghép file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()
        text = convert_html_to_text(html)

        # ✅ Nếu chỉ chứa ảnh → không chap, chỉ thêm ảnh
        if is_text_only_images(text):
            all_text += f"\n{text.strip()}\n"
            continue

        # ✅ Cộng số chương nếu có nội dung chữ
        chapter_count += 1

        if ENABLE_CHAPTER_TITLES:
            if not title_used:
                title = get_title(html)
                if title:
                    chapter_title = f"{CHAPTER_PREFIX} {chapter_count}: {title}"
                    title_used = True
                else:
                    chapter_title = f"{CHAPTER_PREFIX} {chapter_count}:"
            else:
                chapter_title = f"{CHAPTER_PREFIX} {chapter_count}:"

            # ✅ Không xuống dòng giữa chap title và nội dung
            all_text += f"\n\n{CHAPTER_SEPARATOR} {chapter_title} {CHAPTER_SEPARATOR}\n{text.strip()}\n"
        else:
            all_text += f"\n\n{text.strip()}\n"

    output_path = os.path.join(output_folder, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_text.strip())

    print(f"\n✅ Hoàn tất! File TXT đã tạo ở: {output_path}")