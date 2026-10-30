"""v3.13 au téléphone : signer une soumission pour l'entreprise (ton nom en lettres attachées), au choix, soumission par soumission."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

# Signature de l'entreprise gardée dans le téléphone tant que l'ordinateur ne l'a pas reçue
rep('''const avecSig = x => x.signature ? x : ((S.sigs || {})[x.id] ? Object.assign({}, x, {signature: S.sigs[x.id].meta}) : x);''',
    '''const avecSig0 = x => x.signature ? x : ((S.sigs || {})[x.id] ? Object.assign({}, x, {signature: S.sigs[x.id].meta}) : x);
const telCieOK = () => { const t = (S.d && S.d.telephone) || {}; return Array.isArray(t.ops) && t.ops.includes("signature-cie"); };
const memeCie = (a, b) => !!a && !!b && a.nom === b.nom && a.date === b.date && a.heure === b.heure;
function avecSig(x){
  const y = avecSig0(x), c = (S.sigsCie || {})[x.id]; if (!c) return y;
  const brut = ((S.base && S.base.devis) || []).find(d => d.id === x.id) || {};   // telle que l'ordinateur l'a enregistrée (sans les changements en attente)
  if ((c.meta === null && !brut.signatureCie) || memeCie(c.meta, brut.signatureCie)){ delete S.sigsCie[x.id]; IDB.del("__sigcie:" + x.id); return y; }   // l'ordinateur l'a reçue
  const z = Object.assign({}, y); if (c.meta) z.signatureCie = c.meta; else delete z.signatureCie; return z;
}
async function fSignerCie(v){
  const r = R(), res = await sigNomPad({titre: "Signer pour l'entreprise · " + docTitre("devis") + " " + v.numero, texte: "Ton nom s'écrit en lettres attachées dans la case « " + (r.nom || "Entreprise") + " » de " + docGenre("devis").la + ". Seulement sur celle-ci.",
    nom: r.signataire || LS.get("signataire", ""), style: r.signatureStyle || LS.get("signatureStyle", "elegante")}); if (!res) return;
  const meta = {nom: res.nom, date: res.date, heure: res.heure, style: res.style};
  S.sigsCie = S.sigsCie || {}; S.sigsCie[v.id] = {meta, img: res.img}; LS.set("signataire", res.nom); LS.set("signatureStyle", res.style);
  try { await IDB.put("__sigcie:" + v.id, {meta, img: res.img}); } catch(e){}
  await sendOp("signature-cie", {kind: "devis", id: v.id, nom: res.nom, date: res.date, heure: res.heure, style: res.style}, [{blob: res.blob, type: "image/jpeg", ext: ".jpg"}]);
  toast(docTitre("devis") + " " + v.numero + " signée pour l'entreprise"); openDevis(v.id);
}
async function fRetirerCie(v){
  S.sigsCie = S.sigsCie || {}; S.sigsCie[v.id] = {meta: null}; IDB.del("__sigcie:" + v.id);
  await sendOp("signature-cie-suppr", {kind: "devis", id: v.id}); toast("Ta signature est retirée de cette soumission"); openDevis(v.id);
}
const cieBloc = v => !telCieOK() ? "" : v.signatureCie ? '<p class="sig-done">' + ico("i-pen") + "Signée pour l'entreprise par " + esc(v.signatureCie.nom) + ' <button class="btn link" type="button" data-x="sigcie-suppr">Retirer</button></p>'
  : '<button class="btn wide sig-go" type="button" data-x="sigcie">' + ico("i-pen") + "Ajouter ma signature (entreprise)</button>";''')
# PDF : signature de l'entreprise de cette soumission d'abord
rep('''  if (kind !== "facture" && R().signatureCie) out.cie = await driveJpeg(R().signatureCie);''',
    '''  if (kind !== "facture"){
    let c = (S.sigsCie || {})[x.id]; if (c && c.meta && !c.img){ try { c = await IDB.get("__sigcie:" + x.id) || c; } catch(e){} }
    if (c && c.meta && c.img) out.cie = c.img;
    else if (x.signatureCie && x.signatureCie.fichier) out.cie = await driveJpeg(x.signatureCie.fichier);
    else if (!x.signatureCie && R().signatureCie) out.cie = await driveJpeg(R().signatureCie);
  }''')
# Fiche de la soumission
rep('''docBody("devis", v) + sigLigne(v) + (s.k !== "facture" ? sigBouton("devis", v) : "")''', '''docBody("devis", v) + sigLigne(v) + (s.k !== "facture" ? cieBloc(v) + sigBouton("devis", v) : "")''')
rep('''else if (x === "signer") fSigner("devis", v); else if (x === "mod") fDoc("devis", v0);''', '''else if (x === "signer") fSigner("devis", v); else if (x === "sigcie") fSignerCie(v); else if (x === "sigcie-suppr") fRetirerCie(v); else if (x === "mod") fDoc("devis", v0);''')
open(P, "w", encoding="utf-8").write(s); print("ok")
