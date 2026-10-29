"""Test de l'application installable : connexion Google, hors réseau, photos gardées, retour du réseau, jeton expiré, refus."""
import asyncio, json, os, sys, base64, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock
from playwright.async_api import async_playwright
OUT = "pwa/out"; os.makedirs(OUT, exist_ok=True)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
REG = open("phone/fixture.json", encoding="utf-8").read()
URL = "http://127.0.0.1:8090/compta/"
def post(path, obj=None, raw=None):
    data = raw if raw is not None else json.dumps(obj or {}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8091" + path, data=data, method="POST")).read())
def state(): return json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
def telfiles(): return sorted(f["name"] for f in state()["files"] if "tel1" in f.get("parents", []) and not f.get("trashed"))
INIT = "window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth';"
async def lines(pg, sel, n=12): return [x for x in (await pg.inner_text(sel)).split("\n") if x.strip()][:n]
async def sync_t(pg): return await pg.inner_text("#h-sync-t")
async def wait_sync(pg, pred, t=8000):
    await pg.wait_for_function("(p) => { const s = document.getElementById('h-sync-t').textContent; return new RegExp(p).test(s); }", arg=pred, timeout=t)
async def main():
    mock.reset(REG); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        # 1. Premier lancement : connexion Google par redirection silencieuse, livres lus
        await pg.goto(URL)
        await wait_sync(pg, "^À jour")
        print("1 header:", await pg.inner_text("#h-nom"), "|", await sync_t(pg), "| url:", pg.url, "| auth:", state()["log"])
        await pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.ready.then(() => true)")
        await pg.reload(); await wait_sync(pg, "^À jour")
        print("1b sw controller:", await pg.evaluate("!!navigator.serviceWorker.controller"), "| email:", await pg.evaluate("localStorage.getItem('cm-email')"))
        # 2. Hors réseau : l'app s'ouvre quand même (depuis le téléphone)
        await ctx.set_offline(True)
        await pg.reload(); await pg.wait_for_selector("#v-accueil .banner")
        print("2 offline reload:", await sync_t(pg), "|", (await lines(pg, "#v-accueil", 3)))
        await pg.screenshot(path=OUT + "/hors-reseau.png")
        # 3. Dépense avec photo, hors réseau
        await pg.click("#tab-add"); await pg.click('[data-addk="depense"]'); await pg.wait_for_selector("#o-mt")
        await pg.set_input_files("#ph-pick", files=[{"name": "recu.png", "mimeType": "image/png", "buffer": PNG}]); await pg.wait_for_timeout(300)
        await pg.fill("#o-mt", "75,40"); await pg.fill("#o-tiers", "Ultramar"); await pg.dispatch_event("#o-tiers", "change")
        await pg.click('#sh-foot button[type=submit]'); await pg.wait_for_timeout(400)
        print("3 toast:", await pg.inner_text("#toast"), "| sync:", await sync_t(pg))
        # Événement hors réseau
        await pg.click("#tab-add"); await pg.click('[data-addk="evenement"]'); await pg.wait_for_selector("#e-titre")
        await pg.click('[data-evt="soumission"]'); await pg.fill("#e-deb", "13:00"); await pg.fill("#e-titre", "Soumission Tremblay")
        await pg.click('#sh-foot button[type=submit]'); await pg.wait_for_timeout(300)
        print("3b pending:", await pg.evaluate("JSON.parse(localStorage.getItem('cm-pending')).map(p => p.etat + ':' + p.label)"))
        # 4. L'app est fermée puis rouverte, toujours sans réseau : rien n'est perdu (photo comprise)
        await pg.close(); pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append("pageerror2: " + str(e)))
        pg.on("console", lambda m: errs.append("console2: " + m.text) if m.type == "error" and "401" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_selector("#v-accueil .banner")
        print("4 reopen offline:", await sync_t(pg), "| idb photos:", await pg.evaluate("new Promise(r => { const q = indexedDB.open('comptabilite'); q.onsuccess = () => { const g = q.result.transaction('photos').objectStore('photos').getAllKeys(); g.onsuccess = () => r(g.result); }; })"))
        await pg.click('[data-tab="plus"]'); await pg.wait_for_timeout(100); print("4b plus:", await lines(pg, "#v-plus .card", 9))
        await pg.screenshot(path=OUT + "/plus-hors-reseau.png", full_page=True)
        print("4c drive tel before:", telfiles())
        # 5. Retour du réseau : envoi automatique
        await ctx.set_offline(False)
        await wait_sync(pg, "en attente de l'ordinateur", 10000)
        print("5 online:", await sync_t(pg), "| drive tel:", telfiles())
        print("5b idb after:", await pg.evaluate("new Promise(r => { const q = indexedDB.open('comptabilite'); q.onsuccess = () => { const g = q.result.transaction('photos').objectStore('photos').getAllKeys(); g.onsuccess = () => r(g.result); }; })"))
        # 6. Jeton expiré pendant que l'app est ouverte : un ajout déclenche une reconnexion silencieuse, puis l'envoi
        post("/__mode", {"expire": True}); await pg.evaluate("localStorage.setItem('cm-authTry', '0')")
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.click('[data-kmode="manuel"]'); await pg.fill("#k-dest", "Beaumont"); await pg.fill("#k-raison", "Soumission"); await pg.fill("#k-km", "18")
        await pg.click('#sh-foot button[type=submit]')
        await pg.wait_for_timeout(2500)
        print("6 after expire:", await sync_t(pg), "| auth prompts:", [l["prompt"] for l in state()["log"]], "| tel:", len(telfiles()))
        # 7. Google refuse la connexion silencieuse : bandeau, ajouts gardés, bouton Se connecter
        post("/__mode", {"expire": True, "auth": "deny"}); await pg.evaluate("localStorage.setItem('cm-authTry', '0')")
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.click('[data-kmode="manuel"]'); await pg.fill("#k-dest", "Lévis"); await pg.fill("#k-raison", "Garage"); await pg.fill("#k-km", "9")
        await pg.click('#sh-foot button[type=submit]'); await pg.wait_for_timeout(2500)
        await pg.click('[data-tab="accueil"]'); await pg.wait_for_timeout(100)
        print("7 denied:", await sync_t(pg), "| banner:", (await lines(pg, "#v-accueil .banner", 3)))
        await pg.screenshot(path=OUT + "/connexion.png")
        post("/__mode", {"auth": "ok"})
        await pg.click('#v-accueil .banner [data-act="login"]'); await wait_sync(pg, "en attente de l'ordinateur", 10000)
        print("7b after login:", await sync_t(pg), "| prompts:", [l["prompt"] for l in state()["log"]], "| tel:", telfiles())
        # 8. L'ordinateur applique les changements : le téléphone le voit
        ops = [f for f in state()["files"] if "tel1" in f.get("parents", []) and f["name"].startswith("op-")]
        reg = json.loads(REG); reg["telephone"] = {"appliques": [json.loads(base64.b64decode(f["content"]))["id"] for f in ops], "dernier": "2026-10-28T21:00:00Z"}
        json.dump([{"title": f["name"], "content": f["content"]} for f in state()["files"] if "tel1" in f.get("parents", [])], open(OUT + "/ops.json", "w"))
        post("/__setreg", raw=json.dumps(reg).encode()); post("/__consume")
        await pg.click("#h-refresh"); await wait_sync(pg, "^À jour")
        print("8 applied:", await sync_t(pg), "| pending:", await pg.evaluate("JSON.parse(localStorage.getItem('cm-pending')).length"))
        # 9. Bouton Retour d'Android : ferme le panneau sans quitter
        await pg.click("#tab-add"); await pg.click('[data-addk="evenement"]'); await pg.wait_for_selector("#e-titre")
        await pg.go_back(); await pg.wait_for_timeout(300)
        print("9 back closes sheet:", await pg.evaluate("document.getElementById('sheet').hidden"), "| url:", pg.url)
        await pg.click('[data-tab="ventes"]'); await pg.click('#v-ventes [data-fac="fa-1"]'); await pg.wait_for_selector("#sheet:not([hidden])")
        await pg.click('#sh-foot [data-x="pay"]'); await pg.wait_for_selector("#p-date")
        await pg.go_back(); await pg.wait_for_timeout(300)
        print("9b back after chained sheets:", await pg.evaluate("document.getElementById('sheet').hidden"))
        # 10. PDF de facture (partage ou téléchargement)
        await pg.click('#v-ventes [data-fac="fa-1"]'); await pg.wait_for_selector("#sheet:not([hidden])")
        await pg.click('#sh-foot [data-x="pdf"]'); await pg.wait_for_selector('[data-send="save"]')
        async with pg.expect_download() as dl: await pg.click('[data-send="save"]')
        d = await dl.value; pth = await d.path(); print("10 pdf:", d.suggested_filename, open(pth, "rb").read()[:8])
        await pg.keyboard.press("Escape"); await pg.evaluate("document.getElementById('sh-x').click()")
        await pg.emulate_media(color_scheme="dark"); await pg.click('[data-tab="accueil"]'); await pg.screenshot(path=OUT + "/accueil-sombre.png")
        print("overflow:", await pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
