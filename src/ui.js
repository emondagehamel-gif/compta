/* ===== Version téléphone : état ===== */
const S = {d:null, base:null, pending:[], ids:null, tab:"accueil", E:[], cmap:{}, pmap:{}, fmap:{}, tmap:{}, cleared:{}, year:0,
  conn:"init", connMsg:"", lastSync:"", telFiles:[], calM:"", calSel:"", vt:"factures", vtF:"due", busy:false, form:null, blobs:{}, logo:undefined};
const LS = {
  get(k, d){ try { const v = localStorage.getItem("cm-" + k); return v == null ? d : JSON.parse(v); } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem("cm-" + k, JSON.stringify(v)); } catch(e){} }
};
const FOLDER = "application/vnd.google-apps.folder";
/* Identifiant client Google (remplacé à la construction ; sinon saisi une fois dans l'application) */
const CLIENT_ID_DEF = "__CLIENT_ID__";
const API = window.__GAPI || "https://www.googleapis.com", AUTH_URL = window.__GAUTH || "https://accounts.google.com/o/oauth2/v2/auth";
const SCOPE = "https://www.googleapis.com/auth/drive";
const qs = s => String(s).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
const dLoc = s => iso(new Date(s));
const heure = iso_ => { const d = iso_ ? new Date(iso_) : new Date(); return d.getHours() + " h " + pad(d.getMinutes()); };
const online = () => navigator.onLine !== false;
const clientId = () => LS.get("clientId", "") || (CLIENT_ID_DEF.indexOf("__") === 0 ? "" : CLIENT_ID_DEF);
const redirectUri = () => location.origin + location.pathname.replace(/index\.html$/, "");
let TOK = LS.get("tok", null);
const tokOk = m => !!(TOK && TOK.t && TOK.exp - Date.now() > (m || 60000));

/* ===== Connexion à Google (redirection, sans fenêtre surgissante) ===== */
function authRedirect(interactive){
  const st = Math.random().toString(36).slice(2) + Date.now().toString(36);
  LS.set("authState", {st, tab:S.tab, at:Date.now()}); LS.set("authTry", Date.now());
  const p = new URLSearchParams({client_id:clientId(), redirect_uri:redirectUri(), response_type:"token", scope:SCOPE, include_granted_scopes:"true", state:st, prompt: interactive ? "select_account" : "none"});
  const hint = LS.get("email", ""); if (hint) p.set("login_hint", hint);
  setSync("busy", "Connexion à Google…");
  location.assign(AUTH_URL + "?" + p.toString());
}
function readAuthHash(){
  const h = location.hash.slice(1); if (!/(^|&)(access_token|error|state)=/.test(h)) return null;
  const p = new URLSearchParams(h), saved = LS.get("authState", null) || {};
  LS.set("authState", null);
  try { history.replaceState(null, "", location.pathname + location.search + (saved.tab && saved.tab !== "accueil" ? "#" + saved.tab : "")); } catch(e){}
  if (!saved.st || p.get("state") !== saved.st){ LS.set("authFail", Date.now()); return {err:"state"}; }
  if (p.get("access_token")){
    TOK = {t:p.get("access_token"), exp:Date.now() + (Number(p.get("expires_in")) || 3600) * 1000};
    LS.set("tok", TOK); LS.set("authFail", 0); return {ok:true};
  }
  LS.set("authFail", Date.now()); return {err:p.get("error") || "erreur"};
}
function logout(){ TOK = null; LS.set("tok", null); LS.set("email", ""); LS.set("ids", null); S.ids = null; }

/* ===== Google Drive (API directe) ===== */
async function api(path, o){
  o = o || {};
  if (!online()) throw {code:"hors-reseau"};
  if (!tokOk(5000)) throw {code:"login"};
  let r;
  try { r = await fetch((o.upload ? API + "/upload" : API) + path, {method:o.method || "GET", headers:Object.assign({Authorization:"Bearer " + TOK.t}, o.headers || {}), body:o.body, cache:"no-store"}); }
  catch(e){ throw {code:"reseau", message:"Google Drive ne répond pas."}; }
  if (r.status === 401){ TOK = null; LS.set("tok", null); throw {code:"login"}; }
  if (!r.ok){
    let m = ""; try { const j = await r.json(); m = (j.error && j.error.message) || ""; } catch(e){}
    throw {code: r.status === 403 && /insufficient|scope/i.test(m) ? "login" : (r.status >= 500 || r.status === 429 || r.status === 403) ? "reseau" : "drive", message: m || "Erreur " + r.status};
  }
  return o.raw ? r : r.json();
}
async function list(q, n){
  const p = new URLSearchParams({q: q + " and trashed = false", pageSize:String(n || 50), fields:"files(id,name,mimeType,modifiedTime,parents)", orderBy:"modifiedTime desc", spaces:"drive"});
  const r = await api("/drive/v3/files?" + p.toString());
  return (r.files || []).map(f => ({id:f.id, title:f.name, mimeType:f.mimeType, modifiedTime:f.modifiedTime, parentId:(f.parents || [])[0] || ""}));
}
const inP = id => "'" + qs(id) + "' in parents";
async function findRegistre(root){ const L = (await list("name = 'registre.json' and " + inP(root), 10)).filter(f => f.mimeType !== FOLDER); return L[0] || null; }
async function subFolder(root, name){ const L = await list("name = '" + qs(name) + "' and mimeType = '" + FOLDER + "' and " + inP(root), 5); return L[0] ? L[0].id : ""; }
async function findIds(){
  const c = LS.get("ids", null);
  if (c && c.root && await findRegistre(c.root)) return c;
  const folders = await list("name = 'Comptabilite' and mimeType = '" + FOLDER + "'", 30);
  for (const f of folders){ if (await findRegistre(f.id)) return {root:f.id, nom:f.title}; }
  return null;
}
async function existsIn(parent, name){ return (await list("name = '" + qs(name) + "' and " + inP(parent), 1)).length > 0; }
async function downloadJSON(id){ const r = await api("/drive/v3/files/" + encodeURIComponent(id) + "?alt=media", {raw:true}); return JSON.parse(await r.text()); }
async function downloadBlob(id){ const r = await api("/drive/v3/files/" + encodeURIComponent(id) + "?alt=media", {raw:true}); return r.blob(); }
async function createFile(name, parent, blob, type){
  const b = "cmpt" + Math.random().toString(36).slice(2);
  const meta = JSON.stringify({name, parents:[parent], mimeType:type});
  const body = new Blob(["--" + b + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + meta + "\r\n--" + b + "\r\nContent-Type: " + type + "\r\n\r\n", blob, "\r\n--" + b + "--\r\n"], {type:"multipart/related; boundary=" + b});
  return api("/drive/v3/files?uploadType=multipart&fields=id,name", {upload:true, method:"POST", headers:{"Content-Type":"multipart/related; boundary=" + b}, body});
}
async function uploadJSON(title, obj){ await createFile(title, S.ids.tel, new Blob([JSON.stringify(obj)], {type:"application/json"}), "application/json"); }
async function uploadBlob(title, blob, type){ await createFile(title, S.ids.tel, blob, type); }
async function whoAmI(){ try { const r = await api("/drive/v3/about?fields=user(emailAddress,displayName)"); const e = r.user && r.user.emailAddress; if (e) LS.set("email", e); } catch(e){} }

/* ===== Photos gardées dans le téléphone tant qu'elles ne sont pas envoyées ===== */
const IDB = {
  db: null,
  open(){
    if (this.db) return Promise.resolve(this.db);
    return new Promise((res, rej) => { const r = indexedDB.open("comptabilite", 1); r.onupgradeneeded = () => r.result.createObjectStore("photos"); r.onsuccess = () => { this.db = r.result; res(this.db); }; r.onerror = () => rej(r.error); });
  },
  async run(mode, fn){
    const db = await this.open();
    return new Promise((res, rej) => { const tx = db.transaction("photos", mode), q = fn(tx.objectStore("photos")); tx.oncomplete = () => res(q && q.result); tx.onerror = () => rej(tx.error); tx.onabort = () => rej(tx.error); });
  },
  get(k){ return this.run("readonly", s => s.get(k)).catch(() => undefined); },
  put(k, v){ return this.run("readwrite", s => s.put(v, k)); },
  del(k){ return this.run("readwrite", s => s.delete(k)).catch(() => {}); }
};

/* ===== Connexion et synchronisation ===== */
const CONN_MSG = {
  "config": ["Relie l'application à Google", "Colle l'identifiant client Google que tu as créé avec Claude. Il se termine par .apps.googleusercontent.com."],
  "login": ["Connecte-toi à Google", "Choisis le compte Google où se trouve ton dossier Comptabilite. Si Google affiche « Google n'a pas validé cette application », touche Paramètres avancés, puis Accéder : c'est ta propre application."],
  "hors-reseau": ["Pas de réseau", "Ouvre l'application une première fois avec du réseau pour charger tes livres. Ensuite, elle fonctionne même sans réseau."],
  "dossier": ["Dossier Comptabilite introuvable", "Je ne trouve pas le dossier Comptabilite avec registre.json dans ce Google Drive. Vérifie que tu es connecté au bon compte Google (Plus › Synchronisation › Changer de compte)."],
  "telephone": ["Ouvre l'application sur l'ordinateur", "Le dossier « telephone » n'existe pas encore dans tes livres. Ouvre l'application Comptabilité sur l'ordinateur une fois : elle le crée, puis Google Drive le synchronise."],
  "reseau": ["Google Drive ne répond pas", "Le réseau est faible ou Google Drive est lent. Tes ajouts restent gardés dans le téléphone et partiront tout seuls."],
  "drive": ["Erreur de Google Drive", "Google Drive a refusé la demande. Réessaie dans un moment."]
};
function errState(e){ const c = e && e.code; return CONN_MSG[c] ? c : "reseau"; }
let syncing = false, syncTimer = null;
function syncSoon(ms){ clearTimeout(syncTimer); syncTimer = setTimeout(() => syncAll(false), ms == null ? 60 : ms); }
/* Peut-on quitter la page un instant pour renouveler la connexion Google ? Jamais pendant une saisie. */
function canRedirect(manual){
  if (!$("sheet").hidden) return false;
  if (Date.now() - (LS.get("authTry", 0) || 0) < 20000) return false;
  return manual || Date.now() - (LS.get("authFail", 0) || 0) > 15 * 60000;
}
async function syncAll(manual, why){
  if (syncing) return;
  if (!clientId()){ S.conn = "config"; S.connErr = S.d ? "config" : ""; render(); syncLabel(); return; }
  if (!online()){ if (!S.d) S.conn = "hors-reseau"; S.connErr = ""; render(); syncLabel(); return; }
  if (!tokOk(120000)){
    const queued = S.pending.some(p => p.etat === "attente");
    if (canRedirect(manual) && (manual || queued || why === "start" || why === "retour")){ authRedirect(manual && Date.now() - (LS.get("authFail", 0) || 0) < 15 * 60000); return; }
    if (!S.d) S.conn = "login"; S.connErr = "login"; render(); syncLabel(); return;
  }
  syncing = true; setSync("busy", "Synchronisation…");
  try {
    if (!S.ids){
      const ids = await findIds(); if (!ids) throw {code:"dossier"};
      ids.tel = await subFolder(ids.root, "telephone"); ids.docs = await subFolder(ids.root, "documents");
      S.ids = ids; LS.set("ids", ids);
      if (!LS.get("email", "")) whoAmI();
    }
    await fixTrajets();
    for (const p of S.pending.slice()){
      if (p.etat === "attente" || (manual && p.etat === "erreur")) await pushOp(p);
    }
    await refreshCore();
    S.conn = "ok"; S.connErr = "";
  } catch(e){
    if (!(e && e.code)) console.error(e);
    if (e && e.code === "login" && canRedirect(manual) && (manual || why === "start" || why === "retour" || S.pending.some(p => p.etat === "attente"))){ syncing = false; authRedirect(false); return; }
    const st = errState(e);
    if (st === "dossier" && S.ids){ S.ids = null; LS.set("ids", null); }
    if (!S.d) S.conn = st; S.connErr = st; S.connMsg = (e && e.message) || "";
  } finally { syncing = false; savePending(); render(); syncLabel(); }
}
async function refreshCore(){
  const reg = await findRegistre(S.ids.root); if (!reg) throw {code:"dossier"};
  if (!S.ids.tel){ S.ids.tel = await subFolder(S.ids.root, "telephone"); LS.set("ids", S.ids); }
  const base = normalize(await downloadJSON(reg.id)), applied = new Set((base.telephone && base.telephone.appliques) || []);
  S.base = base; S.lastSync = new Date().toISOString(); LS.set("base", base); LS.set("lastSync", S.lastSync);
  S.pending.filter(p => applied.has(p.op.id)).forEach(p => IDB.del(p.op.id));
  S.pending = S.pending.filter(p => !applied.has(p.op.id));
  if (S.ids.tel){
    const files = await list(inP(S.ids.tel), 200), known = new Set(S.pending.map(p => p.op.id + ".json"));
    S.telFiles = files.map(f => f.title);
    for (const f of files){
      if (!/^op-[\w.-]+\.json$/.test(f.title) || known.has(f.title) || applied.has(f.title.replace(/\.json$/, ""))) continue;
      try { const op = await downloadJSON(f.id); if (op && op.id && !applied.has(op.id) && !S.pending.some(p => p.op.id === op.id)) S.pending.push({op, etat:"envoye", label:opLabel(op)}); } catch(e){}
    }
  }
  savePending(); recompute();
}
function syncLabel(){
  if (syncing) return;
  const q = S.pending.filter(p => p.etat === "attente" || p.etat === "envoi").length, w = S.pending.filter(p => p.etat === "envoye").length, err = S.pending.filter(p => p.etat === "erreur").length;
  const s = n => n > 1 ? "s" : "";
  if (!online()) setSync("off", "Hors réseau" + (q ? " · " + q + " ajout" + s(q) + " gardé" + s(q) : ""));
  else if (err) setSync("err", err + " envoi" + s(err) + " à reprendre");
  else if (S.connErr === "login") setSync("err", "Connexion requise" + (q ? " · " + q + " à envoyer" : ""));
  else if (S.connErr === "config") setSync("err", "À configurer");
  else if (S.connErr) setSync("err", (q ? q + " à envoyer · " : "") + "nouvel essai bientôt");
  else if (q) setSync("wait", q + " ajout" + s(q) + " à envoyer");
  else if (w) setSync("wait", w + " ajout" + s(w) + " en attente de l'ordinateur");
  else if (S.lastSync) setSync("", "À jour · " + heure(S.lastSync));
  else setSync("busy", "Connexion…");
}
function setSync(cls, txt){ const b = $("h-sync"); b.className = "sync" + (cls ? " " + cls : ""); $("h-sync-t").textContent = txt; }
function savePending(){ LS.set("pending", S.pending.map(p => ({op:p.op, etat:p.etat, label:p.label, err:p.err || "", tries:p.tries || 0}))); }
function recompute(){
  if (!S.base){ S.d = null; return; }
  const d = normalize(clone(S.base));
  S.pending.forEach(p => { try { applyOp(d, p.op); } catch(e){ console.error(e); } });
  S.d = d; S.year = fyOf(today()); rebuild();
}
function opLabel(op){
  const x = op.data || {};
  return ({evenement:"Agenda : " + (x.titre || ""), "evenement-suppr":"Événement retiré", "evenement-fait":"Événement " + (x.fait ? "fait" : "à faire"), obligation:"Échéance " + (x.fait ? "faite" : "à faire"),
    operation:(x.type === "revenu" ? "Revenu : " : "Dépense : ") + (x.tiers || x.description || ""), photo:"Photo à traiter", trajet:"Trajet : " + (x.destination || "") + ", " + (x.km || 0) + " km",
    paiement:"Paiement reçu", facture:"Facture " + (x.numero || "") + ", " + (x.client || ""), devis:"Devis " + (x.numero || "") + ", " + (x.client || ""), "devis-statut":"Devis : " + (x.statut || ""),
    envoye:"Marqué envoyé", entretien:"Entretien : " + ((x.entretien || {}).type || ""), odometre:"Odomètre : " + (x.km || ""), client:"Client : " + (x.nom || ""), lieu:"Lieu : " + (x.nom || ""), "lieu-suppr":"Lieu retiré", patch: x.msg || "Modification (version complète)", fichier:"Fichier : " + String(x.to || "").split("/").pop(), deplacer:"Document classé", "fichier-suppr":"Document supprimé"})[op.type] || op.type;
}
/* Un ajout est d'abord gardé dans le téléphone (photos comprises), puis envoyé dès que possible */
async function sendOp(type, data, files){
  const id = "op-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
  const op = {format:"tel-op-1", id, type, creeLe:new Date().toISOString(), data, photos:[]};
  const entry = {op, etat:"attente", label:opLabel(op), tries:0};
  const fl = (files || []).map(f => ({blob:f.blob, type:f.type, ext:f.ext}));
  if (fl.length){ try { await IDB.put(id, fl); } catch(e){ S.blobs[id] = fl; } }
  S.pending.push(entry); savePending(); recompute(); render();
  if (!online()) toast("Gardé dans le téléphone. Ça partira tout seul au retour du réseau.");
  syncLabel(); syncSoon(150);
  return entry;
}
async function pushOp(entry){
  const op = entry.op, retry = (entry.tries || 0) > 0;
  let files = S.blobs[op.id]; if (!files) files = (await IDB.get(op.id)) || [];
  entry.tries = (entry.tries || 0) + 1; entry.etat = "envoi"; entry.err = ""; savePending();
  try {
    if (!S.ids || !S.ids.tel){ if (S.ids && S.ids.root) S.ids.tel = await subFolder(S.ids.root, "telephone"); if (!S.ids || !S.ids.tel) throw {code:"telephone"}; LS.set("ids", S.ids); }
    for (let k = op.photos.length; k < files.length; k++){
      const f = files[k], name = "photo-" + op.id.slice(3) + "-" + (k + 1) + f.ext;
      if (!(retry && await existsIn(S.ids.tel, name))) await uploadBlob(name, f.blob, f.type);
      op.photos.push(name); savePending();
    }
    if (!(retry && await existsIn(S.ids.tel, op.id + ".json"))) await uploadJSON(op.id + ".json", op);
    entry.etat = "envoye"; delete S.blobs[op.id]; IDB.del(op.id);
  } catch(e){
    const c = e && e.code;
    if (c === "hors-reseau" || c === "reseau" || c === "login"){ entry.etat = "attente"; entry.err = ""; savePending(); throw e; }
    if (!c) console.error(e);
    entry.etat = "erreur"; entry.err = c === "telephone" ? CONN_MSG.telephone[1] : (e && e.message) || "Envoi impossible";
    if (c === "telephone"){ savePending(); throw e; }
  }
  savePending();
}

/* ===== Photos ===== */
async function prepFile(file){
  if (file.type === "application/pdf" || /\.pdf$/i.test(file.name)) return file.size < 900000 ? {blob:file, type:"application/pdf", ext:".pdf", url:""} : null;
  try {
    const url = URL.createObjectURL(file), img = new Image(); img.src = url; await img.decode();
    const sc = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight)), w = Math.max(1, Math.round(img.naturalWidth * sc)), h = Math.max(1, Math.round(img.naturalHeight * sc));
    const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, w, h); x.drawImage(img, 0, 0, w, h);
    let b = await new Promise(r => c.toBlob(r, "image/jpeg", 0.8)); if (b && b.size > 650000) b = await new Promise(r => c.toBlob(r, "image/jpeg", 0.6));
    return b ? {blob:b, type:"image/jpeg", ext:".jpg", url} : null;
  } catch(e){ return null; }
}
function photoField(){ return '<div class="field"><span>Photos ou PDF</span><div class="photos" id="ph-list"></div><div class="cam"><label class="btn"><svg class="ic"><use href="#i-camera"/></svg>Prendre une photo<input type="file" accept="image/*" capture="environment" id="ph-cam" hidden></label><label class="btn"><svg class="ic"><use href="#i-file"/></svg>Choisir<input type="file" accept="image/*,application/pdf" multiple id="ph-pick" hidden></label></div></div>'; }
function bindPhotos(){
  S.form.photos = S.form.photos || [];
  const show = () => { $("ph-list").innerHTML = S.form.photos.map((p, i) => '<div class="photo">' + (p.url ? '<img src="' + p.url + '" alt="">' : ico("i-pdf")) + '<button type="button" data-ph-rm="' + i + '" aria-label="Retirer">' + ico("i-x") + "</button></div>").join(""); };
  const add = async files => { for (const f of files){ const p = await prepFile(f); if (p) S.form.photos.push(p); else toast("Ce fichier n'a pas pu être ajouté (format ou taille)."); } show(); };
  ["ph-cam","ph-pick"].forEach(id => { $(id).onchange = e => { const f = [...e.target.files]; e.target.value = ""; add(f); }; });
  $("ph-list").onclick = e => { const b = e.target.closest("[data-ph-rm]"); if (b){ S.form.photos.splice(Number(b.dataset.phRm), 1); show(); } };
  show();
}

/* ===== Panneau ===== */
function openSheet(title, body, o){
  o = o || {}; closeSheet(true);
  S.form = Object.assign({}, o.state || {});
  $("sh-title").textContent = title; $("sh-body").innerHTML = body + '<p class="err" id="sh-err" hidden></p>';
  $("sh-foot").innerHTML = (o.secondary || "") + (o.primary ? '<button class="btn primary" type="submit" id="sh-ok">' + esc(o.primary) + "</button>" : '<button class="btn" type="button" data-close>Fermer</button>');
  $("sh-foot").hidden = o.noFoot === true;
  $("sheet").hidden = false; document.body.classList.add("locked", "sheet-open"); $("sh-body").scrollTop = 0;
  if (!sheetHist){ try { history.pushState({sheet:1}, "", location.href); sheetHist = true; } catch(e){} }
  const f = $("sheet-f"); f.onsubmit = async e => { e.preventDefault(); if (!o.onSubmit) return closeSheet(); const b = $("sh-ok"); if (b) b.disabled = true;
    try { const r = await o.onSubmit(); if (typeof r === "string"){ $("sh-err").textContent = r; $("sh-err").hidden = false; return; } if (r !== false) closeSheet(); } finally { if (b) b.disabled = false; } };
  f.onclick = e => { if (e.target.closest("[data-close]")){ closeSheet(); return; } if (o.onClick) o.onClick(e); };
  f.oninput = o.onInput || null; f.onchange = o.onChange || null;
  if (o.ready) o.ready();
}
/* Le bouton Retour d'Android ferme le panneau au lieu de quitter l'application */
let sheetHist = false, ignorePop = 0;
function closeSheet(silent, fromPop){
  const was = !$("sheet").hidden;
  $("sheet").hidden = true; document.body.classList.remove("locked", "sheet-open"); $("sheet-f").onclick = null; if (!silent) S.form = null;
  if (silent) return;
  if (fromPop) sheetHist = false;
  else if (sheetHist){ sheetHist = false; ignorePop++; try { history.back(); } catch(e){ ignorePop--; } }
  if (was && S.pending.some(p => p.etat === "attente")) syncSoon(400);
}
window.addEventListener("popstate", () => { if (ignorePop > 0){ ignorePop--; return; } if (sheetHist){ sheetHist = false; if (!$("sheet").hidden) closeSheet(false, true); } });
$("sh-x").addEventListener("click", () => closeSheet());
$("sheet").addEventListener("mousedown", e => { if (e.target === $("sheet")) closeSheet(); });
const fail = m => { $("sh-err").textContent = m; $("sh-err").hidden = false; return false; };
const pressSet = (sel, attr, v) => document.querySelectorAll(sel).forEach(b => b.setAttribute("aria-pressed", String(b.getAttribute(attr) === v)));

/* ===== Rendu ===== */
const TABS = ["accueil","agenda","ventes","plus"];
function showTab(t){ S.tab = t; TABS.forEach(k => { $("v-" + k).hidden = k !== t; }); document.querySelectorAll(".tabbar [data-tab]").forEach(b => { if (b.dataset.tab === t) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current"); }); try { if (location.hash.slice(1) !== t) history.replaceState(null, "", "#" + t); } catch(e){} render(); window.scrollTo(0, 0); }
document.querySelector(".tabbar").addEventListener("click", e => { const b = e.target.closest("[data-tab]"); if (b) showTab(b.dataset.tab); });
$("tab-add").addEventListener("click", openAdd);
$("h-refresh").addEventListener("click", () => syncAll(true));
$("h-sync").addEventListener("click", () => showTab("plus"));
window.addEventListener("hashchange", () => { const t = location.hash.slice(1); if (TABS.includes(t) && t !== S.tab) showTab(t); });
function render(){
  $("h-nom").textContent = S.d ? (R().nom || "Mon entreprise") : "Comptabilité";
  ({accueil:vAccueil, agenda:vAgenda, ventes:vVentes, plus:vPlus})[S.tab]();
  if (S.d){
    const t0 = today(), ag = agendaEvents(t0, t0).filter(e => !e.done && e.kind !== "info").length, fl = S.d.factures.filter(f => facStatus(f).k === "retard").length, pe = S.pending.filter(p => p.etat === "erreur").length + (S.connErr === "login" ? 1 : 0);
    [["b-agenda", ag], ["b-ventes", fl], ["b-plus", pe]].forEach(([id, n]) => { $(id).textContent = n; $(id).hidden = !n; });
  }
}
function connCard(){
  const m = CONN_MSG[S.conn] || ["Connexion à tes livres", "Un instant…"];
  if (S.conn === "config") return '<div class="card"><h2>' + esc(m[0]) + '</h2><p class="muted">' + esc(m[1]) + '</p><label class="field"><span>Identifiant client Google</span><input id="cfg-id" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="123…apps.googleusercontent.com"></label><button class="btn primary" type="button" data-act="cfg">Enregistrer</button></div>';
  const btn = S.conn === "init" ? "" : S.conn === "login" ? '<button class="btn primary" type="button" data-act="login">Se connecter à Google</button>' : '<button class="btn primary" type="button" data-act="connect">Réessayer</button>';
  return '<div class="card"><h2>' + esc(m[0]) + '</h2><p class="muted">' + esc(m[1]) + "</p>" + btn + "</div>";
}
const kItem = (e, o) => { o = o || {}; const [, m, d] = e.date.split("-").map(Number);
  return '<button class="item" type="button" data-ev="' + esc(evKey(e)) + '">' + (o.noDate ? '<i class="k" style="background:' + evColor(e) + '"></i>' : '<span class="when"><b>' + d + "</b><small>" + MOIS_C[m - 1].replace(".", "") + "</small></span>") +
    '<span class="t"><b>' + esc((e.kind === "note" && e.heure ? fmtRange(e.heure, e.fin) + " · " : "") + e.title) + "</b><small>" + esc(evSub(e)) + "</small></span>" + (e.done ? '<span class="chip ok">Fait</span>' : evLate(e) ? '<span class="chip late">En retard</span>' : "") + "</button>"; };
const evKey = e => e.kind === "note" ? "note:" + e.id : e.key ? "key:" + e.key : "go:" + (e.go || "") + ":" + e.date;
const evLate = e => !e.done && !e.quiet && e.date < today() && ["obl","tax","fac","ap"].includes(e.kind);
function evSub(e){
  if (e.kind === "note") return [e.etype && e.etype !== "note" ? EVT[e.etype].l : "", e.client, e.lieu].filter(Boolean).join(" · ") || (e.detail || "").slice(0, 80);
  return ({obl:"Impôts et obligations", tax:"Taxes de vente", fac:"Factures et devis", ap:"Facture à payer", ent:"Entretien", info:"Exercice"})[e.kind] || "";
}
function todoItems(){
  const t0 = today(), d = S.d, out = [];
  agendaEvents(addDays(t0, -400), addDays(t0, 30)).forEach(e => { if (e.done || e.quiet) return; if ((e.kind === "obl" && (e.todoFrom || addDays(e.date, -30)) <= t0) || (e.kind === "tax" && e.late) || (e.kind === "tax" && e.date >= t0 && e.date <= addDays(t0, 30) && !e.done)) out.push({late: e.date < t0, txt: e.title, sub:"Échéance : " + dLong(e.date), ev: evKey(e)}); });
  d.factures.forEach(f => { if (facStatus(f).k === "retard") out.push({late:true, txt:"Facture " + f.numero + " en retard, " + f.client, sub:fmt(docTotal("facture", f)) + ", due le " + dShort(f.echeance), fac:f.id}); });
  d.transactions.forEach(t => { if (t.type === "depense" && unpaid(t) && (t.echeance || t.date) <= addDays(t0, 7)) out.push({late:(t.echeance || t.date) < t0, txt:"À payer : " + (t.tiers || t.description), sub:fmt(txTotal(t)) + (t.echeance ? ", d'ici le " + dShort(t.echeance) : "")}); });
  invAlerts().forEach(a => out.push({late:a.late, txt:a.txt, sub:"Inventaire", plus:true}));
  return out.sort((a, b) => (b.late ? 1 : 0) - (a.late ? 1 : 0));
}
function vAccueil(){
  const el = $("v-accueil");
  if (!S.d){ put(el, connCard()); return; }
  const t0 = today(), r = R(), h = new Date().getHours();
  const todayEv = agendaEvents(t0, t0).filter(e => e.kind !== "info"), tom = agendaEvents(addDays(t0, 1), addDays(t0, 1)).filter(e => e.kind !== "info" && !e.done);
  const ar = S.d.transactions.filter(t => t.type === "revenu" && unpaid(t)), arT = ar.reduce((s, t) => s + txTotal(t), 0), arLate = ar.filter(t => (t.echeance || t.date) < t0).length;
  const mS = t0.slice(0, 8) + "01", mE = iso(lastDay(Number(t0.slice(0, 4)), Number(t0.slice(5, 7)) - 1)), pm = pnl(mS, mE);
  let tax = null; if (inscrit()){ const all = [...periods(S.year - 1), ...periods(S.year)]; const cur = all.find(x => { const st = perStatus(x, tvhPeriod(x).n); return st.cls === "due" || st.cls === "late"; }) || all.find(x => t0 >= x.start && t0 <= x.end); if (cur) tax = {p:cur, v:tvhPeriod(cur)}; }
  const todo = todoItems(), B = balancesAt(t0);
  const since = esc(S.lastSync ? dShort(dLoc(S.lastSync)) + " à " + heure(S.lastSync) : "téléphone");
  let html = (!online() ? '<div class="banner"><b>Hors réseau</b><span class="small">Tu vois tes livres du ' + since + ". Tout ce que tu ajoutes est gardé dans le téléphone et partira tout seul au retour du réseau.</span></div>" :
    S.connErr === "login" ? '<div class="banner err"><b>' + esc(CONN_MSG.login[0]) + '</b><span class="small">Ta connexion à Google a expiré. Tes ajouts sont gardés dans le téléphone en attendant.</span><button class="btn sm primary" type="button" data-act="login" style="align-self:flex-start">Se connecter à Google</button></div>' :
    S.connErr ? '<div class="banner err"><b>' + esc((CONN_MSG[S.connErr] || ["Hors ligne"])[0]) + '</b><span class="small">Tu vois tes livres du ' + since + ". Tes ajouts partiront à la prochaine connexion.</span></div>" : "") +
    '<div><span class="eyebrow">' + esc(dFull(t0)) + "</span><h1>" + (h < 12 ? "Bonjour" : h < 18 ? "Bon après-midi" : "Bonsoir") + "</h1></div>";
  const trip = tripNow();
  if (trip) html += '<div class="banner info"><b>' + ico("i-car") + " Trajet en cours depuis " + esc(heure(trip.dep.t)) + "</b><span class=\"small\">" + esc((trip.depNom ? "Départ : " + trip.depNom + " · " : "") + kmVehNom(trip.vehicule)) + '</span><div class="row"><button class="btn sm primary" type="button" data-add="trajet">Je suis arrivé</button><button class="btn sm" type="button" data-act="trip-cancel">Annuler</button></div></div>';
  html += '<div class="card"><div class="card-h"><h2>' + ico("i-cal") + "Aujourd'hui</h2>" + '<button class="btn link" type="button" data-tabgo="agenda">Agenda</button></div>' + (todayEv.length ? '<div class="list" style="border:none">' + todayEv.map(e => kItem(e, {noDate:true})).join("") + "</div>" : '<p class="muted small">Rien de prévu aujourd\'hui.</p>') + (tom.length ? '<p class="muted small">Demain : ' + esc(tom.slice(0, 3).map(e => (e.heure ? fmtH(e.heure) + " " : "") + (e.short || e.title)).join(" · ")) + (tom.length > 3 ? "…" : "") + "</p>" : "") + '<button class="btn sm" type="button" data-add="evenement">' + ico("i-plus") + "Ajouter un événement</button></div>";
  html += '<div class="kpis">' +
    '<button class="kpi" type="button" data-tabgo="ventes"><span class="eyebrow">À encaisser</span><span class="val">' + fmt(arT) + "</span><small>" + ar.length + " facture" + (ar.length > 1 ? "s" : "") + (arLate ? ", " + arLate + " en retard" : "") + "</small></button>" +
    '<div class="kpi"><span class="eyebrow">Taxes ' + esc(tax ? tax.p.label.replace(/ \(.*$/, "") : "") + '</span><span class="val">' + (tax ? fmt(Math.abs(tax.v.net)) : "—") + "</span><small>" + (tax ? (tax.v.net >= 0 ? "à remettre" : "à recevoir") + " d'ici le " + dShort(tax.p.due) : "non inscrite") + "</small></div>" +
    '<div class="kpi"><span class="eyebrow">Revenus du mois</span><span class="val">' + fmt(pm.totRev) + "</span><small>avant taxes</small></div>" +
    '<div class="kpi"><span class="eyebrow">Dépenses du mois</span><span class="val">' + fmt(pm.totCv + pm.totExp) + "</span><small>avant taxes</small></div></div>";
  html += '<div class="card"><div class="card-h"><h2>' + ico("i-check") + "À faire</h2><span class=\"muted small\">" + (todo.length || "") + "</span></div>" + (todo.length ? '<div class="list" style="border:none">' + todo.slice(0, 8).map(t => '<button class="item" type="button"' + (t.ev ? ' data-ev="' + esc(t.ev) + '"' : t.fac ? ' data-fac="' + esc(t.fac) + '"' : t.plus ? ' data-tabgo="plus"' : "") + '><i class="k" style="background:' + (t.late ? "var(--neg)" : "var(--warn)") + '"></i><span class="t"><b>' + esc(t.txt) + "</b><small>" + esc(t.sub) + "</small></span></button>").join("") + "</div>" : '<p class="muted small">Tout est à jour.</p>') + "</div>";
  html += '<div class="card"><div class="card-h"><h2>' + ico("i-bank") + 'Soldes</h2></div><div class="kv">' + S.d.comptes.map(c => "<div><span>" + esc(c.nom) + '</span><span class="v">' + fmt(natural(c.id, B["cpt:" + c.id] || 0)) + "</span></div>").join("") + "</div></div>";
  put(el, html);
}
function vAgenda(){
  const el = $("v-agenda"); if (!S.d){ put(el, connCard()); return; }
  const t0 = today(); if (!S.calSel) S.calSel = t0; if (!S.calM) S.calM = S.calSel.slice(0, 7);
  const [y, m] = S.calM.split("-").map(Number), first = new Date(y, m - 1, 1), last = lastDay(y, m - 1), start = addDays(iso(first), -first.getDay()), end = addDays(iso(last), 6 - last.getDay());
  const by = {}; agendaEvents(start, end).forEach(e => { if (e.kind !== "info") (by[e.date] || (by[e.date] = [])).push(e); });
  let cal = ["D","L","M","M","J","V","S"].map(x => '<span class="dow">' + x + "</span>").join("");
  for (let dd = start; dd <= end; dd = addDays(dd, 1)){ const L = by[dd] || []; cal += '<button type="button" data-day="' + dd + '" class="' + (dd.slice(0, 7) !== S.calM ? "other " : "") + (dd === t0 ? "today " : "") + (dd === S.calSel ? "sel" : "") + '" aria-label="' + esc(dLong(dd)) + '"><span class="d">' + Number(dd.slice(8)) + '</span><span class="dots">' + L.slice(0, 4).map(e => '<i style="background:' + evColor(e) + '"></i>').join("") + "</span></button>"; }
  const day = agendaEvents(S.calSel, S.calSel).filter(e => e.kind !== "info"), up = agendaEvents(addDays(t0, 1), addDays(t0, 30)).filter(e => !e.done && e.kind !== "info");
  const late = agendaEvents(addDays(t0, -400), addDays(t0, -1)).filter(evLate);
  put(el, '<div class="card"><div class="card-h"><button class="icon-btn" type="button" data-cal="-1" aria-label="Mois précédent"><svg class="ic" style="transform:rotate(180deg)"><use href="#i-chev"/></svg></button><h2>' + esc(cap(MOIS[m - 1]) + " " + y) + '</h2><button class="icon-btn" type="button" data-cal="1" aria-label="Mois suivant"><svg class="ic"><use href="#i-chev"/></svg></button></div><div class="cal">' + cal + "</div></div>" +
    '<div class="row"><h2 style="flex:1">' + esc(dFull(S.calSel)) + '</h2><button class="btn sm primary" type="button" data-add="evenement">' + ico("i-plus") + "Événement</button></div>" +
    (day.length ? '<div class="list">' + day.map(e => kItem(e, {noDate:true})).join("") + "</div>" : '<p class="muted small">Rien de prévu cette journée.</p>') +
    (late.length ? '<div class="group-h">En retard</div><div class="list">' + late.map(e => kItem(e)).join("") + "</div>" : "") +
    '<div class="group-h">30 prochains jours</div>' + (up.length ? '<div class="list">' + up.map(e => kItem(e)).join("") + "</div>" : '<p class="muted small">Rien de prévu.</p>'));
}
function vVentes(){
  const el = $("v-ventes"); if (!S.d){ put(el, connCard()); return; }
  const F = S.d.factures, V = S.d.devis, C = S.d.clients;
  let html = '<div class="seg" role="group">' + [["factures","Factures",F.length],["devis","Devis",V.length],["clients","Clients",C.length]].map(([k, l, n]) => '<button type="button" data-vt="' + k + '" aria-pressed="' + (S.vt === k) + '">' + l + ' <span class="n">' + n + "</span></button>").join("") + "</div>";
  if (S.vt === "factures"){
    const st = F.map(f => ({f, s:facStatus(f), tot:docTotal("facture", f)})), ch = [["due","À encaisser"],["retard","En retard"],["payee","Payées"],["tous","Toutes"]];
    const L = st.filter(x => S.vtF === "tous" || x.s.k === S.vtF || (S.vtF === "due" && x.s.k === "retard")).sort((a, b) => b.f.date.localeCompare(a.f.date) || b.f.numero.localeCompare(a.f.numero));
    html += '<div class="row"><div class="chips" style="flex:1">' + ch.map(([k, l]) => '<button type="button" class="fchip" data-vtf="' + k + '" aria-pressed="' + (S.vtF === k) + '">' + l + "</button>").join("") + '</div><button class="btn sm primary" type="button" data-add="facture">' + ico("i-plus") + "Facture</button></div>" +
      (L.length ? '<div class="list">' + L.map(x => '<button class="item" type="button" data-fac="' + esc(x.f.id) + '"><span class="t"><b>' + esc(x.f.numero) + " · " + esc(x.f.client) + "</b><small>" + esc(dShort(x.f.date) + ((x.f.lignes[0] || {}).description ? " · " + x.f.lignes[0].description : "")) + '</small></span><span class="v">' + fmt(x.tot) + '<span class="chip ' + x.s.cls + '">' + esc(x.s.l) + "</span></span></button>").join("") + "</div>" : '<div class="empty">' + ico("i-invoice") + "<p>Aucune facture dans cette liste.</p></div>");
  } else if (S.vt === "devis"){
    const L = V.map(v => ({v, s:devStatus(v)})).sort((a, b) => b.v.date.localeCompare(a.v.date));
    html += '<div class="row end"><button class="btn sm primary" type="button" data-add="devis">' + ico("i-plus") + "Devis</button></div>" + (L.length ? '<div class="list">' + L.map(x => '<button class="item" type="button" data-dev="' + esc(x.v.id) + '"><span class="t"><b>' + esc(x.v.numero) + " · " + esc(x.v.client) + "</b><small>" + esc("Valide jusqu'au " + dShort(x.v.echeance)) + '</small></span><span class="v">' + fmt(docTotals(x.v).total) + '<span class="chip ' + x.s.cls + '">' + esc(x.s.l) + "</span></span></button>").join("") + "</div>" : '<div class="empty">' + ico("i-quote") + "<p>Aucun devis. Fais-en un chez ton client : il devient une facture en un clic.</p></div>");
  } else {
    const L = C.slice().sort((a, b) => a.nom.localeCompare(b.nom, "fr"));
    html += L.length ? '<div class="list">' + L.map(c => { const du = F.filter(f => (f.clientId === c.id || norm(f.client) === norm(c.nom)) && ["due","retard"].includes(facStatus(f).k)); return '<button class="item" type="button" data-cli="' + esc(c.id) + '"><span class="t"><b>' + esc(c.nom) + "</b><small>" + esc([c.telephone, c.courriel].filter(Boolean).join(" · ") || "Aucune coordonnée") + '</small></span><span class="v">' + (du.length ? fmt(du.reduce((s, f) => s + docTotal("facture", f), 0)) + '<span class="chip due">À encaisser</span>' : "") + "</span></button>"; }).join("") + "</div>" : '<div class="empty">' + ico("i-users") + "<p>Tes clients s'ajoutent quand tu fais une facture ou un devis.</p></div>";
  }
  put(el, html);
}
function vPlus(){
  const el = $("v-plus"); if (!S.d){ put(el, connCard() + syncCard()); return; }
  put(el, '<div><span class="eyebrow">' + esc(R().nom || "") + "</span><h1>Menu</h1></div>" + menuTelHtml("t", menuTelBadges()) + '<div class="mt-h">Synchronisation</div>' + syncCard());
}
function syncCard(){
  const P = S.pending, off = !online(), st = {attente: off ? ["due","Gardé, hors réseau"] : ["info","À envoyer"], envoi:["info","Envoi…"], envoye:["due","En attente de l'ordinateur"], erreur:["late","Non envoyé"]};
  const email = LS.get("email", "");
  return '<div class="card"><div class="card-h"><h2>' + ico("i-refresh") + 'Synchronisation</h2><button class="btn sm" type="button" data-act="refresh">Actualiser</button></div>' +
    '<p class="muted small">' + (S.lastSync ? "Livres lus dans Google Drive le " + esc(dShort(dLoc(S.lastSync)) + " à " + heure(S.lastSync)) + ". " : "") + "Tes ajouts sont gardés dans le téléphone, puis déposés dans le dossier « telephone » de tes livres dès qu'il y a du réseau. L'application de l'ordinateur les intègre quand elle est ouverte.</p>" +
    (P.length ? '<div class="list">' + P.map((p, i) => '<div class="item"><span class="t"><b>' + esc(p.label) + "</b><small>" + esc(dShort(dLoc(p.op.creeLe)) + " à " + heure(p.op.creeLe) + (p.err ? " · " + p.err : "")) + '</small></span><span class="v"><span class="chip ' + (st[p.etat] || st.attente)[0] + '">' + (st[p.etat] || st.attente)[1] + "</span>" + (p.etat === "erreur" ? '<button class="btn sm" type="button" data-retry="' + i + '">Réessayer</button>' : "") + "</span></div>").join("") + "</div>" : '<p class="small">Aucun ajout en attente.</p>') +
    '<div class="kv"><div><span>Compte Google</span><span class="v">' + esc(email || (tokOk() ? "Connecté" : "Non connecté")) + '</span></div><div><span>Réseau</span><span class="v">' + (off ? "Aucun" : "Disponible") + '</span></div></div>' +
    '<div class="row"><button class="btn sm" type="button" data-act="switch">Changer de compte Google</button></div></div>';
}

/* ===== Clics dans les vues ===== */
document.querySelector("main").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return; const ds = b.dataset;
  if (ds.act === "connect" || ds.act === "refresh") syncAll(true);
  else if (ds.act === "login") authRedirect(true);
  else if (ds.act === "trip-cancel"){ LS.set("trip", null); toast("Trajet annulé"); render(); }
  else if (ds.lieudel){ const l = (S.d.lieux || []).find(x => x.id === ds.lieudel); if (l){ toast("Lieu retiré : " + l.nom); sendOp("lieu-suppr", {id:l.id}); } }
  else if (ds.act === "switch"){ if (!online()) return toast("Il faut du réseau pour changer de compte."); logout(); authRedirect(true); }
  else if (ds.act === "cfg"){ const v = ($("cfg-id").value || "").trim(); if (!/\.apps\.googleusercontent\.com$/.test(v)) return toast("Cet identifiant ne semble pas bon : il doit finir par .apps.googleusercontent.com"); LS.set("clientId", v); S.conn = "init"; render(); syncAll(true); }
  else if (ds.tabgo) showTab(ds.tabgo);
  else if (ds.add) startAdd(ds.add, ds.eq ? {equipement:ds.eq} : {});
  else if (ds.ev) openEv(ds.ev);
  else if (ds.fac) openFacture(ds.fac);
  else if (ds.dev) openDevis(ds.dev);
  else if (ds.cli) openClient(ds.cli);
  else if (ds.day){ S.calSel = ds.day; S.calM = ds.day.slice(0, 7); vAgenda(); }
  else if (ds.cal){ const [y, m] = S.calM.split("-").map(Number), n = iso(new Date(y, m - 1 + Number(ds.cal), 1)); S.calM = n.slice(0, 7); S.calSel = S.calM === today().slice(0, 7) ? today() : n; vAgenda(); }
  else if (ds.vt){ S.vt = ds.vt; vVentes(); }
  else if (ds.vtf){ S.vtF = ds.vtf; vVentes(); }
  else if (ds.odo) fOdometre(ds.odo);
  else if (ds.rdv){ const q = S.d.equipements.find(x => x.id === ds.rdv), nx = q ? nextMaint(q)[0] : null; fEvenement(null, {type:"garage", equipement:ds.rdv, titre:(nx ? nx.type : "Entretien") + ", " + (q ? q.nom : ""), heure:"08:00", fin:"09:00"}); }
  else if (ds.retry){ const p = S.pending[Number(ds.retry)]; if (p){ p.etat = "attente"; savePending(); syncAll(true); } }
});

/* ===== Ajouter ===== */
const ADDS = [["depense","i-camera","Reçu ou dépense","Photo du reçu et montant"],["evenement","i-cal","Événement","Rendez-vous, soumission, garage"],["facture","i-invoice","Facture","Avec TPS et TVQ, en PDF"],["devis","i-quote","Devis","Chez le client"],["trajet","i-car","Trajet","Pour le kilométrage"],["entretien","i-wrench","Entretien","Camion ou équipement"],["revenu","i-in","Revenu","Paiement reçu sans facture"],["photo","i-inbox","Photo à traiter","Je l'inscrirai plus tard"]];
function openAdd(){
  if (!S.d){ toast("Connecte d'abord tes livres."); return; }
  openSheet("Ajouter", '<div class="addgrid">' + ADDS.map(([k, i, l, s]) => '<button type="button" data-addk="' + k + '">' + ico(i) + "<b>" + esc(l) + "</b><small>" + esc(s) + "</small></button>").join("") + '</div><div class="mt-h">Autres</div><div class="m-list">' + ADD_TEL2.map(([k, i, l]) => '<a href="complet.html#nouveau=' + k + '">' + ico(i) + "<span>" + esc(l) + "</span>" + ico("i-chev") + "</a>").join("") + "</div>", {onClick: e => { const b = e.target.closest("[data-addk]"); if (b) startAdd(b.dataset.addk, {}); }});
}
function startAdd(k, p){
  if (!S.d) return;
  if (k === "depense" || k === "revenu") fOperation(k, p);
  else if (k === "evenement") fEvenement(null, Object.assign({date: S.tab === "agenda" ? S.calSel : today()}, p));
  else if (k === "facture" || k === "devis") fDoc(k, null, p);
  else if (k === "trajet") fTrajet();
  else if (k === "entretien") fEntretien(p.equipement);
  else if (k === "photo") fPhoto();
}
const comptePicks = (cur, unpaidLbl) => S.d.comptes.map(c => '<button type="button" class="pick" data-cpt="' + esc(c.id) + '" aria-pressed="' + (c.id === cur) + '">' + ico(SORTE_IC[c.sorte] || "i-bank") + esc(c.nom) + "</button>").join("") + (unpaidLbl ? '<button type="button" class="pick" data-cpt="__impaye" aria-pressed="' + (cur === "__impaye") + '">' + ico("i-cal") + esc(unpaidLbl) + "</button>" : "");
function splitTaxes(total, code){ const [a, b] = taxRates(code); let ht = r2(total / (1 + a / 100 + b / 100)); const tx = r2(ht * a / 100), tq = r2(ht * b / 100); ht = r2(total - tx - tq); return {ht, tx, tq}; }
function dateField(id, v){ return '<div class="field"><span>Date</span><div class="row"><button type="button" class="pick" data-dset="' + id + '|0">Aujourd\'hui</button><button type="button" class="pick" data-dset="' + id + '|-1">Hier</button><input class="ctl" type="date" id="' + id + '" value="' + esc(v || today()) + '" style="flex:1;min-width:150px"></div></div>'; }
function dateClick(e){ const b = e.target.closest("[data-dset]"); if (!b) return false; const [id, n] = b.dataset.dset.split("|"); $(id).value = addDays(today(), Number(n)); return true; }

/* Dépense ou revenu */
function fOperation(type, p){
  const rev = type === "revenu", counts = {};
  S.d.transactions.forEach(t => { if (t.type === type && t.categorie) counts[t.categorie] = (counts[t.categorie] || 0) + 1; });
  const def = rev ? ["ventes","autres-revenus"] : ["carburant","entretien","vehicule","achats","fournitures","repas","telephone","outils"];
  const keys = [...new Set([...Object.keys(counts).sort((a, b) => counts[b] - counts[a]), ...def])].filter(k => cat(type, k)).slice(0, 8), cat0 = keys[0] || (rev ? "ventes" : "autres");
  const cpt0 = rev ? ((S.d.comptes.find(c => c.sorte === "banque") || {}).id || "") : ((S.d.comptes.find(c => c.sorte === "carte") || S.d.comptes[0] || {}).id || "__impaye");
  const tiers = [...new Set([...S.d.fournisseurs.map(f => f.nom), ...S.d.transactions.filter(t => t.type === type).map(t => t.tiers)].filter(Boolean))].slice(0, 200);
  const eqs = S.d.equipements.filter(e => e.statut !== "vendu");
  const body = (rev ? "" : photoField()) +
    '<div class="field"><span>Montant total, taxes incluses</span><span class="money"><input id="o-mt" inputmode="decimal" placeholder="0,00" autocomplete="off"><span>$</span></span><p class="calc" id="o-calc">Entre le total pour voir les taxes.</p></div>' +
    '<label class="field"><span>' + (rev ? "Client" : "Fournisseur") + '</span><input class="ctl" id="o-tiers" list="o-dl" maxlength="120" placeholder="' + (rev ? "Ex. : M. Tremblay" : "Ex. : Ultramar") + '" autocomplete="off"><datalist id="o-dl">' + tiers.map(n => '<option value="' + esc(n) + '">').join("") + "</datalist></label>" +
    '<div class="field"><span>Catégorie</span><div class="picks" id="o-cats">' + keys.map(k => '<button type="button" class="pick" data-ocat="' + k + '" aria-pressed="' + (k === cat0) + '">' + esc(cat(type, k).l) + "</button>").join("") + '</div><select class="ctl" id="o-cat">' + CATS[type].map(c => '<option value="' + c.k + '"' + (c.k === cat0 ? " selected" : "") + ">" + esc(c.l) + "</option>").join("") + "</select></div>" +
    '<div class="field"><span>' + (rev ? "Déposé dans" : "Payé avec") + '</span><div class="picks" id="o-cpts">' + comptePicks(cpt0, rev ? "Pas encore reçu" : "Pas encore payée") + "</div></div>" +
    dateField("o-date") +
    '<details class="more"><summary>Taxes, description et note</summary><div><label class="field"><span>Taxes</span><select class="ctl" id="o-code">' + TAXCODES.map(c => '<option value="' + c + '">' + esc(taxLabel(c)) + "</option>").join("") + '</select></label><label class="field"><span>Description</span><input class="ctl" id="o-desc" maxlength="200" placeholder="' + (rev ? "Ex. : Abattage d'un frêne" : "Ex. : Essence du camion") + '"></label>' +
    (!rev && eqs.length ? '<label class="field"><span>Véhicule ou équipement</span><select class="ctl" id="o-eq"><option value="">Aucun</option>' + eqs.map(e => '<option value="' + esc(e.id) + '"' + (p.equipement === e.id ? " selected" : "") + ">" + esc(e.nom) + "</option>").join("") + "</select></label>" : "") +
    '<label class="field"><span>Note</span><textarea class="ctl" id="o-note" maxlength="600"></textarea></label></div></details><p class="hint" id="o-hint" hidden></p>';
  const applyCat = () => { const c = cat(type, $("o-cat").value); $("o-code").value = c && c.tax && !(rev && !inscrit()) ? defCode() : "AUCUNE"; calc(); };
  const calc = () => { const a = num($("o-mt").value); if (!isFinite(a) || a <= 0){ $("o-calc").textContent = "Entre le total pour voir les taxes."; return null; } const t = splitTaxes(a, $("o-code").value); $("o-calc").textContent = (t.tx || t.tq) ? fmt(t.ht) + " avant taxes + TPS " + fmt(t.tx) + (t.tq ? " + TVQ " + fmt(t.tq) : "") : fmt(t.ht) + ", sans taxes";
    const msgs = []; if (!rev && a >= 100 && (t.tx || t.tq)) msgs.push("100 $ et plus : vérifie que le reçu montre les numéros de TPS et de TVQ du fournisseur."); if ($("o-cat").value === "repas") msgs.push("Repas : la moitié des taxes est récupérée."); $("o-hint").innerHTML = msgs.map(esc).join("<br>"); $("o-hint").hidden = !msgs.length; return t; };
  openSheet(rev ? "Nouveau revenu" : "Reçu ou dépense", body, {primary:"Envoyer", state:{cpt:cpt0},
    ready: () => { if (!rev) bindPhotos(); applyCat(); setTimeout(() => $("o-mt").focus(), 60); },
    onInput: e => { if (e.target.id === "o-mt") calc(); },
    onChange: e => { if (e.target.id === "o-cat"){ pressSet("[data-ocat]", "data-ocat", e.target.value); applyCat(); } if (e.target.id === "o-code") calc();
      if (e.target.id === "o-tiers"){ const f = S.d.fournisseurs.find(x => norm(x.nom) === norm(e.target.value)); const last = S.d.transactions.filter(t => t.type === type && norm(t.tiers) === norm(e.target.value)).sort((a, b) => b.date.localeCompare(a.date))[0]; const k = (f && f.categorie) || (last && last.categorie); if (k && cat(type, k)){ $("o-cat").value = k; pressSet("[data-ocat]", "data-ocat", k); applyCat(); } } },
    onClick: e => { if (dateClick(e)) return; const c = e.target.closest("[data-ocat]"); if (c){ $("o-cat").value = c.dataset.ocat; pressSet("[data-ocat]", "data-ocat", c.dataset.ocat); applyCat(); } const k = e.target.closest("[data-cpt]"); if (k){ S.form.cpt = k.dataset.cpt; pressSet("[data-cpt]", "data-cpt", k.dataset.cpt); } },
    onSubmit: async () => {
      const t = calc(); if (!t) return fail("Entre le montant total, par exemple 64,50.");
      const tiers = $("o-tiers").value.trim(), desc = $("o-desc").value.trim(), date = $("o-date").value || today(), imp = S.form.cpt === "__impaye";
      if (!tiers && !desc) return fail(rev ? "Indique le client ou une description." : "Indique le fournisseur ou une description.");
      if (!S.form.cpt) return fail("Choisis le compte.");
      const data = {id: uid("t"), date, type, description: desc, tiers, categorie: $("o-cat").value, montant: t.ht, taxe: t.tx, tvq: t.tq, codeTaxe: $("o-code").value, compte: imp ? "" : S.form.cpt, statut: imp ? (rev ? "a-recevoir" : "a-payer") : "regle", echeance: imp ? addDays(date, 30) : "", note: $("o-note").value.trim()};
      if ($("o-eq") && $("o-eq").value) data.equipement = $("o-eq").value;
      const photos = (S.form && S.form.photos) || [];
      closeSheet(); toast((rev ? "Revenu envoyé : " : "Dépense envoyée : ") + fmt(t.ht + t.tx + t.tq));
      await sendOp("operation", data, photos);
    }});
}
/* Photo à traiter plus tard */
function fPhoto(){
  openSheet("Photo à traiter", '<p class="muted">La photo va dans le dossier « à traiter » de tes livres. Tu l\'inscriras sur l\'ordinateur, ou Claude le fera pour toi.</p>' + photoField(), {primary:"Envoyer", ready: bindPhotos,
    onSubmit: async () => { const ph = (S.form && S.form.photos) || []; if (!ph.length) return fail("Ajoute au moins une photo."); closeSheet(); toast(ph.length > 1 ? ph.length + " photos envoyées" : "Photo envoyée"); await sendOp("photo", {}, ph); }});
}
/* ===== Trajets : GPS (départ et arrivée) ou à la main ===== */
const OSRM = window.__OSRM || "https://router.project-osrm.org";
const tripNow = () => LS.get("trip", null);
function gpsPos(fresh){
  return new Promise((res0, rej0) => {
    if (!navigator.geolocation) return rej0({message:"Le GPS n'est pas disponible sur cet appareil. Inscris le trajet à la main."});
    let done = false; const res = v => { if (!done){ done = true; clearTimeout(tm); res0(v); } }, rej = v => { if (!done){ done = true; clearTimeout(tm); rej0(v); } };
    const tm = setTimeout(() => rej({message:"Position introuvable pour l'instant. Réessaie dans un moment, ou inscris le trajet à la main."}), 60000);
    navigator.geolocation.getCurrentPosition(
      p => res({lat: +p.coords.latitude.toFixed(6), lng: +p.coords.longitude.toFixed(6), acc: Math.round(p.coords.accuracy || 0), t: new Date().toISOString()}),
      e => rej({message: e && e.code === 1 ? "Le téléphone refuse l'accès à ta position. Autorise-la : Paramètres du téléphone › Applications › Chrome › Autorisations › Position, puis réessaie." : "Position introuvable pour l'instant. Réessaie dans un moment, idéalement à l'extérieur."}),
      {enableHighAccuracy:true, timeout:30000, maximumAge: fresh ? 0 : 15000});
  });
}
/* Distance par la route (OpenStreetMap / OSRM). Sans réseau : estimation à vol d'oiseau × 1,25, recalculée avant l'envoi. */
async function routeKm(a, b){
  if (!online()) return null;
  const ctl = new AbortController(), tm = setTimeout(() => ctl.abort(), 12000);
  try {
    const r = await fetch(OSRM + "/route/v1/driving/" + a.lng + "," + a.lat + ";" + b.lng + "," + b.lat + "?overview=false&alternatives=false&steps=false", {signal: ctl.signal});
    if (!r.ok) return null; const j = await r.json();
    return j && j.code === "Ok" && j.routes && j.routes[0] ? Math.round(j.routes[0].distance / 100) / 10 : null;
  } catch(e){ return null; } finally { clearTimeout(tm); }
}
const estKm = (a, b) => Math.max(0.1, Math.round(distGeo([a.lat, a.lng], [b.lat, b.lng]) * 1.25 * 10) / 10);
const kmTxt = v => String(v).replace(".", ",");
const vehPicks = cur => kmVehicules().map(([k, l]) => '<button type="button" class="pick" data-veh="' + esc(k) + '" aria-pressed="' + (k === cur) + '">' + ico(k === KM_PERSO ? "i-car" : "i-truck") + esc(l) + "</button>").join("");
const lieuxDL = () => '<datalist id="k-dl">' + kmLieuxNoms().map(n => '<option value="' + esc(n) + '">').join("") + "</datalist>";
const lieuNomm = nom => (S.d.lieux || []).find(l => norm(l.nom) === norm(nom));
const modeSeg = m => '<div class="seg" role="group" aria-label="Façon d\'inscrire le trajet"><button type="button" data-kmode="gps" aria-pressed="' + (m === "gps") + '">' + ico("i-map") + 'GPS</button><button type="button" data-kmode="manuel" aria-pressed="' + (m === "manuel") + '">' + ico("i-edit") + "À la main</button></div>";
function fTrajet(force){
  const trip = tripNow();
  if (trip && force !== "manuel") return fArrivee(trip);
  const mode = force || LS.get("kmMode", "gps"); LS.set("kmMode", mode);
  return mode === "gps" ? fDepart() : fManuel();
}
function trajetClick(e){
  if (dateClick(e)) return true;
  const m = e.target.closest("[data-kmode]"); if (m){ fTrajet(m.dataset.kmode); return true; }
  const v = e.target.closest("[data-veh]"); if (v){ S.form.veh = v.dataset.veh; pressSet("[data-veh]", "data-veh", v.dataset.veh); return true; }
  return false;
}
function fDepart(){
  const veh = LS.get("kmVeh", KM_PERSO), vOk = kmVehicules().some(([k]) => k === veh) ? veh : KM_PERSO;
  openSheet("Nouveau trajet", modeSeg("gps") +
    '<p class="muted">Touche <b>Je pars</b> au départ, puis <b>Je suis arrivé</b> en arrivant. Pas besoin de garder l\'application ouverte pendant que tu conduis, et ça marche sans réseau.</p>' +
    '<div class="field"><span>Véhicule</span><div class="picks">' + vehPicks(vOk) + "</div></div>" +
    '<p class="muted small">La distance est calculée par le chemin le plus court sur la route. Tu pourras la corriger, par exemple après un détour.</p>',
    {primary:"Je pars", state:{veh:vOk}, onClick: trajetClick, onSubmit: async () => {
      const b = $("sh-ok"); if (b) b.textContent = "Recherche de ta position…";
      let pos; try { pos = await gpsPos(); } catch(e){ if (b) b.textContent = "Je pars"; return e.message; }
      const l = lieuPres([pos.lat, pos.lng]);
      LS.set("trip", {dep:pos, depNom: l ? l.nom : "", vehicule:S.form.veh}); LS.set("kmVeh", S.form.veh);
      toast("Bon trajet ! " + (l ? "Départ : " + l.nom + ". " : "") + "Touche « Je suis arrivé » à destination.");
      setTimeout(render, 0);
    }});
}
function fArrivee(trip){
  const since = heure(trip.dep.t) + (dLoc(trip.dep.t) !== today() ? " le " + dShort(dLoc(trip.dep.t)) : "");
  openSheet("Trajet en cours", '<div class="kv"><div><span>Départ</span><span class="v">' + esc((trip.depNom || "Position GPS") + " à " + since) + '</span></div><div><span>Véhicule</span><span class="v">' + esc(kmVehNom(trip.vehicule)) + "</span></div></div>" +
    '<p class="muted small">Touche <b>Je suis arrivé</b> une fois à destination : je note ta position et je calcule la distance.</p>',
    {primary:"Je suis arrivé", secondary:'<button class="btn" type="button" data-trip-cancel>Annuler le trajet</button>',
     onClick: e => { if (e.target.closest("[data-trip-cancel]")){ LS.set("trip", null); closeSheet(); toast("Trajet annulé"); render(); } },
     onSubmit: async () => {
      const b = $("sh-ok"); if (b) b.textContent = "Recherche de ta position…";
      let pos; try { pos = await gpsPos(true); } catch(e){ if (b) b.textContent = "Je suis arrivé"; return e.message; }
      fFinTrajet(trip, pos); return false;
    }});
}
function fFinTrajet(trip, arr){
  const lA = lieuPres([arr.lat, arr.lng]), est = estKm(trip.dep, arr);
  openSheet("Fin du trajet", lieuxDL() +
    '<div class="two"><label class="field"><span>Départ</span><input class="ctl" id="k-dep" list="k-dl" maxlength="100" value="' + esc(trip.depNom) + '" placeholder="Ex. : Maison"></label><label class="field"><span>Destination</span><input class="ctl" id="k-dest" list="k-dl" maxlength="100" value="' + esc(lA ? lA.nom : "") + '" placeholder="Ex. : Chantier Gagnon"></label></div>' +
    '<label class="field"><span>Raison d\'affaires</span><input class="ctl" id="k-raison" maxlength="160" placeholder="Ex. : Soumission chez M. Tremblay"></label>' +
    '<div class="field"><span>Kilomètres</span><span class="money"><input id="k-km" inputmode="decimal" value="' + kmTxt(est) + '"><span>km</span></span><p class="calc" id="k-kmnote">Calcul de la distance par la route…</p></div>' +
    '<div class="field"><span>Véhicule</span><div class="picks">' + vehPicks(trip.vehicule || KM_PERSO) + "</div></div>" +
    '<label class="check" id="k-savel-w" hidden><input type="checkbox" id="k-savel" checked><span id="k-savel-t">Enregistrer les nouveaux lieux pour les reconnaître la prochaine fois</span></label>',
    {primary:"Enregistrer le trajet", state:{veh: trip.vehicule || KM_PERSO, routed:false, edited:false, km:est}, onClick: trajetClick,
     ready: async () => {
       const showSave = () => { const n = [$("k-dep").value, $("k-dest").value].filter(x => x.trim() && !lieuNomm(x)); $("k-savel-w").hidden = !n.length; $("k-savel-t").textContent = "Enregistrer " + n.map(x => "« " + x.trim() + " »").join(" et ") + " pour les reconnaître la prochaine fois"; };
       showSave(); setTimeout(() => (trip.depNom ? $("k-dest") : $("k-dep")).focus(), 60);
       const f = S.form, km = await routeKm(trip.dep, arr); if (S.form !== f) return;
       if (km != null){ f.routed = true; f.km = km; if (!f.edited) $("k-km").value = kmTxt(km); $("k-kmnote").textContent = "Par la route : " + kmTxt(km) + " km (OpenStreetMap)."; }
       else $("k-kmnote").textContent = online() ? "Distance par la route indisponible : estimation de " + kmTxt(est) + " km. Corrige-la au besoin." : "Sans réseau : estimation de " + kmTxt(est) + " km. Elle sera recalculée par la route avant l'envoi.";
     },
     onInput: e => { if (e.target.id === "k-km") S.form.edited = true; if (e.target.id === "k-dep" || e.target.id === "k-dest"){ const n = [$("k-dep").value, $("k-dest").value].filter(x => x.trim() && !lieuNomm(x)); $("k-savel-w").hidden = !n.length; $("k-savel-t").textContent = "Enregistrer " + n.map(x => "« " + x.trim() + " »").join(" et ") + " pour les reconnaître la prochaine fois"; } },
     onSubmit: async () => {
      const km = num($("k-km").value); if (!isFinite(km) || km <= 0) return fail("Entre le nombre de kilomètres.");
      const dest = $("k-dest").value.trim(), dep = $("k-dep").value.trim(); if (!dest) return fail("Indique la destination.");
      const raison = $("k-raison").value.trim(); if (!raison) return fail("Indique la raison d'affaires : l'ARC la demande pour chaque trajet.");
      const f = S.form, data = {id: uid("k"), date: dLoc(trip.dep.t), depart: dep, destination: dest, raison, km: Math.round(km * 10) / 10, projet:"", vehicule: f.veh, mode:"gps", gps:{dep:[trip.dep.lat, trip.dep.lng], arr:[arr.lat, arr.lng]}};
      if (f.edited) data.kmManuel = true; else if (!f.routed) data.estime = true;
      const saveL = !$("k-savel-w").hidden && $("k-savel").checked;
      LS.set("trip", null); LS.set("kmVeh", f.veh); closeSheet(); toast("Trajet enregistré : " + kmTxt(data.km) + " km");
      if (saveL){
        if (dep && !lieuNomm(dep)) await sendOp("lieu", {id: uid("l"), nom: dep, adresse:"", lat: trip.dep.lat, lng: trip.dep.lng});
        if (dest && !lieuNomm(dest) && norm(dest) !== norm(dep)) await sendOp("lieu", {id: uid("l"), nom: dest, adresse:"", lat: arr.lat, lng: arr.lng});
      }
      await sendOp("trajet", data);
    }});
}
function fManuel(){
  const veh = LS.get("kmVeh", KM_PERSO), vOk = kmVehicules().some(([k]) => k === veh) ? veh : KM_PERSO, fr = kmFrequents(6), last = S.d.km.slice().sort((a, b) => b.date.localeCompare(a.date))[0];
  openSheet("Nouveau trajet", modeSeg("manuel") + lieuxDL() +
    (fr.length ? '<div class="field"><span>Trajets fréquents</span><div class="chips">' + fr.map((k, i) => '<button type="button" class="fchip" data-kfreq="' + i + '">' + esc((k.depart || "—") + " → " + k.destination) + " · " + kmTxt(k.km) + " km</button>").join("") + "</div></div>" : "") +
    dateField("k-date") +
    '<div class="two"><label class="field"><span>Départ</span><input class="ctl" id="k-dep" list="k-dl" maxlength="100" value="' + esc(last ? last.depart : "") + '" placeholder="Ex. : Maison"></label><label class="field"><span>Destination</span><input class="ctl" id="k-dest" list="k-dl" maxlength="100" placeholder="Ex. : Chantier Gagnon"></label></div>' +
    '<label class="field"><span>Raison d\'affaires</span><input class="ctl" id="k-raison" maxlength="160" placeholder="Ex. : Soumission chez M. Tremblay"></label>' +
    '<div class="field"><span>Kilomètres</span><div class="row"><span class="money" style="flex:1"><input id="k-km" inputmode="decimal" placeholder="42"><span>km</span></span><button class="btn" type="button" id="k-calc" hidden>' + ico("i-map") + 'Calculer</button></div><p class="calc" id="k-kmnote" hidden></p></div>' +
    '<label class="check"><input type="checkbox" id="k-ar"><span>Aller-retour (double les km)</span></label>' +
    '<div class="field"><span>Véhicule</span><div class="picks">' + vehPicks(vOk) + "</div></div>" +
    '<p class="muted small">L\'ARC demande la date, la destination, la raison et les kilomètres de chaque trajet. Seuls les trajets avec ton auto personnelle donnent droit à l\'allocation.</p>',
    {primary:"Enregistrer", state:{veh:vOk},
     ready: () => { setTimeout(() => $("k-dest").focus(), 60); calcBtn(); },
     onInput: e => { if (e.target.id === "k-dep" || e.target.id === "k-dest") calcBtn(); },
     onClick: async e => {
      if (trajetClick(e)) return;
      const q = e.target.closest("[data-kfreq]");
      if (q){ const k = fr[Number(q.dataset.kfreq)]; if (!k) return; $("k-dep").value = k.depart || ""; $("k-dest").value = k.destination || ""; $("k-raison").value = k.raison || ""; $("k-km").value = kmTxt(k.km); $("k-ar").checked = false; S.form.veh = k.vehicule || KM_PERSO; pressSet("[data-veh]", "data-veh", S.form.veh); pressSet("[data-kfreq]", "data-kfreq", q.dataset.kfreq); calcBtn(); $("k-raison").focus(); return; }
      if (e.target.closest("#k-calc")){
        const a = lieuNomm($("k-dep").value), b = lieuNomm($("k-dest").value); if (!a || !b || a.lat == null || b.lat == null) return;
        $("k-kmnote").hidden = false; $("k-kmnote").textContent = "Calcul par la route…";
        const km = await routeKm({lat:a.lat, lng:a.lng}, {lat:b.lat, lng:b.lng});
        if (km != null){ $("k-km").value = kmTxt(km); $("k-kmnote").textContent = "Par la route : " + kmTxt(km) + " km (OpenStreetMap)."; }
        else $("k-kmnote").textContent = "Calcul impossible pour l'instant (réseau). Entre les kilomètres à la main.";
      }
     },
     onSubmit: async () => {
      let km = num($("k-km").value); if (!isFinite(km) || km <= 0) return fail("Entre le nombre de kilomètres, par exemple 42.");
      if (!$("k-dest").value.trim()) return fail("Indique la destination.");
      if ($("k-ar").checked) km *= 2;
      const data = {id: uid("k"), date: $("k-date").value || today(), depart: $("k-dep").value.trim(), destination: $("k-dest").value.trim(), raison: $("k-raison").value.trim(), km: Math.round(km * 10) / 10, projet:"", vehicule:S.form.veh, mode:"manuel"};
      LS.set("kmVeh", S.form.veh); closeSheet(); toast("Trajet enregistré : " + kmTxt(data.km) + " km"); await sendOp("trajet", data); }});
}
function calcBtn(){ const a = lieuNomm($("k-dep").value), b = lieuNomm($("k-dest").value), ok = !!(a && b && a.lat != null && b.lat != null && a.id !== b.id); $("k-calc").hidden = !ok; }
/* Avant l'envoi : une distance estimée sans réseau est recalculée par la route */
async function fixTrajets(){
  for (const p of S.pending){
    const x = p.op.data || {};
    if (p.op.type !== "trajet" || p.etat !== "attente" || (p.tries || 0) > 0 || !x.estime || x.kmManuel || !x.gps) continue;
    const km = await routeKm({lat:x.gps.dep[0], lng:x.gps.dep[1]}, {lat:x.gps.arr[0], lng:x.gps.arr[1]});
    if (km == null) return;
    x.km = km; delete x.estime; p.label = opLabel(p.op); savePending(); recompute();
  }
}
/* Odomètre */
function fOdometre(id){
  const e = S.d.equipements.find(x => x.id === id); if (!e) return;
  openSheet("Odomètre : " + e.nom, '<label class="field"><span>Kilométrage affiché</span><input class="ctl" id="od-km" inputmode="numeric" value="' + esc(e.odometre ? String(Math.round(e.odometre)) : "") + '"></label>', {primary:"Envoyer", onSubmit: async () => {
    const v = num($("od-km").value); if (!isFinite(v) || v <= 0) return fail("Entre le kilométrage, par exemple 125000.");
    closeSheet(); toast("Odomètre envoyé"); await sendOp("odometre", {equipement:id, km:Math.round(v), date:today()}); }});
}
/* Événement */
function fEvenement(n, p){
  p = p || {}; const t0 = n ? evtOf(n) : (EVT[p.type] ? p.type : "rdv"), allDay = n ? !n.heure : p.heure === "";
  const h0 = n ? (n.heure || "09:00") : (p.heure || "09:00"), f0 = n ? (n.fin || fromMin(toMin(h0) + 60)) : (p.fin || fromMin(toMin(h0) + 60)), v = k => esc(n ? n[k] || "" : p[k] || "");
  const eqs = S.d.equipements.filter(e => e.statut !== "vendu" || (n && n.equipement === e.id));
  const body = '<div class="field"><span>Type</span><div class="picks">' + Object.entries(EVT).map(([k, x]) => '<button type="button" class="pick" data-evt="' + k + '" aria-pressed="' + (k === t0) + '"><i class="sw" style="background:' + x.c + '"></i>' + esc(x.l) + "</button>").join("") + "</div></div>" +
    '<label class="field"><span>Titre</span><input class="ctl" id="e-titre" maxlength="140" value="' + v("titre") + '" placeholder="' + esc(EVT[t0].ph) + '"></label>' +
    '<label class="field"><span>Date</span><input class="ctl" type="date" id="e-date" value="' + esc(n ? n.date : (p.date || today())) + '"></label>' +
    '<label class="check"><input type="checkbox" id="e-all"' + (allDay ? " checked" : "") + "><span>Toute la journée</span></label>" +
    '<div class="two" data-evh><label class="field"><span>Début</span><input class="ctl" type="time" id="e-deb" step="300" value="' + esc(h0) + '"></label><label class="field"><span>Fin</span><input class="ctl" type="time" id="e-fin" step="300" value="' + esc(f0) + '"></label></div>' +
    '<div class="picks" data-evh>' + [[30,"30 min"],[60,"1 h"],[120,"2 h"],[240,"Demi-journée"],[480,"Journée"]].map(([m, l]) => '<button type="button" class="pick" data-dur="' + m + '">' + l + "</button>").join("") + "</div>" +
    '<label class="field" data-evf="client"><span>Client</span><input class="ctl" id="e-cli" list="e-dl" maxlength="120" autocomplete="off" value="' + v("client") + '"><datalist id="e-dl">' + S.d.clients.map(c => '<option value="' + esc(c.nom) + '">').join("") + "</datalist></label>" +
    '<label class="field" data-evf="garage"><span>Véhicule ou équipement</span><select class="ctl" id="e-eq"><option value="">' + (eqs.length ? "Choisis" : "Aucun équipement") + "</option>" + eqs.map(e => '<option value="' + esc(e.id) + '"' + ((n ? n.equipement : p.equipement) === e.id ? " selected" : "") + ">" + esc(e.nom) + "</option>").join("") + "</select></label>" +
    '<label class="field"><span>Lieu ou adresse</span><input class="ctl" id="e-lieu" maxlength="200" value="' + v("lieu") + '"></label>' +
    '<label class="field"><span>Rappel</span><select class="ctl" id="e-rap">' + RAPPELS.map(([k, l]) => '<option value="' + k + '"' + (String(n ? n.rappel || 0 : (p.rappel != null ? p.rappel : (t0 === "note" ? 0 : 60))) === k ? " selected" : "") + ">" + l + "</option>").join("") + "</select><small>Le rappel apparaît dans l'application de l'ordinateur, et dans Outlook ou Google si tu y exportes l'agenda.</small></label>" +
    '<label class="field"><span>Détails</span><textarea class="ctl" id="e-note" maxlength="4000">' + esc(n ? n.note || "" : p.note || "") + "</textarea></label>";
  const sync = () => { document.querySelector('[data-evf="client"]').hidden = S.form.type === "garage" || S.form.type === "note"; document.querySelector('[data-evf="garage"]').hidden = S.form.type !== "garage"; document.querySelectorAll("[data-evh]").forEach(x => { x.hidden = $("e-all").checked; }); $("e-titre").placeholder = EVT[S.form.type].ph; };
  let prev = h0;
  openSheet(n ? "Modifier l'événement" : "Nouvel événement", body, {primary: n ? "Enregistrer" : "Ajouter", state:{type:t0},
    secondary: n ? '<button class="btn danger" type="button" data-evdel>Supprimer</button>' : "",
    ready: sync,
    onChange: e => { if (e.target.id === "e-all") sync(); if (e.target.id === "e-cli"){ const c = S.d.clients.find(x => norm(x.nom) === norm(e.target.value)); if (c && c.adresse && !$("e-lieu").value.trim()) $("e-lieu").value = c.adresse.replace(/\s*\r?\n\s*/g, ", "); } },
    onInput: e => { if (e.target.id === "e-deb" && e.target.value){ const dur = prev && $("e-fin").value ? toMin($("e-fin").value) - toMin(prev) : 60; $("e-fin").value = fromMin(toMin(e.target.value) + (dur > 0 ? dur : 60)); prev = e.target.value; } },
    onClick: async e => { const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.evt){ S.form.type = b.dataset.evt; pressSet("[data-evt]", "data-evt", S.form.type); sync(); }
      else if (b.dataset.dur) $("e-fin").value = fromMin(toMin($("e-deb").value || "09:00") + Number(b.dataset.dur));
      else if (b.hasAttribute("data-evdel")){ closeSheet(); toast("Événement retiré"); await sendOp("evenement-suppr", {id:n.id}); } },
    onSubmit: async () => {
      let titre = $("e-titre").value.trim(); const date = $("e-date").value, all = $("e-all").checked, deb = all ? "" : $("e-deb").value, fin = all ? "" : $("e-fin").value, t = S.form.type, cli = $("e-cli").value.trim(), eq = $("e-eq").value;
      if (!date) return fail("Choisis la date.");
      if (!all && !deb) return fail("Choisis l'heure de début, ou coche « Toute la journée ».");
      if (!all && fin && toMin(fin) <= toMin(deb)) return fail("L'heure de fin doit être après l'heure de début.");
      if (!titre){ const who = t === "garage" ? (S.d.equipements.find(x => x.id === eq) || {}).nom : cli; if (t !== "note" && who) titre = EVT[t].l + " : " + who; else return fail("Entre un titre."); }
      const data = Object.assign({}, n || {id: uid("n")}, {type:t, titre, date, heure:deb, fin, lieu:$("e-lieu").value.trim(), client: t === "garage" || t === "note" ? "" : cli, equipement: t === "garage" ? eq : "", rappel:Number($("e-rap").value) || 0, note:$("e-note").value.trim(), fait: n ? !!n.fait : false});
      S.calSel = date; S.calM = date.slice(0, 7); closeSheet(); toast((n ? "Modifié" : "Ajouté") + " : " + dShort(date) + (deb ? ", " + fmtH(deb) : "")); await sendOp("evenement", data); }});
}
/* Fiche d'un élément de l'agenda */
function openEv(key){
  const t0 = today(), all = agendaEvents(addDays(t0, -420), addDays(t0, 800)), e = all.find(x => evKey(x) === key); if (!e) return;
  if (e.kind === "note"){
    const n = S.d.agenda.find(x => x.id === e.id); if (!n) return;
    const q = n.equipement ? S.d.equipements.find(x => x.id === n.equipement) : null;
    openSheet(EVT[evtOf(n)].l, '<div><span class="eyebrow">' + esc(dFull(n.date)) + "</span><h2>" + esc(n.titre) + '</h2><p class="muted">' + esc(fmtRange(n.heure, n.fin)) + "</p></div>" +
      '<div class="kv">' + (n.client ? "<div><span>Client</span><span class=\"v\">" + esc(n.client) + "</span></div>" : "") + (q ? "<div><span>Équipement</span><span class=\"v\">" + esc(q.nom) + "</span></div>" : "") + (n.lieu ? "<div><span>Lieu</span><span class=\"v\">" + esc(n.lieu) + "</span></div>" : "") + (Number(n.rappel) ? "<div><span>Rappel</span><span class=\"v\">" + esc((RAPPELS.find(r => r[0] === String(n.rappel)) || ["", ""])[1]) + "</span></div>" : "") + "</div>" +
      (n.note ? '<p style="white-space:pre-wrap">' + esc(n.note) + "</p>" : "") +
      '<div class="row">' + (n.lieu ? '<a class="btn" href="' + esc(mapURL(n.lieu)) + '" target="_blank" rel="noopener">' + ico("i-map") + "Itinéraire</a>" : "") +
      (evtOf(n) === "soumission" ? '<button class="btn" type="button" data-x="devis">' + ico("i-quote") + "Faire le devis</button>" : "") + (evtOf(n) === "chantier" ? '<button class="btn" type="button" data-x="facture">' + ico("i-invoice") + "Facturer</button>" : "") + (evtOf(n) === "garage" && q ? '<button class="btn" type="button" data-x="entretien">' + ico("i-wrench") + "Inscrire l'entretien</button>" : "") + "</div>",
      {secondary:'<button class="btn" type="button" data-x="modifier">Modifier</button><button class="btn' + (n.fait ? "" : " primary") + '" type="button" data-x="fait">' + (n.fait ? "Remettre à faire" : "Marquer fait") + "</button>",
       onClick: async ev => { const b = ev.target.closest("[data-x]"); if (!b) return; const x = b.dataset.x;
         if (x === "modifier") fEvenement(n);
         else if (x === "fait"){ closeSheet(); await sendOp("evenement-fait", {id:n.id, fait:!n.fait}); }
         else if (x === "devis") fDoc("devis", null, {client:n.client});
         else if (x === "facture") fDoc("facture", null, {client:n.client});
         else if (x === "entretien") fEntretien(n.equipement); }});
    return;
  }
  if (e.kind === "fac" && e.go){ const id = e.go.split(":")[1]; if (e.go.startsWith("fac:")) return openFacture(id); if (e.go.startsWith("dev:")) return openDevis(id); }
  const canDone = e.kind === "obl" && e.key;
  openSheet(evSub(e) || "Échéance", '<div><span class="eyebrow">' + esc(dFull(e.date)) + "</span><h2>" + esc(e.title) + "</h2></div>" + (e.detail ? "<p>" + esc(e.detail) + "</p>" : "") + (evLate(e) ? '<span class="chip late">En retard</span>' : "") +
    (e.kind === "tax" ? '<p class="muted small">Les montants ligne par ligne sont dans l\'onglet Taxes de vente de l\'application de l\'ordinateur.</p>' : "") +
    (e.kind === "ent" ? '<button class="btn" type="button" data-x="rdv">' + ico("i-cal") + "Prendre rendez-vous au garage</button>" : ""),
    {secondary: canDone ? '<button class="btn' + (e.done ? "" : " primary") + '" type="button" data-x="obl">' + (e.done ? "Remettre à faire" : "Marquer fait") + "</button>" : "",
     onClick: async ev => { const b = ev.target.closest("[data-x]"); if (!b) return;
       if (b.dataset.x === "obl"){ closeSheet(); await sendOp("obligation", {key:e.key, fait:!e.done, date:today()}); }
       else if (b.dataset.x === "rdv") fEvenement(null, {type:"garage", equipement:e.eqId, titre:(e.mtype || "Entretien") + ", " + ((S.d.equipements.find(x => x.id === e.eqId) || {}).nom || ""), date:today(), heure:"08:00", fin:"09:00"}); }});
}
/* Entretien */
function fEntretien(eqId){
  const eqs = S.d.equipements.filter(e => e.statut !== "vendu"); if (!eqs.length){ toast("Ajoute d'abord ton camion dans l'application de l'ordinateur (Inventaire)."); return; }
  const e0 = eqs.find(e => e.id === eqId) || eqs[0], cpt0 = (S.d.comptes.find(c => c.sorte === "carte") || S.d.comptes[0] || {}).id || "__impaye";
  const body = '<label class="field"><span>Équipement</span><select class="ctl" id="n-eq">' + eqs.map(e => '<option value="' + esc(e.id) + '"' + (e.id === e0.id ? " selected" : "") + ">" + esc(e.nom) + "</option>").join("") + "</select></label>" +
    '<div class="field"><span>Type d\'entretien</span><div class="picks">' + ENT_TYPES.map(k => '<button type="button" class="pick" data-nt="' + esc(k) + '">' + esc(k) + "</button>").join("") + '</div><input class="ctl" id="n-type" maxlength="80" placeholder="Ou écris le type"></div>' +
    dateField("n-date") + '<div class="two"><label class="field"><span>Odomètre (km)</span><input class="ctl" id="n-odo" inputmode="numeric" value="' + esc(e0.odometre ? String(Math.round(e0.odometre)) : "") + '"></label><label class="field"><span>Garage</span><input class="ctl" id="n-four" maxlength="120" placeholder="Garage Tremblay"></label></div>' +
    '<label class="field"><span>Travaux faits</span><input class="ctl" id="n-desc" maxlength="200" placeholder="Ex. : Huile 5W30 et filtre"></label>' + photoField() +
    '<div class="field"><span>Montant total payé, taxes incluses</span><span class="money"><input id="n-mt" inputmode="decimal" placeholder="0,00"><span>$</span></span><p class="calc" id="n-calc">Laisse vide si rien n\'a été payé.</p></div>' +
    '<div class="field"><span>Payé avec</span><div class="picks">' + comptePicks(cpt0, "Pas encore payée") + "</div></div>" +
    '<div class="field"><span>Prochain entretien</span><div class="two"><input class="ctl" type="date" id="n-nd" aria-label="Date du prochain entretien"><input class="ctl" id="n-nk" inputmode="numeric" placeholder="ou à … km" aria-label="Kilométrage du prochain entretien"></div><div class="picks">' + [[6,"+ 6 mois"],[12,"+ 1 an"]].map(([m, l]) => '<button type="button" class="pick" data-nm="' + m + '">' + l + "</button>").join("") + [5000, 8000].map(k => '<button type="button" class="pick" data-nk="' + k + '">+ ' + k.toLocaleString("fr-CA") + " km</button>").join("") + "</div></div>";
  openSheet("Entretien", body, {primary:"Envoyer", state:{cpt:cpt0},
    ready: bindPhotos,
    onInput: e => { if (e.target.id === "n-mt"){ const a = num(e.target.value); if (isFinite(a) && a > 0){ const t = splitTaxes(a, defCode()); $("n-calc").textContent = fmt(t.ht) + " avant taxes + TPS " + fmt(t.tx) + " + TVQ " + fmt(t.tq) + ". La dépense sera inscrite dans tes livres."; } else $("n-calc").textContent = "Laisse vide si rien n'a été payé."; } },
    onClick: e => { if (dateClick(e)) return; const b = e.target.closest("button"); if (!b) return; const ds = b.dataset;
      if (ds.nt){ $("n-type").value = ds.nt; pressSet("[data-nt]", "data-nt", ds.nt); if (ds.nt === "Changement d'huile" && !$("n-nk").value && num($("n-odo").value) > 0) $("n-nk").value = String(Math.round(num($("n-odo").value) + 8000)); }
      else if (ds.cpt){ S.form.cpt = ds.cpt; pressSet("[data-cpt]", "data-cpt", ds.cpt); }
      else if (ds.nm){ const [y, m, d] = ($("n-date").value || today()).split("-").map(Number); $("n-nd").value = iso(new Date(y, m - 1 + Number(ds.nm), d)); }
      else if (ds.nk){ const o = num($("n-odo").value); $("n-nk").value = String(Math.round((isFinite(o) ? o : 0) + Number(ds.nk))); } },
    onSubmit: async () => {
      const type = $("n-type").value.trim(), date = $("n-date").value || today(), amt = num($("n-mt").value), odo = num($("n-odo").value), nk = num($("n-nk").value), eq = $("n-eq").value, four = $("n-four").value.trim(), imp = S.form.cpt === "__impaye";
      if (!type) return fail("Choisis le type d'entretien.");
      const en = {id: uid("en"), date, type, description:$("n-desc").value.trim(), odometre: isFinite(odo) ? Math.round(odo) : 0, fournisseur:four, montant: isFinite(amt) ? r2(amt) : 0, prochaineDate:$("n-nd").value, prochainKm: isFinite(nk) ? Math.round(nk) : 0, note:""};
      let dep = null; if (isFinite(amt) && amt > 0){ const t = splitTaxes(amt, defCode()); dep = {id: uid("t"), montant:t.ht, taxe:t.tx, tvq:t.tq, codeTaxe:defCode(), compte: imp ? "" : S.form.cpt, statut: imp ? "a-payer" : "regle", echeance: imp ? addDays(date, 30) : ""}; }
      const photos = (S.form && S.form.photos) || []; closeSheet(); toast("Entretien envoyé"); await sendOp("entretien", {equipement:eq, entretien:en, depense:dep}, photos); }});
}

/* ===== Factures et devis ===== */
/* Les nouveautés (types de frais, rabais, taxes incluses) attendent que l'ordinateur soit en version 3.7 */
const telDocV2 = () => { const t = (S.d && S.d.telephone) || {}; return Array.isArray(t.ops) && t.ops.includes("doc-v2"); };
function fDoc(kind, doc, p){
  p = p || {}; const isF = kind === "facture", r = R(), v2 = telDocV2(), titre = docTitre(kind);
  const lignes = doc ? clone(doc.lignes) : (p.lignes ? clone(p.lignes) : [{type:"service", description:"", qte:1, unite:"", prix:0}]);
  lignes.forEach(l => { if (!l.type) l.type = "service"; });
  const cli = S.d.clients.find(c => norm(c.nom) === norm(doc ? doc.client : p.client || "")) || {};
  const date0 = doc ? doc.date : today(), n0 = String(doc ? daysBetween(doc.date, doc.echeance || doc.date) : (isF ? (r.termes != null ? r.termes : 30) : (r.validiteDevis || 30)));
  const terms = isF ? TERMS_F : TERMS_D, termVal = terms.some(t => t[0] === n0) ? n0 : "autre";
  const prods = S.d.produits, tfs = r.tarifs || [], ttc0 = v2 && !!(doc ? doc.taxesIncluses : (p.taxesIncluses != null ? p.taxesIncluses : r.docTTC));
  const addOpts = '<option value="">+ Ajouter une ligne…</option><optgroup label="Nouvelle ligne">' + LT.filter(t => t.k !== "rabais" || v2).map(t => '<option value="t:' + t.k + '">' + esc(t.l) + "</option>").join("") + "</optgroup>" +
    (tfs.length ? '<optgroup label="Tarifs enregistrés">' + tfs.map(t => '<option value="f:' + esc(t.id) + '">' + esc(t.description + " · " + fmt(t.prix) + (t.unite ? " / " + t.unite : "")) + "</option>").join("") + "</optgroup>" : "") +
    (prods.length ? '<optgroup label="Produits du stock">' + prods.map(x => '<option value="p:' + esc(x.id) + '">' + esc(x.nom + " (" + fq(stockOf(x)) + ")") + "</option>").join("") + "</optgroup>" : "");
  const body = '<label class="field"><span>Client</span><input class="ctl" id="d-cli" list="d-dl" maxlength="120" autocomplete="off" value="' + esc(doc ? doc.client : p.client || "") + '" placeholder="Nom du client"><datalist id="d-dl">' + S.d.clients.map(c => '<option value="' + esc(c.nom) + '">').join("") + "</datalist></label>" +
    '<details class="more"><summary>Coordonnées du client</summary><div><label class="field"><span>Téléphone</span><input class="ctl" id="d-tel" type="tel" value="' + esc(cli.telephone || "") + '"></label><label class="field"><span>Courriel</span><input class="ctl" id="d-mail" type="email" value="' + esc(cli.courriel || "") + '"></label><label class="field"><span>Adresse</span><textarea class="ctl" id="d-adr" rows="2">' + esc(cli.adresse || "") + "</textarea></label></div></details>" +
    '<div class="two"><label class="field"><span>Date</span><input class="ctl" type="date" id="d-date" value="' + esc(date0) + '"></label><label class="field"><span>' + (isF ? "Payable" : "Valide") + '</span><select class="ctl" id="d-terms">' + terms.map(([k, l]) => '<option value="' + k + '"' + (k === termVal ? " selected" : "") + ">" + esc(l) + "</option>").join("") + "</select></label></div>" +
    '<label class="field" id="d-ech-f"' + (termVal === "autre" ? "" : " hidden") + '><span>' + (isF ? "Échéance" : "Valide jusqu'au") + '</span><input class="ctl" type="date" id="d-ech" value="' + esc(doc ? doc.echeance : addDays(date0, Number(n0) || 0)) + '"></label>' +
    '<label class="field"><span>Description des travaux (facultatif)</span><textarea class="ctl" id="d-trav" rows="2" maxlength="1500" placeholder="Ex. : Émondage de 3 érables en façade et ramassage des branches">' + esc(doc ? doc.travaux || "" : p.travaux || "") + "</textarea></label>" +
    '<div class="two"><label class="field"><span>Lieu des travaux</span><input class="ctl" id="d-lieu" maxlength="200" value="' + esc(doc ? doc.lieu || "" : p.lieu || "") + '" placeholder="Si différent"></label><label class="field"><span>' + (isF ? "Date des travaux" : "Date prévue") + '</span><input class="ctl" type="date" id="d-dtrav" value="' + esc(doc ? doc.dateTravaux || "" : p.dateTravaux || "") + '"></label></div>' +
    '<div class="field"><span>Services et frais</span>' + (v2 ? '<div class="picks" style="margin-bottom:8px"><button type="button" class="pick" data-ttc="0" aria-pressed="' + !ttc0 + '">Prix avant taxes</button><button type="button" class="pick" data-ttc="1" aria-pressed="' + ttc0 + '">Prix taxes incluses</button></div>' : "") +
    '<div id="d-lines" style="display:flex;flex-direction:column;gap:8px"></div><select class="ctl" id="d-add" style="margin-top:8px">' + addOpts + "</select></div>" +
    '<div class="tot" id="d-tot"></div>' +
    '<label class="field"><span>Taxes</span><select class="ctl" id="d-code">' + TAXCODES.map(c => '<option value="' + c + '"' + ((doc ? doc.codeTaxe : (p.codeTaxe || (inscrit() ? defCode() : "AUCUNE"))) === c ? " selected" : "") + ">" + esc(taxLabel(c)) + "</option>").join("") + "</select></label>" +
    (isF && !doc ? '<div class="field"><span>Paiement</span><div class="picks"><button type="button" class="pick" data-dpay="" aria-pressed="true">' + ico("i-cal") + "À encaisser</button>" + S.d.comptes.filter(c => c.sorte === "banque" || c.sorte === "caisse").map(c => '<button type="button" class="pick" data-dpay="' + esc(c.id) + '" aria-pressed="false">' + ico("i-bank") + "Déjà payée : " + esc(c.nom) + "</button>").join("") + "</div></div>" : "") +
    '<label class="field"><span>Message sur le document</span><textarea class="ctl" id="d-msg" rows="2" maxlength="600">' + esc(doc ? doc.message || "" : (p.message != null ? p.message : r.messageFacture || "")) + "</textarea></label>" +
    (v2 ? "" : '<p class="hint">Les rabais et les prix taxes incluses seront offerts quand l\'application de l\'ordinateur aura été ouverte une fois après sa mise à jour.</p>') +
    '<p class="hint" id="d-hint" hidden></p>';
  const types = LT.filter(t => t.k !== "rabais" || v2 || lignes.some(l => l.type === "rabais"));
  const mtTxt = l => { const m = ligneMt(l); return (m < 0 ? "−" : "") + fmt(Math.abs(m)); };
  const linesHTML = () => S.form.lignes.map((l, i) => { const t = LTM[ligneType(l)];
    return '<div class="line' + (l.type === "rabais" ? " rabais" : "") + '" data-li="' + i + '"><div class="row" style="justify-content:space-between"><select class="ctl lt-sel" data-lf="type" aria-label="Type">' + types.map(x => '<option value="' + x.k + '"' + (x.k === t.k ? " selected" : "") + ">" + esc(x.l) + "</option>").join("") + '</select><button class="icon-btn" type="button" data-dl="rm" data-i="' + i + '" aria-label="Retirer la ligne"' + (S.form.lignes.length < 2 ? " disabled" : "") + ">" + ico("i-x") + "</button></div>" +
      '<textarea class="ctl" rows="2" data-lf="description" placeholder="' + esc(t.ph) + '" aria-label="Description">' + esc(l.description) + "</textarea>" +
      '<div class="three q3"><label class="field"><span>Qté</span><input class="ctl" data-lf="qte" inputmode="decimal" value="' + esc(fq(l.qte)) + '"></label><label class="field"><span>Unité</span><input class="ctl" data-lf="unite" list="d-units" maxlength="12" value="' + esc(l.unite || "") + '"></label><label class="field"><span>' + (S.form.ttc ? "Prix (tx incl.)" : "Prix unitaire") + '</span><input class="ctl" data-lf="prix" inputmode="decimal" value="' + (l.prix ? esc(n2s(l.prix)) : "") + '" placeholder="0,00"></label></div>' +
      '<span class="muted small" data-amt="' + i + '">' + mtTxt(l) + "</span></div>"; }).join("") + '<datalist id="d-units">' + LUNITES.map(u => '<option value="' + esc(u) + '">').join("") + "</datalist>";
  const recalc = () => { const t = docTotals({lignes:S.form.lignes, codeTaxe:$("d-code").value, taxesIncluses:S.form.ttc});
    $("d-tot").innerHTML = "<div><span>" + (t.ttc ? "Montant avant taxes" : "Sous-total") + "</span><span>" + fmt(t.st) + "</span></div>" + taxLines($("d-code").value, t).map(([k, v]) => '<div class="muted"><span>' + esc(k) + "</span><span>" + fmt(v) + "</span></div>").join("") + '<div class="g"><span>Total' + (t.ttc ? " (taxes incl.)" : "") + "</span><span>" + fmt(t.total) + "</span></div>";
    S.form.lignes.forEach((l, i) => { const a = document.querySelector('[data-amt="' + i + '"]'); if (a) a.textContent = mtTxt(l); });
    const msgs = []; if (isF && t.total >= 100 && (t.tx || t.tq) && (!r.noTPS || (t.tq && !r.noTVQ))) msgs.push("Ajoute tes numéros de TPS et de TVQ dans les Réglages de l'application de l'ordinateur : ils doivent figurer sur les factures de 100 $ et plus."); $("d-hint").innerHTML = msgs.map(esc).join("<br>"); $("d-hint").hidden = !msgs.length; return t; };
  const drawLines = () => { $("d-lines").innerHTML = linesHTML(); recalc(); };
  const prixPour = (prix, ttc) => { const [a, b] = taxRates($("d-code").value || "AUCUNE"); if (!!ttc === !!S.form.ttc || !(a || b)) return r2(prix); return ttc ? r2(prix * 100 / (100 + a + b)) : r2(prix * (100 + a + b) / 100); };
  const addLine = ln => { const L = S.form.lignes; if (L.length === 1 && !L[0].description && !L[0].prix) L[0] = ln; else L.push(ln); drawLines(); if (!ln.description){ const t = document.querySelectorAll('[data-lf="description"]'); t[t.length - 1].focus(); } };
  const title = doc ? titre + " " + doc.numero : isF ? (p.fromDevis ? "Facture " + docGenre("devis").de : "Nouvelle facture") : (titre === "Devis" ? "Nouveau devis" : "Nouvelle " + titre.toLowerCase());
  openSheet(title, body, {primary:"Enregistrer", state:{lignes, pay:"", ttc:ttc0},
    secondary:'<button class="btn" type="button" data-dsave="send">' + ico("i-send") + "Enregistrer et envoyer</button>",
    ready: drawLines,
    onInput: e => { const f = e.target.closest("[data-lf]"); if (f && f.dataset.lf !== "type"){ const l = S.form.lignes[Number(f.closest("[data-li]").dataset.li)]; if (f.dataset.lf === "description") l.description = f.value; else if (f.dataset.lf === "unite") l.unite = f.value; else { const v = num(f.value); l[f.dataset.lf] = isFinite(v) ? v : 0; } recalc(); } },
    onChange: e => { const id = e.target.id;
      if (id === "d-code") recalc();
      if (e.target.dataset && e.target.dataset.lf === "type"){ const l = S.form.lignes[Number(e.target.closest("[data-li]").dataset.li)], was = LTM[ligneType(l)]; l.type = e.target.value; if (!l.unite || l.unite === was.u) l.unite = (LTM[l.type] || {}).u || ""; drawLines(); }
      if (id === "d-terms" || id === "d-date"){ const t = $("d-terms").value; $("d-ech-f").hidden = t !== "autre"; if (t !== "autre") $("d-ech").value = addDays($("d-date").value || today(), Number(t) || 0); }
      if (id === "d-cli"){ const c = S.d.clients.find(x => norm(x.nom) === norm(e.target.value)) || {}; $("d-tel").value = c.telephone || ""; $("d-mail").value = c.courriel || ""; $("d-adr").value = c.adresse || ""; }
      if (id === "d-add"){ const v = e.target.value; e.target.value = ""; if (!v) return; const k = v.slice(2);
        if (v[0] === "t") addLine({type:k, description:"", qte:1, unite:(LTM[k] || {}).u || "", prix:0});
        else if (v[0] === "f"){ const t = tfs.find(x => x.id === k); if (t) addLine({type:t.type || "service", description:t.description, qte:1, unite:t.unite || "", prix:prixPour(t.prix, t.ttc)}); }
        else if (v[0] === "p"){ const x = S.d.produits.find(q => q.id === k); if (x) addLine({type:"materiaux", description:x.nom + (x.code ? " (" + x.code + ")" : ""), qte:1, unite:x.unite || "unité", prix:prixPour(Number(x.prix) || 0, false), produit:x.id}); } } },
    onClick: e => { const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.dl === "rm"){ S.form.lignes.splice(Number(b.dataset.i), 1); drawLines(); }
      else if (b.dataset.ttc != null){ S.form.ttc = b.dataset.ttc === "1"; pressSet("[data-ttc]", "data-ttc", b.dataset.ttc); drawLines(); }
      else if (b.dataset.dpay != null){ S.form.pay = b.dataset.dpay; pressSet("[data-dpay]", "data-dpay", b.dataset.dpay); }
      else if (b.dataset.dsave){ S.form.withSend = true; $("sheet-f").requestSubmit(); } },
    onSubmit: async () => {
      const client = $("d-cli").value.trim(), date = $("d-date").value; if (!client) return fail("Entre le nom du client."); if (!date) return fail("Choisis la date.");
      const L = S.form.lignes.map(l => { const x = {type:ligneType(l), description:String(l.description || "").trim(), qte:Number(l.qte) || 0, unite:String(l.unite || "").trim(), prix:r2(l.prix)}; if (l.produit) x.produit = l.produit; return x; }).filter(l => l.description || l.prix);
      if (!L.length) return fail("Ajoute au moins une ligne avec une description et un prix."); if (L.some(l => !l.description)) return fail("Chaque ligne doit avoir une description.");
      const t = $("d-terms").value, ech = t === "autre" ? ($("d-ech").value || date) : addDays(date, Number(t) || 0);
      const data = Object.assign({}, doc || {id: uid(isF ? "fa" : "dv"), numero: nextNum(kind, date)}, {date, echeance: ech < date ? date : ech, client, lignes:L, codeTaxe:$("d-code").value, message:$("d-msg").value.trim(), clientInfo:{telephone:$("d-tel").value.trim(), courriel:$("d-mail").value.trim(), adresse:$("d-adr").value.trim()},
        travaux:$("d-trav").value.trim(), lieu:$("d-lieu").value.trim(), dateTravaux:$("d-dtrav").value || ""});
      if (S.form.ttc) data.taxesIncluses = true; else delete data.taxesIncluses;
      ["travaux","lieu","dateTravaux"].forEach(k => { if (!data[k]) delete data[k]; });
      if (isF){ data.categorie = (doc && doc.categorie) || "ventes"; if (p.fromDevis) data.devis = p.fromDevis; if (!doc) data.paye = S.form.pay || ""; }
      else if (!doc) data.statut = "ouvert";
      const withSend = S.form.withSend; if (!withSend) closeSheet(); toast(titre + " " + data.numero + (doc ? " modifié" + (isF || titre !== "Devis" ? "e" : "") : " envoyé" + (isF || titre !== "Devis" ? "e" : "") + " à tes livres"));
      await sendOp(kind, data);
      S.vt = isF ? "factures" : "devis"; if (isF) S.vtF = "tous"; if (S.tab === "ventes") vVentes();
      if (withSend){ const fresh = (isF ? S.d.factures : S.d.devis).find(x => x.id === data.id) || Object.assign({}, data, {clientId: cli.id || ""}); sendDoc(kind, fresh); return false; } }});
}
function docBody(kind, x){
  const t = docTotals(x), isF = kind === "facture", s = isF ? facStatus(x) : devStatus(x), c = clientOf(x) || {}, G = docGroupes(x);
  return '<div><span class="eyebrow">' + esc(docTitre(kind) + " · " + dLong(x.date)) + "</span><h2>" + esc(x.numero + " · " + x.client) + '</h2><div class="row" style="margin-top:6px"><span class="chip ' + s.cls + '">' + esc(s.l) + '</span><span class="muted small">' + esc(isF ? (x.echeance && x.echeance > x.date ? "Payable d'ici le " + dLong(x.echeance) : "Payable à réception") : "Valide jusqu'au " + dLong(x.echeance)) + "</span></div></div>" +
    (x.travaux ? '<p class="small">' + esc(x.travaux) + "</p>" : "") + (x.lieu ? '<p class="muted small">Lieu : ' + esc(x.lieu) + "</p>" : "") +
    '<table class="doc-lines">' + G.map(g => (G.length > 1 ? '<tr><td colspan="2" class="grp">' + esc(g.t.g) + "</td></tr>" : "") + g.lignes.map(l => { const m = ligneMt(l); return "<tr><td>" + esc(l.description).replace(/\n/g, "<br>") + '<br><span class="muted small">' + esc(qteTxt(l) + " × " + fmt(l.prix)) + '</span></td><td class="n">' + (m < 0 ? "−" : "") + fmt(Math.abs(m)) + "</td></tr>"; }).join("")).join("") + "</table>" +
    '<div class="tot"><div><span>' + (t.ttc ? "Montant avant taxes" : "Sous-total") + "</span><span>" + fmt(t.st) + "</span></div>" + taxLines(x.codeTaxe, t).map(([k, v]) => '<div class="muted"><span>' + esc(k) + "</span><span>" + fmt(v) + "</span></div>").join("") + '<div class="g"><span>Total' + (t.ttc ? " (taxes incl.)" : "") + "</span><span>" + fmt(t.total) + "</span></div></div>" +
    (c.telephone ? '<div class="copy"><span>' + esc(c.telephone) + '</span><a class="btn sm" href="tel:' + esc(c.telephone.replace(/[^\d+]/g, "")) + '">Appeler</a><button class="btn sm" type="button" data-copy="' + esc(c.telephone) + '">Copier</button></div>' : "") +
    (c.courriel ? '<div class="copy"><span>' + esc(c.courriel) + '</span><button class="btn sm" type="button" data-copy="' + esc(c.courriel) + '">Copier</button></div>' : "");
}
/* Envoyer une facture ou une soumission : PDF ou image (courriel, texto, Messenger, Snapchat…) */
function sendDoc(kind, x){
  const isF = kind === "facture", G = docGenre(kind), c = clientOf(x) || {}, tel = String(c.telephone || "").replace(/[^\d+]/g, ""), share = !!(navigator.canShare && navigator.share);
  const opt = (k, icon, t, s) => '<button type="button" class="item send-opt" data-send="' + k + '">' + ico(icon) + '<span class="t"><b>' + esc(t) + "</b><small>" + esc(s) + "</small></span></button>";
  openSheet("Envoyer " + G.la + " " + x.numero, '<p class="muted small">' + esc(x.client) + " · " + esc(fmt(docTotals(x).total)) + '</p><label class="field"><span>Message</span><textarea class="ctl" id="snd-msg" rows="6">' + esc(docMessage(kind, x)) + "</textarea></label>" +
    '<div class="list">' + (share ? opt("img", "i-image", "Envoyer en image", "Texto, Snapchat, Messenger, Instagram…") + opt("pdf", "i-pdf", "Envoyer le PDF", "Courriel (Gmail), Messenger, WhatsApp, Drive…") : "") +
    (tel ? opt("sms", "i-phone", "Texto à " + c.telephone, "Le message seulement ; ajoute l'image avec « Envoyer en image »") : "") +
    opt("copy", "i-copy", "Copier le message", "Pour le coller où tu veux") + opt("save", "i-download", "Enregistrer le PDF", "Dans Téléchargements") + "</div>",
    {onClick: async ev => { const b = ev.target.closest("[data-send]"); if (!b) return; const how = b.dataset.send, text = $("snd-msg").value, name = fileSafe(x.numero + " " + x.client), subj = docTitre(kind) + " " + x.numero + (R().nom ? " · " + R().nom : "");
      const mark = () => { if (!(isF ? x.envoyeeLe : x.envoyeLe)) sendOp("envoye", {kind, id:x.id, date:today()}); };
      try { b.disabled = true;
        if (how === "copy"){ await copyTxt(text); return; }
        if (how === "sms"){ location.href = "sms:" + tel + "?body=" + encodeURIComponent(text); mark(); return; }
        const logo = await phoneLogo();
        if (how === "save"){ const f = new File([docPDF(kind, x, logo)], name + ".pdf", {type:"application/pdf"}), url = URL.createObjectURL(f), a = document.createElement("a"); a.href = url; a.download = f.name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 60000); toast("PDF enregistré dans Téléchargements."); return; }
        const files = how === "img" ? await docImages(kind, x, logo) : [new File([docPDF(kind, x, logo)], name + ".pdf", {type:"application/pdf"})];
        if (!navigator.canShare({files})) throw new Error("ce téléphone ne partage pas ce fichier");
        if (how === "pdf" && c.courriel){ try { await navigator.clipboard.writeText(c.courriel); toast("Courriel du client copié : colle-le dans « À »"); } catch(e){} }
        await navigator.share({files, title: subj, text}); mark(); closeSheet();
      } catch(e){ if (e && e.name === "AbortError") return; toast("Envoi impossible : " + ((e && e.message) || "erreur")); }
      finally { b.disabled = false; } }});
}
async function copyTxt(v){ try { await navigator.clipboard.writeText(v); toast("Copié"); } catch(e){ toast("Copie impossible : sélectionne le texte."); } }
function openFacture(id){
  const f = S.d.factures.find(x => x.id === id); if (!f) return; const t = S.tmap[f.transaction];
  openSheet("Facture " + f.numero, docBody("facture", f) + '<p class="muted small">Le PDF est aussi créé sur l\'ordinateur, dans le dossier factures, quand il reçoit la facture.</p>',
    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-send") + "Envoyer</button>" + (f.statut !== "annulee" ? '<button class="btn" type="button" data-x="mod">Modifier</button>' : "") + (t && unpaid(t) ? '<button class="btn primary" type="button" data-x="pay">Encaisser</button>' : ""),
     onClick: ev => { const b = ev.target.closest("button"); if (!b) return; if (b.dataset.copy) return copyTxt(b.dataset.copy);
       const x = b.dataset.x; if (x === "pdf") sendDoc("facture", f); else if (x === "mod") fDoc("facture", f); else if (x === "pay") fEncaisser(f); }});
}
function openDevis(id){
  const v = S.d.devis.find(x => x.id === id); if (!v) return; const s = devStatus(v);
  openSheet(docTitre("devis") + " " + v.numero, docBody("devis", v) + (s.k !== "facture" ? '<div class="row"><button class="btn sm" type="button" data-x="accepte">Accepté par le client</button><button class="btn sm" type="button" data-x="refuse">Refusé</button></div>' : ""),
    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-send") + "Envoyer</button>" + (s.k !== "facture" ? '<button class="btn" type="button" data-x="mod">Modifier</button><button class="btn primary" type="button" data-x="fac">Facturer</button>' : ""),
     onClick: async ev => { const b = ev.target.closest("button"); if (!b) return; if (b.dataset.copy) return copyTxt(b.dataset.copy);
       const x = b.dataset.x; if (x === "pdf") sendDoc("devis", v); else if (x === "mod") fDoc("devis", v); else if (x === "fac") fDoc("facture", null, {client:v.client, lignes:v.lignes, codeTaxe:v.codeTaxe, message:v.message, fromDevis:v.id, taxesIncluses:!!v.taxesIncluses, travaux:v.travaux || "", lieu:v.lieu || "", dateTravaux:v.dateTravaux || ""});
       else if (x === "accepte" || x === "refuse"){ closeSheet(); toast("Devis " + (x === "accepte" ? "accepté" : "refusé")); await sendOp("devis-statut", {id:v.id, statut:x}); } }});
}
function openClient(id){
  const c = S.d.clients.find(x => x.id === id); if (!c) return;
  const fs = S.d.factures.filter(f => f.clientId === c.id || norm(f.client) === norm(c.nom)).sort((a, b) => b.date.localeCompare(a.date));
  openSheet(c.nom, (c.telephone ? '<div class="copy"><span>' + esc(c.telephone) + '</span><a class="btn sm" href="tel:' + esc(c.telephone.replace(/[^\d+]/g, "")) + '">Appeler</a><button class="btn sm" type="button" data-copy="' + esc(c.telephone) + '">Copier</button></div>' : "") + (c.courriel ? '<div class="copy"><span>' + esc(c.courriel) + '</span><button class="btn sm" type="button" data-copy="' + esc(c.courriel) + '">Copier</button></div>' : "") +
    (c.adresse ? '<div class="copy"><span>' + esc(c.adresse) + '</span><a class="btn sm" href="' + esc(mapURL(c.adresse)) + '" target="_blank" rel="noopener">Itinéraire</a></div>' : "") +
    (fs.length ? '<div class="list">' + fs.map(f => { const s = facStatus(f); return '<button class="item" type="button" data-f="' + esc(f.id) + '"><span class="t"><b>' + esc(f.numero) + "</b><small>" + esc(dShort(f.date)) + '</small></span><span class="v">' + fmt(docTotal("facture", f)) + '<span class="chip ' + s.cls + '">' + esc(s.l) + "</span></span></button>"; }).join("") + "</div>" : '<p class="muted small">Aucune facture pour ce client.</p>'),
    {secondary:'<button class="btn" type="button" data-x="devis">Devis</button><button class="btn primary" type="button" data-x="facture">Facture</button>',
     onClick: ev => { const b = ev.target.closest("button"); if (!b) return; if (b.dataset.copy) return copyTxt(b.dataset.copy); if (b.dataset.f) return openFacture(b.dataset.f); if (b.dataset.x) fDoc(b.dataset.x, null, {client:c.nom}); }});
}
function fEncaisser(f){
  const t = S.tmap[f.transaction]; if (!t) return; const def = (S.d.comptes.find(c => c.sorte === "banque") || S.d.comptes[0] || {}).id;
  openSheet("Encaisser " + f.numero, '<p><b>' + fmt(txTotal(t)) + "</b> de " + esc(f.client) + '</p><div class="field"><span>Déposé dans</span><div class="picks">' + comptePicks(def, "") + "</div></div>" + dateField("p-date"),
    {primary:"Enregistrer le paiement", state:{cpt:def}, onClick: e => { if (dateClick(e)) return; const k = e.target.closest("[data-cpt]"); if (k){ S.form.cpt = k.dataset.cpt; pressSet("[data-cpt]", "data-cpt", k.dataset.cpt); } },
     onSubmit: async () => { const compte = S.form.cpt; if (!compte) return fail("Choisis le compte."); const date = $("p-date").value || today(); closeSheet(); toast("Paiement de " + fmt(txTotal(t)) + " envoyé"); await sendOp("paiement", {transaction:t.id, date, compte}); }});
}
/* PDF : créé sur le téléphone, puis partagé (texto, courriel…) ou enregistré */
async function phoneLogo(){
  if (S.logo !== undefined) return S.logo; S.logo = null;
  const p = R().logo; if (!p) return null;
  const saved = await IDB.get("__logo");
  if (saved && saved.src === p){ S.logo = {w:saved.w, h:saved.h, data:saved.data}; return S.logo; }
  if (!S.ids || !S.ids.docs || !online() || !tokOk()) return null;
  try {
    const L = await list("name = '" + qs(p.split("/").pop()) + "' and " + inP(S.ids.docs), 3); if (!L[0]) return null;
    const bl = await downloadBlob(L[0].id), url = URL.createObjectURL(bl), img = new Image(); img.src = url; await img.decode();
    const sc = Math.min(1, 700 / Math.max(img.naturalWidth, img.naturalHeight)), w = Math.max(1, Math.round(img.naturalWidth * sc)), h = Math.max(1, Math.round(img.naturalHeight * sc));
    const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, w, h); x.drawImage(img, 0, 0, w, h);
    const b = await new Promise(res => c.toBlob(res, "image/jpeg", 0.92)); S.logo = b ? {w, h, data:new Uint8Array(await b.arrayBuffer())} : null;
    if (S.logo) IDB.put("__logo", Object.assign({src:p}, S.logo)).catch(() => {});
  } catch(e){ S.logo = null; }
  return S.logo;
}
async function savePDF(kind, x){
  try {
    const name = fileSafe(x.numero + " " + x.client) + ".pdf";
    const file = new File([docPDF(kind, x, await phoneLogo())], name, {type:"application/pdf"});
    if (navigator.canShare && navigator.canShare({files:[file]})){
      try { await navigator.share({files:[file], title:name}); return; }
      catch(e){ if (e && e.name === "AbortError") return; }
    }
    const url = URL.createObjectURL(file), a = document.createElement("a"); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    toast("PDF enregistré dans Téléchargements.");
  } catch(e){ toast("PDF non créé : " + ((e && e.message) || "erreur")); }
}

/* ===== Démarrage ===== */
(function start(){
  /* La version complète demande une connexion Google : on la fait ici (adresse autorisée), puis on y retourne */
  const qp = new URLSearchParams(location.search);
  if (qp.get("auth")){
    const r = qp.get("retour") || ""; LS.set("retour", /^complet\.html(#[\w-]*)?$/.test(r) ? r : "");
    try { history.replaceState(null, "", location.pathname); } catch(e){}
    if (online() && clientId()){ authRedirect(qp.get("auth") === "2"); return; }
  }
  const auth = readAuthHash();
  if (auth && auth.ok && LS.get("retour", "")){ const r = LS.get("retour", ""); LS.set("retour", ""); location.replace(r); return; }
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {}); } catch(e){}
  S.pending = LS.get("pending", []).filter(p => p && p.op && p.op.id).map(p => (p.etat === "envoi" || p.etat === "verifier") ? Object.assign(p, {etat:"attente", tries:Math.max(1, p.tries || 0)}) : p);
  const cached = LS.get("base", null); S.lastSync = LS.get("lastSync", "");
  if (cached){ S.base = normalize(cached); S.conn = "ok"; recompute(); }
  if (auth && auth.err){ S.connErr = "login"; if (!S.d) S.conn = "login"; }
  if (auth && auth.ok) whoAmI();
  const h = location.hash.slice(1); showTab(TABS.includes(h) ? h : "accueil");
  if (h === "ajout-trajet" && S.d) setTimeout(() => fTrajet(), 60);
  syncLabel();
  syncAll(false, "start");
  if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register("sw.js").catch(e => console.warn("sw", e));
  window.addEventListener("online", () => { render(); syncLabel(); syncSoon(800); });
  window.addEventListener("offline", () => { render(); syncLabel(); });
  setInterval(() => {
    if (document.visibilityState !== "visible" || syncing || !$("sheet").hidden) return;
    const queued = S.pending.some(p => p.etat === "attente"), old = Date.now() - new Date(S.lastSync || 0).getTime() > 90000;
    if (online() && (queued || (old && tokOk()))) syncAll(false, "minuterie");
  }, 30000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !syncing && (S.pending.some(p => p.etat === "attente") || Date.now() - new Date(S.lastSync || 0).getTime() > 30000)) syncAll(false, "retour");
  });
})();
