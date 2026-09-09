// Workbox Service Worker for CropHealthAI
// Caches static assets, community trends, and advisory responses for offline access

importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');

if (workbox) {
  console.log('[ServiceWorker] Workbox loaded successfully');

  workbox.core.skipWaiting();
  workbox.core.clientsClaim();

  // 1. Cache Navigation HTML
  workbox.routing.registerRoute(
    ({ request }) => request.mode === 'navigate',
    new workbox.strategies.NetworkFirst({
      cacheName: 'app-navigation-cache',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
      ],
    })
  );

  // 2. Cache Images & Icons (CacheFirst, 30 days)
  workbox.routing.registerRoute(
    ({ request }) => request.destination === 'image',
    new workbox.strategies.CacheFirst({
      cacheName: 'plant-images-cache',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 100,
          maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
        }),
      ],
    })
  );

  // 3. Cache Community Trends API responses (StaleWhileRevalidate)
  workbox.routing.registerRoute(
    ({ url }) => url.pathname.includes('/community/trends'),
    new workbox.strategies.StaleWhileRevalidate({
      cacheName: 'community-trends-api-cache',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 50,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        }),
      ],
    })
  );

  // 4. Cache Integrated Advisory API responses (StaleWhileRevalidate)
  workbox.routing.registerRoute(
    ({ url }) => url.pathname.includes('/advisory/'),
    new workbox.strategies.StaleWhileRevalidate({
      cacheName: 'advisory-api-cache',
      plugins: [
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [200],
        }),
        new workbox.expiration.ExpirationPlugin({
          maxEntries: 50,
          maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        }),
      ],
    })
  );

  // 5. Cache scripts and styles (StaleWhileRevalidate)
  workbox.routing.registerRoute(
    ({ request }) => request.destination === 'style' || request.destination === 'script' || request.destination === 'font',
    new workbox.strategies.StaleWhileRevalidate({
      cacheName: 'static-resources-cache',
    })
  );
} else {
  console.warn('[ServiceWorker] Workbox failed to load');
}
