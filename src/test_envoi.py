"""Envoi depuis l'ordinateur : Gmail (compte de l'entreprise) avec le PDF téléchargé, copie du document en image."""
import asyncio, json, os, base64, urllib.parse
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "courriel": "emondagehamel@gmail.com", "titreDevis": "Soumission"})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "", "adresse": "1600, rue Saint-François", "note": ""}]
reg["devis"] = [{"id": "dv-e1", "numero": "D-2026-010", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": [{"type": "service", "description": "Travaux d'émondage", "qte": 1, "unite": "forfait", "prix": 400}], "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
REG = json.dumps(reg)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True, permissions=["clipboard-read", "clipboard-write"])
        await ctx.route("https://mail.google.com/**", lambda r: r.fulfill(body="<title>Gmail</title>gmail", content_type="text/html"))
        pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        print("1 options:", await pg.eval_on_selector_all("#ent-form [data-send]", "a => a.map(x => x.dataset.send + ': ' + x.querySelector('b').textContent)"))
        async with ctx.expect_page() as pop, pg.expect_download() as dl:
            await pg.click('[data-send="gmail"]')
        w = await pop.value; d = await dl.value; await w.wait_for_load_state()
        u = urllib.parse.urlsplit(w.url); q = urllib.parse.parse_qs(u.query)
        print("2 gmail:", u.netloc + u.path, "| compte:", q.get("authuser"), "| à:", q.get("to"), "| sujet:", q.get("su"), "| corps:", (q.get("body") or [""])[0][:60].replace("\n", " / "))
        print("2b pdf:", d.suggested_filename, open(await d.path(), "rb").read()[:8])
        await pg.wait_for_selector("#snd-guide:not([hidden])"); print("2c guide:", (await pg.inner_text("#snd-guide"))[:200].replace("\n", " "))
        await w.close()
        await pg.screenshot(path=OUT + "/envoi-gmail.png")
        await pg.click('[data-send="copyimg"]'); await pg.wait_for_timeout(1500)
        types = await pg.evaluate("navigator.clipboard.read().then(items => items.map(i => i.types.join(',')))")
        size = await pg.evaluate("navigator.clipboard.read().then(async items => (await items[0].getType('image/png')).size)")
        print("3 presse-papiers:", types, size, "| guide:", (await pg.inner_text("#snd-guide"))[:120].replace("\n", " "))
        await pg.click('[data-send="copy"]'); await pg.wait_for_timeout(300)
        print("4 texte:", (await pg.evaluate("navigator.clipboard.readText()"))[:50].replace("\n", " / "))
        d2 = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); print("5 envoyé le:", d2["devis"][0].get("envoyeLe"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
