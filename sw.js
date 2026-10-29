/* Comptabilité : garde l'application dans le téléphone pour qu'elle s'ouvre sans réseau. Version f83b063d97 */
const CACHE = "compta-f83b063d97";
const SHELL = ["./", "complet.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable.png", "apple-touch-icon.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("compta-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
/* Fichiers de l'application : réponse immédiate depuis le téléphone, mise à jour en arrière-plan.
   Les demandes vers Google ne passent pas par ici. */
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url); if (u.origin !== self.location.origin) return;
  const key = r.mode === "navigate" ? (/complet\.html$/.test(u.pathname) ? "complet.html" : "./") : r;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(key, {ignoreSearch: true});
    const net = (r.mode === "navigate" ? fetch(r.url, {cache: "no-cache", credentials: "same-origin"}) : fetch(r)).then(res => { if (res && res.ok && res.type === "basic") c.put(key, res.clone()); return res; }).catch(() => null);
    if (hit){ e.waitUntil(net); return hit; }
    return (await net) || new Response("Hors réseau", {status: 503, headers: {"Content-Type": "text/plain; charset=utf-8"}});
  }));
});
