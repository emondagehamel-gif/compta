"""v3.13 : signature de l'entreprise en lettres attachées, ajoutée soumission par soumission (au choix).
Aussi : la fenêtre d'envoi Gmail s'ouvre toujours dans sa dernière version, et Réglages signale un service de signature à mettre à jour."""
import sys, json, base64, os
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); CORE = open(sys.argv[2], encoding="utf-8").read(); POL = sys.argv[3]
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)
fonts = {k: base64.b64encode(open(os.path.join(POL, f), "rb").read()).decode() for k, f in
         [("elegante", "great-vibes-latin-400-normal.woff2"), ("classique", "allura-latin-400-normal.woff2"), ("simple", "dancing-script-latin-400-normal.woff2")]}
CORE = CORE.replace("__SIG_FONTS__", json.dumps(fonts))

# 1. Cœur partagé (aussi extrait pour le téléphone)
rep('''function docPDF(kind, doc, logo, sigs){''', CORE.rstrip() + '''\nfunction docPDF(kind, doc, logo, sigs){''')
rep('''signerUrl:"", signerCle:"",''', '''signerUrl:"", signerCle:"", signataire:"", signatureStyle:"elegante",''')

# 2. PDF : la signature de l'entreprise de cette soumission d'abord, sinon celle des Réglages (si elle existe)
rep('''cie: kind !== "facture" && r.signatureCie ? await loadJpeg(r.signatureCie) : null}; }''',
    '''cie: kind === "facture" ? null : doc.signatureCie && doc.signatureCie.fichier ? await loadJpeg(doc.signatureCie.fichier) : r.signatureCie ? await loadJpeg(r.signatureCie) : null}; }''')

# 3. Signer pour l'entreprise / retirer
rep('''const sigResume = sg =>''', '''/* Signature de l'entreprise : ton nom en lettres attachées, sur cette soumission seulement */
async function signCie(id){
  const doc = S.d.devis.find(x => x.id === id); if (!doc) return false;
  const r = R(), G = docGenre("devis");
  const res = await sigNomPad({titre: "Signer pour l'entreprise · " + G.t + " " + doc.numero, texte: "Ton nom s'écrit en lettres attachées dans la case « " + (r.nom || "Entreprise") + " » de " + G.la + ". Seulement sur celle-ci.", nom: r.signataire || "", style: r.signatureStyle || "elegante"});
  if (!res) return false;
  const path = "signatures/" + fileSafe(doc.numero + " entreprise") + "-" + Math.random().toString(36).slice(2, 6) + ".jpg";
  try { await writeFile(path, res.blob); } catch(e){ toast("Signature non enregistrée : " + (e.message || e)); return false; }
  const ok = await mutate(d => { const x = d.devis.find(y => y.id === id); if (!x) return false;
    x.signatureCie = {fichier: path, nom: res.nom, date: res.date, heure: res.heure, style: res.style}; x.modifieLe = new Date().toISOString();
    d.reglages.signataire = res.nom; d.reglages.signatureStyle = res.style; }, G.t + " " + doc.numero + " signée pour l'entreprise par " + res.nom);
  if (!ok) return false;
  if (S.doc && S.doc.orig && S.doc.orig.id === id){ S.doc.orig = S.d.devis.find(x => x.id === id) || S.doc.orig; renderDocExtra(); }
  await makeDocPDF("devis", id, false, true); return true;
}
async function retirerSigCie(id){
  const ok = await mutate(d => { const x = d.devis.find(y => y.id === id); if (!x || !x.signatureCie) return false; delete x.signatureCie; x.modifieLe = new Date().toISOString(); }, "Ta signature est retirée de cette soumission");
  if (!ok) return false;
  if (S.doc && S.doc.orig && S.doc.orig.id === id){ S.doc.orig = S.d.devis.find(x => x.id === id) || S.doc.orig; renderDocExtra(); }
  await makeDocPDF("devis", id, false, true); return true;
}
/* Ligne « signature de l'entreprise » (éditeur et fenêtre d'envoi) ; attr : data-dact ou data-scie */
const cieLigne = (d, attr) => ico("i-feuille") + (d.signatureCie ? "Signée pour l'entreprise par <b>" + esc(d.signatureCie.nom) + "</b>. " + '<button class="btn link" type="button" ' + attr + '="sigcie-suppr">Retirer ma signature</button>'
  : "Pas encore signée pour l'entreprise. " + '<button class="btn sm" type="button" ' + attr + '="sigcie">' + ico("i-pen") + "Ajouter ma signature</button>");
const sigResume = sg =>''')

# 4. Éditeur des soumissions : ligne de la signature de l'entreprise
rep('''    const s = devStatus(o); parts.push('<span class="chip ' + s.cls + '">' + esc(s.l) + "</span>");
    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));
    parts.push('<br><span class="sig-st">' + ico("i-pen") + (o.signature ? sigResume(o.signature) + ' <button class="btn link" type="button" data-dact="sig-suppr">Retirer la signature</button>' : 'Pas encore signée par le client. <button class="btn sm" type="button" data-dact="signer">' + ico("i-pen") + "Faire signer le client</button>") + "</span>");''',
    '''    const s = devStatus(o); parts.push('<span class="chip ' + s.cls + '">' + esc(s.l) + "</span>");
    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));
    parts.push('<br><span class="sig-st">' + ico("i-pen") + (o.signature ? sigResume(o.signature) + ' <button class="btn link" type="button" data-dact="sig-suppr">Retirer la signature</button>' : 'Pas encore signée par le client. <button class="btn sm" type="button" data-dact="signer">' + ico("i-pen") + "Faire signer le client</button>") + "</span>");
    parts.push('<br><span class="sig-st">' + cieLigne(o, "data-dact") + "</span>");''')
rep('''  else if (act === "sig-suppr") retirerSignature(kind, o.id);''', '''  else if (act === "sig-suppr") retirerSignature(kind, o.id);
  else if (act === "sigcie") signCie(o.id);
  else if (act === "sigcie-suppr") retirerSigCie(o.id);''')

# 5. Fenêtre d'envoi : ajouter (ou retirer) ta signature avant d'envoyer
rep('''  const isF = kind === "facture", doc = (isF ? S.d.factures : S.d.devis).find(x => x.id === id); if (!doc) return;
  const G = docGenre(kind), c = clientOf(doc) || {}, msg = docMessage(kind, doc), canShare''', '''  const isF = kind === "facture"; let doc = (isF ? S.d.factures : S.d.devis).find(x => x.id === id); if (!doc) return;
  const G = docGenre(kind), c = clientOf(doc) || {}, msg = docMessage(kind, doc), canShare''')
rep('''+ esc(msg) + "</textarea></label>" +''', '''+ esc(msg) + "</textarea></label>" + (isF ? "" : '<p class="sig-st snd-cie" id="snd-cie">' + cieLigne(doc, "data-scie") + "</p>") +''')
rep('''        const b = e.target.closest("[data-send]"); if (!b) return; const how = b.dataset.send,''', '''        const sc = e.target.closest("[data-scie]");
        if (sc){ sc.disabled = true;
          try { await (sc.dataset.scie === "sigcie" ? signCie(id) : retirerSigCie(id)); } finally { sc.disabled = false; }
          doc = S.d.devis.find(x => x.id === id) || doc; if ($("snd-cie")) $("snd-cie").innerHTML = cieLigne(doc, "data-scie"); return; }
        const b = e.target.closest("[data-send]"); if (!b) return;
        const how = b.dataset.send,''')
rep('''.sg-steps{''', '''.snd-cie{margin:2px 0 12px}.sig-st .ic{flex:none}
.sg-steps{''')

# 6. Signature de l'entreprise faite au téléphone
rep('''"doc-v2","signature"];''', '''"doc-v2","signature","signature-cie","signature-cie-suppr"];''')
rep('''    case "fichier": { const to = safePath(x.to);''', '''    case "signature-cie": {
      const e = d.devis.find(v => v.id === x.id); if (!e || !photos[0]) break;
      const to = "signatures/" + fileSafe(e.numero + " entreprise") + "-" + String(op.id).slice(-4) + (extOf(photos[0]) || ".jpg");
      res.moves.push({from:"telephone/" + photos[0], to});
      e.signatureCie = {fichier: to, nom: String(x.nom || "").trim().slice(0, 60), date: x.date || today(), heure: String(x.heure || "").slice(0, 5), style: String(x.style || "")};
      if (e.signatureCie.nom){ d.reglages.signataire = e.signatureCie.nom; if (x.style) d.reglages.signatureStyle = String(x.style); }
      res.pdfs.push(["devis", e.id]); res.msg = "Signature de l'entreprise : " + e.numero + " (" + e.signatureCie.nom + ")"; break; }
    case "signature-cie-suppr": { const e = d.devis.find(v => v.id === x.id); if (e && e.signatureCie){ delete e.signatureCie; res.pdfs.push(["devis", e.id]); res.msg = "Signature de l'entreprise retirée : " + e.numero; } break; }
    case "fichier": { const to = safePath(x.to);''')

# 7. Fenêtre Gmail : toujours la dernière version (le navigateur garde les pages jusqu'à 10 minutes)
rep('''const w = window.open(ENVOI_URL, "compta-envoi",''', '''const w = window.open(ENVOI_URL + "?v=" + Date.now().toString(36), "compta-envoi",''')

# 8. Service de signature en ligne : signaler une version à mettre à jour (v2 : soumission complète au client et dans l'avis)
rep('''      if (p && p.ok && p.cle){ toast("Signature en ligne activée");''', '''      if (p && p.ok && (Number(p.v) || 1) < SIGNER_V){ say("<b>Service trouvé, mais à mettre à jour (version " + (Number(p.v) || 1) + ").</b> Copie le code (étape 1), ouvre ton projet sur script.google.com, remplace tout le texte par le nouveau code et clique 💾. Ensuite : <b>Déployer</b> › <b>Gérer les déploiements</b> › ✏️ <b>Modifier</b> › Version : <b>Nouvelle version</b> › <b>Déployer</b>. L'adresse reste la même."); return false; }
      if (p && p.ok && p.cle){ toast("Signature en ligne activée");''')
rep('''const SIGNER_GS = ''', '''const SIGNER_V = 2;
const SIGNER_GS = ''')
rep('''    '<li><b>Copie l\\'URL de l\\'application Web</b>''', '''    '<li><b>Copie l\\'URL de l\\'application Web</b>''')
rep('''    '<div class="banner info" id="sg-res" hidden></div>',''', '''    '<p class="muted small">Déjà installé ? Pour mettre à jour le service : copie le code, remplace tout le texte de ton projet Apps Script, 💾, puis Déployer › Gérer les déploiements › ✏️ Modifier › Version : Nouvelle version › Déployer. L\\'adresse ne change pas.</p>' +
    '<div class="banner info" id="sg-res" hidden></div>',''')
open(P, "w", encoding="utf-8").write(s); print("ok")
