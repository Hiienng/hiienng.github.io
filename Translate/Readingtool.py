from bs4 import BeautifulSoup
import glob
import os

# Nội dung HTML hiện có
html_header = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog: Cẩm nang nghề data</title>
    <link rel="stylesheet" href="styles_3.css">
</head>
<body>
    <nav class="top-nav">
        <a href="http:/datascience101hub.com">
            <div class="logo">DATA SCIENCE 101</div>
        </a>
        <div class="nav-items">
            <a href="http:/datascience101hub.com">Projects</a>
            <a href="http:/datascience101hub.com/index_blog_preface.html">Blog</a>
            <a href="http:/datascience101hub.com">About us</a>
        </div>
    </nav>
    <nav class="side-nav">
        <ul>
            <li><a href="https://datascience101hub.com/index_blog_preface.html">Giới Thiệu</a></li>
            <li><a href="https://datascience101hub.com/index_blog_C1.html">C1: Data Career Path <span class="toggle-icon">▶</span></a>
                <ul class="sub-menu" style="display: none;">
                    <li><a href="index_blog_preface_1.html">Mục con 1</a></li>
                    <li><a href="index_blog_preface_2.html">Mục con 2</a></li>
                    <li><a href="index_blog_preface_3.html">Mục con 3</a></li>
                </ul>
            </li>
            <li><a href="https://datascience101hub.com/index_blog_C2.html">C2: Hệ quản trị dữ liệu <span class="toggle-icon">▶</span></a>
                <ul class="sub-menu" style="display: none;">
                    <li><a href="index_blog_preface_1.html">Mục con 1</a></li>
                    <li><a href="index_blog_preface_2.html">Mục con 2</a></li>
                    <li><a href="index_blog_preface_3.html">Mục con 3</a></li>
                </ul>
            </li>
            <li><a href="https://datascience101hub.com/ndex_blog_C3.html">C3: Công cụ báo cáo <span class="toggle-icon">▶</span></a>
                <ul class="sub-menu" style="display: none;">
                    <li><a href="index_blog_preface_1.html">Mục con 1</a></li>
                    <li><a href="index_blog_preface_2.html">Mục con 2</a></li>
                    <li><a href="index_blog_preface_3.html">Mục con 3</a></li>
                </ul>
            </li>
            <li><a href="https://datascience101hub.com/ndex_blog_C4.html">C4: Ngôn ngữ lập trình <span class="toggle-icon">▶</span></a></li>
        </ul>
    </nav>

    <main>
        <!-- Nội dung cần thêm vào đây -->
    </main>
    
    <script src="script_3.js"></script>
</body>
</html>
"""

# Phân tích cú pháp HTML
soup = BeautifulSoup(html_header, 'html.parser')

# Đường dẫn tới thư mục chứa tệp HTML
folder_path = r'C:\Users\admin\Desktop\Hiensfolder\1. Working\Github\Hiienng.github.io\Translate'
# Tìm tất cả các tệp HTML trong thư mục
html_files = glob.glob(os.path.join(folder_path, '*.html'))

# Tìm thẻ <main>
main_tag = soup.find('main')

# Đọc và thêm nội dung của từng tệp HTML vào thẻ <main>
for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        file_soup = BeautifulSoup(file_content, 'html.parser')
        main_tag.append(file_soup)

# Ghi lại nội dung HTML đã chỉnh sửa vào một tệp
output_path = os.path.join(folder_path, 'output.html')
with open(output_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

print("Nội dung đã được thêm vào thẻ <main> và ghi lại vào tệp 'output.html'.")
