function toggleActiveTab(tab) {
    if (tab.classList.contains('active')) {
        tab.classList.remove('active');
    } else {
        tab.classList.add('active');
    }

    let contentId = tab.getAttribute('data-tab');
    let contents = document.querySelectorAll('.tab-content');
    contents.forEach(function (content) {
        if (content.id === contentId) {
            content.classList.remove('hidden');
        } else {
            content.classList.add('hidden');
        }
    });

    let hiddenInputs = tab.querySelectorAll('input[type="hidden"]');
    hiddenInputs.forEach(function(input) {
        let currentValue = input.value;
        if (currentValue === "true") {
            input.value = "false";
        } else {
            input.value = "true";
        }
    });
}