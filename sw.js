const CACHE = 'cantata-v1';
const FILES = ['/', '/manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(cache => cache.addAll(FILES)));
});

self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});

self.addEventListener('push', e => {
  const data = e.data?.json() || { title: "새 공지!", body: "칸타타 투어 소식" };
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: 'https://via.placeholder.com/192x192/ff1744/ffffff?text=🎄',
    badge: 'https://via.placeholder.com/64x64/ff1744/ffffff?text=!',
    vibrate: [200, 100, 200],
    tag: 'cantata-notice'
  });
});
