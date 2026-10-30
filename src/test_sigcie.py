"""v3.13 : signature de l'entreprise en lettres attachées, au choix, soumission par soumission.
Ordinateur (fenêtre d'envoi et éditeur), téléphone (fiche de la soumission, op signature-cie), puis l'ordinateur reçoit l'op du téléphone."""
import asyncio, json, os, sys, base64, subprocess, urllib.request
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "courriel": "emondagehamel@gmail.com", "telephone": "581-991-4738", "titreDevis": "Soumission", "styleDoc": "nature"})
reg["telephone"] = {"ops": ["devis", "facture", "doc-v2", "signature", "signature-cie", "signature-cie-suppr"], "appliques": []}
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "", "adresse": "1600, rue Saint-François", "note": ""}]
L = [{"type": "service", "description": "Abattage d'un frêne mort", "qte": 1, "unite": "forfait", "prix": 650}]
reg["devis"] = [{"id": "dv-c1", "numero": "D-2026-030", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L, "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""},
                {"id": "dv-c2", "numero": "D-2026-031", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L, "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
REG = json.dumps(reg)
def pdftext(p): return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout
def pdfimgs(p): return len(subprocess.run(["pdfimages", "-list", p], capture_output=True, text=True).stdout.strip().split("\n")[2:])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        def watch(pg, tag):
            pg.on("pageerror", lambda e: errs.append(tag + " pageerror: " + str(e)))
            pg.on("console", lambda m: errs.append(tag + " console: " + m.text) if m.type == "error" else None)
        ctx = await b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True); pg = await ctx.new_page(); watch(pg, "app")
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html")); await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        data = lambda: pg.evaluate("__fs['registre.json'].content.text()")
        # 1. Fenêtre d'envoi : pas de signature au départ, on l'ajoute
        await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-c1"]'); await pg.wait_for_selector("#snd-cie")
        print("1 envoi:", await pg.inner_text("#snd-cie"))
        await pg.click('#snd-cie [data-scie="sigcie"]'); await pg.wait_for_selector(".sig-ov .sig-style")
        await pg.wait_for_function("[...document.querySelectorAll('.sig-apercu')].every(x => x.style.fontFamily)")
        print("1b fenêtre:", await pg.inner_text(".sig-ov .sig-t"), "| styles:", await pg.eval_on_selector_all(".sig-style small", "a => a.map(x => x.textContent)"), "| bouton actif sans nom:", not await pg.is_disabled(".sig-ok"))
        await pg.fill(".sig-n input", "Dimitry Hamel"); await pg.click('.sig-style[data-style="classique"]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=OUT + "/sigcie-fenetre.png")
        await pg.click(".sig-ok"); await pg.wait_for_function("document.getElementById('snd-cie').textContent.includes('Dimitry')", timeout=8000)
        d = json.loads(await data()); v = d["devis"][0]; fs = await pg.evaluate("Object.keys(__fs)")
        print("2 après:", await pg.inner_text("#snd-cie"), "|", json.dumps(v.get("signatureCie"), ensure_ascii=False), "| image:", v["signatureCie"]["fichier"] in fs, "| retenu:", d["reglages"].get("signataire"), d["reglages"].get("signatureStyle"))
        print("2b autre soumission sans signature:", "signatureCie" not in d["devis"][1])
        got = []
        async with pg.expect_download() as dl: await pg.click('[data-send="files"]')
        dd = await dl.value; await dd.save_as(OUT + "/sigcie.pdf")
        async with pg.expect_download() as dl2: pass
        await (await dl2.value).save_as(OUT + "/sigcie.jpg")
        print("2c pdf:", pdfimgs(OUT + "/sigcie.pdf"), "image(s) |", [l.strip()[:80] for l in pdftext(OUT + "/sigcie.pdf").split("\n") if "entreprise par" in l])
        await pg.click('#snd-cie [data-scie="sigcie-suppr"]'); await pg.wait_for_function("document.getElementById('snd-cie').textContent.includes('Pas encore')", timeout=8000)
        print("3 retirée:", await pg.inner_text("#snd-cie"), "|", "signatureCie" not in json.loads(await data())["devis"][0]); await pg.click("#e-cancel")
        # 4. Éditeur de la soumission : nom et style retenus
        await pg.click('[data-dev="dv-c2"]'); await pg.wait_for_selector("#ov-doc:not([hidden])"); await pg.wait_for_timeout(300)
        print("4 éditeur:", [l for l in (await pg.inner_text("#d-paid")).split("\n") if "entreprise" in l])
        await pg.click('[data-dact="sigcie"]'); await pg.wait_for_selector(".sig-ov .sig-style")
        print("4b nom proposé:", await pg.input_value(".sig-n input"), "| style choisi:", await pg.get_attribute('.sig-style[aria-checked="true"]', "data-style"))
        await pg.click(".sig-ok"); await pg.wait_for_function("document.getElementById('d-paid').textContent.includes('Signée pour')", timeout=8000)
        v2 = json.loads(await data())["devis"][1]; print("4c éditeur après:", [l for l in (await pg.inner_text("#d-paid")).split("\n") if "entreprise" in l], "| pdf:", v2.get("pdf"))
        print("ERRORS app:", errs)
        # 5. Téléphone : signer une soumission pour l'entreprise
        reg2 = json.loads(REG); reg2["devis"][1] = v2; reg2["reglages"]["signataire"] = "Dimitry Hamel"; reg2["reglages"]["signatureStyle"] = "classique"
        mock.reset(json.dumps(reg2)); mock.start()
        tel = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await tel.add_init_script("window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth';")
        t = await tel.new_page(); watch(t, "tel")
        await t.goto("http://127.0.0.1:8090/compta/"); await t.wait_for_function("document.getElementById('h-sync-t').textContent.startsWith('À jour')", timeout=10000)
        await t.click('[data-tab="ventes"]'); await t.click('#v-ventes [data-vt="devis"]'); await t.click("text=D-2026-030"); await t.wait_for_selector('#sheet [data-x="sigcie"]')
        await t.click('#sheet [data-x="sigcie"]'); await t.wait_for_selector(".sig-ov .sig-style"); print("5 téléphone, nom proposé:", await t.input_value(".sig-n input"))
        await t.wait_for_function("[...document.querySelectorAll('.sig-apercu')].every(x => x.style.fontFamily)"); await t.screenshot(path=OUT + "/sigcie-tel.png")
        await t.click(".sig-ok"); await t.wait_for_selector("#sheet .sig-done"); await t.wait_for_timeout(2500)
        print("5b fiche:", [x for x in (await t.inner_text("#sheet")).split("\n") if "entreprise" in x])
        st = json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
        ops = [f for f in st["files"] if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed")]
        op = json.loads(base64.b64decode(ops[-1]["content"])); print("5c op:", op["type"], json.dumps(op["data"], ensure_ascii=False), op["photos"])
        photo = [f for f in st["files"] if f["name"] == op["photos"][0]][0]
        await t.click('#sheet [data-x="pdf"]'); await t.wait_for_selector('[data-send="save"]')
        async with t.expect_download() as dl: await t.click('[data-send="save"]')
        dd = await dl.value; await dd.save_as(OUT + "/sigcie-tel.pdf"); print("5d pdf du téléphone:", pdfimgs(OUT + "/sigcie-tel.pdf"), "image(s) |", [l.strip()[:60] for l in pdftext(OUT + "/sigcie-tel.pdf").split("\n") if "entreprise par" in l])
        # 6. L'ordinateur reçoit l'op du téléphone
        seed = "__fs['telephone/%s.json'] = {content:new Blob([%s]), mod:Date.now()};" % (op["id"], json.dumps(json.dumps(op)))
        seed += "{ const s = atob(%s), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs['telephone/%s'] = {content:new Blob([u]), mod:Date.now()}; }" % (json.dumps(photo["content"]), op["photos"][0])
        await pg.click("#d-cancel") if await pg.is_visible("#d-cancel") else None
        await pg.evaluate(seed); await pg.wait_for_timeout(7000)
        d = json.loads(await data()); v = d["devis"][0]; fs = await pg.evaluate("Object.keys(__fs)")
        print("6 ordinateur:", json.dumps(v.get("signatureCie"), ensure_ascii=False), "| image rangée:", v.get("signatureCie", {}).get("fichier") in fs, "| toast:", await pg.inner_text("#toast"))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
