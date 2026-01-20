
let notificationStack = [];

function showNotification(message, id) {
    const notifBox = document.createElement('div');
    notifBox.className = 'notification-popup';
    notifBox.style.position = 'fixed';
    notifBox.style.right = '30px';
    notifBox.style.zIndex = '9999';
    notifBox.style.background = '#007bff';
    notifBox.style.color = 'white';
    notifBox.style.padding = '16px 24px';
    notifBox.style.borderRadius = '8px';
    notifBox.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
    notifBox.style.minWidth = '300px';
    notifBox.style.maxWidth = '400px';
    notifBox.style.wordWrap = 'break-word';
    
    
    const bottomOffset = 30 + (notificationStack.length * 90);
    notifBox.style.bottom = bottomOffset + 'px';
    
    notifBox.innerHTML = `<span>${message}</span> <button class="notif-close-btn" style="margin-left:16px;background:none;border:none;color:white;font-weight:bold;cursor:pointer;">&times;</button>`;
    
    document.body.appendChild(notifBox);
    notificationStack.push(notifBox);
    
    const closeBtn = notifBox.querySelector('.notif-close-btn');
    closeBtn.onclick = function() {
        removeNotification(notifBox, id);
    };
}

function removeNotification(notifBox, id) {
    notifBox.remove();
    notificationStack = notificationStack.filter(n => n !== notifBox);
    
    
    notificationStack.forEach((n, idx) => {
        const bottomOffset = 30 + (idx * 90);
        n.style.bottom = bottomOffset + 'px';
    });
    
    if (id) markNotificationRead(id);
}

function markNotificationRead(id) {
    fetch(`/api/notifications/read/${id}`, {method: 'POST'});
}

function pollNotifications() {
    fetch('/api/notifications')
        .then(r => r.json())
        .then(data => {
            console.log('[Notifications] Polled /api/notifications, got:', data);
            if (data.notifications && data.notifications.length > 0) {
                console.log('[Notifications] Showing ' + data.notifications.length + ' notifications');
                
                data.notifications.forEach((n) => {
                    console.log('[Notifications] Showing: ' + n.message);
                    showNotification(n.message, n.id);
                });
            }
        })
        .catch(err => console.error('[Notifications] Poll error:', err));
}


if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => {
        console.log('[Notifications] Page loaded, starting poll...');
        pollNotifications();
    });
} else {
    console.log('[Notifications] Page already loaded, starting poll...');
    pollNotifications();
}

setTimeout(() => {
    console.log('[Notifications] Polling for delayed login notifications...');
    pollNotifications();
}, 12000);

console.log('[Notifications] Starting polling every 90 seconds');
setInterval(pollNotifications, 90000);  
