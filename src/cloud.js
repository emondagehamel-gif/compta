/* ===== Version complète sur le téléphone : livres lus dans Google Drive (mode nuage) =====
   Sur un téléphone (ou depuis l'adresse GitHub), l'application ne peut pas ouvrir le dossier de l'ordinateur.
   Elle lit registre.json dans Google Drive et chaque modification devient un changement « telephone/op-….json »
   que l'application de l'ordinateur inscrit dans les livres, comme pour l'app terrain. Les deux partagent la même
   connexion Google, la même file d'attente et les mêmes photos en attente (même origine). */
const CLOUD = !window.showDirectoryPicker || /(^|\.)github\.io$/.test(location.hostname) || /[?&]nuage=1/.test(location.search) || window.__NUAGE === true;
const NU = {base:null, pending:[], ids:null, syncing:false, last:"", err:"", timer:null, fold:{}, blobs:{}};
const NU_API = window.__GAPI || "https://www.googleapis.com", NU_FOLDER = "application/vnd.google-apps.folder";
const LSN = {get(k, d){ try { const v = localStorage.getItem("cm-" + k); return v == null ? d : JSON.parse(v); } catch(e){ return d; } }, set(k, v){ try { localStorage.setItem("cm-" + k, JSON.stringify(v)); } catch(e){} }};
const nuOnline = () => navigator.onLine !== false;
const nuTok = () => LSN.get("tok", null);
const nuTokOk = m => { const t = nuTok(); return !!(t && t.t && t.exp - Date.now() > (m || 60000)); };
const nuQ = s => String(s).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
const nuInP = id => "'" + nuQ(id) + "' in parents";
/* La connexion Google se fait par l'app terrain (adresse autorisée dans Google Cloud), puis revient ici. */
function nuLogin(interactive){ LSN.set("authTry", Date.now()); location.assign("./?auth=" + (interactive ? "2" : "1") + "&retour=" + encodeURIComponent("complet.html" + (location.hash || ""))); }
async function nuApi(path, o){
  o = o || {};
  if (!nuOnline()) throw {code:"hors-reseau"};
  if (!nuTokOk(5000)) throw {code:"login"};
  let r;
  try { r = await fetch((o.upload ? NU_API + "/upload" : NU_API) + path, {method:o.method || "GET", headers:Object.assign({Authorization:"Bearer " + nuTok().t}, o.headers || {}), body:o.body, cache:"no-store"}); }
  catch(e){ throw {code:"reseau"}; }
  if (r.status === 401){ LSN.set("tok", null); throw {code:"login"}; }
  if (!r.ok){ let m = ""; try { const j = await r.json(); m = (j.error && j.error.message) || ""; } catch(e){} throw {code: r.status === 403 && /insufficient|scope/i.test(m) ? "login" : (r.status >= 500 || r.status === 429 || r.status === 403) ? "reseau" : "drive", message: m || "Erreur " + r.status}; }
  return o.raw ? r : r.json();
}
async function nuList(q, n){
  const p = new URLSearchParams({q: q + " and trashed = false", pageSize:String(n || 100), fields:"files(id,name,mimeType,modifiedTime,parents,size)", orderBy:"modifiedTime desc", spaces:"drive"});
  const r = await nuApi("/drive/v3/files?" + p.toString());
  return (r.files || []).map(f => ({id:f.id, title:f.name, mimeType:f.mimeType, modifiedTime:f.modifiedTime, size:Number(f.size) || 0}));
}
async function nuSub(root, name){ const L = await nuList("name = '" + nuQ(name) + "' and mimeType = '" + NU_FOLDER + "' and " + nuInP(root), 5); return L[0] ? L[0].id : ""; }
async function nuReg(root){ const L = (await nuList("name = 'registre.json' and " + nuInP(root), 10)).filter(f => f.mimeType !== NU_FOLDER); return L[0] || null; }
async function nuFindIds(){
  const c = LSN.get("ids", null);
  if (c && c.root && await nuReg(c.root)) return c;
  for (const f of await nuList("name = 'Comptabilite' and mimeType = '" + NU_FOLDER + "'", 30)){ if (await nuReg(f.id)) return {root:f.id, nom:f.title}; }
  return null;
}
async function nuExists(parent, name){ return (await nuList("name = '" + nuQ(name) + "' and " + nuInP(parent), 1)).length > 0; }
async function nuDownload(id){ return (await nuApi("/drive/v3/files/" + encodeURIComponent(id) + "?alt=media", {raw:true})).blob(); }
async function nuCreate(name, parent, blob, type){
  const b = "cmpt" + Math.random().toString(36).slice(2), meta = JSON.stringify({name, parents:[parent], mimeType:type});
  const body = new Blob(["--" + b + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + meta + "\r\n--" + b + "\r\nContent-Type: " + type + "\r\n\r\n", blob, "\r\n--" + b + "--\r\n"]);
  return nuApi("/drive/v3/files?uploadType=multipart&fields=id,name", {upload:true, method:"POST", headers:{"Content-Type":"multipart/related; boundary=" + b}, body});
}
/* Photos et fichiers en attente d'envoi : même base que l'app terrain ; fichiers déjà vus : cache local */
function nuDB(name, store){ return new Promise((res, rej) => { const r = indexedDB.open(name, 1); r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains(store)) r.result.createObjectStore(store); }; r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }); }
async function nuIdb(name, store, mode, fn){ const db = await nuDB(name, store); return new Promise((res, rej) => { const tx = db.transaction(store, mode), q = fn(tx.objectStore(store)); tx.oncomplete = () => res(q && q.result); tx.onerror = () => rej(tx.error); tx.onabort = () => rej(tx.error); }); }
const nuPhotos = {get: k => nuIdb("comptabilite", "photos", "readonly", s => s.get(k)).catch(() => undefined), put: (k, v) => nuIdb("comptabilite", "photos", "readwrite", s => s.put(v, k)), del: k => nuIdb("comptabilite", "photos", "readwrite", s => s.delete(k)).catch(() => {})};
const nuCache = {get: k => nuIdb("comptabilite-fichiers", "f", "readonly", s => s.get(k)).catch(() => undefined), put: (k, v) => nuIdb("comptabilite-fichiers", "f", "readwrite", s => s.put(v, k)).catch(() => {}), del: k => nuIdb("comptabilite-fichiers", "f", "readwrite", s => s.delete(k)).catch(() => {})};

function nuLabel(op){
  const x = op.data || {};
  return ({patch: x.msg || "Modification", fichier: "Fichier : " + String(x.to || "").split("/").pop(), deplacer: "Document classé", "fichier-suppr": "Document supprimé"})[op.type] || op.type;
}
function nuSave(){ LSN.set("pending", NU.pending.map(p => ({op:p.op, etat:p.etat, label:p.label, err:p.err || "", tries:p.tries || 0}))); }
const nuCapable = () => !!(NU.base && NU.base.telephone && Array.isArray(NU.base.telephone.ops) && NU.base.telephone.ops.includes("patch"));
/* Livres affichés = livres de Google Drive + changements pas encore inscrits par l'ordinateur */
function nuRecompute(quiet){
  if (!NU.base) return;
  const d = normalize(clone(NU.base));
  NU.pending.forEach(p => { try { applyOp(d, p.op); } catch(e){ console.error(e); } });
  S.d = d; if (!S.year) S.year = fyOf(today()); rebuild(); if (!quiet) render();
}
async function nuEnqueue(type, data, files){
  const id = "op-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
  const op = {format:"tel-op-1", id, type, creeLe:new Date().toISOString(), data, photos:[]};
  if (files && files.length){ try { await nuPhotos.put(id, files); } catch(e){ NU.blobs[id] = files; } }
  NU.pending.push({op, etat:"attente", label:nuLabel(op), tries:0}); nuSave(); nuStatus();
  clearTimeout(NU.timer); NU.timer = setTimeout(() => nuSync(false), 500);
  return op;
}
/* Ce qui a changé entre deux versions des livres : champs modifiés, fiches ajoutées ou retirées */
function nuDiff(a, b){
  const out = [], j = v => JSON.stringify(v === undefined ? null : v);
  COLLECTIONS.forEach(col => {
    const A = new Map((a[col] || []).filter(x => x && x.id).map(x => [x.id, x])), B = new Map((b[col] || []).filter(x => x && x.id).map(x => [x.id, x]));
    B.forEach((doc, id) => {
      const old = A.get(id); if (!old){ out.push({col, id, doc:clone(doc)}); return; }
      const set = {}, unset = []; Object.keys(doc).forEach(k => { if (j(doc[k]) !== j(old[k])) set[k] = clone(doc[k]); }); Object.keys(old).forEach(k => { if (!(k in doc)) unset.push(k); });
      if (Object.keys(set).length || unset.length) out.push({col, id, set, unset});
    });
    A.forEach((doc, id) => { if (!B.has(id)) out.push({col, id, suppr:true}); });
  });
  const ra = a.reglages || {}, rb = b.reglages || {}, set = {}, unset = [];
  Object.keys(rb).forEach(k => { if (j(rb[k]) !== j(ra[k])) set[k] = clone(rb[k]); }); Object.keys(ra).forEach(k => { if (!(k in rb)) unset.push(k); });
  if (Object.keys(set).length || unset.length) out.push({col:"reglages", set, unset});
  return out;
}
function nuMutate(fn, msg, action){
  const run = async () => {
    if (!nuCapable()){ toast("Ouvre d'abord l'application de l'ordinateur une fois (mise à jour requise) : elle pourra ensuite recevoir les modifications faites ici."); return false; }
    S.busy = true;
    try {
      const before = S.d, d = clone(S.d), res = await fn(d);
      if (res === false) return false;
      const changes = nuDiff(before, d);
      if (changes.length) await nuEnqueue("patch", {changes, msg: msg || ""});
      nuRecompute();
      if (msg) toast(msg + (nuOnline() ? "" : " · gardé dans le téléphone"), action);
      return res === undefined ? true : res;
    } catch(e){ console.error(e); toast("La modification a échoué : " + (e.message || e)); return false; }
    finally { S.busy = false; }
  };
  const p = S.q.then(run, run); S.q = p.catch(() => {}); return p;
}
/* Envoi : photos et fichiers d'abord, puis le changement */
async function nuPush(entry){
  const op = entry.op, retry = (entry.tries || 0) > 0;
  const files = NU.blobs[op.id] || (await nuPhotos.get(op.id)) || [];
  entry.tries = (entry.tries || 0) + 1; entry.etat = "envoi"; entry.err = ""; nuSave();
  try {
    if (!NU.ids.tel){ NU.ids.tel = await nuSub(NU.ids.root, "telephone"); if (!NU.ids.tel) throw {code:"telephone"}; LSN.set("ids", NU.ids); }
    for (let k = op.photos.length; k < files.length; k++){
      const f = files[k], name = "photo-" + op.id.slice(3) + "-" + (k + 1) + (f.ext || ".bin");
      if (!(retry && await nuExists(NU.ids.tel, name))) await nuCreate(name, NU.ids.tel, f.blob, f.type || "application/octet-stream");
      op.photos.push(name); nuSave();
    }
    if (!(retry && await nuExists(NU.ids.tel, op.id + ".json"))) await nuCreate(op.id + ".json", NU.ids.tel, new Blob([JSON.stringify(op)], {type:"application/json"}), "application/json");
    entry.etat = "envoye"; delete NU.blobs[op.id]; nuPhotos.del(op.id);
  } catch(e){
    const c = e && e.code;
    if (c === "hors-reseau" || c === "reseau" || c === "login" || c === "telephone"){ entry.etat = "attente"; nuSave(); throw e; }
    console.error(e); entry.etat = "erreur"; entry.err = (e && e.message) || "Envoi impossible";
  }
  nuSave();
}
async function nuRefresh(){
  const reg = await nuReg(NU.ids.root); if (!reg) throw {code:"dossier"};
  const base = JSON.parse(await (await nuDownload(reg.id)).text()), applied = new Set((base.telephone && base.telephone.appliques) || []);
  NU.base = base; NU.last = new Date().toISOString(); LSN.set("base", base); LSN.set("lastSync", NU.last);
  NU.pending.filter(p => applied.has(p.op.id)).forEach(p => nuPhotos.del(p.op.id));
  NU.pending = NU.pending.filter(p => !applied.has(p.op.id));
  if (NU.ids.tel){
    const known = new Set(NU.pending.map(p => p.op.id + ".json"));
    for (const f of await nuList(nuInP(NU.ids.tel), 300)){
      if (!/^op-[\w.-]+\.json$/.test(f.title) || known.has(f.title) || applied.has(f.title.replace(/\.json$/, ""))) continue;
      try { const op = JSON.parse(await (await nuDownload(f.id)).text()); if (op && op.id && !applied.has(op.id) && !NU.pending.some(p => p.op.id === op.id)) NU.pending.push({op, etat:"envoye", label:nuLabel(op)}); } catch(e){}
    }
  }
  nuSave(); nuRecompute();
}
async function nuSync(manual){
  if (NU.syncing) return;
  if (!nuOnline()){ nuStatus(); return; }
  if (!nuTokOk(120000)){ NU.err = "login"; nuStatus(); if (manual) nuLogin(false); return; }
  NU.syncing = true; nuStatus();
  try {
    if (!NU.ids){ const ids = await nuFindIds(); if (!ids) throw {code:"dossier"}; ids.tel = await nuSub(ids.root, "telephone"); NU.ids = ids; LSN.set("ids", ids); }
    for (const p of NU.pending.slice()) if (p.etat === "attente" || p.etat === "envoi" || (manual && p.etat === "erreur")) await nuPush(p);
    await nuRefresh(); NU.err = "";
    if ($("app").hidden){ $("splash").hidden = true; $("app").hidden = false; route(); render(); }
    refreshInbox();
  } catch(e){
    NU.err = (e && e.code) || "reseau"; if (!(e && e.code)) console.error(e);
    if (NU.err === "dossier"){ NU.ids = null; LSN.set("ids", null); }
    if (NU.err === "login" && manual) nuLogin(false);
    if (!NU.base) nuSplash();
  } finally { NU.syncing = false; nuStatus(); }
}
function nuStatus(){
  const q = NU.pending.filter(p => p.etat === "attente" || p.etat === "envoi").length, w = NU.pending.filter(p => p.etat === "envoye").length, er = NU.pending.filter(p => p.etat === "erreur").length;
  const s = n => n > 1 ? "s" : "", h = NU.last ? new Date(NU.last).toLocaleTimeString("fr-CA", {hour:"2-digit", minute:"2-digit"}) : "";
  let txt, cls = "", btn = "";
  if (NU.syncing){ txt = "Synchronisation…"; cls = "busy"; }
  else if (!nuOnline()){ txt = "Hors réseau" + (q ? " · " + q + " modification" + s(q) + " gardée" + s(q) + " dans le téléphone" : " · livres du " + (NU.last ? dShort(iso(new Date(NU.last))) + " à " + h : "téléphone")); cls = "off"; }
  else if (NU.err === "login"){ txt = "Connexion à Google requise" + (q ? " · " + q + " à envoyer" : ""); cls = "err"; btn = '<button class="btn sm primary" type="button" data-nu="login">Se connecter</button>'; }
  else if (er){ txt = er + " envoi" + s(er) + " refusé" + s(er) + " par Google Drive"; cls = "err"; btn = '<button class="btn sm" type="button" data-nu="retry">Réessayer</button>'; }
  else if (NU.err === "dossier"){ txt = "Dossier Comptabilite introuvable dans ce Google Drive"; cls = "err"; }
  else if (NU.err){ txt = "Google Drive ne répond pas" + (q ? " · " + q + " à envoyer" : "") + " · nouvel essai bientôt"; cls = "err"; }
  else if (q){ txt = q + " modification" + s(q) + " à envoyer"; cls = "wait"; }
  else if (w){ txt = w + " modification" + s(w) + " en attente de l'ordinateur"; cls = "wait"; }
  else txt = "À jour · " + h;
  const el = $("nu-bar"); if (el){ el.className = "nu-bar " + cls; $("nu-txt").textContent = txt; $("nu-btn").innerHTML = btn; }
  setSync(txt);
  const warn = $("nu-maj"); if (warn) warn.hidden = !NU.base || nuCapable();
}
function nuSplash(){
  const m = !nuOnline() ? ["Pas de réseau", "Ouvre l'application une première fois avec du réseau pour charger tes livres. Ensuite, elle fonctionne même sans réseau."]
    : NU.err === "dossier" ? ["Dossier Comptabilite introuvable", "Je ne trouve pas le dossier Comptabilite avec registre.json dans ce Google Drive. Connecte-toi avec le compte où il se trouve."]
    : NU.err === "login" || !nuTokOk() ? ["Connecte-toi à Google", "Choisis le compte Google où se trouve ton dossier Comptabilite."] : ["Connexion à tes livres…", "Un instant."];
  splash('<span class="eyebrow">Comptabilité · version complète</span><h1>' + esc(m[0]) + '</h1><p class="muted">' + esc(m[1]) + '</p><div class="actions"><button class="btn primary" id="sp-nu" type="button">' + (NU.err === "login" || !nuTokOk() ? "Se connecter à Google" : "Réessayer") + '</button><a class="btn" href="./">Retour à l\'app terrain</a></div>');
  $("sp-nu").onclick = () => (NU.err === "login" || !nuTokOk()) ? nuLogin(true) : nuSync(true);
}
async function nuBoot(){
  S.dir = {name:"Google Drive › Comptabilite", cloud:true};
  document.body.classList.add("nuage");
  NU.pending = LSN.get("pending", []).filter(p => p && p.op && p.op.id).map(p => (p.etat === "envoi" || p.etat === "verifier") ? Object.assign(p, {etat:"attente", tries:Math.max(1, p.tries || 0)}) : p);
  NU.ids = LSN.get("ids", null); NU.last = LSN.get("lastSync", ""); NU.base = LSN.get("base", null);
  const card = document.querySelector(".claude-card b"); if (card) card.textContent = "Google Drive";
  ["btn-change-dir","tel-card"].forEach(id => { const e = $(id); if (e) e.hidden = true; });
  const dn = $("btn-reload"); if (dn) dn.textContent = "Actualiser depuis Google Drive";
  if (NU.base){ nuRecompute(true); $("splash").hidden = true; $("app").hidden = false; route(); render(); }
  else nuSplash();
  nuStatus();
  window.addEventListener("online", () => { nuStatus(); nuSync(false); });
  window.addEventListener("offline", nuStatus);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && nuTokOk() && Date.now() - new Date(NU.last || 0).getTime() > 30000) nuSync(false); });
  setInterval(() => { if (document.hidden || S.busy) return; checkReminders(); if (nuOnline() && nuTokOk() && (NU.pending.some(p => p.etat === "attente") || Date.now() - new Date(NU.last || 0).getTime() > 90000)) nuSync(false); }, 30000);
  if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register("sw.js").catch(() => {});
  if (!nuTokOk(120000) && nuOnline() && Date.now() - (LSN.get("authTry", 0) || 0) > 20000){ nuLogin(false); return; }
  nuSync(false);
}
document.addEventListener("click", e => { const b = e.target.closest("[data-nu]"); if (!b) return; const a = b.dataset.nu; if (a === "login") nuLogin(true); else if (a === "sync") nuSync(true); else if (a === "retry"){ NU.pending.forEach(p => { if (p.etat === "erreur") p.etat = "attente"; }); nuSave(); nuSync(true); } });
/* Fichiers en mode nuage */
async function nuFolder(name){
  if (NU.fold[name]) return NU.fold[name];
  if (!NU.ids) return ""; const id = await nuSub(NU.ids.root, name); if (id) NU.fold[name] = id; return id;
}
async function nuFile(path){
  const hit = await nuCache.get(path); if (hit && hit.blob) return hit.blob;
  const parts = String(path).split("/"); if (parts.length !== 2) throw new Error("Chemin inconnu : " + path);
  if (!nuOnline()) throw new Error("Ce fichier n'est pas encore dans le téléphone. Ouvre-le avec du réseau.");
  const fid = await nuFolder(parts[0]); if (!fid) throw new Error("Fichier introuvable : " + path);
  const L = await nuList("name = '" + nuQ(parts[1]) + "' and " + nuInP(fid), 1); if (!L[0]) throw new Error("Fichier introuvable : " + path);
  const blob = await nuDownload(L[0].id); if (blob.size < 8e6) nuCache.put(path, {blob, t:Date.now()});
  return blob;
}
async function nuWrite(path, content){
  const blob = content instanceof Blob ? content : new Blob([content]);
  await nuCache.put(path, {blob, t:Date.now()});
  if (/^(exports|agenda|factures|devis)\//.test(path)) return;   // l'ordinateur refait ces fichiers ; ici ils servent à l'affichage ou au téléchargement
  await nuEnqueue("fichier", {to:path}, [{blob, type: blob.type || "application/octet-stream", ext: extOf(path) || ".bin"}]);
}
async function nuShrink(f){
  if (!f || f.type === "application/pdf" || /\.pdf$/i.test(f.name || "") || !/^image\//.test(f.type || "") || f.size < 500000) return f;
  try {
    const url = URL.createObjectURL(f), img = new Image(); img.src = url; await img.decode();
    const sc = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight)), w = Math.max(1, Math.round(img.naturalWidth * sc)), h = Math.max(1, Math.round(img.naturalHeight * sc));
    const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, w, h); x.drawImage(img, 0, 0, w, h); URL.revokeObjectURL(url);
    const b = await new Promise(r => c.toBlob(r, "image/jpeg", 0.82));
    return b ? new File([b], String(f.name || "photo").replace(/\.[^.]+$/, "") + ".jpg", {type:"image/jpeg"}) : f;
  } catch(e){ return f; }
}
async function nuShare(blob, name, text){
  const file = new File([blob], name, {type: blob.type || "application/pdf"});
  if (navigator.canShare && navigator.canShare({files:[file]})){ try { await navigator.share(Object.assign({files:[file], title:name}, text ? {text} : {})); return true; } catch(e){ if (e && e.name === "AbortError") return true; } }
  downloadBlob(file, name); toast("Fichier enregistré dans Téléchargements"); return false;
}
async function nuInbox(){
  const gone = new Set(), local = [];
  NU.pending.forEach(p => { const x = p.op.data || {}; if (p.op.type === "deplacer") gone.add(x.from); if (p.op.type === "fichier-suppr") gone.add(x.path); if (p.op.type === "fichier" && /^a-traiter\//.test(x.to || "")) local.push({name:x.to.split("/").pop(), path:x.to, size:0, mod:new Date(p.op.creeLe).getTime(), type:""}); });
  let out = S.inboxCloud || [];
  if (NU.ids && nuOnline() && nuTokOk()){
    try { const fid = await nuFolder("a-traiter"); out = fid ? (await nuList(nuInP(fid), 200)).filter(f => DOC_RE.test(f.title)).map(f => ({name:f.title, path:"a-traiter/" + f.title, size:f.size, mod:new Date(f.modifiedTime).getTime(), type:f.mimeType})) : []; S.inboxCloud = out; } catch(e){}
  }
  const seen = new Set(out.map(x => x.path));
  return out.filter(x => !gone.has(x.path)).concat(local.filter(x => !seen.has(x.path) && !gone.has(x.path))).sort((a, b) => b.mod - a.mod || a.name.localeCompare(b.name));
}
