"""Une seule app au téléphone : Menu à tuiles, mêmes onglets dans les sections complètes, bouton +, retour Android."""
import asyncio, json, os, sys
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
FIX = json.load(open("phone/fixture.json", encoding="utf-8"))
OPS_ALL = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr"]
URL = "http://127.0.0.1:8090/compta/"
INIT = "if (/complet\\.html/.test(location.pathname)) window.__NUAGE = true; window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
async def main():
    reg = json.loads(json.dumps(FIX)); reg["telephone"] = {"ops": OPS_ALL, "appliques": []}
    mock.reset(json.dumps(reg)); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, geolocation={"latitude": 46.73, "longitude": -71.25}, permissions=["geolocation"])
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        # 1. Menu de l'app terrain
        await pg.click('[data-tab="plus"]'); await pg.wait_for_selector(".mt-tile")
        print("1 tab label:", await pg.inner_text('[data-tab="plus"]'), "| tiles:", await pg.eval_on_selector_all(".mt-tile", "a => a.map(x => x.getAttribute('href') + ' ' + x.querySelector('small').textContent)"))
        await pg.screenshot(path=OUT + "/menu-terrain.png", full_page=True)
        # 2. Tuile Kilométrage -> section complète avec les mêmes onglets
        await pg.click('.mt-tile[data-mt="km"]'); await pg.wait_for_selector("#m-head", timeout=15000); await pg.wait_for_selector("#view-km:not([hidden])")
        await pg.wait_for_function("document.getElementById('m-sync-t').textContent.startsWith('À jour')", timeout=15000)
        print("2 url:", pg.url, "| title:", await pg.inner_text("#top-title"), "| side hidden:", await pg.is_hidden(".side"), "| tabs:", await pg.inner_text(".m-tabs"), "| head:", (await pg.inner_text("#m-head")).replace("\n", " | "))
        await pg.screenshot(path=OUT + "/section-km.png")
        # 3. Menu dans la section complète -> Banque
        await pg.click('.m-tabs [data-nu="menu"]'); await pg.wait_for_selector("#m-menu:not([hidden]) .mt-tile")
        print("3 overlay tiles:", await pg.eval_on_selector_all("#m-menu .mt-tile", "a => a.map(x => x.getAttribute('href'))"))
        await pg.screenshot(path=OUT + "/menu-complet.png")
        await pg.click('#m-menu .mt-tile[data-mt="banque"]'); await pg.wait_for_timeout(300)
        print("3b view:", await pg.inner_text("#top-title"), "| overlay hidden:", await pg.is_hidden("#m-menu"), "| url:", pg.url)
        # 4. Retour Android : section précédente
        await pg.go_back(); await pg.wait_for_timeout(400); print("4 back:", pg.url, "| title:", await pg.inner_text("#top-title"))
        # 5. Le menu se ferme avec Retour
        await pg.click('.m-tabs [data-nu="menu"]'); await pg.wait_for_selector("#m-menu:not([hidden])"); await pg.go_back(); await pg.wait_for_timeout(400)
        print("5 back closes menu:", await pg.is_hidden("#m-menu"), "| still:", pg.url)
        # 6. + dans une section complète : Revenu (formulaire sur place)
        await pg.click('.m-tabs [data-nu="add"]'); await pg.wait_for_selector("#m-add:not([hidden])"); await pg.screenshot(path=OUT + "/ajout-complet.png")
        await pg.click('#m-add [data-nuadd="revenu"]'); await pg.wait_for_selector("#m-montant", state="visible"); print("6 form:", await pg.inner_text("#m-title"), "| add hidden:", await pg.is_hidden("#m-add"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#m-montant"): await pg.click("#tx-form .drawer-x, #m-cancel") if await pg.locator("#m-cancel").count() else None
        # 7. + Trajet -> GPS de l'app terrain
        await pg.click('.m-tabs [data-nu="add"]'); await pg.click('#m-add [data-nuadd="trajet"]'); await pg.wait_for_selector('[data-kmode]', timeout=15000)
        print("7 trajet:", pg.url, "| sheet:", await pg.inner_text("#sh-title"))
        await pg.click("#sh-x")
        # 8. + Autres dans l'app terrain -> transfert dans la section complète
        await pg.click("#tab-add"); await pg.wait_for_selector(".m-list a"); print("8 autres:", await pg.eval_on_selector_all(".m-list a", "a => a.map(x => x.textContent)"))
        await pg.screenshot(path=OUT + "/ajout-terrain.png")
        await pg.click('.m-list a[href$="nouveau=transfert"]'); await pg.wait_for_selector("#m-title", state="visible", timeout=15000); await pg.wait_for_timeout(300)
        print("8b:", pg.url, "| form:", await pg.inner_text("#m-title"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
        # 9. Onglet Accueil depuis une section complète -> app terrain
        await pg.click('.m-tabs a[href="./#accueil"]'); await pg.wait_for_selector("#v-accueil:not([hidden])", timeout=15000); print("9 accueil:", pg.url)
        # 10. Synchronisation (en-tête) depuis une section
        await pg.goto(URL + "complet.html#rapports"); await pg.wait_for_selector("#m-head"); await pg.click("#m-sync"); await pg.wait_for_selector("#v-plus:not([hidden])", timeout=15000); print("10 sync ->", pg.url)
        await pg.emulate_media(color_scheme="dark"); await pg.goto(URL + "complet.html#tvh"); await pg.wait_for_selector("#view-tvh:not([hidden])"); await pg.wait_for_timeout(300); await pg.screenshot(path=OUT + "/section-tvh-sombre.png")
        print("overflow:", await pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        # 11. Grand écran en mode nuage : mise en page de l'ordinateur
        pw = await ctx.new_page(); await pw.set_viewport_size({"width": 1300, "height": 850}); await pw.goto(URL + "complet.html#km"); await pw.wait_for_selector("#view-km:not([hidden])", timeout=15000)
        print("11 wide: side visible:", await pw.is_visible(".side"), "| tabs hidden:", await pw.is_hidden(".m-tabs"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
