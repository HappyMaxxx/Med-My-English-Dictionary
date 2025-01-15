document.querySelectorAll(".tab-btn").forEach(button => {
    button.addEventListener("click", () => {
        const tab = button.dataset.tab;

        document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");

        document.querySelectorAll(".tab-content").forEach(content => content.classList.add("hidden"));
        document.getElementById(tab).classList.remove("hidden");
    });
});