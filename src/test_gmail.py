"""v3.11 : « Envoyer par Gmail » depuis l'ordinateur avec le PDF joint (page d'envoi + faux Gmail).
Connexion Google par la page principale, courriel MIME vérifié, date d'envoi notée, API non activée, refus de Google, dépannage."""
import asyncio, json, os, sys, base64, urllib.request, email, email.policy, time
sys.path.insert(0, "pwa")
import mock
from playwright.async_api import async_playwright
exec(open('test4.py').read().split('OUT = ')[0].split('from playwright.async_api import async_playwright')[1])
OUT = "nuage/out"; os.makedirs(OUT, exist_ok=True)
reg = json.load(open("phone/fixture.json", encoding="utf-8"))
reg["reglages"].update({"nom": "Émondage Hamel", "courriel": "emondagehamel@gmail.com", "titreDevis": "Soumission", "telephone": "581-991-4738"})
reg["clients"] = [{"id": "c-ma", "nom": "Michel Auger", "courriel": "michel.auger@exemple.ca", "telephone": "", "adresse": "1600, rue Saint-François", "note": ""},
                  {"id": "c-sc", "nom": "Sophie Côté", "courriel": "", "telephone": "", "adresse": "", "note": ""}]
L = [{"type": "service", "description": "Travaux d'émondage", "qte": 1, "unite": "forfait", "prix": 400}]
reg["devis"] = [{"id": "dv-e1", "numero": "D-2026-010", "date": "2026-10-29", "echeance": "2026-11-28", "client": "Michel Auger", "clientId": "c-ma", "lignes": L, "codeTaxe": "QC", "taxesIncluses": True, "statut": "ouvert", "projet": "", "message": ""}]
reg["factures"] = [{"id": "fa-e1", "numero": "F-2026-024", "date": "2026-10-29", "echeance": "2026-10-29", "client": "Sophie Côté", "clientId": "c-sc", "lignes": L, "codeTaxe": "QC", "taxesIncluses": False, "categorie": "ventes", "statut": "emise", "projet": "", "message": ""}]
REG = json.dumps(reg)
INIT = "window.__GAPI = 'http://127.0.0.1:8091'; window.__GAUTH = 'http://127.0.0.1:8091/o/oauth2/v2/auth';"
ENV = "http://127.0.0.1:8090/compta/envoi.html"
def post(path, obj=None): return json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8091" + path, data=json.dumps(obj or {}).encode(), method="POST")).read())
def state(): return json.loads(urllib.request.urlopen("http://127.0.0.1:8091/__state").read())
def mail(i):
    m = email.message_from_bytes(base64.b64decode(state()["mails"][i]), policy=email.policy.default)
    att = [(a.get_filename(), a.get_content_type(), a.get_content()) for a in m.iter_attachments()]
    return {"from": str(m["From"]), "to": str(m["To"]), "subject": str(m["Subject"]), "body": m.get_body(("plain",)).get_content(), "att": [(n, t, len(c), c[:5]) for n, t, c in att]}
async def main():
    mock.reset(open("phone/fixture.json", encoding="utf-8").read()); mock.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True)
        await ctx.add_init_script(INIT)
        await ctx.route("https://mail.google.com/**", lambda r: r.fulfill(body="<title>Gmail</title>gmail", content_type="text/html"))
        def watch(pg, tag):
            pg.on("pageerror", lambda e: errs.append(tag + " pageerror: " + str(e)))
            pg.on("console", lambda m: errs.append(tag + " console: " + m.text) if m.type == "error" and "favicon" not in m.text and "404" not in m.text else None)
        ctx.on("page", lambda pg: watch(pg, "popup"))
        pg = await ctx.new_page(); watch(pg, "app")
        await pg.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};\nwindow.__ENVOI = " + json.dumps(ENV) + ";")
        await pg.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html"))
        await pg.click("#sp-pick"); await pg.wait_for_selector("#app:not([hidden])")
        await pg.evaluate("location.hash='ventes'"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        print("1 option:", (await pg.inner_text('[data-send="gmail"]')).replace("\n", " | "))
        # 2. Premier envoi : la page s'ouvre, connexion Google (permission Gmail), puis le courriel prêt avec le PDF
        async with ctx.expect_page() as pop: await pg.click('[data-send="gmail"]')
        w = await pop.value
        await w.wait_for_selector("#f:not([hidden])", timeout=15000)
        lg = state()["log"]; print("2 connexion:", len(lg), lg[-1] if lg else None)
        print("2b fenêtre:", w.url, "| opener:", await w.evaluate("!!window.opener"), "| de:", (await w.inner_text("#de")).replace("\n", " "), "| sous:", await w.inner_text("#sous"))
        print("2c à:", await w.input_value("#to"), "| objet:", await w.input_value("#su"), "| pj:", await w.inner_text("#pj-nom"), await w.inner_text("#pj-taille"))
        print("2d message:", (await w.input_value("#bo"))[:90].replace("\n", " / "))
        print("2e guide app:", (await pg.inner_text("#snd-guide"))[:160].replace("\n", " "))
        await w.screenshot(path=OUT + "/gmail-fenetre.png"); await pg.screenshot(path=OUT + "/gmail-app.png")
        closed = asyncio.get_event_loop().create_future(); w.on("close", lambda _: closed.done() or closed.set_result(1))
        await w.click("#envoyer"); await w.wait_for_selector("#fini:not([hidden])")
        print("3 fini:", (await w.inner_text("#fini")).replace("\n", " | "))
        m = mail(0); print("3b courriel:", m["from"], "|", m["to"], "|", m["subject"], "|", m["att"]); print("3c corps:", m["body"][:80].replace("\r\n", " / ").replace("\n", " / "))
        await pg.wait_for_function("document.getElementById('snd-guide').textContent.includes('envoyé')")
        print("3d guide app:", (await pg.inner_text("#snd-guide"))[:200].replace("\n", " "))
        d2 = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); print("3e envoyé le:", d2["devis"][0].get("envoyeLe"))
        await asyncio.wait_for(closed, 8); print("3f fenêtre fermée toute seule")
        # 4. Facture d'un client sans courriel : jeton encore bon (pas de nouvelle connexion), adresse à écrire, API pas activée puis activée
        await pg.click("#e-cancel"); await pg.click('[data-vt="factures"]'); await pg.click('[data-fmail="fa-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        n0 = len(state()["log"])
        async with ctx.expect_page() as pop: await pg.click('[data-send="gmail"]')
        w = await pop.value; await w.wait_for_selector("#f:not([hidden])", timeout=15000)
        print("4 sans nouvelle connexion:", len(state()["log"]) == n0, "| à:", repr(await w.input_value("#to")), "| focus:", await w.evaluate("document.activeElement.id"))
        await w.click("#envoyer"); print("4b adresse manquante:", await w.inner_text("#to-hint"))
        await w.fill("#to", "sophie.cote@exemple.ca ; comptable@exemple.ca"); await w.fill("#su", "Facture F-2026-024 · Émondage Hamel — travaux à l'érablière")
        post("/__mode", {"gmail": "disabled"}); await w.click("#envoyer"); await w.wait_for_selector("#err:not([hidden])")
        print("4c api:", (await w.inner_text("#err")).replace("\n", " | ")[:260], "| lien:", await w.get_attribute("#err a", "href"))
        await w.screenshot(path=OUT + "/gmail-api.png")
        post("/__mode", {"gmail": "ok"}); await w.click('#err [data-a="renvoyer"]'); await w.wait_for_selector("#fini:not([hidden])")
        m = mail(1); print("4d courriel:", m["to"], "|", m["subject"], "|", m["att"])
        await pg.wait_for_function("document.getElementById('snd-guide') && document.getElementById('snd-guide').textContent.includes('envoyé')")
        d2 = json.loads(await pg.evaluate("__fs['registre.json'].content.text()")); print("4e envoyée le:", d2["factures"][0].get("envoyeeLe"))
        # 4f. La forme JSON est bloquée par le navigateur : l'envoi passe par l'autre forme
        if not w.is_closed(): await w.wait_for_event("close", timeout=8000)
        post("/__mode", {"gmail": "json-cors"}); n1 = len(state()["mails"])
        await pg.click("#e-cancel"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        async with ctx.expect_page() as pop: await pg.click('[data-send="gmail"]')
        w = await pop.value; await w.wait_for_selector("#f:not([hidden])", timeout=15000); await w.click("#envoyer"); await w.wait_for_selector("#fini:not([hidden])")
        print("4f relais:", len(state()["mails"]) == n1 + 1, "| pj:", mail(n1)["att"]); post("/__mode", {"gmail": "ok"})
        # 5. Google refuse la permission : la page l'explique, « Réessayer » redemande le compte
        await w.evaluate("localStorage.removeItem('cm-tok')"); post("/__mode", {"auth": "refuse"})
        if not w.is_closed(): await w.wait_for_event("close", timeout=8000)
        if not w.is_closed(): await w.wait_for_event("close", timeout=8000)
        await pg.click("#e-cancel"); await pg.click('[data-vt="devis"]'); await pg.click('[data-dmail="dv-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        async with ctx.expect_page() as pop: await pg.click('[data-send="gmail"]')
        w = await pop.value; await w.wait_for_function("document.querySelector('#st:not([hidden]) [data-a=\"auth\"]')", timeout=15000)
        print("5 refus:", (await w.inner_text("#st")).replace("\n", " | ")[:220], "| url:", w.url)
        post("/__mode", {"auth": "ok"}); await w.click('[data-a="auth"]'); await w.wait_for_selector("#f:not([hidden])", timeout=15000)
        print("5b réessai:", state()["log"][-1]["prompt"], "| formulaire:", await w.input_value("#to"))
        # 6. Jeton expiré pendant l'envoi : reconnexion automatique, ce qui a été modifié est gardé
        await w.fill("#bo", "Bonjour Michel,\n\nVoici la soumission modifiée.\n\nMerci!"); post("/__mode", {"expire": True})
        n0 = len(state()["log"]); await w.click("#envoyer")
        for _ in range(100):
            if len(state()["log"]) > n0: break
            await asyncio.sleep(0.1)
        await w.wait_for_selector("#f:not([hidden])", timeout=15000); await w.wait_for_timeout(300)
        print("6 après reconnexion:", (await w.input_value("#bo"))[:40].replace("\n", " / "), "| connexions:", len(state()["log"]))
        await w.click("#envoyer"); await w.wait_for_selector("#fini:not([hidden])"); print("6b corps envoyé:", mail(len(state()["mails"]) - 1)["body"][:45].replace("\n", " / "))
        # 7. Dépannage : ancienne façon (Gmail s'ouvre, le PDF se télécharge)
        if not w.is_closed(): await w.wait_for_event("close", timeout=8000)
        await pg.click("#e-cancel"); await pg.click('[data-vt="factures"]'); await pg.click('[data-fmail="fa-e1"]'); await pg.wait_for_selector("#ent-form .send-opts")
        async with ctx.expect_page() as pop: await pg.click('[data-send="gmail"]')
        w = await pop.value; await w.wait_for_selector("#f:not([hidden])", timeout=15000); await w.click("#annuler")
        await pg.wait_for_selector('[data-send="gmailm"]')
        async with ctx.expect_page() as pop, pg.expect_download() as dl: await pg.click('[data-send="gmailm"]')
        g = await pop.value; d = await dl.value; await g.wait_for_load_state(); print("7 manuel:", g.url.split("?")[0], d.suggested_filename); await g.close()
        # 8. Page ouverte toute seule : rien à envoyer
        q = await ctx.new_page(); await q.goto(ENV); await q.wait_for_selector("#st b"); await q.wait_for_timeout(300); print("8 seule:", await q.inner_text("#st b")); await q.close()
        # 9. Page d'envoi qui ne répond pas : deux recharges, puis l'autre façon est proposée
        ctx = await b.new_context(viewport={"width": 1366, "height": 900}); await ctx.add_init_script(INIT)
        pg2 = await ctx.new_page(); watch(pg2, "app2")
        await pg2.add_init_script(STUB + "\n__fs['registre.json'] = {content:new Blob([" + json.dumps(REG) + "]), mod:1};\nwindow.__ENVOI = 'http://127.0.0.1:8090/compta/manifest.webmanifest';")
        await pg2.goto("file://" + os.path.abspath("Comptabilite/Comptabilite.html")); await pg2.wait_for_selector("#app:not([hidden]), #sp-pick")
        if await pg2.is_visible("#sp-pick"): await pg2.click("#sp-pick")
        await pg2.wait_for_selector("#app:not([hidden])")
        await pg2.evaluate("location.hash='ventes'"); await pg2.click('[data-vt="devis"]'); await pg2.click('[data-dmail="dv-e1"]'); await pg2.wait_for_selector("#ent-form .send-opts")
        t0 = time.time()
        async with ctx.expect_page() as pop: await pg2.click('[data-send="gmail"]')
        w = await pop.value
        await pg2.wait_for_function("document.getElementById('snd-guide').textContent.includes('ne répond pas')", timeout=40000)
        print("9 sans réponse après %.0f s:" % (time.time() - t0), w.url.split("/")[-1], "|", (await pg2.inner_text("#snd-guide"))[:120].replace("\n", " "))
        print("ERRORS:", errs); await b.close()
asyncio.run(main())
