"""Version complète au téléphone (mode nuage) : connexion par l'app terrain, modifications envoyées comme changements, fichiers, hors réseau."""
import asyncio, json, os, sys, base64, urllib.request, time
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
FIX = json.load(open("phone/fixture.json", encoding="utf-8"))
OPS_ALL = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr"]
URL = "http://127.0.0.1:8090/compta/"
INIT = "if (/complet\\.html/.test(location.pathname)) window.__NUAGE = true; window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth'; window.__OSRM = 'http://127.0.0.1:8091';"
def post(path, obj=None, raw=None):
    return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8091" + path, data=raw if raw is not None else json.dumps(obj or {}).encode(), method="POST")).read())
def state(): return json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
def tel_ops():
    out = []
    for f in state()["files"]:
        if "tel1" in f.get("parents", []) and f["name"].startswith("op-") and not f.get("trashed"): out.append(json.loads(base64.b64decode(f["content"])))
    return sorted(out, key=lambda o: o["creeLe"])
def add_drive(**o):
    F = mock.STATE["files"]; o.setdefault("modifiedTime", time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())); o.setdefault("trashed", False); o.setdefault("mimeType", "application/octet-stream"); F[o["id"]] = o
async def bar(pg): return await pg.inner_text("#nu-txt")
async def wait_bar(pg, pat, t=12000): await pg.wait_for_function("(p) => new RegExp(p).test(document.getElementById('nu-txt').textContent)", arg=pat, timeout=t)
async def main():
    reg = json.loads(json.dumps(FIX)); reg["telephone"] = {"ops": OPS_ALL, "appliques": []}
    mock.reset(json.dumps(reg)); mock.start()
    add_drive(id="at1", name="a-traiter", mimeType="application/vnd.google-apps.folder", parents=["root1"])
    add_drive(id="hy1", name="facture-hydro.png", mimeType="image/png", parents=["at1"], content=PNG, size=len(PNG))
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 400, "height": 860}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "401" not in m.text else None)
        # 1. Ouverture directe de la version complète : connexion par l'app terrain puis retour
        await pg.goto(URL + "complet.html#transactions")
        await pg.wait_for_selector("#app:not([hidden])", timeout=15000); await wait_bar(pg, "^À jour")
        print("1 url:", pg.url, "| bar:", await bar(pg), "| auth:", [l["prompt"] for l in state()["log"]], "| maj banner hidden:", await pg.is_hidden("#nu-maj"))
        await pg.screenshot(path=OUT + "/complet-accueil.png")
        # 2. Nouvelle dépense avec reçu (appareil photo)
        await pg.click('.m-tabs [data-nu="add"]'); await pg.click('#m-add [data-nuadd="depense"]'); await pg.wait_for_selector("#m-montant")
        await pg.set_input_files("#m-file", files=[{"name": "recu-canadian-tire.png", "mimeType": "image/png", "buffer": PNG}]); await pg.wait_for_timeout(300)
        await pg.fill("#m-montant", "57,49"); await pg.fill("#m-tiers", "Canadian Tire"); await pg.fill("#m-desc", "Chaîne de scie")
        await pg.screenshot(path=OUT + "/complet-depense.png")
        await pg.click("#m-save"); await pg.wait_for_timeout(500)
        await wait_bar(pg, "en attente de l'ordinateur")
        ops = tel_ops(); print("2 ops:", [(o["type"], o["data"].get("to") or o["data"].get("msg"), len(o["photos"])) for o in ops])
        pt = [o for o in ops if o["type"] == "patch"][-1]; ch = pt["data"]["changes"]; print("2b changes:", [(c["col"], "doc" in c, (c.get("doc") or {}).get("tiers"), (c.get("doc") or {}).get("recus")) for c in ch])
        # 3. Modifier une opération existante
        await pg.evaluate("location.hash='transactions'"); await pg.wait_for_timeout(300)
        tid = [t for t in FIX["transactions"] if t["type"] == "depense"][0]["id"]
        await pg.click('[data-edit="' + tid + '"]'); await pg.wait_for_selector("#m-desc"); await pg.fill("#m-desc", "Description corrigée au téléphone"); await pg.click("#m-save"); await pg.wait_for_timeout(600)
        c = [o for o in tel_ops() if o["type"] == "patch"][-1:] or []
        await wait_bar(pg, "en attente de l'ordinateur"); c = [o for o in tel_ops() if o["type"] == "patch"][-1]
        print("3 edit:", c["data"]["msg"], [(x["col"], x.get("set")) for x in c["data"]["changes"]])
        # 4. Fournisseur
        await pg.evaluate("location.hash='fournisseurs'"); await pg.wait_for_timeout(300)
        await pg.click("#btn-add-fourn"); await pg.fill("#e-nom", "Husqvarna Lévis"); await pg.click('#ent-form button[type="submit"]'); await pg.wait_for_timeout(500)
        # 5. Réglages : numéros de taxes
        await pg.evaluate("location.hash='reglages'"); await pg.wait_for_timeout(300)
        print("5a reglages hidden:", await pg.is_hidden("#btn-change-dir"), await pg.is_hidden("#tel-card"))
        await pg.fill("#r-notvq", "1234567890 TQ0001"); await pg.fill("#r-adresse", "45, rang Saint-Joseph, Saint-Henri"); await pg.click('#cfg-form button[type="submit"]'); await pg.wait_for_timeout(500)
        print("5b cfg:", await pg.inner_text("#toast"), "| err:", await pg.is_visible("#cfg-err"))
        # 6. Document « à traiter » déjà dans Google Drive -> dépense
        await pg.evaluate("location.hash='documents'"); await pg.wait_for_timeout(1500)
        print("6 inbox:", (await pg.inner_text("#dc-inbox")).replace("\n", " | ")[-260:])
        await pg.click('[data-ib="depense"][data-i="0"]'); await pg.wait_for_selector("#m-montant"); await pg.fill("#m-montant", "212,30"); await pg.fill("#m-tiers", "Hydro-Québec"); await pg.click("#m-save"); await pg.wait_for_timeout(800); print("6b toast:", await pg.inner_text("#toast"), "| drawer ouvert:", await pg.is_visible("#ov-tx"), "| err:", await pg.evaluate("(document.getElementById('m-err') || {}).textContent"))
        # 7. Kilométrage : trajet + allocation
        await pg.evaluate("location.hash='km'"); await pg.wait_for_timeout(300)
        await pg.fill("#km-dest", "Saint-Henri"); await pg.fill("#km-raison", "Élagage chez M. Roy"); await pg.fill("#km-km", "24"); await pg.click("#km-submit"); await pg.wait_for_timeout(500)
        await pg.click("[data-km-alloc]"); await pg.wait_for_timeout(500)
        # 8. Hors réseau : revenu gardé, puis envoyé au retour du réseau
        await wait_bar(pg, "en attente de l'ordinateur", 15000)
        await ctx.set_offline(True); await pg.wait_for_timeout(200)
        await pg.click('.m-tabs [data-nu="add"]'); await pg.click('#m-add [data-nuadd="revenu"]'); await pg.wait_for_selector("#m-montant"); await pg.fill("#m-montant", "450"); await pg.fill("#m-tiers", "Mme Gagnon"); await pg.fill("#m-desc", "Abattage d'un frêne"); await pg.click("#m-save"); await pg.wait_for_timeout(500)
        print("8 offline bar:", await bar(pg), "| toast:", await pg.inner_text("#toast"))
        await pg.screenshot(path=OUT + "/complet-hors-reseau.png")
        await pg.reload(); await pg.wait_for_timeout(2500)
        print("8b reload offline:", pg.url, "| app hidden:", await pg.evaluate("document.getElementById('app') ? document.getElementById('app').hidden : 'none'"), "|", (await pg.inner_text("body"))[:200].replace("\n", " | "), "| sw:", await pg.evaluate("!!navigator.serviceWorker.controller"), "| base:", await pg.evaluate("!!localStorage.getItem('cm-base')"), "| errs:", errs[-3:])
        await pg.wait_for_selector("#app:not([hidden])")
        await ctx.set_offline(False); await wait_bar(pg, "en attente de l'ordinateur", 15000)
        print("8c online bar:", await bar(pg))
        # 9. PDF et exports (les factures sont dans l'onglet Ventes de l'app terrain)
        await pg.evaluate("location.hash='km'"); await pg.wait_for_timeout(300)
        async with pg.expect_download() as dl: await pg.click("#btn-km-pdf")
        d = await dl.value; print("9c registre:", d.suggested_filename, open(await d.path(), "rb").read()[:8])
        await pg.evaluate("location.hash='transactions'"); await pg.wait_for_timeout(300)
        async with pg.expect_download() as dl: await pg.click("#btn-tx-csv")
        d = await dl.value; print("9d csv:", d.suggested_filename)
        await pg.evaluate("location.hash='documents'"); await pg.wait_for_timeout(300); await pg.click('[data-dc="export"]'); await pg.wait_for_timeout(200)
        async with pg.expect_download(timeout=20000) as dl: await pg.click("#btn-export")
        d = await dl.value; print("9e zip:", d.suggested_filename, os.path.getsize(await d.path()))
        await wait_bar(pg, "en attente de l'ordinateur|À jour", 15000)
        # 10. Tous les changements envoyés
        ops = tel_ops(); print("10 all ops:", [(o["type"], (o["data"].get("msg") or o["data"].get("to") or o["data"].get("from") or "")[:40]) for o in ops])
        files = [{"title": f["name"], "content": f["content"]} for f in state()["files"] if "tel1" in f.get("parents", []) and not f.get("trashed")]
        json.dump({"reg": reg, "files": files}, open(OUT + "/envoi.json", "w"))
        print("overflow:", await pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        # 11. Ordinateur pas encore à jour : modifications bloquées
        reg2 = json.loads(json.dumps(FIX)); post("/__setreg", raw=json.dumps(reg2).encode())
        await pg.click('[data-nu="sync"]'); await wait_bar(pg, "À jour|attente", 15000); await pg.wait_for_timeout(500)
        print("11 banner visible:", await pg.is_visible("#nu-maj"))
        await pg.evaluate("location.hash='fournisseurs'"); await pg.wait_for_timeout(200); await pg.click("#btn-add-fourn"); await pg.fill("#e-nom", "Bloqué"); await pg.click('#ent-form button[type="submit"]'); await pg.wait_for_timeout(400)
        print("11b toast:", (await pg.inner_text("#toast"))[:70])
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
