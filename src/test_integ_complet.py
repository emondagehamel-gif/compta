"""L'ordinateur reçoit les changements de la version complète du téléphone."""
import asyncio, json, os, base64
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
E = json.load(open("nuage/out/envoi.json"))
PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width":1366,"height":900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        put = lambda path, b64: "{ const s = atob(" + json.dumps(b64) + "), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs[" + json.dumps(path) + "] = {content:new Blob([u]), mod:Date.now() - 1000}; }"
        seed = "__fs['registre.json'] = {content:new Blob([" + json.dumps(json.dumps(E["reg"])) + "]), mod:1};" + put("a-traiter/facture-hydro.png", PNG)
        for f in E["files"]: seed += put("telephone/" + f["title"], f["content"])
        await pg.add_init_script(STUB + "\n" + seed)
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.wait_for_timeout(4000)
        print("toast:", await pg.inner_text("#toast"))
        d = json.loads(await pg.evaluate("__fs['registre.json'].content.text()"))
        fs = await pg.evaluate("Object.keys(__fs)")
        print("appliques:", len(d["telephone"]["appliques"]), "| ops connus:", "patch" in d["telephone"].get("ops", []))
        print("telephone left:", [k for k in fs if k.startswith("telephone/")])
        print("a-traiter left:", [k for k in fs if k.startswith("a-traiter/")], "| recus:", [k for k in fs if k.startswith("recus/")])
        tx = d["transactions"]
        ct = [t for t in tx if t.get("tiers") == "Canadian Tire"]; print("canadian tire:", [(t["montant"], t["taxe"], t["tvq"], t["recus"]) for t in ct], "| file ok:", all(r["fichier"] in fs for t in ct for r in t["recus"]))
        hy = [t for t in tx if t.get("tiers") == "Hydro-Québec"]; print("hydro:", [(t["montant"], t["recus"]) for t in hy], "| file ok:", all(r["fichier"] in fs for t in hy for r in t["recus"]))
        print("edited:", [t["description"] for t in tx if "corrigée" in (t.get("description") or "")])
        print("fournisseurs:", [f["nom"] for f in d["fournisseurs"]], "| noTVQ:", d["reglages"].get("noTVQ"), "| adresse:", d["reglages"].get("adresse"))
        print("km:", [(k["destination"], k["km"], bool(k.get("alloc"))) for k in d["km"]], "| alloc tx:", [t["description"] for t in tx if t.get("categorie") == "km"])
        print("revenu:", [(t["tiers"], t["montant"], t["taxe"], t["tvq"]) for t in tx if t.get("tiers") == "Mme Gagnon"])
        await pg.evaluate("location.hash='rapports'"); await pg.select_option("#rp-type", "bilan"); await pg.wait_for_timeout(200)
        print("bilan:", (await pg.inner_text("#rp-body .row-head")).replace("\n", " "))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
