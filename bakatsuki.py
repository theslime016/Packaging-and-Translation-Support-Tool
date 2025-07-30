import re
import os
from bs4 import BeautifulSoup, Tag

class OutputFormatter:
    def __init__(self):
        self.volume_prefix = "Volume"
        self.chapter_prefix = "Chap"
        self.final_title_format = "{prefix} {num}: {title}"
        self.image_prefix = "[IMAGE: .../"
        self.image_suffix = "]"

    def format_volume(self, text: str) -> str:
        volume_number = re.search(r'\d+', text)
        return f"{self.volume_prefix} {volume_number.group(0)}" if volume_number else text

    def format_title(self, number: int, text: str) -> str:
        return self.final_title_format.format(prefix=self.chapter_prefix, num=number, title=text)

    def format_image(self, url: str) -> str:
        return f"{self.image_prefix}{url}{self.image_suffix}"

def extract_volume_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find('title')
    if title_tag:
        match = re.search(r'Volume\s+\d+', title_tag.get_text(), re.IGNORECASE)
        if match:
            return match.group(0)
    return "Unknown_Volume"

def get_content_container(soup: BeautifulSoup) -> Tag:
    for selector in ['div.mw-parser-output', 'div#mw-content-text', 'div#bodyContent']:
        container = soup.select_one(selector)
        if container:
            return container
    return None

def process_element_content(element: Tag, formatter: OutputFormatter) -> str:
    if element.name == 'p':
        return element.get_text(strip=True) + '\n'
    
    if element.name in ['ul', 'figure'] and 'gallery' in element.get('class', []):
        image_lines = [formatter.format_image(a.get('href').split('File:')[-1])
                       for a in element.find_all('a', class_='mw-file-description')
                       if a.get('href') and 'File:' in a.get('href')]
        return '\n'.join(image_lines) + '\n' if image_lines else ""
        
    if element.name == 'figure':
        img_link = element.find('a', class_='mw-file-description')
        if img_link and 'href' in img_link.attrs and 'File:' in img_link['href']:
            return formatter.format_image(img_link['href'].split('File:')[-1]) + '\n'
                
    return ""

def extract_and_format_content(soup: BeautifulSoup, formatter: OutputFormatter, include_illustrations: bool) -> str:
    content_div = get_content_container(soup)
    if not content_div:
        print("  ❌ Không tìm thấy nội dung chính trong file HTML.")
        return ""

    output_parts = []
    chapter_counter = 0
    last_h2_text = ""
    skip_current_section = False

    # ✅ Đã sửa recursive=True (hoặc bỏ hẳn vì mặc định là True)
    elements = content_div.find_all(['h2', 'h3', 'p', 'figure', 'ul'])

    print(f"  -> Tìm thấy {len(elements)} phần tử nội dung.")

    for element in elements:
        if element.find_parent(id='toc'):
            continue

        if skip_current_section and element.name != 'h2':
            continue

        if element.name == 'h2':
            skip_current_section = False
            h2_text = element.get_text(strip=True).replace('[edit]', '').strip()

            if "Translator's Notes & References" in h2_text:
                print("\n  -> Đã đến cuối nội dung, dừng lại.")
                break 

            if "Novel Illustrations" in h2_text and not include_illustrations:
                print(f"\nBỏ qua phần: '{h2_text}' (theo cấu hình)")
                skip_current_section = True
                continue

            last_h2_text = h2_text
            next_tag = element.find_next_sibling(lambda tag: isinstance(tag, Tag) and tag.name in ['p', 'figure', 'ul', 'h3'])

            if not (next_tag and next_tag.name == 'h3'):
                chapter_counter += 1
                formatted_title = formatter.format_title(chapter_counter, h2_text)
                output_parts.append(f"\n{formatted_title}\n\n")
                print(f"\nĐã thêm chương: {formatted_title}")

        elif element.name == 'h3':
            chapter_counter += 1
            part_text = element.get_text(strip=True).replace('[edit]', '').strip()
            part_number_match = re.search(r'\d+', part_text)
            part_number = part_number_match.group(0) if part_number_match else part_text.replace('Part ', '')

            title_parts = last_h2_text.split('–', 1)
            main_title = title_parts[0].strip()
            subtitle = f": {title_parts[1].strip()}" if len(title_parts) > 1 else ""
            new_formatted_title_part = f"{main_title}.{part_number}{subtitle}"

            final_title = formatter.format_title(chapter_counter, new_formatted_title_part)
            output_parts.append(f"{final_title}\n\n")
            print(f"  -> Đã thêm phần: {final_title}")
        
        else:
            content = process_element_content(element, formatter)
            if content:
                output_parts.append(content)

    return "".join(output_parts)

def process_single_file(html_path: str, output_path: str, include_illustrations: bool):
    print(f"\n--- Bắt đầu xử lý file: {os.path.basename(html_path)} ---")
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        formatter = OutputFormatter()
        volume = extract_volume_title(soup)
        formatted_volume = formatter.format_volume(volume)
        print(f"Đang trích xuất: {formatted_volume}")
        
        extracted_text = extract_and_format_content(soup, formatter, include_illustrations)

        if not extracted_text.strip():
            print("  ⚠️ Không có nội dung nào được trích xuất. File có thể trống hoặc sai định dạng.")
            return

        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(formatted_volume + '\n')
            outfile.write(extracted_text)

        print(f"--- ✅ Hoàn tất. Đã lưu vào: '{os.path.abspath(output_path)}' ---")

    except FileNotFoundError:
        print(f"  ❌ Lỗi: Không tìm thấy file '{html_path}'")
    except Exception as e:
        print(f"  ❌ Đã xảy ra lỗi khi xử lý file '{html_path}': {e}")

def main():
    PROCESS_MODE = 'single' #folder/single
    INPUT_PATH = "sources/Magi/1 - Maou na Ore to Fushihime no Yubiwa_Volume 5 - Baka-Tsuki.html"
    OUTPUT_DIR = "sources/Magi2"
    INCLUDE_ILLUSTRATIONS = False

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Đã tạo thư mục đầu ra: '{OUTPUT_DIR}'")

    if PROCESS_MODE.lower() == 'single':
        if not os.path.isfile(INPUT_PATH):
            print(f"❌ Lỗi: File đầu vào '{INPUT_PATH}' không tồn tại.")
            return
        output_filename = os.path.splitext(os.path.basename(INPUT_PATH))[0] + ".txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        process_single_file(INPUT_PATH, output_path, INCLUDE_ILLUSTRATIONS)

    elif PROCESS_MODE.lower() == 'folder':
        if not os.path.isdir(INPUT_PATH):
            print(f"❌ Lỗi: Thư mục đầu vào '{INPUT_PATH}' không tồn tại.")
            return

        html_files = sorted([f for f in os.listdir(INPUT_PATH) if f.lower().endswith(('.html', '.htm'))])
        if not html_files:
            print(f"Không tìm thấy file .html nào trong thư mục '{INPUT_PATH}'.")
            return

        print(f"Tìm thấy {len(html_files)} file HTML. Bắt đầu xử lý...")
        for filename in html_files:
            input_file_path = os.path.join(INPUT_PATH, filename)
            output_filename = os.path.splitext(filename)[0] + ".txt"
            output_file_path = os.path.join(OUTPUT_DIR, output_filename)
            process_single_file(input_file_path, output_file_path, INCLUDE_ILLUSTRATIONS)
        print("\n🎉 Đã xử lý xong tất cả các file.")
    else:
        print(f"❌ PROCESS_MODE không hợp lệ. Chọn 'single' hoặc 'folder'.")

if __name__ == '__main__':
    main()