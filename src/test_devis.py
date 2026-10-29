"""Soumissions et factures complètes : types de frais, unités, taxes incluses, tarifs, nouvelle mise en page, envoi."""
import asyncio, json, os, base64, subprocess, re
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "telephone": "581-991-4738", "courriel": "emondagehamel@gmail.com", "noTPS": "70622 0357 RT 0001", "noTVQ": "12 3214 0824 TQ 0001",
  "neq": "1180262769", "slogan": "Élagage · Abattage · Entretien d'arbres", "modePaiement": "virement Interac à emondagehamel@gmail.com", "titreDevis": "Soumission", "termes": 0,
  "messageFacture": "Il nous fera plaisir de vous accompagner pour vos prochains besoins en émondage et en entretien d'arbres.", "adresse": ""})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "418-555-0142", "adresse": "1600, rue Saint-François\nL'Ancienne-Lorette (Québec)  G2E 3G7", "note": ""}]
REG = json.dumps(reg)
async def getb(pg, path):
    b64 = await pg.evaluate("""async p => { const e = __fs[p]; if (!e) return null; const u = new Uint8Array(await e.content.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); }""", path)
    return base64.b64decode(b64) if b64 else None
async def data(pg): return json.loads(await pg.evaluate("__fs['registre.json'].content.text()"))
async def line(pg, i, **v):
    row = '#d-lines [data-l="%d"] ' % i
    for k, x in v.items():
        if k == "type": await pg.select_option(row + '[data-f="type"]', x)
        else: await pg.fill(row + '[data-f="%s"]' % k, str(x))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width": 1366, "height": 900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('#vt-actions [data-new-doc="devis"]'); await pg.wait_for_selector("#ov-doc:not([hidden])")
        print("1 titre:", await pg.inner_text("#d-title"), "| ttc visible:", await pg.is_visible("#d-ttc"), "| chips:", await pg.eval_on_selector_all("#d-lt-add [data-addlt]", "a => a.map(x => x.textContent)"))
        # 1. La soumission de Michel Auger, prix forfaitaire taxes incluses (400 $)
        await pg.fill("#d-client", "Michel Auger"); await pg.dispatch_event("#d-client", "input")
        await pg.click('#d-ttc [data-ttc="incl"]')
        await line(pg, 0, description="Travaux d'émondage\n1600, rue Saint-François, L'Ancienne-Lorette", qte="1", unite="forfait", prix="400")
        tot = await pg.inner_text("#d-tot"); print("2 totaux taxes incluses:", tot.replace("\n", " | "))
        # 2. Ajouts : location, déplacement, consommables, rabais
        await pg.click('[data-addlt="location"]'); await line(pg, 1, description="Nacelle de 60 pi", qte="1", prix="450")
        await pg.click('[data-addlt="deplacement"]'); await line(pg, 2, description="Aller-retour au chantier", qte="40", prix="1,25")
        await pg.click('[data-addlt="consommables"]'); await line(pg, 3, description="Essence et huile à chaîne", qte="1", prix="35")
        await pg.click('[data-addlt="rabais"]'); await line(pg, 4, description="Rabais client fidèle", qte="1", prix="50")
        await pg.fill("#d-travaux", "Émondage de 3 érables argentés en façade, dégagement de la toiture et ramassage complet des branches.")
        await pg.fill("#d-lieu", "1600, rue Saint-François, L'Ancienne-Lorette"); await pg.fill("#d-dtrav", "2026-11-05")
        units = await pg.eval_on_selector_all('#d-lines [data-f="unite"]', "a => a.map(x => x.value)"); print("3 unités par défaut:", units)
        tot = await pg.inner_text("#d-tot"); print("3 totaux:", tot.replace("\n", " | "))
        exp = 400 + 450 + 50 - 50 + 35; k = 114.975; tx = round(exp * 5 / k, 2); tq = round(exp * 9.975 / k, 2); print("   attendu total", exp, "TPS", tx, "TVQ", tq, "avant taxes", round(exp - tx - tq, 2))
        # 3. Garder la ligne Nacelle comme tarif
        await pg.click('#d-lines [data-tfsave="1"]'); await pg.wait_for_timeout(400); print("4 tarif:", (await data(pg))["reglages"]["tarifs"])
        await pg.screenshot(path=OUT + "/devis-editeur.png", full_page=False)
        await pg.click("#d-save-pdf"); await pg.wait_for_timeout(1200)
        d = await data(pg); v = d["devis"][-1]; print("5 devis:", v["numero"], v.get("taxesIncluses"), v.get("total"), v.get("sousTotal"), v.get("tps"), v.get("tvq"), "| lignes:", [(l["type"], l["unite"], l["prix"]) for l in v["lignes"]], "| docTTC:", d["reglages"].get("docTTC"))
        pdf = await getb(pg, v["pdf"]); open(OUT + "/soumission.pdf", "wb").write(pdf)
        print("6 pdf:", subprocess.run(["qpdf", "--check", OUT + "/soumission.pdf"], capture_output=True, text=True).stdout.strip().split("\n")[-1])
        txt = subprocess.run(["pdftotext", "-layout", OUT + "/soumission.pdf", "-"], capture_output=True, text=True).stdout; print("   '?':", txt.count("?"), "| pages:", txt.count("\f"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        # 4. Facturer la soumission : les lignes et les taxes incluses suivent
        await pg.click('[data-dfac="' + v["id"] + '"]'); await pg.wait_for_selector("#ov-doc:not([hidden])")
        print("7 facture du devis: ttc", await pg.get_attribute('#d-ttc [data-ttc="incl"]', "aria-pressed"), "| lignes", await pg.eval_on_selector_all('#d-lines [data-f="type"]', "a => a.map(x => x.value)"), "| lieu", await pg.input_value("#d-lieu"))
        await pg.fill("#d-dtrav", "2026-11-05")
        await pg.click("#d-save-pdf"); await pg.wait_for_timeout(1200)
        d = await data(pg); f = d["factures"][-1]; t = [t for t in d["transactions"] if t.get("facture") == f["id"]][0]
        print("8 facture:", f["numero"], "| revenu montant", t["montant"], "taxe", t["taxe"], "tvq", t["tvq"], "total", round(t["montant"] + t["taxe"] + t["tvq"], 2))
        pdf = await getb(pg, f["pdf"]); open(OUT + "/facture.pdf", "wb").write(pdf)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        # 5. Facture simple avant taxes, avec un tarif enregistré
        await pg.click('[data-vt="factures"]'); await pg.click('#vt-actions [data-new-doc="facture"]'); await pg.wait_for_selector("#ov-doc:not([hidden])")
        await pg.click('#d-ttc [data-ttc="plus"]')
        await pg.fill("#d-client", "Michel Auger"); await pg.select_option("#d-add-tarif", index=1); await pg.wait_for_timeout(200)
        print("9 tarif ajouté:", await pg.eval_on_selector_all('#d-lines [data-l]', "a => a.map(r => [r.querySelector('[data-f=description]').value, r.querySelector('[data-f=prix]').value, r.querySelector('[data-f=unite]').value])"), "| attendu prix", round(450 * 100 / 114.975, 2))
        await line(pg, 0, qte="2"); tot = await pg.inner_text("#d-tot"); print("   totaux:", tot.replace("\n", " | "))
        await pg.click('#d-ttc [data-ttc="aucune"]'); print("9b sans taxes:", await pg.input_value("#d-code"), "|", (await pg.inner_text("#d-tot")).replace("\n", " | "), "|", await pg.inner_text("#d-ttc-txt"), "| bouton:", await pg.get_attribute('#d-ttc [data-ttc="aucune"]', "aria-pressed"))
        await pg.click('#d-ttc [data-ttc="incl"]'); print("9c taxes incluses:", await pg.input_value("#d-code"), "|", (await pg.inner_text("#d-tot")).replace("\n", " | "), "|", await pg.inner_text("#d-ttc-txt"))
        await pg.select_option("#d-code", "AUCUNE"); print("9d menu Aucune:", await pg.get_attribute('#d-ttc [data-ttc="aucune"]', "aria-pressed"), await pg.get_attribute('#d-ttc [data-ttc="incl"]', "aria-pressed"))
        await pg.click('#d-ttc [data-ttc="plus"]'); print("9e taxes en plus:", await pg.input_value("#d-code"), "|", (await pg.inner_text("#d-tot")).replace("\n", " | "))
        await pg.screenshot(path=OUT + "/devis-taxes.png")
        await pg.keyboard.press("Escape")
        # 6. Envoyer : options
        await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="' + v["id"] + '"]'); await pg.wait_for_selector("#ent-form .send-opts")
        print("10 envoi:", await pg.eval_on_selector_all("#ent-form [data-send]", "a => a.map(x => x.dataset.send + ': ' + x.querySelector('b').textContent)"), "| message:", (await pg.input_value("#snd-msg"))[:120].replace("\n", " / "))
        await pg.screenshot(path=OUT + "/devis-envoi.png")
        async with pg.expect_download() as dl: await pg.click('[data-send="files"]')
        dd = await dl.value; print("11 téléchargement:", dd.suggested_filename)
        await pg.wait_for_timeout(1500)
        # 7. Image JPEG de la soumission (pour Snapchat, texto)
        await pg.keyboard.press("Escape")
        # 8. Réglages
        await pg.evaluate("location.hash='reglages'"); await pg.wait_for_timeout(300)
        print("12 réglages:", await pg.input_value("#r-slogan"), "|", await pg.input_value("#r-titredevis"), "|", (await pg.inner_text("#r-tarifs")).replace("\n", " "))
        await pg.screenshot(path=OUT + "/reglages-factures.png", full_page=True)
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
