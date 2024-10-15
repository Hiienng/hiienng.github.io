// script.js

// Menu Hamburger trên màn hình mobile
const hamburger = document.getElementById("hamburger");
const navItems = document.getElementById("nav-items");
const closeBtn = document.querySelector('.close-btn');

// Xử lý sự kiện nhấn hamburger và nút close
hamburger.addEventListener('click', () => {
    navItems.classList.toggle('active'); // Thêm/xóa class active để hiển thị/ẩn menu
    closeBtn.style.display = navItems.classList.contains('active') ? 'block' : 'none'; // Hiện nút "X" khi menu mở
});

closeBtn.addEventListener('click', () => {
    navItems.classList.remove('active');
    closeBtn.style.display = 'none'; // Ẩn nút "X" khi menu đóng
});

// #Blog #Tất cả các biểu tượng toggle (▼ ▶) cho sub-menu
const toggleIcons = document.querySelectorAll('.toggle-icon');

// #Index #Mobile #Thêm sự kiện click cho từng biểu tượng
toggleIcons.forEach(function(icon) {
    icon.addEventListener('click', function(event) {
        event.preventDefault(); // Ngăn chặn hành vi mặc định

        // Lấy menu con tương ứng với biểu tượng
        var subMenu = this.parentElement.nextElementSibling;

        // Sử dụng class để điều khiển hiển thị/ẩn
        if (subMenu.classList.contains('hidden')) {
            subMenu.classList.remove('hidden');
            this.textContent = '▼'; // Thay đổi biểu tượng
        } else {
            subMenu.classList.add('hidden');
            this.textContent = '▶'; // Thay đổi biểu tượng
        }
    });
});
