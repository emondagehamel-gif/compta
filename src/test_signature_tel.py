"""Signature du client au téléphone (app terrain) : pavé, op « signature » avec l'image, copie signée à envoyer."""
import asyncio, json, os, sys, base64, urllib.request, subprocess
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
FIX = json.load(open("phone/fixture.json", encoding="utf-8"))
OPS_ALL = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr","doc-v2","signature"]
URL = "http://127.0.0.1:8090/compta/"
INIT = "if (/complet\\.html/.test(location.pathname)) window.__NUAGE = true; window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
def state(): return json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
async def main():
    reg = json.loads(json.dumps(FIX)); reg["telephone"] = {"ops": OPS_ALL, "appliques": []}
    reg["reglages"].update({"titreDevis": "Soumission", "nom": "Émondage Hamel"})
    reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "", "telephone": "418-555-0142", "adresse": "1600, rue Saint-François", "note": ""}]
    reg["devis"] = [{"id": "dv-s1", "numero": "D-2026-009", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": [{"type": "service", "description": "Travaux d'émondage", "qte": 1, "unite": "forfait", "prix": 400}], "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
    mock.reset(json.dumps(reg)); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await ctx.add_init_script(INIT); pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await pg.click('[data-tab="ventes"]'); await pg.click('#v-ventes [data-vt="devis"]'); await pg.click('#v-ventes [data-dev="dv-s1"]'); await pg.wait_for_selector("#sheet:not([hidden])")
        print("1 bouton signer:", await pg.is_visible('[data-x="signer"]'))
        await pg.click('[data-x="signer"]'); await pg.wait_for_selector(".sig-ov")
        await pg.screenshot(path=OUT + "/signature-tel.png")
        box = await pg.locator(".sig-zone canvas").bounding_box(); print("1b pavé:", round(box["width"]), "x", round(box["height"]))
        x0, y0 = box["x"] + 30, box["y"] + box["height"] * 0.6
        await pg.mouse.move(x0, y0); await pg.mouse.down()
        for k in range(1, 25): await pg.mouse.move(x0 + k * 11, y0 - 40 * ((k % 5) / 5), steps=2)
        await pg.mouse.up(); await pg.click(".sig-ok"); await pg.wait_for_selector('[data-send="save"]', timeout=8000)
        print("2 envoi:", await pg.inner_text("#sh-title"))
        async with pg.expect_download() as dl: await pg.click('[data-send="save"]')
        d = await dl.value; path = OUT + "/tel-signee.pdf"; await d.save_as(path)
        imgs = subprocess.run(["pdfimages", "-list", path], capture_output=True, text=True).stdout.strip().split("\n")[2:]
        txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
        print("3 pdf:", d.suggested_filename, "| images:", len(imgs), "|", [l.strip()[:90] for l in txt.split("\n") if "Signé" in l or "Client :" in l])
        await pg.wait_for_timeout(2500)
        st = state(); ops = []
        for f in st["files"]:
            if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed"): ops.append(json.loads(base64.b64decode(f["content"])))
        sg = [o for o in ops if o["type"] == "signature"]; print("4 op:", [(o["data"], o["photos"]) for o in sg])
        await pg.click("#sh-x"); await pg.wait_for_timeout(400); await pg.click('#v-ventes [data-dev="dv-s1"]'); await pg.wait_for_selector("#sheet:not([hidden])")
        print("5 fiche:", await pg.inner_text(".sig-done") if await pg.locator(".sig-done").count() else "—", "| bouton signer:", await pg.locator('[data-x="signer"]').count())
        files = [{"title": f["name"], "content": f["content"]} for f in st["files"] if "tel1" in f.get("parents", []) and not f.get("trashed")]
        json.dump({"reg": reg, "files": files}, open(OUT + "/envoi-signature.json", "w"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
