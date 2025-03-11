function updateOrder() {
    const tabs = [...container.children];
    tabs.forEach((tab, index) => {
        tab.dataset.index = index;
    });
}

function logOrder() {
    const order = [...container.children].map(tab => tab.textContent.trim());
    document.getElementById('word-stat-order').value = order.join(',');
    document.getElementById('words-show-form').dispatchEvent(new Event('change'));
}