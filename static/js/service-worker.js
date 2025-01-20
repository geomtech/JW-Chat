self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('jw-chat-cache').then(cache => {
            return cache.addAll([
                '/',
                '/index.html',
                '/static/css/jw-chat.css',
                '/static/css/jw-chat-custom.css',
                '/static/js/jw-chat.js',
                '/static/js/bible.js',
                'https://cdn.socket.io/4.0.1/socket.io.min.js',
                'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
            ]);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== 'jw-chat-cache') {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});