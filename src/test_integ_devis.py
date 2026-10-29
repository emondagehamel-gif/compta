"""L'ordinateur reçoit une soumission et une facture faites au téléphone (types de frais, taxes incluses, rabais)."""
import asyncio, json, os, base64, subprocess
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
E = json.load(open("nuage/out/envoi-devis.json"))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width":1366,"height":900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        put = lambda path, b64: "{ const s = atob(" + json.dumps(b64) + "), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs[" + json.dumps(path) + "] = {content:new Blob([u]), mod:Date.now() - 1000}; }"
        seed = "__fs['registre.json'] = {content:new Blob([" + json.dumps(json.dumps(E["reg"])) + "]), mod:1};"
        for f in E["files"]: seed += put("telephone/" + f["title"], f["content"])
        await pg.add_init_script(STUB + "\n" + seed)
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])"); await pg.wait_for_timeout(4000)
        d = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); fs = await pg.evaluate("Object.keys(__fs)")
        print("ops connus doc-v2:", "doc-v2" in d["telephone"].get("ops", []), "| telephone left:", [k for k in fs if k.startswith("telephone/")])
        v = d["devis"][-1]; print("devis:", v["numero"], v.get("taxesIncluses"), v.get("total"), v.get("tps"), v.get("tvq"), v.get("travaux"), v.get("pdf"))
        f = d["factures"][-1]; t = [t for t in d["transactions"] if t.get("facture") == f["id"]][0]
        exp = 375; tx = round(exp * 5 / 114.975, 2); tq = round(exp * 9.975 / 114.975, 2)
        print("facture:", f["numero"], f.get("taxesIncluses"), "| revenu", t["montant"], t["taxe"], t["tvq"], "| attendu", round(exp - tx - tq, 2), tx, tq, "| pdf", f.get("pdf"))
        for path in [v.get("pdf"), f.get("pdf")]:
            if not path: continue
            b64 = await pg.evaluate("""async p => { const e = __fs[p]; const u = new Uint8Array(await e.content.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); }""", path)
            open("nuage/out/integ.pdf", "wb").write(base64.b64decode(b64)); txt = subprocess.run(["pdftotext", "-layout", "nuage/out/integ.pdf", "-"], capture_output=True, text=True).stdout
            print("  pdf", path, "| total:", [l.strip() for l in txt.split("\n") if "Total" in l][:2])
        await pg.evaluate("location.hash='rapports'"); await pg.select_option("#rp-type", "bilan"); await pg.wait_for_timeout(200)
        print("bilan:", (await pg.inner_text("#rp-body .row-head")).replace("\n", " "))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
