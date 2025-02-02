document.addEventListener("DOMContentLoaded", function() {
    const themeToggle = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const languageToggle = document.getElementById("language-toggle");
    const languageText = document.getElementById("language-text");

    // Get stored theme and language preference
    const savedTheme = localStorage.getItem("theme");
    const savedLanguage = localStorage.getItem("language");

    // Apply saved theme
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        themeIcon.classList.replace("fa-moon", "fa-sun");
    }

    // Apply saved language
    if (savedLanguage === "vi") {
        switchToVietnamese();
    }

    // Toggle Dark Mode
    themeToggle.addEventListener("click", function() {
        document.body.classList.toggle("dark-mode");

        if (document.body.classList.contains("dark-mode")) {
            themeIcon.classList.replace("fa-moon", "fa-sun");
            localStorage.setItem("theme", "dark");
        } else {
            themeIcon.classList.replace("fa-sun", "fa-moon");
            localStorage.setItem("theme", "light");
        }
    });

    // Toggle Language (English/Vietnamese)
    languageToggle.addEventListener("click", function() {
        if (languageText.innerText === "EN") {
            switchToVietnamese();
        } else {
            switchToEnglish();
        }
    });

    function switchToVietnamese() {
        document.querySelectorAll("[data-vi]").forEach(el => {
            el.innerText = el.getAttribute("data-vi");
        });
        languageText.innerText = "VI";
        localStorage.setItem("language", "vi");
    }

    function switchToEnglish() {
        document.querySelectorAll("[data-en]").forEach(el => {
            el.innerText = el.getAttribute("data-en");
        });
        languageText.innerText = "EN";
        localStorage.setItem("language", "en");
    }
});
