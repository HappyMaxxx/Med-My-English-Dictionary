document.addEventListener('DOMContentLoaded', function() {
    const notificationsLink = document.getElementById('notifications-link');
    const notificationsDropdown = document.getElementById('notifications-dropdown');

    function updateNotifications() {
        const notiUrl = document.body.dataset.notiUrl;

        fetch(notiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            const unreadCountSpan = notificationsLink.querySelector('.notification-count');
            if (data.unread_count > 0) {
                if (!unreadCountSpan) {
                    const newSpan = document.createElement('span');
                    newSpan.className = 'notification-count';
                    notificationsLink.appendChild(newSpan);
                }
                notificationsLink.querySelector('.notification-count').textContent = 
                    data.unread_count > 99 ? '99+' : data.unread_count;
            } else if (unreadCountSpan) {
                unreadCountSpan.remove();
            }

            const ul = notificationsDropdown.querySelector('ul');
            ul.innerHTML = ''; 
            if (data.notifications.length > 0) {
                data.notifications.forEach(notification => {
                    const li = document.createElement('li');
                    li.innerHTML = `${notification.message} <small>${notification.time_create}</small>`;
                    ul.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'There are no unread messages';
                ul.appendChild(li);
            }
        })
        .catch(error => console.error('Error fetching notifications:', error));
    }

    updateNotifications();

    setInterval(updateNotifications, 10000);
});
