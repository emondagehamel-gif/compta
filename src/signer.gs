/* Comptabilité : signature en ligne des soumissions. Version 1.
   Ce petit service tourne dans TON compte Google. Quand un client signe une soumission sur la page
   « Signer en ligne », il dépose la signature dans ton dossier Comptabilite/telephone (Google Drive)
   et t'envoie un courriel. L'application Comptabilité ajoute ensuite la signature à la soumission.
   Il ne fait rien d'autre : il lit registre.json pour vérifier le lien, et n'envoie qu'un avis à toi. */
const VERSION = 1, TZ = "America/Toronto";
const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];

function doGet(e){ return reponse(traiter((e && e.parameter) || {}, false)); }
function doPost(e){
  let b = null; try { b = JSON.parse(e.postData.contents); } catch(er){}
  return reponse(b && typeof b === "object" ? traiter(b, true) : {ok:false, err:"donnees"});
}
function reponse(o){ return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

/* Le dossier Comptabilite (celui qui contient registre.json et le dossier telephone) */
function dossier(){
  const P = PropertiesService.getScriptProperties(), id = P.getProperty("dossier");
  if (id){ try { const f = DriveApp.getFolderById(id); if (!f.isTrashed() && f.getFilesByName("registre.json").hasNext()) return f; } catch(e){} }
  let best = null, t = -1; const it = DriveApp.getFoldersByName("Comptabilite");
  while (it.hasNext()){
    const f = it.next(); if (f.isTrashed()) continue;
    const r = f.getFilesByName("registre.json"); if (!r.hasNext() || !f.getFoldersByName("telephone").hasNext()) continue;
    const m = r.next().getLastUpdated().getTime(); if (m > t){ t = m; best = f; }
  }
  if (best) P.setProperty("dossier", best.getId());
  return best;
}
function lire(d){ try { return JSON.parse(d.getFilesByName("registre.json").next().getBlob().getDataAsString("UTF-8")) || {}; } catch(e){ return {}; } }
const hex = bytes => bytes.map(b => ("0" + ((b + 256) % 256).toString(16)).slice(-2)).join("");
const jour = d => Utilities.formatDate(d, TZ, "yyyy-MM-dd");
const dLong = s => { const m = String(s).match(/^(\d{4})-(\d\d)-(\d\d)$/); return m ? Number(m[3]) + (m[3] === "01" ? "er" : "") + " " + MOIS[Number(m[2]) - 1] + " " + m[1] : s; };
const argent = c => (Number(c) / 100).toFixed(2).replace(".", ",").replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " $";

function traiter(b, signer){
  const d = dossier(); if (!d) return {ok:false, err:"dossier"};
  const reg = lire(d), R = reg.reglages || {}, cle = String(R.signerCle || "");
  if (b.a === "ping") return {ok:true, v:VERSION, nom:R.nom || "", cle:!!cle};
  if (!cle) return {ok:false, err:"config"};
  const o = {i:String(b.i || ""), n:String(b.n || ""), c:String(b.c || ""), t:String(b.t || ""), e:String(b.e || ""), en:String(b.en || "")};
  const msg = ["v1", o.i, o.n, encodeURIComponent(o.c), o.t, o.e, encodeURIComponent(o.en)].join("|");
  if (!o.i || String(b.k || "") !== hex(Utilities.computeHmacSha256Signature(msg, cle)).slice(0, 32)) return {ok:false, err:"lien"};
  const P = PropertiesService.getScriptProperties(), tel = R.telephone || "";
  const etat = () => {
    const v = (reg.devis || []).filter(x => x && x.id === o.i)[0];
    if (v && v.signature) return {ok:false, err:"deja", nom:v.signature.nom || "", date:v.signature.date || "", heure:v.signature.heure || ""};
    const s = P.getProperty("signe-" + o.i);
    if (s){ const x = JSON.parse(s), faits = ((reg.telephone || {}).appliques) || [];
      /* signature déjà reçue, sauf si l'application l'a appliquée puis retirée (on peut alors signer de nouveau) */
      if (!(v && faits.indexOf(x.op) >= 0)) return {ok:false, err:"deja", nom:x.nom, date:x.date, heure:x.heure};
      P.deleteProperty("signe-" + o.i); }
    if (v && (v.statut === "refuse" || v.statut === "facture")) return {ok:false, err:"ferme", statut:v.statut, tel};
    /* la soumission a été modifiée depuis l'envoi du lien : le montant signé doit être le bon */
    if (v && typeof v.total === "number" && Math.round(v.total * 100) !== Number(o.t)) return {ok:false, err:"modifiee", tel};
    if (o.e && o.e < jour(new Date())) return {ok:false, err:"expire", e:o.e, tel};
    return null;
  };
  let x = etat(); if (x) return x;
  if (!signer) return {ok:true, etat:"ouvert", tel};
  const nom = String(b.nom || "").replace(/\s+/g, " ").trim().slice(0, 80), m = String(b.sig || "").match(/^data:image\/jpeg;base64,([A-Za-z0-9+\/=]+)$/);
  if (!nom || !m || m[1].length > 3000000) return {ok:false, err:"signature"};
  const lock = LockService.getScriptLock(); if (!lock.tryLock(25000)) return {ok:false, err:"occupe"};
  try {
    x = etat(); if (x) return x;
    const now = new Date(), date = jour(now), heure = Utilities.formatDate(now, TZ, "HH:mm"), img = Utilities.base64Decode(m[1]);
    const opid = "op-" + now.getTime().toString(36) + "-" + Math.random().toString(36).slice(2, 7), photo = "photo-" + opid.slice(3) + "-1.jpg";
    const dt = d.getFoldersByName("telephone").next();
    dt.createFile(Utilities.newBlob(img, "image/jpeg", photo));
    const op = {format:"tel-op-1", id:opid, type:"signature", creeLe:now.toISOString(), photos:[photo],
      data:{kind:"devis", id:o.i, numero:o.n, nom, date, heure, signeLe:now.toISOString(), appareil:"en ligne", total:Number(o.t) / 100}};
    dt.createFile(Utilities.newBlob(JSON.stringify(op), "application/json", opid + ".json"));
    P.setProperty("signe-" + o.i, JSON.stringify({nom, date, heure, op:opid}));
    try { avis(R, o, nom, date, heure, img); } catch(er){ console.warn("avis : " + er); }
    return {ok:true, etat:"signe", nom, date, heure};
  } finally { lock.releaseLock(); }
}

/* Courriel à l'entreprise : qui a signé, quand, et l'image de la signature */
function avis(R, o, nom, date, heure, img){
  const to = String(R.courriel || "").trim() || Session.getEffectiveUser().getEmail(); if (!to) return;
  const titre = R.titreDevis || "Soumission";
  MailApp.sendEmail({to, name:"Comptabilité", subject:titre + " " + o.n + " signée par " + nom,
    body:nom + " a signé en ligne " + (titre === "Devis" ? "le devis " : "la soumission ") + o.n + (o.c && o.c.toLowerCase() !== nom.toLowerCase() ? " (client : " + o.c + ")" : "") +
      ", au montant de " + argent(o.t) + ", le " + dLong(date) + " à " + heure.replace(":", " h ") + ".\n\n" +
      "Elle passera à « acceptée » dans ton application Comptabilité, avec la signature sur le PDF, la prochaine fois que tu l'ouvriras.\n\nL'image de la signature est jointe.",
    attachments:[Utilities.newBlob(img, "image/jpeg", "signature " + o.n + ".jpg")]});
}

/* Pour vérifier l'installation dans l'éditeur : choisis « test » puis clique Exécuter. Google te demande les autorisations. */
function test(){ const d = dossier(); console.log(d ? "Dossier trouvé : " + d.getName() + " (" + d.getId() + ")" : "Dossier Comptabilite introuvable"); MailApp.getRemainingDailyQuota(); }
