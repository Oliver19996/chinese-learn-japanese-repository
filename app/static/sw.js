const CACHE = "hanashi-v1";
const PRECACHE = [
  "/",
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/icons/icon-192.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/media/")) return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
