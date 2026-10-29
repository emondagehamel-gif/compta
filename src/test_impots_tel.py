"""Impôts de fin d'année au téléphone : tuile du Menu, affichage mobile, saisie envoyée à l'ordinateur."""
import asyncio, json, os, sys, base64
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
FIX = json.load(open("phone/fixture.json", encoding="utf-8"))
OPS_ALL = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr"]
URL = "http://127.0.0.1:8090/compta/"
INIT = "if (/complet\\.html/.test(location.pathname)) window.__NUAGE = true; window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
import urllib.request
def tel_ops():
    st = json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read()); out = []
    for f in st["files"]:
        if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed"): out.append(json.loads(base64.b64decode(f["content"])))
    return sorted(out, key=lambda o: o["creeLe"])
async def main():
    reg = json.loads(json.dumps(FIX)); reg["telephone"] = {"ops": OPS_ALL, "appliques": []}
    mock.reset(json.dumps(reg)); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True)
        await ctx.add_init_script(INIT); pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await pg.click('[data-tab="plus"]'); await pg.wait_for_selector('.mt-tile[data-mt="impots"]')
        print("1 tuile:", (await pg.inner_text('.mt-tile[data-mt="impots"]')).replace("\n", " | "))
        await pg.click('.mt-tile[data-mt="impots"]')
        try: await pg.wait_for_selector("#view-impots:not([hidden]) #fa-body .card", timeout=15000)
        except Exception as e: print("FAIL url", pg.url, errs, (await pg.inner_text("body"))[:400]); await pg.screenshot(path=OUT + "/fail.png"); raise
        await pg.wait_for_function("document.getElementById('m-sync-t').textContent.startsWith('À jour')", timeout=15000)
        print("2 titre:", await pg.inner_text("#top-title"), "| cartes:", await pg.eval_on_selector_all("#fa-body > .card h2", "a => a.length"), "| débordement:", await pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        wide = await pg.evaluate("[...document.querySelectorAll('#fa-body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.sheet')).map(e => e.tagName + '.' + e.className).slice(0, 6)")
        print("2b dépasse l'écran:", wide)
        await pg.screenshot(path=OUT + "/impots-tel-1.png", full_page=True)
        await pg.fill('[data-fa="heures"]', "6000"); await pg.press('[data-fa="heures"]', "Enter"); await pg.wait_for_timeout(1500)
        q = await pg.evaluate("(() => { for (const d of document.querySelectorAll('#fa-body .kv > div')){ const a = d.children[0]; if (a && a.textContent.trim().startsWith('Québec')) return a.textContent.trim().slice(0, 80) + ' = ' + d.children[1].textContent.trim(); } })()")
        print("3 Québec après 6000 h:", q)
        await pg.wait_for_function("/attente|À jour/.test(document.getElementById('m-sync-t').textContent)", timeout=15000)
        pt = [o for o in tel_ops() if o["type"] == "patch"]
        print("3b op:", [(o["data"].get("msg"), [(c["col"], c.get("path") or c.get("key") or c.get("id"), json.dumps(c.get("set") or c.get("doc") or c.get("val"), ensure_ascii=False)[:120]) for c in o["data"]["changes"]]) for o in pt])
        await pg.screenshot(path=OUT + "/impots-tel-2.png")
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
