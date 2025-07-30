import re
import os
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# === CẤU HÌNH ===
TOC_URLS = [
    "https://cclawtranslations.home.blog/anata-wo-akiramekirenai-moto-iinazuke-ja-dame-desu-ka-toc/"
]
CRAWL_REAL_TITLE_FROM_CHAPTER = True
OUTPUT_DIR = "sources/2HN"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# === HÀM XỬ LÝ ===
def extract_real_chapter_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find('h2', class_='wp-block-heading')
    if title_tag:
        return title_tag.get_text(strip=True)

    for tag in soup.select("h1, h2, h3, p strong"):
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)

    return "No Title"


def extract_chapter_text(soup: BeautifulSoup) -> str:
    content_div = soup.find("div", class_="entry-content")
    if not content_div:
        return ""
    paras = content_div.find_all("p")
    return "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))


def get_project_name_from_url(url: str) -> str:
    slug = urlparse(url).path.strip("/").split("/")[-1]
    return re.sub(r'\W+', '_', slug).strip("_").title()


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^\w\s.-]', '', name)
    return name.replace(" ", "_")


def get_toc_entries(toc_url):
    resp = requests.get(toc_url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    content_div = soup.find("div", class_="entry-content")
    if not content_div:
        print("❌ Không tìm thấy nội dung TOC.")
        return []

    entries = []
    seen = set()
    current_volume = None

    for elem in content_div.find_all(['p', 'h2', 'h3', 'a']):
        text = elem.get_text(strip=True)
        if not text:
            continue

        vol_match = re.search(r"(Volume\s*\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if vol_match:
            current_volume = vol_match.group(1).strip()
            continue

        if elem.name == "a" and elem.has_attr("href"):
            href = elem['href'].split('?')[0].strip()

            if not re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                continue

            if (
                "illustration" in text.lower()
                or "?share=" in href
                or "#" in href
                or href in seen
            ):
                continue

            seen.add(href)
            entries.append((current_volume, text, href))

    print(f"✅ Tìm thấy {len(entries)} chương (sau khi lọc).")
    return entries


def format_chapter_title(index: int, title: str) -> str:
    if title.lower().startswith("prologue"):
        return f"Prologue: {title[len('Prologue'):].strip()}"
    return f"Chap {index}: {title}"


def save_volume_file(output_dir, project_name, volume_name, lines):
    if not lines:
        return
    safe_volume = sanitize_filename(volume_name)
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{project_name} - {safe_volume}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"💾 Đã lưu {volume_name} vào: {filename}")


def crawl_project(toc_url):
    project_name = get_project_name_from_url(toc_url)
    print(f"\n{'=' * 60}")
    print(f"📘 DỰ ÁN: {project_name}")
    print(f"🔗 TOC: {toc_url}")

    entries = get_toc_entries(toc_url)
    if not entries:
        print("⚠️ Không có chương nào để xử lý.")
        return

    current_volume = ""
    chapter_index = 0
    volume_lines = []

    for idx, (volume, toc_title, url) in enumerate(entries, 1):
        if volume != current_volume:
            if current_volume and volume_lines:
                save_volume_file(OUTPUT_DIR, project_name, current_volume, volume_lines)
            current_volume = volume
            chapter_index = 0
            volume_lines = [f"{current_volume}\n\n"]
            print(f"\n📚 BẮT ĐẦU VOLUME: {current_volume}")

        short_url = url.split("/")[-2:]
        print(f"  ├─ [{idx:02}] 🕐 {short_url}...", end=' ', flush=True)

        try:
            resp = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(resp.text, "html.parser")

            if CRAWL_REAL_TITLE_FROM_CHAPTER:
                real_title = extract_real_chapter_title(soup)
            else:
                real_title = toc_title

            content = extract_chapter_text(soup)
            if not content.strip():
                print("⚠️ Rỗng / lỗi.")
                continue

            chapter_index += 1
            title_line = format_chapter_title(chapter_index, real_title)
            volume_lines.append(f"{title_line}\n\n{content}\n\n")
            print(f"✅ {title_line}")
            time.sleep(1.5)

        except Exception as e:
            print(f"❌ Lỗi: {e}")

    if current_volume and volume_lines:
        save_volume_file(OUTPUT_DIR, project_name, current_volume, volume_lines)

    print(f"\n🎉 HOÀN TẤT DỰ ÁN: {project_name}")
    print(f"{'=' * 60}\n")

# === MAIN ===
def main():
    for url in TOC_URLS:
        crawl_project(url)
    print("\n🏁 ĐÃ XỬ LÝ TOÀN BỘ LINK.")


if __name__ == "__main__":
    main()