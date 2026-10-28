"""Trajets sur le téléphone : GPS en ligne, GPS sans réseau (recalcul avant l'envoi), à la main avec trajets fréquents, camion, lieux."""
import asyncio, json, os, sys, base64, urllib.request
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "km/out"; os.makedirs(OUT, exist_ok=True)
REG = open("phone/fixture.json", encoding="utf-8").read()
URL = "http://127.0.0.1:8090/compta/"
INIT = "window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
BUREAU = {"latitude": 46.7330, "longitude": -71.2560}   # Saint-Romuald (approx.)
LEVIS = {"latitude": 46.8030, "longitude": -71.1780}
BEAUMONT = {"latitude": 46.8410, "longitude": -70.9970}
def post(path, obj=None, raw=None):
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8091" + path, data=raw if raw is not None else json.dumps(obj or {}).encode(), method="POST")).read())
def state(): return json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
def ops():
    out = []
    for f in state()["files"]:
        if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed"):
            out.append(json.loads(base64.b64decode(f["content"])))
    return sorted(out, key=lambda o: o["creeLe"])
async def wait_sync(pg, pred, t=10000):
    await pg.wait_for_function("(p) => new RegExp(p).test(document.getElementById('h-sync-t').textContent)", arg=pred, timeout=t)
async def main():
    mock.reset(REG); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, geolocation=BUREAU, permissions=["geolocation"])
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text and "503" not in m.text else None)
        await pg.goto(URL); await wait_sync(pg, "^À jour")
        # 1. GPS, en ligne
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.wait_for_selector('[data-kmode="gps"][aria-pressed="true"]')
        print("1 gps sheet:", [x for x in (await pg.inner_text("#sh-body")).split("\n") if x.strip()][:6])
        await pg.screenshot(path=OUT + "/tel-depart.png")
        await pg.click("#sh-ok"); await pg.wait_for_selector("#v-accueil .banner.info", timeout=8000)
        print("1b banner:", (await pg.inner_text("#v-accueil .banner.info")).replace("\n", " | "))
        await pg.screenshot(path=OUT + "/tel-en-cours.png")
        await ctx.set_geolocation(LEVIS)
        await pg.click('#v-accueil .banner.info [data-add="trajet"]'); await pg.wait_for_selector("#sh-ok")
        print("1c arrivee sheet:", (await pg.inner_text("#sh-body")).replace("\n", " | ")[:120])
        await pg.click("#sh-ok"); await pg.wait_for_selector("#k-kmnote"); await pg.wait_for_function("document.getElementById('k-kmnote').textContent.startsWith('Par la route')", timeout=8000)
        print("1d fin:", await pg.input_value("#k-km"), "|", await pg.inner_text("#k-kmnote"))
        await pg.fill("#k-dep", "Maison"); await pg.fill("#k-dest", "Chantier Gagnon"); await pg.fill("#k-raison", "Soumission Gagnon")
        print("1e save lieux:", await pg.is_visible("#k-savel-w"), await pg.inner_text("#k-savel-t"))
        await pg.screenshot(path=OUT + "/tel-fin.png")
        await pg.click("#sh-ok"); await pg.wait_for_timeout(2500)
        print("1f sync:", await pg.inner_text("#h-sync-t"), "| sheet hidden:", await pg.evaluate("document.getElementById('sheet').hidden"), "| err:", await pg.inner_text("#sh-err") if not await pg.evaluate("document.getElementById('sheet').hidden") else "", "| pending:", await pg.evaluate("localStorage.getItem('cm-pending')"))
        print("1f ops:", [(o["type"], o["data"].get("nom") or o["data"].get("destination"), o["data"].get("km"), o["data"].get("mode"), o["data"].get("vehicule"), o["data"].get("lat")) for o in ops()])
        # 2. GPS sans réseau, de Lévis à la maison : lieux reconnus, estimation puis recalcul par la route
        await ctx.set_offline(True)
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.click("#sh-ok"); await pg.wait_for_selector("#v-accueil .banner.info")
        print("2 toast:", await pg.inner_text("#toast"))
        await ctx.set_geolocation(BUREAU)
        await pg.click('#v-accueil .banner.info [data-add="trajet"]'); await pg.click("#sh-ok"); await pg.wait_for_selector("#k-kmnote")
        await pg.wait_for_function("document.getElementById('k-kmnote').textContent.startsWith('Sans réseau')", timeout=8000)
        print("2b offline fin:", await pg.input_value("#k-dep"), "->", await pg.input_value("#k-dest"), "|", await pg.input_value("#k-km"), "|", await pg.inner_text("#k-kmnote"), "| save hidden:", await pg.is_hidden("#k-savel-w"))
        await pg.fill("#k-raison", "Retour du chantier"); await pg.click("#sh-ok"); await pg.wait_for_timeout(300)
        pend = await pg.evaluate("JSON.parse(localStorage.getItem('cm-pending')).filter(p => p.etat === 'attente').map(p => [p.op.type, p.op.data.km, p.op.data.estime || false])")
        print("2c pending offline:", pend)
        await ctx.set_offline(False); await wait_sync(pg, "en attente de l'ordinateur", 12000)
        last = ops()[-1]["data"]; print("2d sent:", last["depart"], "->", last["destination"], last["km"], "estime" in last, "| routes calls:", state()["routes"])
        # 3. À la main : trajet fréquent, calcul par la route, camion
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.click('[data-kmode="manuel"]'); await pg.wait_for_selector("#k-km")
        print("3 freq:", await pg.eval_on_selector_all("[data-kfreq]", "b => b.map(x => x.textContent)"))
        await pg.click('[data-kfreq="0"]'); print("3b filled:", await pg.input_value("#k-dep"), "->", await pg.input_value("#k-dest"), await pg.input_value("#k-km"), "| calc visible:", await pg.is_visible("#k-calc"))
        await pg.fill("#k-km", ""); await pg.click("#k-calc"); await pg.wait_for_timeout(400); print("3c calc:", await pg.input_value("#k-km"), "|", await pg.inner_text("#k-kmnote"))
        await pg.click('[data-veh="eq-1"]'); await pg.fill("#k-raison", "Transport de la déchiqueteuse")
        await pg.screenshot(path=OUT + "/tel-manuel.png")
        await pg.click("#sh-ok"); await wait_sync(pg, "en attente de l'ordinateur")
        o = ops()[-1]["data"]; print("3d sent:", o["vehicule"], o["mode"], o["km"], o["raison"])
        # 4. Plus : totaux et lieux
        await pg.click('[data-tab="plus"]'); await pg.wait_for_timeout(200)
        txt = await pg.inner_text("#v-plus"); i = txt.find("Trajets "); print("4 plus:", [x for x in txt[i:].split("\n") if x.strip()][:22])
        await pg.screenshot(path=OUT + "/tel-plus.png", full_page=True)
        # 5. Trajet commencé puis annulé
        await pg.click("#tab-add"); await pg.click('[data-addk="trajet"]'); await pg.click('[data-kmode="gps"]'); await pg.click("#sh-ok"); await pg.wait_for_timeout(600)
        await pg.click('[data-tab="accueil"]'); await pg.wait_for_selector("#v-accueil .banner.info")
        await pg.click('#v-accueil [data-act="trip-cancel"]'); await pg.wait_for_timeout(200)
        print("5 cancel:", await pg.inner_text("#toast"), "| banner gone:", await pg.locator("#v-accueil .banner.info").count() == 0, "| trip:", await pg.evaluate("localStorage.getItem('cm-trip')"))
        json.dump([{"title": f["name"], "content": f["content"]} for f in state()["files"] if "tel1" in f.get("parents", []) and not f.get("trashed")], open(OUT + "/ops.json", "w"))
        print("overflow:", await pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
