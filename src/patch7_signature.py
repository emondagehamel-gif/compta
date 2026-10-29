"""v3.8 : le client signe la soumission ou la facture à l'écran (ordinateur et version complète du téléphone) ; signature de l'entreprise ; op « signature » du téléphone."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

# Icône stylo
i = s.index('<symbol id="i-pdf"'); j = s.index('</symbol>', i) + len('</symbol>')
s = s[:j] + '\n  <symbol id="i-pen" viewBox="0 0 24 24"><path d="M3 21c3-1 5-3 7-6l7-7a2.1 2.1 0 0 0-3-3l-7 7c-3 2-5 4-6 7z"/><path d="M14 6l3 3"/><path d="M13 21h8"/></symbol>' + s[j:]

# Chemins permis pour les fichiers envoyés par la version complète du téléphone
rep('''return /^(recus|a-traiter|documents|exports)\\/[^\\/\\\\:*?"<>|]+$/.test(p)''', '''return /^(recus|a-traiter|documents|exports|signatures)\\/[^\\/\\\\:*?"<>|]+$/.test(p)''')
rep('''"patch","fichier","deplacer","fichier-suppr","doc-v2"];''', '''"patch","fichier","deplacer","fichier-suppr","doc-v2","signature"];''')
# Op « signature » du téléphone (app terrain)
rep('''    case "fichier": { const to = safePath(x.to);''', '''    case "signature": {
      const L = x.kind === "devis" ? d.devis : d.factures, e = L.find(v => v.id === x.id); if (!e || !photos[0]) break;
      const to = "signatures/" + fileSafe(e.numero + " " + (e.client || "")) + "-" + String(op.id).slice(-4) + (extOf(photos[0]) || ".jpg");
      res.moves.push({from:"telephone/" + photos[0], to});
      e.signature = {fichier: to, nom: String(x.nom || e.client || "").trim().slice(0, 80), date: x.date || today(), heure: String(x.heure || "").slice(0, 5), signeLe: x.signeLe || now, appareil: "téléphone"};
      if (x.kind === "devis" && (!e.statut || e.statut === "ouvert")) e.statut = "accepte";
      res.pdfs.push([x.kind === "devis" ? "devis" : "facture", e.id]); res.msg = "Signature du client : " + e.numero + " (" + e.signature.nom + ")"; break; }
    case "fichier": { const to = safePath(x.to);''')

# Signatures pour le PDF
rep('''async function makeDocPDF(kind, id, open, quiet){''', '''async function loadJpeg(path){ try { return await jpegObj(await readBlob(path)); } catch(e){ return null; } }
async function docSigs(kind, doc){ const r = R(); return {client: doc.signature && doc.signature.fichier ? await loadJpeg(doc.signature.fichier) : null, cie: kind !== "facture" && r.signatureCie ? await loadJpeg(r.signatureCie) : null}; }
/* Faire signer le client à l'écran */
async function signDoc(kind, id){
  const isF = kind === "facture", doc = (isF ? S.d.factures : S.d.devis).find(x => x.id === id); if (!doc) return;
  const res = await sigPad({titre: "Signature du client · " + docTitre(kind) + " " + doc.numero, texte: sigTexte(kind, doc), nom: doc.client || ""}); if (!res) return;
  const path = "signatures/" + fileSafe(doc.numero + " " + (doc.client || "")) + "-" + Math.random().toString(36).slice(2, 6) + ".jpg";
  try { await writeFile(path, res.blob); } catch(e){ toast("Signature non enregistrée : " + (e.message || e)); return; }
  const ok = await mutate(d => { const x = (isF ? d.factures : d.devis).find(y => y.id === id); if (!x) return false;
    x.signature = {fichier: path, nom: res.nom, date: res.date, heure: res.heure, signeLe: res.signeLe, appareil: CLOUD ? "téléphone" : "ordinateur"}; x.modifieLe = new Date().toISOString();
    if (!isF && (!x.statut || x.statut === "ouvert")) x.statut = "accepte"; if (isF) syncFactureTx(d, x, ""); }, (isF ? "Facture " : docTitre(kind) + " ") + doc.numero + " signée par " + res.nom + (isF ? "" : " : acceptée"), {label:"Envoyer la copie signée", fn: () => shareDoc(kind, id)});
  if (!ok) return;
  if (S.doc && S.doc.orig && S.doc.orig.id === id){ S.doc.orig = (isF ? S.d.factures : S.d.devis).find(x => x.id === id) || S.doc.orig; if (!isF) $("d-etat").value = S.doc.orig.statut || "ouvert"; renderDocExtra(); }
  await makeDocPDF(kind, id, false, true);
}
function retirerSignature(kind, id){
  const isF = kind === "facture"; mutate(d => { const x = (isF ? d.factures : d.devis).find(y => y.id === id); if (!x || !x.signature) return false; delete x.signature; x.modifieLe = new Date().toISOString(); }, "Signature retirée").then(ok => { if (ok){ if (S.doc && S.doc.orig && S.doc.orig.id === id){ S.doc.orig = (isF ? S.d.factures : S.d.devis).find(x => x.id === id) || S.doc.orig; renderDocExtra(); } makeDocPDF(kind, id, false, true); } });
}
const sigResume = sg => "Signée par " + esc(sg.nom) + " le " + esc(dLong(sg.date)) + (sg.heure ? " à " + esc(hmTxt(sg.heure)) : "") + ".";
async function makeDocPDF(kind, id, open, quiet){''')
rep('''    const bytes = docPDF(kind, doc, await loadLogo());''', '''    const bytes = docPDF(kind, doc, await loadLogo(), await docSigs(kind, doc));''')
rep('''          b.disabled = true; const logo = await loadLogo(), name = fileSafe(doc.numero + " " + (doc.client || ""));''', '''          b.disabled = true; const logo = await loadLogo(), sigs = await docSigs(kind, doc), name = fileSafe(doc.numero + " " + (doc.client || ""));''')
rep('''            const files = how === "img" ? await docImages(kind, doc, logo) : [new File([docPDF(kind, doc, logo)], name + ".pdf", {type:"application/pdf"})];''',
    '''            const files = how === "img" ? await docImages(kind, doc, logo, sigs) : [new File([docPDF(kind, doc, logo, sigs)], name + ".pdf", {type:"application/pdf"})];''')
rep('''          if (how === "files"){ const all = [new File([docPDF(kind, doc, logo)], name + ".pdf", {type:"application/pdf"}), ...await docImages(kind, doc, logo)];''',
    '''          if (how === "files"){ const all = [new File([docPDF(kind, doc, logo, sigs)], name + ".pdf", {type:"application/pdf"}), ...await docImages(kind, doc, logo, sigs)];''')

# Éditeur : état de la signature et boutons
rep('''    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));
    if (S.doc.confirm === "annuler")''', '''    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));
    parts.push('<br><span class="sig-st">' + ico("i-pen") + (o.signature ? sigResume(o.signature) + ' <button class="btn link" type="button" data-dact="sig-suppr">Retirer la signature</button>' : 'Pas encore signée par le client. <button class="btn sm" type="button" data-dact="signer">' + ico("i-pen") + "Faire signer le client</button>") + "</span>");
    if (S.doc.confirm === "annuler")''')
rep('''    const s = devStatus(o); parts.push('<span class="chip ' + s.cls + '">' + esc(s.l) + "</span>");
    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));''', '''    const s = devStatus(o); parts.push('<span class="chip ' + s.cls + '">' + esc(s.l) + "</span>");
    if (o.pdf) parts.push("PDF : " + esc(winPath(o.pdf)));
    parts.push('<br><span class="sig-st">' + ico("i-pen") + (o.signature ? sigResume(o.signature) + ' <button class="btn link" type="button" data-dact="sig-suppr">Retirer la signature</button>' : 'Pas encore signée par le client. <button class="btn sm" type="button" data-dact="signer">' + ico("i-pen") + "Faire signer le client</button>") + "</span>");''')
rep('''  else if (act === "facturer"){ closeDoc(); devisToFacture(o); }''', '''  else if (act === "facturer"){ closeDoc(); devisToFacture(o); }
  else if (act === "signer") signDoc(kind, o.id);
  else if (act === "sig-suppr") retirerSignature(kind, o.id);''')
# Liste des ventes : bouton Signer
rep('''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + "</button>") + "</div></td></tr>"; }).join("") +''',
    '''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + '</button><button class="icon-btn' + (f.signature ? " signed" : "") + '" type="button" data-fsig="' + esc(f.id) + '" title="' + (f.signature ? "Signée par " + esc(f.signature.nom) : "Faire signer le client") + '" aria-label="Faire signer le client">' + ico("i-pen") + "</button>") + "</div></td></tr>"; }).join("") +''')
rep('''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + "</button></div></td></tr>").join("") + "</tbody></table>"''',
    '''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + '</button><button class="icon-btn' + (v.signature ? " signed" : "") + '" type="button" data-dsig="' + esc(v.id) + '" title="' + (v.signature ? "Signée par " + esc(v.signature.nom) : "Faire signer le client") + '" aria-label="Faire signer le client">' + ico("i-pen") + "</button></div></td></tr>").join("") + "</tbody></table>"''')
rep('''  else if (ds.fmail) shareDoc("facture", ds.fmail);''', '''  else if (ds.fsig){ const f = S.d.factures.find(x => x.id === ds.fsig); if (f && f.signature) openDoc("facture", f); else signDoc("facture", ds.fsig); }
  else if (ds.dsig){ const v = S.d.devis.find(x => x.id === ds.dsig); if (v && v.signature) openDoc("devis", v); else signDoc("devis", ds.dsig); }
  else if (ds.fmail) shareDoc("facture", ds.fmail);''')

# Réglages : signature de l'entreprise
rep('''          <div class="field full"><span>Logo (facultatif)</span>''', '''          <div class="field full"><span>Signature de l'entreprise (sur les soumissions, facultatif)</span><div class="inline-form"><span class="muted small" id="r-sigcie-st">Aucune</span><button class="btn sm" type="button" id="r-sigcie"><svg class="ic"><use href="#i-pen"/></svg>Dessiner ma signature</button><button class="btn link" type="button" id="r-sigcie-rm" hidden>Retirer</button></div></div>
          <div class="field full"><span>Logo (facultatif)</span>''')
rep('''  $("r-logo-st").textContent = r.logo ? "Logo : " + r.logo.split("/").pop() : "Aucun logo"; $("r-logo-rm").hidden = !r.logo;''',
    '''  $("r-logo-st").textContent = r.logo ? "Logo : " + r.logo.split("/").pop() : "Aucun logo"; $("r-logo-rm").hidden = !r.logo;
  $("r-sigcie-st").textContent = r.signatureCie ? "Enregistrée : elle s'imprime sur chaque soumission" : "Aucune : la case de l'entreprise reste à signer à la main"; $("r-sigcie-rm").hidden = !r.signatureCie; $("r-sigcie").lastChild.textContent = r.signatureCie ? "Refaire ma signature" : "Dessiner ma signature";''')
rep('''$("r-logo-rm").addEventListener("click", () => mutate(d => { d.reglages.logo = ""; }, "Logo retiré"));''', '''$("r-logo-rm").addEventListener("click", () => mutate(d => { d.reglages.logo = ""; }, "Logo retiré"));
$("r-sigcie").addEventListener("click", async () => {
  const res = await sigPad({titre: "Signature de l'entreprise", texte: "Elle s'imprimera dans la case « " + (R().nom || "Entreprise") + " » de tes soumissions.", nom: false, ok: "Enregistrer"}); if (!res) return;
  const path = "signatures/entreprise-" + Math.random().toString(36).slice(2, 6) + ".jpg";
  try { await writeFile(path, res.blob); await mutate(d => { d.reglages.signatureCie = path; }, "Signature de l'entreprise enregistrée"); } catch(e){ toast("Signature non enregistrée : " + (e.message || e)); }
});
$("r-sigcie-rm").addEventListener("click", () => mutate(d => { d.reglages.signatureCie = ""; }, "Signature de l'entreprise retirée"));''')
rep('''slogan:"", neq:"", modePaiement:"",''', '''slogan:"", neq:"", modePaiement:"", signatureCie:"",''')

# Styles du pavé de signature
rep('''</style>''', '''/* Signature à l'écran */
.sig-ov{position:fixed;inset:0;z-index:300;background:rgba(15,20,18,.55);display:flex;align-items:center;justify-content:center;padding:12px}
.sig-box{background:#fff;color:#1e2622;border-radius:14px;width:min(720px,100%);max-height:100%;display:flex;flex-direction:column;gap:10px;padding:16px;box-shadow:0 10px 40px rgba(0,0,0,.3)}
.sig-h{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:1.05rem}
.sig-x{border:0;background:none;font-size:1.7rem;line-height:1;cursor:pointer;color:#67716b;padding:0 4px}
.sig-t{margin:0;font-size:.92rem;color:#3b453f;line-height:1.45}
.sig-zone{position:relative;height:min(260px,42vh);border:1.5px dashed #9aa79f;border-radius:10px;background:#fbfcfb;touch-action:none;overflow:hidden}
.sig-zone canvas{position:absolute;inset:0;touch-action:none;cursor:crosshair}
.sig-ph{position:absolute;left:16px;top:12px;color:#9aa79f;font-size:.9rem;pointer-events:none}
.sig-l{position:absolute;left:16px;right:16px;bottom:40px;border-bottom:1.5px solid #c9d2cc;pointer-events:none}
.sig-n{display:flex;flex-direction:column;gap:4px;font-size:.8rem;font-weight:600;color:#67716b}
.sig-n input{font:inherit;font-size:1rem;font-weight:400;color:#1e2622;background:#fff;padding:9px 10px;border:1px solid #c9d2cc;border-radius:8px}
.sig-f{display:flex;gap:8px;align-items:center}
.sig-b{font:inherit;font-weight:600;padding:10px 16px;border-radius:10px;border:1px solid #c9d2cc;background:#fff;cursor:pointer;color:#1e2622}
.sig-ok{background:#2f6b3b;border-color:#2f6b3b;color:#fff}
.sig-ok:disabled{opacity:.45;cursor:not-allowed}
@media (max-width:600px){.sig-ov{padding:0;align-items:flex-end}.sig-box{border-radius:16px 16px 0 0;padding:14px 14px calc(14px + env(safe-area-inset-bottom))}.sig-zone{height:min(300px,46vh)}}
body.sig-open{overflow:hidden}
.sig-st{display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px}
.sig-st .ic{width:16px;height:16px;color:var(--accent)}
.icon-btn.signed{color:var(--pos)}
</style>''')
open(P, "w", encoding="utf-8").write(s); print("ok")
