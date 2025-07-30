import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
from colorama import Fore, Style, init

# ========== CẤU HÌNH ==========
TOC_URLS = [
    "https://cclawtranslations.home.blog/anata-wo-akiramekirenai-moto-iinazuke-ja-dame-desu-ka-toc/",
    "https://cclawtranslations.home.blog/asahina-wakaba-to-marumaru-na-kareshi-toc/",
    "https://cclawtranslations.home.blog/ankoku-kishi-to-issho-toc/",
    "https://cclawtranslations.home.blog/kibishii-onna-joushi-ga-koukousei-ni-modottara-ore-ni-dere-dere-suru-riyuu-ryoukataomoi-no-yaronaoshi-koukousei-seikatsu-toc/",
    "https://cclawtranslations.home.blog/mayo-chiki-toc/",
    "https://cclawtranslations.home.blog/overwrite-toc/",
    "https://cclawtranslations.home.blog/kawaikereba-hentai-demo-suki-ni-natte-kuremasu-ka-toc/",
    "https://cclawtranslations.home.blog/ore-ga-suki-nano-wa-imouto-dakedo-imouto-janai/",
    "https://cclawtranslations.home.blog/tsuyokute-new-saga-ln-toc/",
    "https://cclawtranslations.home.blog/inkyara-na-ore-to-ichatsukitai-tte-maji-kayo-toc"
]

VALID_IMG_DOMAIN = "https://cclawtranslations.home.blog/wp-content/uploads/"
OUTPUT_DIR = "test/results"
MAX_COVER_SIZE = 1024 * 1024  # 1MB

init(autoreset=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== HÀM TIỆN ÍCH ==========
def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "_", text)

def get_soup(url):
    try:
        res = requests.get(url)
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"❌ Lỗi khi tải {url}: {e}")
        return None

def compress_image_to_under_1mb(img_data, img_format):
    buffer = BytesIO()

    if img_format.upper() == "PNG":
        # Chuyển PNG sang JPEG để dễ nén nếu cần
        img_data = img_data.convert("RGB")
        img_format = "JPEG"

    quality = 95
    while True:
        buffer.seek(0)
        buffer.truncate(0)
        img_data.save(buffer, format=img_format, quality=quality, optimize=True)
        if buffer.tell() <= MAX_COVER_SIZE or quality <= 10:
            break
        quality -= 5
    
    return buffer.getvalue()


def save_compressed_image(img_url, output_path):
    try:
        res = requests.get(img_url)
        res.raise_for_status()
        img = Image.open(BytesIO(res.content))
        img_format = img.format if img.format in ['JPEG', 'PNG'] else 'JPEG'
        compressed = compress_image_to_under_1mb(img, img_format)
        
        print(f"    📦 Dung lượng sau nén: {len(compressed) // 1024} KB")

        with open(output_path, "wb") as f:
            f.write(compressed)
        print(f"✅ Đã tải cover: {output_path}")
    except Exception as e:
        print(f"❌ Lỗi tải ảnh cover: {img_url} – {e}")

def extract_project_name(url):
    path = urlparse(url).path.strip("/").replace("-toc", "")
    return sanitize_filename(path.split("/")[-1].replace("-", "_").title())

# ========== MAIN ==========
for TOC_URL in TOC_URLS:
    PROJECT_NAME = extract_project_name(TOC_URL)
    OUTPUT_LINK_FILE = os.path.join(OUTPUT_DIR, f"{PROJECT_NAME}_Links.txt")
    OUTPUT_IMAGE_DIR = os.path.join(OUTPUT_DIR, "Covers")
    os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

    print(f"\n🌐 Đang xử lý PJ: {Fore.CYAN}{PROJECT_NAME}{Style.RESET_ALL} ({TOC_URL})")
    soup = get_soup(TOC_URL)
    if not soup:
        continue

    all_links = soup.find_all("a", href=True)
    chap_links = [a["href"] for a in all_links if re.match(r"^https://cclawtranslations\.home\.blog/\d{4}/\d{2}/\d{2}/.+", a["href"])]

    volume_dict = {}
    for link in chap_links:
        match = re.search(r"volume[-\s]?(\d+(?:\.\d+)?)", link, re.IGNORECASE)
        volume = f"Volume {match.group(1)}" if match else "Unknown_Volume"
        volume_dict.setdefault(volume, []).append(link)

    with open(OUTPUT_LINK_FILE, "w", encoding="utf-8") as out_file:
        for volume, chapters in volume_dict.items():
            print(f"\n{Fore.CYAN}📦 Volume: {volume}{Style.RESET_ALL}")
            out_file.write(f"\n=== {volume} ===\n")

            for chap_idx, chap_url in enumerate(chapters, start=1):
                chap_soup = get_soup(chap_url)
                if not chap_soup:
                    continue

                title = chap_soup.title.string.strip() if chap_soup.title else chap_url
                print(f"{Fore.YELLOW}├─ 📖 Chương {chap_idx}: {title}{Style.RESET_ALL}")

                imgs = chap_soup.find_all("img")
                img_links = [
                    img["src"].split("?")[0]
                    for img in imgs
                    if img.get("src", "").startswith(VALID_IMG_DOMAIN)
                    and "cclawlogo1.png" not in img["src"]
                ]

                print(f"{Fore.GREEN}│   ├─ 🔗 {len(img_links)} ảnh hợp lệ{Style.RESET_ALL}")
                for link in img_links:
                    out_file.write(link + "\n")

                if "illustration" in chap_url.lower() and img_links:
                    ext = ".png" if img_links[0].endswith(".png") else ".jpg"
                    filename = f"{PROJECT_NAME}_{volume.replace(' ', '')}_Cover{ext}"
                    output_path = os.path.join(OUTPUT_IMAGE_DIR, sanitize_filename(filename))

                    print(f"{Fore.MAGENTA}│   └─ 🎯 Tải ảnh cover: {img_links[0]}{Style.RESET_ALL}")
                    save_compressed_image(img_links[0], output_path)

    print(f"\n📁 Đã lưu link ảnh: {Fore.GREEN}{OUTPUT_LINK_FILE}{Style.RESET_ALL}")
    print(f"🖼️ Ảnh cover lưu trong thư mục: {Fore.GREEN}{OUTPUT_IMAGE_DIR}{Style.RESET_ALL}")