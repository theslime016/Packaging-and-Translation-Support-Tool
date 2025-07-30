# Bộ công cụ hỗ trợ dịch thuật Light Novel

Tổng hợp các script Python dùng để tải, dọn dẹp, và gộp nội dung light novel từ các nguồn khác nhau như Baka-Tsuki, CClaw Translations, hoặc từ các file HTML/TXT có sẵn.

## Mục lục
- [Yêu cầu cài đặt](#yêu-cầu-cài-đặt)
- [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
  - [1. `clear.py` - Dọn dẹp và gộp file HTML](#1-clearpy---dọn-dẹp-và-gộp-file-html)
  - [2. `merge.py` - Gộp file TXT](#2-mergepy---gộp-file-txt)
  - [3. `bakatsuki.py` - Chuyển đổi file HTML từ Baka-Tsuki](#3-bakatsukipy---chuyển-đổi-file-html-từ-baka-tsuki)
  - [4. `CClaw.py` - Tải truyện từ CClaw Translations](#4-cclawpy---tải-truyện-từ-cclaw-translations)
  - [5. `bakatsuki-illustrations.py` - Tải ảnh minh họa từ Baka-Tsuki](#5-bakatsuki-illustrationspy---tải-ảnh-minh-họa-từ-baka-tsuki)
  - [6. `CClaw-illustrations.py` - Tải ảnh minh họa từ CClaw](#6-cclaw-illustrationspy---tải-ảnh-minh-họa-từ-cclaw)
  - [7. `change.py` - Đổi tên file hàng loạt](#7-changepy---đổi-tên-file-hàng-loạt)

## Yêu cầu cài đặt

Trước khi sử dụng, bạn cần cài đặt các thư viện Python cần thiết.

1.  Tạo một file tên là `requirements.txt` với nội dung sau:
    ```txt
    requests
    beautifulsoup4
    selenium
    Pillow
    colorama
    ```
2.  Mở terminal hoặc command prompt và chạy lệnh:
    ```bash
    pip install -r requirements.txt
    ```
3.  Đối với các script sử dụng **Selenium** (`bakatsuki-illustrations.py`), bạn cần cài đặt [Google Chrome](https://www.google.com/chrome/) và [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/) phiên bản tương thích.

---

## Hướng dẫn sử dụng

Mỗi script đều có phần **CẤU HÌNH** ở đầu file. Bạn chỉ cần chỉnh sửa các biến trong phần này để phù hợp với nhu cầu của mình.

### 1. `clear.py` - Dọn dẹp và gộp file HTML

*   **Chức năng:** Gộp nhiều file HTML/XHTML từ một thư mục thành một file TXT duy nhất, đồng thời làm sạch các tag HTML và thêm tiêu đề chương.
*   **Cách hoạt động:**
    1.  Tìm tất cả file `.html` hoặc `.xhtml` trong `input_folder`.
    2.  Sắp xếp các file theo thứ tự số trong tên file.
    3.  Với mỗi file, dùng biểu thức chính quy (regex) để:
        *   Xóa tag `<title>`.
        *   Chuyển tag `<img>` thành `[IMAGE: đường_dẫn]`.
        *   Tạo dòng mới từ tag `<br>` và `</p>`.
        *   Loại bỏ tất cả các tag HTML còn lại.
    4.  Tự động thêm tiêu đề "Chap X:" cho mỗi file có chứa chữ.
    5.  Ghi toàn bộ nội dung đã xử lý vào một file TXT duy nhất.
*   **Cấu hình:**
    ```python
    # ========== CẤU HÌNH ==========  
    input_folder = r"sources\HTML"
    output_folder = r"sources"
    output_filename = "MaouA V11.txt"
    ENABLE_CHAPTER_TITLES = True # True để bật, False để tắt tiêu đề chương
    # ==============================
    ```
*   **Ví dụ:** Bạn có thư mục `sources\HTML` chứa các file `1.html`, `2.html`,... Sau khi chạy script, bạn sẽ có một file `sources\MaouA V11.txt` chứa toàn bộ nội dung đã được làm sạch.

### 2. `merge.py` - Gộp file TXT

*   **Chức năng:** Gộp nhiều file TXT từ một thư mục thành một file duy nhất, với khả năng tự động thêm số chương và tiêu đề từ tên file.
*   **Cách hoạt động:**
    1.  Đọc tất cả các file `.txt` trong `folder_path`.
    2.  Phân tích tên file để trích xuất số chương và tiêu đề. Hỗ trợ nhiều định dạng như `第01話 Tên chap`, `01 - Tên chap`.
    3.  Sắp xếp các file một cách tự nhiên (natural sort) để đảm bảo `chap-2.txt` đứng trước `chap-10.txt`.
    4.  Thêm tiêu đề chương vào đầu mỗi file (nếu được bật).
    5.  Tự động thử nhiều bảng mã (utf-16, utf-8,...) để đọc file một cách an toàn.
*   **Cấu hình:**
    ```python
    # ===== CẤU HÌNH TÙY CHỌN =====
    ADD_CHAP_NUMBER = True  # Bật/Tắt thêm "Chap + số"
    ADD_CHAP_TITLE  = True  # Bật/Tắt thêm "Tên chap"
    REMOVE_DAI_WA   = False # Bỏ phần "第〇〇話" nếu có
    folder_path = r"sources\Maou"
    output_file = os.path.join(r"sources", "MaouA.txt")
    # ==============================
    ```

### 3. `bakatsuki.py` - Chuyển đổi file HTML từ Baka-Tsuki

*   **Chức năng:** Chuyển đổi một file HTML **đã tải về** từ Baka-Tsuki thành một file TXT có định dạng sạch đẹp, phân chia chương mục rõ ràng.
*   **Cách hoạt động:**
    1.  Đọc và phân tích file HTML bằng `BeautifulSoup`.
    2.  Xác định cấu trúc chương dựa trên các thẻ `<h2>` (chương chính) và `<h3>` (phần nhỏ).
    3.  Trích xuất văn bản từ thẻ `<p>` và chuyển đổi các gallary ảnh thành định dạng `[IMAGE: ...]`.
    4.  Bỏ qua các phần không cần thiết như "Translator's Notes".
    5.  Lưu nội dung đã định dạng vào file TXT.
*   **Cấu hình:**
    ```python
    PROCESS_MODE = 'single' # 'single' để xử lý 1 file, 'folder' để xử lý cả thư mục
    INPUT_PATH = "sources/Magi/input.html" # Đường dẫn file hoặc thư mục
    OUTPUT_DIR = "sources/Magi2"
    INCLUDE_ILLUSTRATIONS = False # True để lấy cả phần ảnh minh họa
    ```

### 4. `CClaw.py` - Tải truyện từ CClaw Translations

*   **Chức năng:** Tự động tải toàn bộ các chương của một bộ truyện từ trang Mục lục (TOC) của CClaw Translations và lưu thành các file TXT theo từng Volume.
*   **Cách hoạt động:**
    1.  Truy cập URL của trang TOC.
    2.  Tìm tất cả các link chương và phân loại chúng theo Volume.
    3.  Truy cập tuần tự từng link chương.
    4.  Trên trang chương, trích xuất tiêu đề và nội dung chính.
    5.  Gộp nội dung các chương thuộc cùng một Volume và lưu vào một file TXT riêng.
*   **Cấu hình:**
    ```python
    TOC_URLS = [
        "https://cclawtranslations.home.blog/anata-wo-akiramekirenai-moto-iinazuke-ja-dame-desu-ka-toc/"
    ]
    CRAWL_REAL_TITLE_FROM_CHAPTER = True # Lấy tiêu đề từ trang chương thay vì từ TOC
    OUTPUT_DIR = "sources/2HN"
    ```

### 5. `bakatsuki-illustrations.py` - Tải ảnh minh họa từ Baka-Tsuki

*   **Chức năng:** Tự động lấy link toàn bộ ảnh minh họa và tải về ảnh bìa của mỗi Volume từ một trang project trên Baka-Tsuki.
*   **Cách hoạt động:**
    1.  Sử dụng `Selenium` để truy cập trang project và tìm các link đến trang "Illustrations" của mỗi volume.
    2.  Truy cập từng trang "Illustrations" để lấy link ảnh chất lượng cao.
    3.  Lưu tất cả các link ảnh vào một file `.txt` duy nhất, được sắp xếp theo Volume.
    4.  Tải ảnh đầu tiên của mỗi volume về làm ảnh bìa.
    5.  Sử dụng thư viện `Pillow` để nén ảnh bìa xuống dưới 1MB và lưu dưới dạng `.jpg`.
*   **Cấu hình:**
    ```python
    PROJECT_URL = 'https://www.baka-tsuki.org/project/index.php?title=Absolute_Duo'
    OUTPUT_FOLDER = 'test/results'
    ```

### 6. `CClaw-illustrations.py` - Tải ảnh minh họa từ CClaw

*   **Chức năng:** Tương tự script cho Baka-Tsuki, nhưng được tùy chỉnh để hoạt động với cấu trúc trang của CClaw Translations.
*   **Cách hoạt động:**
    1.  Truy cập trang TOC để lấy danh sách link các chương.
    2.  Truy cập từng link chương và tìm tất cả các thẻ `<img>` hợp lệ.
    3.  Lưu tất cả link ảnh vào một file `.txt`, phân loại theo Volume.
    4.  Nếu một chương là trang "Illustrations", tải ảnh đầu tiên về làm bìa và nén nó xuống dưới 1MB.
*   **Cấu hình:**
    ```python
    TOC_URLS = [
        "https://cclawtranslations.home.blog/mayo-chiki-toc/",
        # Thêm các URL TOC khác vào đây
    ]
    OUTPUT_DIR = "test/results"
    ```

### 7. `change.py` - Đổi tên file hàng loạt

*   **Chức năng:** Một tiện ích đơn giản để đổi tên tất cả các file trong một thư mục thành một chuỗi số thứ tự (1, 2, 3,...).
*   **Cách hoạt động:**
    1.  Liệt kê tất cả các file trong `folder_path`.
    2.  Sắp xếp các file dựa trên số có trong tên file cũ.
    3.  Đổi tên từng file theo thứ tự `1.ext`, `2.ext`, `3.ext`... (giữ lại phần mở rộng `.ext` của file gốc).
*   **Cấu hình:**
    ```python
    folder_path = r"sources\ODSEPUB"
    ```
*   **Ví dụ:** Thư mục của bạn chứa `chapter-1.txt`, `chapter-10.txt`, `chapter-2.txt`. Sau khi chạy, chúng sẽ được đổi tên thành `1.txt`, `2.txt`, `3.txt`.
