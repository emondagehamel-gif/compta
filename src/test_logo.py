"""Nouveau logo : barre latérale, écran d'accueil, en-tête du téléphone, icônes de la PWA."""
import asyncio, json, os, sys, base64
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"
reg = json.load(open("phone/fixture.json", encoding="utf-8")); reg["reglages"]["nom"] = "Émondage Hamel"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width": 1366, "height": 800}); pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(json.dumps(reg)) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html")); await pg.wait_for_selector("#splash:not([hidden])")
        await pg.screenshot(path=OUT + "/logo-splash.png")
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=OUT + "/logo-bureau.png", clip={"x": 0, "y": 0, "width": 420, "height": 160})
        print("favicon:", (await pg.evaluate("document.querySelector('link[rel=icon]').href"))[:60])
        mock.reset(json.dumps(dict(reg, telephone={"ops": ["patch"], "appliques": []}))); mock.start()
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True)
        await ctx.add_init_script("window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth';")
        t = await ctx.new_page(); t.on("pageerror", lambda e: errs.append(str(e)))
        await t.goto("http://127.0.0.1:8090/compta/"); await t.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await t.screenshot(path=OUT + "/logo-tel.png", clip={"x": 0, "y": 0, "width": 400, "height": 120})
        man = await t.evaluate("fetch('manifest.webmanifest').then(r => r.json())"); print("manifest:", [i["src"] for i in man["icons"]])
        ok = await t.evaluate("Promise.all(['icon-feuille-192.png','icon-feuille-512.png','icon-feuille-maskable.png','apple-touch-icon-feuille.png'].map(u => fetch(u).then(r => r.status + ':' + r.headers.get('content-type'))))"); print("icônes:", ok)
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
