"""Soumissions et factures au téléphone (app terrain) : types de frais, taxes incluses, tarifs, envoi."""
import asyncio, json, os, sys, base64, urllib.request
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
FIX = json.load(open("phone/fixture.json", encoding="utf-8"))
OPS_ALL = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr","doc-v2"]
URL = "http://127.0.0.1:8090/compta/"
INIT = "if (/complet\\.html/.test(location.pathname)) window.__NUAGE = true; window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
def tel_ops():
    st = json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read()); out = []
    for f in st["files"]:
        if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed"): out.append(json.loads(base64.b64decode(f["content"])))
    return sorted(out, key=lambda o: o["creeLe"])
async def run(ops, label):
    reg = json.loads(json.dumps(FIX)); reg["telephone"] = {"ops": ops, "appliques": []}
    reg["reglages"].update({"titreDevis": "Soumission", "nom": "Émondage Hamel", "tarifs": [{"id": "tf-1", "type": "location", "description": "Nacelle de 60 pi", "unite": "jour", "prix": 450, "ttc": True}]})
    mock.reset(json.dumps(reg))
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await ctx.add_init_script(INIT); pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await pg.click('[data-tab="ventes"]'); await pg.click('#v-ventes [data-vt="devis"]'); await pg.click('#v-ventes [data-add="devis"]'); await pg.wait_for_selector("#d-lines .line")
        print(label, "1 titre:", await pg.inner_text("#sh-title"), "| ttc:", await pg.locator("[data-ttc]").count(), "| options:", await pg.eval_on_selector_all("#d-add option", "a => a.map(x => x.textContent).slice(0, 14)"))
        if "doc-v2" not in ops:
            print(label, "hint:", await pg.inner_text("#sh-body .hint")); await b.close(); return
        await pg.fill("#d-cli", "Michel Auger"); await pg.click('[data-ttc="1"]')
        await pg.fill('[data-li="0"] [data-lf="description"]', "Travaux d'émondage"); await pg.fill('[data-li="0"] [data-lf="prix"]', "400")
        await pg.select_option("#d-add", "f:tf-1"); await pg.select_option("#d-add", "t:deplacement")
        await pg.fill('[data-li="2"] [data-lf="description"]', "Aller-retour"); await pg.fill('[data-li="2"] [data-lf="qte"]', "40"); await pg.fill('[data-li="2"] [data-lf="prix"]', "1,25")
        await pg.select_option("#d-add", "t:rabais"); await pg.fill('[data-li="3"] [data-lf="description"]', "Rabais"); await pg.fill('[data-li="3"] [data-lf="prix"]', "50")
        await pg.fill("#d-trav", "Émondage de 3 érables"); await pg.fill("#d-lieu", "1600, rue Saint-François")
        print(label, "2 lignes:", await pg.eval_on_selector_all("#d-lines .line", "a => a.map(r => [r.querySelector('[data-lf=type]').value, r.querySelector('[data-lf=unite]').value, r.querySelector('[data-amt]').textContent])"), "| tot:", (await pg.inner_text("#d-tot")).replace("\n", " | "))
        await pg.screenshot(path=OUT + "/devis-tel-form.png")
        await pg.evaluate("document.querySelector('[data-li=\"1\"]').scrollIntoView()"); await pg.wait_for_timeout(200); await pg.screenshot(path=OUT + "/devis-tel-lignes.png")
        print(label, "H0", await pg.evaluate("history.length + ' ' + JSON.stringify(history.state)"))
        await pg.click('#sh-foot [data-dsave="send"]'); await pg.wait_for_selector('[data-send="save"]', timeout=8000)
        await pg.wait_for_timeout(500); print(label, "H1", await pg.evaluate("history.length + ' ' + JSON.stringify(history.state)"))
        print(label, "3 envoi:", await pg.inner_text("#sh-title"), "|", await pg.eval_on_selector_all("[data-send]", "a => a.map(x => x.dataset.send)"), "|", (await pg.input_value("#snd-msg"))[:90].replace("\n", " / "))
        await pg.screenshot(path=OUT + "/devis-tel-envoi.png")
        async with pg.expect_download() as dl: await pg.click('[data-send="save"]')
        d = await dl.value; print(label, "4 pdf:", d.suggested_filename, open(await d.path(), "rb").read()[:8])
        await pg.wait_for_timeout(2500)
        op = [o for o in tel_ops() if o["type"] == "devis"][-1]["data"]
        print(label, "5 op:", op["numero"], op.get("taxesIncluses"), op.get("travaux"), op.get("lieu"), [(l["type"], l["unite"], l["prix"]) for l in op["lignes"]])
        # Facture taxes incluses avec rabais, payée tout de suite
        print(label, "H2", await pg.evaluate("history.length + ' ' + JSON.stringify(history.state) + ' ' + location.href"))
        await pg.click("#sh-x"); await pg.wait_for_timeout(500); print(label, "url:", pg.url, await pg.evaluate("[...document.querySelectorAll('section[id^=v-]')].filter(x => !x.hidden).map(x => x.id)"))
        await pg.click('[data-tab="ventes"]'); await pg.wait_for_timeout(300)
        await pg.click('#v-ventes [data-vt="factures"]'); await pg.click('#v-ventes [data-add="facture"]'); await pg.wait_for_selector("#d-lines .line")
        await pg.fill("#d-cli", "Michel Auger"); await pg.click('[data-ttc="1"]')
        await pg.fill('[data-li="0"] [data-lf="description"]', "Travaux d'émondage\n1600, rue Saint-François"); await pg.fill('[data-li="0"] [data-lf="prix"]', "400")
        await pg.select_option("#d-add", "t:rabais"); await pg.fill('[data-li="1"] [data-lf="description"]', "Rabais"); await pg.fill('[data-li="1"] [data-lf="prix"]', "25")
        await pg.fill("#d-dtrav", "2026-10-28")
        await pg.click('#sh-foot #sh-ok'); await pg.wait_for_timeout(2500)
        st = json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
        files = [{"title": f["name"], "content": f["content"]} for f in st["files"] if "tel1" in f.get("parents", []) and not f.get("trashed")]
        json.dump({"reg": reg, "files": files}, open(OUT + "/envoi-devis.json", "w")); print(label, "6 fichiers envoyés:", [f["title"][:20] for f in files])
        print("ERRORS:", errs); await b.close()
async def main():
    mock.start()
    await run(OPS_ALL, "[v2]")
    await run([o for o in OPS_ALL if o != "doc-v2"], "[ancien]")
asyncio.run(main())
