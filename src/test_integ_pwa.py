import asyncio, json, os, base64
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
REG = open("phone/fixture.json", encoding="utf-8").read()
OPS = json.load(open("pwa/out/ops.json"))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width":1366,"height":900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        seed = "__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};"
        for f in OPS:
            seed += "{ const s = atob(" + json.dumps(f["content"]) + "), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs['telephone/" + f["title"] + "'] = {content:new Blob([u]), mod:Date.now() - 1000}; }"
        await pg.add_init_script(STUB + "\n" + seed)
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.wait_for_timeout(3500)
        print("toast:", await pg.inner_text("#toast"))
        d = json.loads(await pg.evaluate("__fs['registre.json'].content.text()"))
        print("appliques:", len(d.get("telephone", {}).get("appliques", [])))
        print("tel files left:", await pg.evaluate("Object.keys(__fs).filter(k => k.startsWith('telephone/'))"))
        ul = [t for t in d["transactions"] if t.get("source") == "telephone"]; print("tx from phone:", [(t["tiers"], t["categorie"], t["montant"], t["taxe"], t["tvq"], [r["fichier"] for r in t.get("recus", [])]) for t in ul])
        print("recus files:", await pg.evaluate("Object.keys(__fs).filter(k => k.startsWith('recus/'))"))
        print("agenda:", [(n["titre"], n.get("type"), n.get("heure")) for n in d["agenda"]][-2:])
        print("km:", [(k["destination"], k["km"]) for k in d["km"]])
        await pg.evaluate("location.hash='rapports'"); await pg.select_option("#rp-type", "bilan"); await pg.wait_for_timeout(200)
        print("bilan:", (await pg.inner_text("#rp-body .row-head")).replace("\n", " "))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
