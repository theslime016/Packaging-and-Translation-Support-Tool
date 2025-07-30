import os
import re
import time
import requests
import io # Cần thiết cho việc nén trong bộ nhớ
from PIL import Image # Thư viện Pillow để xử lý ảnh
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# === CẤU HÌNH ===
PROJECT_URL = 'https://www.baka-tsuki.org/project/index.php?title=Absolute_Duo'
OUTPUT_FOLDER = 'test/results'
BASE_URL = 'https://www.baka-tsuki.org'

# Cấu hình Selenium
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

try:
    driver = webdriver.Chrome(options=chrome_options)
except WebDriverException as e:
    print(f"Lỗi khởi tạo WebDriver: {e}")
    print("Vui lòng đảm bảo bạn đã cài đặt Chrome và ChromeDriver phiên bản tương thích.")
    exit()

def compress_and_save_image(image_path, save_path, target_mb=1.0):
    """
    Nén một ảnh để có kích thước dưới target_mb và lưu lại.
    """
    target_bytes = target_mb * 1024 * 1024
    
    # Nếu ảnh gốc đã đủ nhỏ, chỉ cần sao chép nó
    if os.path.getsize(image_path) <= target_bytes:
        print(f"      → Ảnh gốc đã nhỏ hơn {target_mb}MB. Sao chép trực tiếp.")
        os.rename(image_path, save_path)
        return

    try:
        with Image.open(image_path) as img:
            # Chuyển đổi sang RGB nếu là RGBA hoặc P (PNG) để lưu dưới dạng JPEG
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Thử giảm chất lượng trước
            for quality in range(85, 10, -5):
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality)
                if buffer.tell() <= target_bytes:
                    print(f"      → Đã nén ảnh thành công (chất lượng: {quality}%)")
                    with open(save_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return
            
            # Nếu giảm chất lượng không đủ, hãy giảm kích thước ảnh
            print("      → Giảm chất lượng không đủ, tiến hành giảm độ phân giải...")
            w, h = img.size
            img.thumbnail((w * 0.9, h * 0.9)) # Giảm 10% mỗi lần
            
            # Thử lại với chất lượng cao sau khi đã giảm kích thước
            for quality in range(95, 10, -5):
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality)
                if buffer.tell() <= target_bytes:
                    print(f"      → Đã nén ảnh thành công (giảm res, chất lượng: {quality}%)")
                    with open(save_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return
            
            print(f"      ✗ Không thể nén ảnh xuống dưới {target_mb}MB. Lưu phiên bản cuối cùng.")
            img.save(save_path, format='JPEG', quality=10)

    except Exception as e:
        print(f"      ✗ Lỗi khi nén ảnh: {e}")
        # Nếu lỗi, chỉ cần di chuyển file gốc
        os.rename(image_path, save_path)
    finally:
        # Dọn dẹp file tạm nếu còn tồn tại
        if os.path.exists(image_path):
            os.remove(image_path)

def download_image_and_compress(url, folder, filename):
    """Tải một file ảnh, sau đó nén và lưu lại."""
    os.makedirs(folder, exist_ok=True)
    base_filename, _ = os.path.splitext(filename)
    final_save_path = os.path.join(folder, base_filename + ".jpg") # Luôn lưu dưới dạng JPG sau khi nén
    temp_save_path = os.path.join(folder, "temp_" + filename)

    try:
        print(f"      ↳ Đang tải ảnh bìa: {url}")
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        
        with open(temp_save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"      ✓ Tải xong, bắt đầu nén...")
        compress_and_save_image(temp_save_path, final_save_path, target_mb=1.0)
        
    except requests.exceptions.RequestException as e:
        print(f"      ✗ Lỗi khi tải ảnh bìa: {e}")
        # Dọn dẹp file tạm nếu có lỗi tải
        if os.path.exists(temp_save_path):
            os.remove(temp_save_path)
            
# --- Các hàm khác giữ nguyên từ trước ---

def get_page_soup(url, wait_for_selector=None):
    try:
        driver.get(url)
        if wait_for_selector:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector)))
        return BeautifulSoup(driver.page_source, 'html.parser')
    except Exception as e:
        print(f"    ✗ Lỗi khi tải URL {url}: {e}")
        return None

def get_project_title_and_soup(url):
    soup = get_page_soup(url)
    if not soup: return "Untitled Project", None
    title_tag = soup.find('h1', id='firstHeading')
    title = title_tag.text.split(' - ')[0].strip() if title_tag else "Untitled Project"
    return re.sub(r'[\\/*?:"<>|]', '', title), soup

def get_illustration_pages(soup):
    links = {}
    if not soup: return {}
    for a in soup.select('a[title*="Illustrations"]'):
        vol_match = re.search(r'Volume\s*(\d+)', a.get('title', ''), re.IGNORECASE)
        if vol_match:
            links[f"Volume {vol_match.group(1)}"] = BASE_URL + a['href']
    return links

def extract_all_image_links(illustration_page_url):
    print(f"    🔎 Đang phân tích trang: {illustration_page_url}")
    soup = get_page_soup(illustration_page_url, wait_for_selector="li.gallerybox")
    if soup is None: return []
    all_links = []
    for link_tag in soup.select('li.gallerybox .thumb a'):
        if not link_tag.has_attr('href'): continue
        image_soup = get_page_soup(BASE_URL + link_tag['href'])
        if not image_soup: continue
        full_image_link_tag = image_soup.select_one('div.fullImageLink a, #file a')
        if full_image_link_tag and full_image_link_tag.has_attr('href'):
            url = full_image_link_tag['href']
            all_links.append('https:' + url if url.startswith('//') else BASE_URL + url if url.startswith('/') else url)
    print(f"    ➤ Hoàn tất. Lấy được {len(all_links)} link ảnh.")
    return all_links

def save_links_to_file(folder, filename, links_by_volume):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    sort_key = lambda item: int(re.search(r'\d+', item[0]).group())
    total_links = 0
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"=== TẤT CẢ LINK ẢNH - {os.path.basename(filename).replace('.txt', '')} ===\n\n")
        for volume, links in sorted(links_by_volume.items(), key=sort_key):
            if links:
                f.write(f"--- {volume} ---\n")
                for link in links: f.write(link + '\n')
                f.write('\n')
                total_links += len(links)
    print(f"\n✅ Đã lưu danh sách {total_links} link vào tệp: {path}")

# === MAIN ===
try:
    print(f"🌐 Đang truy cập PJ: {PROJECT_URL}")
    title, soup = get_project_title_and_soup(PROJECT_URL)
    print(f"📘 Tên PJ: {title}")

    illustration_pages = get_illustration_pages(soup)
    print(f"📄 Tìm thấy {len(illustration_pages)} trang minh họa.")

    all_volume_links = {}
    if not illustration_pages:
        print("Không tìm thấy trang minh họa nào.")
    else:
        cover_download_folder = os.path.join(OUTPUT_FOLDER, "Covers_Compressed")
        for volume, url in sorted(illustration_pages.items(), key=lambda item: int(re.search(r'\d+', item[0]).group())):
            print(f"\n📥 Bắt đầu xử lý {volume}...")
            all_links = extract_all_image_links(url)
            if all_links:
                all_volume_links[volume] = all_links
                cover_url = all_links[0]
                file_ext = os.path.splitext(cover_url.split('?')[0])[1] or '.jpg'
                safe_volume_name = re.sub(r'[\\/*?:"<>|]', '', volume)
                filename = f"{title} - {safe_volume_name}{file_ext}"
                download_image_and_compress(cover_url, cover_download_folder, filename)
            else:
                print(f"    - Không lấy được link nào cho {volume}.")

    if all_volume_links:
        save_links_to_file(OUTPUT_FOLDER, f"{title} - All Links.txt", all_volume_links)
    else:
        print("\nKhông có link ảnh nào được thu thập.")
finally:
    if 'driver' in locals() and driver:
        driver.quit()
    print("\nHoàn tất. Trình duyệt đã đóng.")