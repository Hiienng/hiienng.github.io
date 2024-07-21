// script.js
document.getElementById("hamburger").onclick = function() {
  var navItems = document.getElementById("nav-items");
  if (navItems.style.display === "flex") {
      navItems.style.display = "none";
  } else {
      navItems.style.display = "flex";
  }
};
