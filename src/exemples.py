"""Exemples pour l'utilisateur : la facture et la soumission de Michel Auger refaites avec la nouvelle mise en page (PDF et image)."""
import asyncio, json, os, base64, subprocess
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
STYLE = os.environ.get("STYLE", "origine"); OUT = "nuage/exemples-" + STYLE; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
for k in ["transactions", "factures", "devis", "clients"]: reg[k] = []
reg["reglages"].update({"nom": "Émondage Hamel", "telephone": "581-991-4738", "courriel": "emondagehamel@gmail.com", "noTPS": "70622 0357 RT 0001", "noTVQ": "12 3214 0824 TQ 0001",
  "neq": "1180262769", "slogan": "Élagage · Abattage · Entretien d'arbres", "modePaiement": "virement Interac à emondagehamel@gmail.com", "titreDevis": "Soumission", "termes": 0, "validiteDevis": 30,
  "messageFacture": "Il nous fera plaisir de vous accompagner pour vos prochains besoins en émondage et en entretien d'arbres.", "adresse": "", "logo": "", "styleDoc": STYLE})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "", "telephone": "", "adresse": "1600, rue Saint-François\nL'Ancienne-Lorette (Québec)  G2E 3G7", "note": ""}]
L1 = [{"type": "service", "description": "Travaux d'émondage\n1600, rue Saint-François, L'Ancienne-Lorette", "qte": 1, "unite": "", "prix": 400}]
reg["devis"] = [{"id": "dv-ex1", "numero": "D-2026-001", "date": "2026-09-23", "echeance": "2026-10-23", "client": "Michel Auger", "clientId": "c-ma", "lignes": L1, "codeTaxe": "QC", "taxesIncluses": True, "message": reg["reglages"]["messageFacture"], "statut": "ouvert", "projet": ""},
  {"id": "dv-ex2", "numero": "D-2026-002", "date": "2026-10-28", "echeance": "2026-11-27", "client": "Michel Auger", "clientId": "c-ma", "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "dateTravaux": "2026-11-05",
   "travaux": "Abattage d'un frêne mort près du garage, émondage de 2 érables en façade et ramassage complet des branches.", "message": reg["reglages"]["messageFacture"],
   "lignes": [{"type": "service", "description": "Abattage d'un frêne mort (démontage par sections)", "qte": 1, "unite": "forfait", "prix": 650},
              {"type": "service", "description": "Émondage de 2 érables en façade", "qte": 6, "unite": "h", "prix": 85},
              {"type": "location", "description": "Nacelle de 60 pi", "qte": 1, "unite": "jour", "prix": 450},
              {"type": "outils", "description": "Déchiqueteuse à branches", "qte": 1, "unite": "jour", "prix": 150},
              {"type": "deplacement", "description": "Aller-retour au chantier", "qte": 40, "unite": "km", "prix": 1.25},
              {"type": "consommables", "description": "Essence et huile à chaîne", "qte": 1, "unite": "forfait", "prix": 35},
              {"type": "disposition", "description": "Transport des branches et du bois à l'écocentre", "qte": 2, "unite": "voyage", "prix": 75},
              {"type": "rabais", "description": "Rabais client fidèle", "qte": 1, "unite": "", "prix": 100}]}]
reg["factures"] = [{"id": "fa-ex1", "numero": "F-2026-001", "date": "2026-09-24", "echeance": "2026-09-24", "dateTravaux": "2026-09-24", "client": "Michel Auger", "clientId": "c-ma", "lignes": L1, "codeTaxe": "QC", "taxesIncluses": True, "categorie": "ventes", "statut": "emise", "devis": "dv-ex1", "message": reg["reglages"]["messageFacture"], "projet": ""}]
REG = json.dumps(reg)
async def getb(pg, path):
    b64 = await pg.evaluate("""async p => { const e = __fs[p]; if (!e) return null; const u = new Uint8Array(await e.content.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); }""", path)
    return base64.b64decode(b64) if b64 else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True); pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.evaluate("location.hash='ventes'"); await pg.wait_for_timeout(300)
        for kind, tab, ids in [("devis", "devis", ["dv-ex1", "dv-ex2"]), ("facture", "factures", ["fa-ex1"])]:
            await pg.click('[data-vt="%s"]' % tab); await pg.wait_for_timeout(200)
            for i in ids:
                await pg.click('[data-%s="%s"]' % ("dmail" if kind == "devis" else "fmail", i)); await pg.wait_for_selector("#ent-form .send-opts")
                got = []
                for n in range(2):
                    async with pg.expect_download() as dl:
                        if n == 0: await pg.click('[data-send="files"]')
                    d = await dl.value; dest = OUT + "/" + d.suggested_filename; await d.save_as(dest); got.append(dest)
                print(kind, i, got); await pg.click("#e-cancel"); await pg.wait_for_timeout(300)
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
