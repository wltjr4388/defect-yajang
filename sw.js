// 결함 야장 오프라인 캐시 — build_pwa.py가 생성
const CACHE = "dy-a05ac28493";
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png', 'vendor/pdf.min.js', 'vendor/pdf.worker.min.js', 'vendor/pdf-lib.min.js', 'vendor/xlsx.full.min.js'];
// 새 버전은 기다리지 않고 바로 적용 (아이패드는 앱을 닫아도 옛 버전이 남는 경우가 있음)
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  // 앱 화면(index.html): 인터넷이 되면 새로 받고, 4초 안에 안 되면 저장본
  if (e.request.mode === "navigate") {
    e.respondWith((async () => {
      const cached = await caches.match("index.html");
      try {
        const net = await Promise.race([fetch(e.request, { cache: "no-store" }), new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), 4000))]);
        if (net && net.ok) return net;
      } catch (err) {}
      return cached || fetch(e.request);
    })());
    return;
  }
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((hit) => hit || fetch(e.request).catch(() => caches.match("index.html")))
  );
});
