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
    if (theme === "dark") {
        logo.setAttribute("src", logo.getAttribute("data-dark-src"));
    } else {
        logo.setAttribute("src", logo.getAttribute("data-light-src"));
    }
}

const themeToggleLight = document.getElementById("theme-toggle-light");
const themeToggleDark = document.getElementById("theme-toggle-dark");

themeToggleLight.addEventListener("click", (event) => {
    event.preventDefault();
    setTheme("light");
    updateButtonText();
});

themeToggleDark.addEventListener("click", (event) => {
    event.preventDefault();
    setTheme("dark");
    updateButtonText();
});

function updateButtonText() {
    const isDarkTheme = document.body.classList.contains("dark-theme");
    themeToggleLight.style.display = isDarkTheme ? "inline" : "none";
    themeToggleDark.style.display = isDarkTheme ? "none" : "inline";
}
