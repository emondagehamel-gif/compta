"""L'ordinateur reçoit la signature faite au téléphone."""
import asyncio, json, os, base64, subprocess
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
E = json.load(open("nuage/out/envoi-signature.json"))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width":1366,"height":900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        put = lambda path, b64: "{ const s = atob(" + json.dumps(b64) + "), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs[" + json.dumps(path) + "] = {content:new Blob([u], {type: " + json.dumps("image/jpeg" if path.endswith(".jpg") else "application/json") + "}), mod:Date.now() - 1000}; }"
        seed = "__fs['registre.json'] = {content:new Blob([" + json.dumps(json.dumps(E["reg"])) + "]), mod:1};"
        for f in E["files"]: seed += put("telephone/" + f["title"], f["content"])
        await pg.add_init_script(STUB + "\n" + seed)
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])"); await pg.wait_for_timeout(4000)
        d = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); fs = await pg.evaluate("Object.keys(__fs)")
        v = d["devis"][0]; print("devis:", v["statut"], json.dumps(v.get("signature"), ensure_ascii=False)[:180], "| fichier présent:", v.get("signature", {}).get("fichier") in fs, "| telephone:", [k for k in fs if k.startswith("telephone/")])
        print("ops:", "signature" in d["telephone"]["ops"], "| toast:", await pg.inner_text("#toast"))
        b64 = await pg.evaluate("""async p => { const e = __fs[p]; const u = new Uint8Array(await e.content.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); }""", v["pdf"])
        open("nuage/out/integ-sig.pdf", "wb").write(base64.b64decode(b64))
        print("pdf images:", len(subprocess.run(["pdfimages", "-list", "nuage/out/integ-sig.pdf"], capture_output=True, text=True).stdout.strip().split("\n")[2:]), "|", [l.strip()[:80] for l in subprocess.run(["pdftotext", "-layout", "nuage/out/integ-sig.pdf", "-"], capture_output=True, text=True).stdout.split("\n") if "Signé" in l])
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
