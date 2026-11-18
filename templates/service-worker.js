const CACHE_NAME = 'tracker-v2'; // ভার্সন বাড়ানো হলো
const urlsToCache = ['/', '/target', '/manifest.json'];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) return caches.delete(cacheName);
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    // PWA-তে API কল ক্যাশে করা যাবে না
    if (event.request.url.includes('/api/')) {
        return; 
    }
    
    // বাকি ফাইলগুলোর জন্য নেটওয়ার্ক ফার্স্ট স্ট্র্যাটেজি
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
