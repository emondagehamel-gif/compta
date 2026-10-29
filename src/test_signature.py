"""Signature du client à l'ordinateur : soumission acceptée, facture confirmée, signature de l'entreprise, PDF."""
import asyncio, json, os, base64, subprocess
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "telephone": "581-991-4738", "courriel": "emondagehamel@gmail.com", "noTPS": "70622 0357 RT 0001", "noTVQ": "12 3214 0824 TQ 0001", "neq": "1180262769",
  "slogan": "Élagage · Abattage · Entretien d'arbres", "modePaiement": "virement Interac à emondagehamel@gmail.com", "titreDevis": "Soumission", "termes": 0})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "", "telephone": "", "adresse": "1600, rue Saint-François\nL'Ancienne-Lorette (Québec)  G2E 3G7", "note": ""}]
L1 = [{"type": "service", "description": "Travaux d'émondage", "qte": 1, "unite": "forfait", "prix": 400}]
reg["devis"] = [{"id": "dv-s1", "numero": "D-2026-009", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L1, "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
REG = json.dumps(reg)
async def draw(pg, sel=".sig-zone canvas"):
    box = await pg.locator(sel).bounding_box(); x0, y0 = box["x"] + 40, box["y"] + box["height"] * 0.6
    await pg.mouse.move(x0, y0); await pg.mouse.down()
    for k in range(1, 30): await pg.mouse.move(x0 + k * 9, y0 - 30 * ((k % 6) / 6), steps=2)
    await pg.mouse.up()
async def getb(pg, path):
    b64 = await pg.evaluate("""async p => { const e = __fs[p]; if (!e) return null; const u = new Uint8Array(await e.content.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); }""", path)
    return base64.b64decode(b64) if b64 else None
async def data(pg): return json.loads(await pg.evaluate("__fs['registre.json'].content.text()"))
def pdfinfo(path):
    imgs = subprocess.run(["pdfimages", "-list", path], capture_output=True, text=True).stdout.strip().split("\n")[2:]
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
    return len(imgs), [l.strip()[:110] for l in txt.split("\n") if "Signé" in l or "Client" in l or "Date :" in l]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width": 1366, "height": 900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        # 1. Signature de l'entreprise (Réglages)
        await pg.evaluate("location.hash='reglages'"); await pg.wait_for_timeout(300); await pg.click("#r-sigcie"); await pg.wait_for_selector(".sig-ov")
        print("1 nom demandé:", await pg.locator(".sig-n").count(), "| ok désactivé:", await pg.is_disabled(".sig-ok"))
        await draw(pg); await pg.click(".sig-ok"); await pg.wait_for_timeout(600)
        d = await data(pg); print("1b signatureCie:", d["reglages"].get("signatureCie"), "| fichier:", (await getb(pg, d["reglages"]["signatureCie"]) or b"")[:3], "|", await pg.inner_text("#r-sigcie-st"))
        # 2. Soumission : le client signe depuis la liste
        await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dsig="dv-s1"]'); await pg.wait_for_selector(".sig-ov")
        print("2 texte:", await pg.inner_text(".sig-t"), "| nom:", await pg.input_value(".sig-n input"))
        await pg.screenshot(path=OUT + "/signature-pave.png")
        await pg.click(".sig-clear"); print("2b après Effacer, ok désactivé:", await pg.is_disabled(".sig-ok"))
        await draw(pg); await pg.click(".sig-ok"); await pg.wait_for_timeout(1500)
        d = await data(pg); v = d["devis"][0]; print("3 devis:", v["statut"], json.dumps(v.get("signature"), ensure_ascii=False)[:200], "| pdf:", v.get("pdf"), "| toast:", await pg.inner_text("#toast"))
        open(OUT + "/soumission-signee.pdf", "wb").write(await getb(pg, v["pdf"])); print("3b pdf images, lignes:", pdfinfo(OUT + "/soumission-signee.pdf"))
        print("3c bouton liste:", await pg.get_attribute('[data-dsig="dv-s1"]', "class"))
        # 3. Facture tirée de la soumission, puis signée depuis l'éditeur
        await pg.click('[data-dfac="dv-s1"]'); await pg.wait_for_selector("#ov-doc:not([hidden])"); await pg.fill("#d-dtrav", "2026-10-29"); await pg.click('#doc-form button[type="submit"]'); await pg.wait_for_timeout(800)
        d = await data(pg); f = d["factures"][-1]; print("4 facture:", f["numero"], "| signature héritée:", "signature" in f)
        await pg.click('[data-vt="factures"]'); await pg.click('[data-fac="' + f["id"] + '"]'); await pg.wait_for_selector("#ov-doc:not([hidden])")
        print("4b éditeur:", (await pg.inner_text("#d-paid")).replace("\n", " ")[:160])
        await pg.click('[data-dact="signer"]'); await pg.wait_for_selector(".sig-ov"); print("4c texte:", await pg.inner_text(".sig-t"))
        await pg.fill(".sig-n input", "Michel Auger"); await draw(pg); await pg.click(".sig-ok"); await pg.wait_for_timeout(1500)
        print("4d éditeur après:", (await pg.inner_text("#d-paid")).replace("\n", " ")[:200])
        d = await data(pg); f = [x for x in d["factures"] if x["id"] == f["id"]][0]; t = [t for t in d["transactions"] if t.get("facture") == f["id"]][0]
        print("5 facture signée:", json.dumps(f.get("signature"), ensure_ascii=False)[:160], "| revenu:", t["montant"], t["taxe"], t["tvq"])
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        open(OUT + "/facture-signee.pdf", "wb").write(await getb(pg, f["pdf"])); print("5b pdf:", pdfinfo(OUT + "/facture-signee.pdf"))
        # 4. Retirer la signature
        await pg.click('[data-fac="' + f["id"] + '"]'); await pg.wait_for_selector("#ov-doc:not([hidden])"); await pg.click('[data-dact="sig-suppr"]'); await pg.wait_for_timeout(800)
        d = await data(pg); print("6 retirée:", "signature" in [x for x in d["factures"] if x["id"] == f["id"]][0], "|", (await pg.inner_text("#d-paid")).replace("\n", " ")[:120])
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
