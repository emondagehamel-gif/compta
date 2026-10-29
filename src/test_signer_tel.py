"""v3.12 au téléphone : le message et le PDF envoyés depuis l'app terrain ont aussi le lien « Signer en ligne »."""
import asyncio, json, os, sys, re
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; URL = "http://127.0.0.1:8090/compta/"
INIT = "window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__SCRIPT = 'http://127.0.0.1:8093/macros/s/';"
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["telephone"] = {"ops": ["devis", "facture", "doc-v2", "signature"], "appliques": []}
reg["reglages"].update({"nom": "Émondage Hamel", "titreDevis": "Soumission", "signerUrl": "http://127.0.0.1:8093/macros/s/AKfycbTESTtestTESTtest1234567890abcdef/exec", "signerCle": "6f1c2a9e0b7d4c3a8e5f1029384756abcdef0123456789ab"})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "", "adresse": "", "note": ""}]
reg["devis"] = [{"id": "dv-s1", "numero": "D-2026-020", "date": "2026-10-29", "echeance": "2099-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": [{"type": "service", "description": "Abattage", "qte": 1, "unite": "forfait", "prix": 650}], "codeTaxe": "QC", "taxesIncluses": False, "statut": "ouvert", "projet": "", "message": ""}]
async def main():
    mock.reset(json.dumps(reg)); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await ctx.add_init_script(INIT); pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await pg.click('[data-tab="ventes"]'); await pg.click('#v-ventes [data-vt="devis"]'); await pg.click("text=D-2026-020"); await pg.wait_for_timeout(800)
        print("0 feuille:", await pg.eval_on_selector_all("#sheet [data-x]", "a => a.map(x => x.dataset.x + ':' + x.textContent.trim())"))
        await pg.click('#sheet [data-x="pdf"]'); await pg.wait_for_selector('[data-send="save"]')
        msg = await pg.input_value("#snd-msg"); m = re.search(r"https://emondagehamel-gif\.github\.io/compta/signer\.html#\S+", msg)
        print("1 message:", bool(m), "|", (m.group(0)[:100] + "…") if m else msg[:200])
        async with pg.expect_download() as dl: await pg.click('[data-send="save"]')
        d = await dl.value; pdf = open(await d.path(), "rb").read(); u = re.search(rb"/URI \((.*?)\) >>", pdf)
        print("2 pdf:", d.suggested_filename, "| lien:", bool(u) and m and u.group(1).decode() == m.group(0))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
