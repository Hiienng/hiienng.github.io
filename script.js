// script.js
document.getElementById("hamburger").onclick = function() {
  var navItems = document.getElementById("nav-items");
  if (navItems.style.display === "flex") {
      navItems.style.display = "none";
  } else {
      navItems.style.display = "flex";
  }
};

/////////////////////////////////////////////////////
// Màn hình BLOG
// Lấy tất cả các biểu tượng có class "toggle-icon"
var toggleIcons = document.querySelectorAll('.toggle-icon');

// Thêm sự kiện click cho từng biểu tượng
toggleIcons.forEach(function(icon) {
icon.addEventListener('click', function(event) {
  event.preventDefault(); // Ngăn chặn hành vi mặc định của biểu tượng

  // Lấy menu con tương ứng với biểu tượng
  var subMenu = this.parentElement.nextElementSibling;

  // Hiển thị/ẩn menu con
  if (subMenu.style.display === 'none') {
    subMenu.style.display = 'block';
    this.textContent = '▼'; // Thay đổi biểu tượng
  } else {
    subMenu.style.display = 'none';
    this.textContent = '▶'; // Thay đổi biểu tượng
  }
});
});

/////////////////////////////////////////////////////
// Màn hình HAMBUGER
const hamburger = document.querySelector('.hamburger');
const navItems = document.querySelector('.nav-items');
const closeBtn = document.querySelector('.close-btn');

hamburger.addEventListener('click', () => {
    navItems.classList.toggle('active');
    closeBtn.style.display = navItems.classList.contains('active') ? 'block' : 'none'; // Hiện nút "X" khi menu mở
});

closeBtn.addEventListener('click', () => {
    navItems.classList.remove('active');
    closeBtn.style.display = 'none'; // Ẩn nút "X" khi menu đóng
});