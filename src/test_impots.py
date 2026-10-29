"""Impôts de fin d'année : calculs vérifiés à la main sur un cas chiffré."""
import asyncio, json, os, base64, subprocess, re
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"]["dateConstitution"] = "2024-03-01"
T = reg["transactions"]
def tx(**o):
    base = {"type":"depense","description":"","tiers":"","categorie":"autres","montant":0,"taxe":0,"tvq":0,"codeTaxe":"QC","compte":"c-banque","statut":"regle","echeance":"","projet":"","note":"","aVerifier":False,"recus":[]}
    base.update(o); T.append(base)
tx(id="t-v1", date="2026-06-30", type="revenu", categorie="ventes", description="Contrats d'émondage", tiers="Clients divers", montant=120000, taxe=6000, tvq=11970)
tx(id="t-r1", date="2026-07-02", categorie="repas", description="Dîners clients", tiers="Restaurants", montant=400, taxe=20, tvq=39.9)
tx(id="t-i1", date="2026-05-10", categorie="equipement", description="Déchiqueteuse", tiers="Vermeer", montant=8000, taxe=400, tvq=798)
tx(id="t-i2", date="2026-08-15", categorie="equipement-info", description="Ordinateur portable", tiers="Bureau en Gros", montant=1500, taxe=75, tvq=149.63)
tx(id="t-d1", date="2026-12-15", type="dividende", categorie="", description="Dividende", tiers="Dimitry Hamel", montant=10000, taxe=0, tvq=0, codeTaxe="")
reg["equipements"][0]["coutAchat"] = 45000; reg["equipements"][0]["dateAchat"] = "2026-03-01"
REG = json.dumps(reg)
async def kv(pg, card):
    return [x for x in (await pg.inner_text("#fa-body .card:nth-of-type(%d)" % card)).split("\n") if x.strip()]
def money(s): return float(s.replace("\xa0", "").replace(" ", "").replace("$", "").replace(",", ".").replace("−", "-"))
async def val(pg, label):
    return await pg.evaluate("(l) => { for (const d of document.querySelectorAll('#fa-body .kv > div')){ const a = d.children[0], b = d.children[1]; if (a && b && a.textContent.trim().startsWith(l)) return b.textContent.trim(); } return null; }", label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        pg = await b.new_page(viewport={"width":1366,"height":900})
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};")
        await pg.goto("file://" + os.environ.get("APPHTML", os.path.abspath("Comptabilite/Comptabilite.html")))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.evaluate("location.hash='impots'"); await pg.wait_for_selector("#fa-body .card")
        await pg.screenshot(path=OUT + "/impots-1.png", full_page=True)
        net = money(await val(pg, "Bénéfice net comptable"))
        rows = await pg.evaluate("[...document.querySelectorAll('#fa-body > .card')[2].querySelectorAll('tbody tr')].map(r => [...r.children].map(c => c.innerText.trim()))")
        print("net comptable:", net)
        print("DPA rows:", [(r[0].split("\n")[0], r[2], r[4], r[6]) for r in rows])
        cca = {"8": 8000 * 0.2 * 1.5, "10": 45000 * 0.3 * 1.5, "50": 1500 * 0.55 * 1.5}
        got = {re.search(r"Catégorie ([\d.]+)", r[0]).group(1): money(r[4].split("\n")[0]) for r in rows}
        print("CCA attendue:", cca, "| obtenue:", got, "| OK:", all(abs(got[k] - v) < 0.01 for k, v in cca.items()))
        tot = sum(cca.values()); rep = (400 + (20 + 39.9) * 0.5) * 0.5  # repas : 50 % du coût, y compris la moitié des taxes non récupérables
        exp_net = round(net + rep - tot, 2)
        got_net = money(await val(pg, "Revenu net aux fins"))
        print("revenu net fiscal attendu:", exp_net, "| obtenu:", got_net, "| OK:", abs(exp_net - got_net) < 0.01)
        fed = money(await val(pg, "Fédéral")); qc = money(await val(pg, "Québec"))
        print("impôt fédéral:", fed, "attendu", round(exp_net * 0.09, 2), "| Québec sans DPE:", qc, "attendu", round(exp_net * 0.115, 2))
        # heures rémunérées : 6 000 -> déduction complète (3,2 %)
        await pg.fill('[data-fa="heures"]', "6000"); await pg.dispatch_event('[data-fa="heures"]', "change"); await pg.wait_for_timeout(400)
        qc2 = money(await val(pg, "Québec")); print("Québec avec 6 000 h:", qc2, "attendu", round(exp_net * 0.032, 2), "| focus gardé:", await pg.evaluate("document.activeElement.dataset.fa"))
        await pg.fill('[data-fa="heures"]', "5250"); await pg.dispatch_event('[data-fa="heures"]', "change"); await pg.wait_for_timeout(400)
        qc3 = money(await val(pg, "Québec")); print("Québec avec 5 250 h (moitié):", qc3, "attendu", round(exp_net * 0.115 - exp_net * 0.083 * 0.5, 2))
        # camion en catégorie 10.1 : coût limité à 39 000 $
        await pg.select_option('[data-fa-bien="e:eq-1"][data-fa-k="cat"]', "10.1"); await pg.wait_for_timeout(400)
        rows = await pg.evaluate("[...document.querySelectorAll('#fa-body > .card')[2].querySelectorAll('tbody tr')].map(r => [...r.children].map(c => c.innerText.trim()))")
        print("10.1:", [(r[0].split("\n")[0], r[2], r[4].split("\n")[0]) for r in rows if "10.1" in r[0]], "attendu", 39000 * 0.3 * 1.5)
        await pg.select_option('[data-fa-bien="e:eq-1"][data-fa-k="cat"]', "10"); await pg.wait_for_timeout(300)
        # DPA demandée plus petite, ajustement, pertes, acomptes
        await pg.fill('[data-fa="dpaDemandee|10"]', "10000"); await pg.dispatch_event('[data-fa="dpaDemandee|10"]', "change"); await pg.wait_for_timeout(400)
        print("DPA totale après choix:", await pg.evaluate("document.querySelectorAll('#fa-body > .card')[2].querySelector('.card-h span').textContent"), "attendu", 2400 + 10000 + 1237.5)
        await pg.click('[data-fa-d="ad"] summary'); await pg.fill("#fa-ad-l", "Pénalités sur impôts"); await pg.fill("#fa-ad-v", "150"); await pg.click("#fa-ad-ok"); await pg.wait_for_timeout(400)
        await pg.fill('[data-fa="pertes"]', "1000"); await pg.dispatch_event('[data-fa="pertes"]', "change"); await pg.wait_for_timeout(400)
        net2 = money(await val(pg, "Revenu net aux fins")); imp2 = money(await val(pg, "Revenu imposable"))
        exp2 = round(net + rep + 150 - (2400 + 10000 + 1237.5), 2); print("après ajustements: net", net2, "attendu", exp2, "| imposable", imp2, "attendu", exp2 - 1000)
        await pg.fill('[data-fa="acomptesFed"]', "1000"); await pg.dispatch_event('[data-fa="acomptesFed"]', "change"); await pg.wait_for_timeout(400)
        print("solde fédéral:", await val(pg, "Solde à payer au fédéral"), "attendu", round((exp2 - 1000) * 0.09 - 1000, 2))
        # dividendes
        print("T5:", await val(pg, "Case 10"), await val(pg, "Case 11"), await val(pg, "Case 12"), "| attendu 10000 / 11500 /", round(11500 * 0.090301, 2))
        print("RL-3:", await val(pg, "Case A2"), await val(pg, "Case B"), await val(pg, "Case C"), "| attendu C", round(11500 * 0.0342, 2))
        print("dates:", await val(pg, "Solde d'impôt"), "|", await val(pg, "Déclarations T2"), "|", await val(pg, "Feuillets"))
        print("verifs:", [x for x in (await kv(pg, 2))][:14])
        await pg.screenshot(path=OUT + "/impots-2.png", full_page=True)
        # PDF
        await pg.click("#btn-fa-pdf"); await pg.wait_for_timeout(800)
        b64 = await pg.evaluate("(async () => { const f = __fs['exports/fin-annee-2026.pdf']; if (!f) return ''; const u = new Uint8Array(await f.content.arrayBuffer()); let s = ''; for (const x of u) s += String.fromCharCode(x); return btoa(s); })()")
        open(OUT + "/fin-annee.pdf", "wb").write(base64.b64decode(b64))
        print("pdf:", subprocess.run(["qpdf", "--check", OUT + "/fin-annee.pdf"], capture_output=True, text=True).stdout.strip().split("\n")[-1])
        txt = subprocess.run(["pdftotext", "-layout", OUT + "/fin-annee.pdf", "-"], capture_output=True, text=True).stdout
        print("pdf pages:", txt.count("\f"), "| has T5:", "T5 case 11" in txt, "| has DPA:", "Catégorie 10" in txt, "| '?' chars:", txt.count("?"))
        d = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); print("saved fiscal:", json.dumps(d["reglages"].get("fiscal"), ensure_ascii=False)[:300])
        await pg.keyboard.press("Escape")
        await pg.evaluate("location.hash='rapports'"); await pg.select_option("#rp-type", "bilan"); await pg.wait_for_timeout(200)
        print("bilan:", (await pg.inner_text("#rp-body .row-head")).replace("\n", " "))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
