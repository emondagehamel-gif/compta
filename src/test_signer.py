"""v3.12 : signature en ligne des soumissions, de bout en bout.
Lien signé dans le courriel et bouton cliquable dans le PDF ; le client signe sur signer.html (cellulaire) ; le faux Apps Script
(signer.gs exécuté par Node) dépose l'op dans telephone/ ; l'ordinateur l'applique (« en ligne », acceptée). Liens modifiés, expirés, déjà signés.
Mise en place dans Réglages (code copié, adresse, vérification)."""
import asyncio, json, os, sys, base64, subprocess, shutil, time, tempfile, urllib.parse, re
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
SID = "AKfycbTESTtestTESTtest1234567890abcdef"
GAS = "http://127.0.0.1:8093/macros/s/"; SURL = GAS + SID + "/exec"; PAGE = "http://127.0.0.1:8090/compta/signer.html"
CLE = "6f1c2a9e0b7d4c3a8e5f1029384756abcdef0123456789ab"
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "courriel": "emondagehamel@gmail.com", "telephone": "581-991-4738", "titreDevis": "Soumission", "styleDoc": "nature", "signerUrl": SURL, "signerCle": CLE})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "", "adresse": "1600, rue Saint-François\nL'Ancienne-Lorette", "note": ""}]
L = [{"type": "service", "description": "Abattage d'un frêne mort", "qte": 1, "unite": "forfait", "prix": 650}, {"type": "location", "description": "Nacelle de 60 pi", "qte": 1, "unite": "jour", "prix": 450}]
reg["devis"] = [{"id": "dv-s1", "numero": "D-2026-020", "date": "2026-10-29", "echeance": "2099-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L, "codeTaxe": "QC", "taxesIncluses": False, "statut": "ouvert", "projet": "", "message": ""},
                {"id": "dv-s3", "numero": "D-2026-021", "date": "2026-10-29", "echeance": "2099-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L[:1], "codeTaxe": "QC", "taxesIncluses": False, "statut": "ouvert", "projet": "", "message": "", "total": 1.0},
                {"id": "dv-s2", "numero": "D-2026-005", "date": "2026-08-01", "echeance": "2026-08-31", "client": "Michel Auger", "clientId": "c-ma", "lignes": L[:1], "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
reg["devis"][0]["signatureCie"] = {"fichier": "signatures/D-2026-020-entreprise-ab12.jpg", "nom": "Dimitry Hamel", "date": "2026-10-29", "heure": "09:00", "style": "elegante"}
from PIL import Image, ImageDraw
_im = Image.new("RGB", (520, 160), "white"); ImageDraw.Draw(_im).text((20, 60), "Dimitry Hamel (signature)", fill=(34, 53, 111)); import io as _io; _b = _io.BytesIO(); _im.save(_b, "JPEG"); SIGCIE = _b.getvalue()
REG = json.dumps(reg)
INIT = "window.__SCRIPT = %s; window.__SIGNER = %s;" % (json.dumps(GAS), json.dumps(PAGE))
async def main():
    D = tempfile.mkdtemp(); C = os.path.join(D, "Comptabilite"); os.makedirs(os.path.join(C, "telephone")); os.makedirs(os.path.join(C, "signatures"))
    open(os.path.join(C, "signatures", "D-2026-020-entreprise-ab12.jpg"), "wb").write(SIGCIE)
    open(os.path.join(C, "registre.json"), "w", encoding="utf-8").write(REG)
    gas = subprocess.Popen(["node", "nuage/fake_gas.js", D, "8093"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True); print("0", gas.stdout.readline().strip())
    mock.reset(open("phone/fixture.json", encoding="utf-8").read()); mock.start()
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); errs = []
            def watch(pg, tag):
                pg.on("pageerror", lambda e: errs.append(tag + " pageerror: " + str(e)))
                pg.on("console", lambda m: errs.append(tag + " console: " + m.text) if m.type == "error" else None)
            ctx = await b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True, permissions=["clipboard-read", "clipboard-write"])
            await ctx.add_init_script(INIT); pg = await ctx.new_page(); watch(pg, "app")
            await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};" +
                "{ const s = atob(%s), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs['signatures/D-2026-020-entreprise-ab12.jpg'] = {content:new Blob([u], {type:'image/jpeg'}), mod:1}; }" % json.dumps(base64.b64encode(SIGCIE).decode()))
            await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
            await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
            # 1. Le message contient le lien de signature ; le PDF a un bouton cliquable
            await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-s1"]'); await pg.wait_for_selector("#ent-form .send-opts")
            msg = await pg.input_value("#snd-msg"); print("1 message:", msg.split("\n\n")[2].replace("\n", " / ")[:220], "| adresse visible:", "signer.html" in msg)
            got = []
            async with pg.expect_download() as dl: await pg.click('[data-send="files"]')
            d = await dl.value; dest = OUT + "/signer-" + d.suggested_filename; await d.save_as(dest); got.append(dest)
            async with pg.expect_download() as dl2: pass
            d2 = await dl2.value; img = OUT + "/signer-" + d2.suggested_filename; await d2.save_as(img)
            pdf = open(dest, "rb").read(); m = re.search(rb"/URI \((.*?)\) >>", pdf); lien = m.group(1).decode()
            print("1b lien du PDF:", len(lien), "car. |", lien[:110] + "…"); print("1c pdf:", d.suggested_filename, "| annotation:", b"/Subtype /Link" in pdf, "| image:", img)
            txt = subprocess.run(["pdftotext", "-layout", dest, "-"], capture_output=True, text=True).stdout
            print("1d texte:", [l.strip() for l in txt.split("\n") if "Signer en ligne" in l or "Touchez" in l])
            print("1e qpdf:", subprocess.run(["qpdf", "--check", dest], capture_output=True, text=True).stdout.strip().split("\n")[-1] if shutil.which("qpdf") else "(qpdf absent)")
            await pg.click("#e-cancel")
            # 2. Le client ouvre le lien sur son cellulaire et signe
            mob = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
            await mob.add_init_script(INIT); c = await mob.new_page(); watch(c, "client")
            await c.goto(lien); await c.wait_for_selector("#f:not([hidden])")
            print("2a aperçu complet:", await c.is_visible("#apercu"), "| pages:", await c.locator("#pages img").count(), "| note PDF cachée:", not await c.is_visible("#resume .note"))
            await c.screenshot(path=OUT + "/signer-apercu.png", full_page=True)
            print("2 résumé:", (await c.inner_text("#resume")).replace("\n", " | "))
            print("2b case:", await c.inner_text("#ok-t")); print("2c bouton actif au départ:", not await c.is_disabled("#go"))
            await c.wait_for_function("[...document.querySelectorAll('#pages img')].every(i => i.complete && i.naturalWidth)"); await c.locator("#cv").scroll_into_view_if_needed(); await c.wait_for_timeout(200)
            box = await c.locator("#cv").bounding_box()
            pts = [(0.12, 0.6), (0.2, 0.3), (0.3, 0.7), (0.42, 0.35), (0.55, 0.65), (0.68, 0.3), (0.8, 0.62)]
            await c.mouse.move(box["x"] + box["width"] * pts[0][0], box["y"] + box["height"] * pts[0][1]); await c.mouse.down()
            for x, y in pts[1:]: await c.mouse.move(box["x"] + box["width"] * x, box["y"] + box["height"] * y, steps=6)
            await c.mouse.up()
            print("2d après la signature, sans la case:", await c.is_disabled("#go")); await c.check("#ok")
            await c.screenshot(path=OUT + "/signer-client.png", full_page=True)
            await c.click("#go"); await c.wait_for_selector("#fini:not([hidden])")
            print("2e fini:", (await c.inner_text("#fini")).replace("\n", " | "), "| copie:", await c.get_attribute("#copie", "download"))
            async with c.expect_download() as dlc: await c.click("#copie")
            cp = await dlc.value; await cp.save_as(OUT + "/signer-copie-client.pdf"); print("2e2 copie client:", cp.suggested_filename, open(OUT + "/signer-copie-client.pdf", "rb").read()[:5])
            await c.screenshot(path=OUT + "/signer-merci.png")
            tel = sorted(os.listdir(os.path.join(C, "telephone"))); print("2f drive telephone:", tel)
            op = json.load(open(os.path.join(C, "telephone", [f for f in tel if f.endswith(".json")][0]), encoding="utf-8")); print("2g op:", op["type"], json.dumps(op["data"], ensure_ascii=False))
            mails = json.load(open(os.path.join(D, ".mails.json"), encoding="utf-8")); print("2h2 avis pièces:", mails[0]["attachments"], "| images dans le courriel:", mails[0]["inline"], "| html:", "cid:page1" in mails[0]["html"])
            shutil.copy(os.path.join(D, ".mail-page1.jpg"), OUT + "/signer-avis-page1.jpg") if os.path.exists(os.path.join(D, ".mail-page1.jpg")) else None
            print("2h avis:", mails[0]["to"], "|", mails[0]["subject"], "|", mails[0]["body"][:150].replace("\n", " "), "|", mails[0]["attachments"])
            # 3. Le même lien : déjà signée ; lien modifié ; soumission expirée ; lien incomplet
            await c.goto("about:blank"); await c.goto(lien); await c.wait_for_selector("#st b:not(:has(.spin))"); await c.wait_for_timeout(400)
            print("3 rouvert:", (await c.inner_text("#st")).replace("\n", " | "))
            faux = lien.replace("&t=", "&t=1").replace("#s=", "#s=")
            await c.goto("about:blank"); await c.goto(faux); await c.wait_for_timeout(1200); print("3b montant changé:", (await c.inner_text("#st")).replace("\n", " | ")[:120])
            async def lien_pdf(i):
                await pg.click('[data-dmail="%s"]' % i); await pg.wait_for_selector("#ent-form .send-opts")
                async with pg.expect_download() as dlx: await pg.click('[data-send="files"]')
                x = re.search(rb"/URI \((.*?)\) >>", open(await (await dlx.value).path(), "rb").read())
                async with pg.expect_download() as dly: pass
                await dly.value; await pg.click("#e-cancel"); return x.group(1).decode() if x else None
            l2 = await lien_pdf("dv-s2"); l2 = re.search(r".+", l2) if l2 else None
            print("3c lien de la soumission expirée dans le message:", bool(l2))
            if l2:
                await c.goto("about:blank"); await c.goto(l2.group(0)); await c.wait_for_timeout(1200); print("3d expirée:", (await c.inner_text("#st")).replace("\n", " | ")[:160])
            l3 = await lien_pdf("dv-s3")
            await c.goto("about:blank"); await c.goto(l3); await c.wait_for_timeout(1200); print("3f modifiée depuis l'envoi:", (await c.inner_text("#st")).replace("\n", " | ")[:140])
            await c.goto("about:blank"); await c.goto(PAGE + "#i=x"); await c.wait_for_timeout(500); print("3e incomplet:", (await c.inner_text("#st")).replace("\n", " | ")[:90])
            # 4. L'ordinateur reçoit la signature (Google Drive synchronise le dossier telephone)
            seed = ""
            for f in tel:
                b64 = base64.b64encode(open(os.path.join(C, "telephone", f), "rb").read()).decode()
                seed += "{ const s = atob(%s), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); __fs[%s] = {content:new Blob([u]), mod:Date.now()}; }" % (json.dumps(b64), json.dumps("telephone/" + f))
            await pg.evaluate(seed); await pg.wait_for_timeout(7000)
            dd = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); v = dd["devis"][0]; fsk = await pg.evaluate("Object.keys(__fs)")
            print("4 devis:", v["statut"], json.dumps(v.get("signature"), ensure_ascii=False), "| image rangée:", v.get("signature", {}).get("fichier") in fsk, "| telephone vide:", not [k for k in fsk if k.startswith("telephone/")])
            print("4b toast:", await pg.inner_text("#toast"))
            await pg.click('[data-dmail="dv-s1"]'); await pg.wait_for_selector("#ent-form .send-opts"); m3 = await pg.input_value("#snd-msg")
            print("4c message après signature (plus de bouton):", "Signer en ligne" not in m3, "|", m3.split("\n\n")[1][:90].replace("\n", " / "))
            async with pg.expect_download() as dl: await pg.click('[data-send="files"]')
            d = await dl.value; await d.save_as(OUT + "/signer-signee.pdf")
            async with pg.expect_download() as dl2: pass
            await (await dl2.value).save_as(OUT + "/signer-signee.jpg")
            t2 = subprocess.run(["pdftotext", "-layout", OUT + "/signer-signee.pdf", "-"], capture_output=True, text=True).stdout
            print("4d pdf signé:", [l.strip()[:90] for l in t2.split("\n") if "lectroniquement" in l or "Signer en ligne" in l], "| lien:", b"/URI" in open(OUT + "/signer-signee.pdf", "rb").read())
            await pg.click("#e-cancel")
            # 5. Réglages : vérification du service, code copié
            await pg.evaluate("location.hash='reglages'"); await pg.wait_for_selector("#r-sg-st"); await pg.wait_for_timeout(300)
            print("5 réglages:", await pg.inner_text("#r-sg-st"), "|", await pg.inner_text("#r-sg"))
            await pg.click("#r-sg"); await pg.wait_for_selector("#sg-url"); print("5b adresse:", await pg.input_value("#sg-url") == SURL)
            await pg.click("#sg-copy"); code = await pg.evaluate("navigator.clipboard.readText()"); print("5c code copié:", len(code), "car. |", "function doPost" in code, "| identique:", code == open("nuage/signer.gs", encoding="utf-8").read())
            await pg.fill("#sg-url", "https://exemple.com/x"); await pg.click('#ent-form footer button[type="submit"]'); await pg.wait_for_timeout(300); print("5d mauvaise adresse:", await pg.inner_text("#e-err"))
            await pg.fill("#sg-url", SURL); await pg.click('#ent-form footer button[type="submit"]'); await pg.wait_for_function("document.getElementById('sg-res').textContent.includes('✓')", timeout=8000)
            print("5e vérifié:", (await pg.inner_text("#sg-res"))[:120]); await pg.screenshot(path=OUT + "/signer-reglages.png"); await pg.click("#e-cancel")
            await pg.click("#r-sg-rm"); await pg.wait_for_timeout(500); print("5f désactivée:", await pg.inner_text("#r-sg-st"), "| clé gardée:", bool(json.loads(await pg.evaluate("__fs['registre.json'].content.text()"))["reglages"].get("signerCle")))
            print("ERRORS:", errs); await b.close()
    finally:
        gas.terminate()
asyncio.run(main())
