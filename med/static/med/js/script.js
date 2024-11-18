document.addEventListener("DOMContentLoaded", () => {
    const userPreference = localStorage.getItem("theme");
    const systemPreference = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

    if (userPreference) {
        setTheme(userPreference);
    } else {
        setTheme(systemPreference);
    }

    updateButtonText();
});

function setTheme(theme) {
    document.body.classList.toggle("dark-theme", theme === "dark");
    localStorage.setItem("theme", theme);

    const logo = document.querySelector("header img");
    const edit_imgs = document.querySelectorAll(".edit_img");
    const f_img = document.querySelectorAll(".f_img");
    
    if (logo) {
        if (theme === "dark") {
            logo.setAttribute("src", logo.getAttribute("data-dark-src"));
        } else {
            logo.setAttribute("src", logo.getAttribute("data-light-src"));
        }
    }

    edit_imgs.forEach(img => {
        if (theme === "dark") {
            img.setAttribute("src", img.getAttribute("data-dark-src"));
        } else {
            img.setAttribute("src", img.getAttribute("data-light-src"));
        }
    });

    f_img.forEach(img => {
        if (theme === "dark") {
            img.setAttribute("src", img.getAttribute("data-dark-src"));
        } else {
            img.setAttribute("src", img.getAttribute("data-light-src"));
        }
    });
}

const themeToggleLight = document.getElementById("theme-toggle-light");
const themeToggleDark = document.getElementById("theme-toggle-dark");

if (themeToggleLight) {
    themeToggleLight.addEventListener("click", (event) => {
        event.preventDefault();
        setTheme("light");
        updateButtonText();
    });
}

if (themeToggleDark) {
    themeToggleDark.addEventListener("click", (event) => {
        event.preventDefault();
        setTheme("dark");
        updateButtonText();
    });
}

function updateButtonText() {
    const isDarkTheme = document.body.classList.contains("dark-theme");
    if (themeToggleLight) {
        themeToggleLight.style.display = isDarkTheme ? "inline" : "none";
    }
    if (themeToggleDark) {
        themeToggleDark.style.display = isDarkTheme ? "none" : "inline";
    }
}
