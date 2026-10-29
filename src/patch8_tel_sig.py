"""v3.8 au téléphone (app terrain) : le client signe la soumission ou la facture à l'écran."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

rep('''function openFacture(id){''', '''/* Signature du client : gardée dans le téléphone, envoyée à l'ordinateur (op « signature »), puis imprimée sur le PDF */
const telSigOK = () => { const t = (S.d && S.d.telephone) || {}; return Array.isArray(t.ops) && t.ops.includes("signature"); };
const avecSig = x => x.signature ? x : ((S.sigs || {})[x.id] ? Object.assign({}, x, {signature: S.sigs[x.id].meta}) : x);
async function driveJpeg(path){
  const key = "__f:" + path; try { const c = await IDB.get(key); if (c && c.data) return c; } catch(e){}
  if (!S.ids || !S.ids.root || !online() || !tokOk()) return null;
  try { const parts = String(path).split("/"); let parent = S.ids.root; for (const p of parts.slice(0, -1)){ parent = await subFolder(parent, p); if (!parent) return null; }
    const L = await list("name = '" + qs(parts[parts.length - 1]) + "' and " + inP(parent), 2); if (!L[0]) return null;
    const o = await jpegObj(await downloadBlob(L[0].id)); IDB.put(key, o).catch(() => {}); return o; } catch(e){ return null; }
}
async function phoneSigs(kind, x){
  const out = {client: null, cie: null}; let loc = (S.sigs || {})[x.id];
  if (!loc){ try { loc = await IDB.get("__sig:" + x.id); } catch(e){} }
  if (x.signature) out.client = loc && loc.img ? loc.img : (x.signature.fichier ? await driveJpeg(x.signature.fichier) : null);
  if (kind !== "facture" && R().signatureCie) out.cie = await driveJpeg(R().signatureCie);
  return out;
}
async function fSigner(kind, x){
  const res = await sigPad({titre: "Signature du client · " + docTitre(kind) + " " + x.numero, texte: sigTexte(kind, x), nom: x.client || ""}); if (!res) return;
  const meta = {nom: res.nom, date: res.date, heure: res.heure, signeLe: res.signeLe, appareil: "téléphone"};
  S.sigs = S.sigs || {}; S.sigs[x.id] = {meta, img: res.img};
  try { await IDB.put("__sig:" + x.id, {meta, img: res.img}); } catch(e){}
  await sendOp("signature", {kind, id: x.id, nom: res.nom, date: res.date, heure: res.heure, signeLe: res.signeLe}, [{blob: res.blob, type: "image/jpeg", ext: ".jpg"}]);
  toast(docTitre(kind) + " " + x.numero + " signée par " + res.nom);
  sendDoc(kind, Object.assign({}, x, {signature: meta}));
}
const sigLigne = x => x.signature ? '<p class="sig-done">' + ico("i-pen") + "Signée par " + esc(x.signature.nom) + " le " + esc(dLong(x.signature.date)) + (x.signature.heure ? " à " + esc(hmTxt(x.signature.heure)) : "") + "</p>" : "";
const sigBouton = (kind, x) => !x.signature && telSigOK() && x.statut !== "annulee" ? '<button class="btn wide sig-go" type="button" data-x="signer">' + ico("i-pen") + "Faire signer le client</button>" : "";
function openFacture(id){''')
rep('''  const f = S.d.factures.find(x => x.id === id); if (!f) return; const t = S.tmap[f.transaction];
  openSheet("Facture " + f.numero, docBody("facture", f) + '<p class="muted small">''', '''  const f0 = S.d.factures.find(x => x.id === id); if (!f0) return; const f = avecSig(f0), t = S.tmap[f.transaction];
  openSheet("Facture " + f.numero, docBody("facture", f) + sigLigne(f) + sigBouton("facture", f) + '<p class="muted small">''')
rep('''const x = b.dataset.x; if (x === "pdf") sendDoc("facture", f); else if (x === "mod") fDoc("facture", f); else if (x === "pay") fEncaisser(f); }});''',
    '''const x = b.dataset.x; if (x === "pdf") sendDoc("facture", f); else if (x === "signer") fSigner("facture", f); else if (x === "mod") fDoc("facture", f0); else if (x === "pay") fEncaisser(f0); }});''')
rep('''  const v = S.d.devis.find(x => x.id === id); if (!v) return; const s = devStatus(v);
  openSheet(docTitre("devis") + " " + v.numero, docBody("devis", v) + (s.k !== "facture" ?''', '''  const v0 = S.d.devis.find(x => x.id === id); if (!v0) return; const v = avecSig(v0), s = devStatus(v0);
  openSheet(docTitre("devis") + " " + v.numero, docBody("devis", v) + sigLigne(v) + (s.k !== "facture" ? sigBouton("devis", v) : "") + (s.k !== "facture" && !v.signature ?''')
rep('''const x = b.dataset.x; if (x === "pdf") sendDoc("devis", v); else if (x === "mod") fDoc("devis", v);''', '''const x = b.dataset.x; if (x === "pdf") sendDoc("devis", v); else if (x === "signer") fSigner("devis", v); else if (x === "mod") fDoc("devis", v0);''')
# Envoi : avec les signatures
rep('''        const logo = await phoneLogo();''', '''        const logo = await phoneLogo(), sigs = await phoneSigs(kind, x);''')
rep('''        if (how === "save"){ const f = new File([docPDF(kind, x, logo)], name + ".pdf",''', '''        if (how === "save"){ const f = new File([docPDF(kind, x, logo, sigs)], name + ".pdf",''')
rep('''        const files = how === "img" ? await docImages(kind, x, logo) : [new File([docPDF(kind, x, logo)], name + ".pdf", {type:"application/pdf"})];''',
    '''        const files = how === "img" ? await docImages(kind, x, logo, sigs) : [new File([docPDF(kind, x, logo, sigs)], name + ".pdf", {type:"application/pdf"})];''')
rep('''  openSheet("Envoyer " + G.la + " " + x.numero,''', '''  x = avecSig(x);
  openSheet("Envoyer " + G.la + " " + x.numero + (x.signature ? (G.t === "Devis" ? " signé" : " signée") : ""),''')
open(P, "w", encoding="utf-8").write(s); print("ok")
