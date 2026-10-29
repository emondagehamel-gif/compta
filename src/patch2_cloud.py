"""v3.4 (2/2) : version complète sur le téléphone (mode nuage)."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
CLOUDJS = open(sys.argv[2], encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:90]))
    s = s.replace(a, b)
# CSS + barre d'état
rep('''.claude-card{display:flex;''', '''.nu-bar{display:none;align-items:center;gap:10px;flex-wrap:wrap;border:1px solid var(--line);background:var(--surface);border-radius:var(--r);padding:8px 12px;font-size:.85rem;margin-bottom:12px}
body.nuage .nu-bar{display:flex}
.nu-bar i{width:9px;height:9px;border-radius:50%;background:var(--pos);flex:none}
.nu-bar.wait i{background:var(--warn)} .nu-bar.err i{background:var(--neg)} .nu-bar.off i{background:var(--muted)} .nu-bar.busy i{background:var(--accent)}
.nu-bar .t{flex:1;min-width:150px;color:var(--ink-2)}
.nu-bar .acts{display:flex;gap:6px;flex-wrap:wrap}
.claude-card{display:flex;''')
rep('''  <main class="main">''', '''  <main class="main">
    <div class="nu-bar" id="nu-bar"><i></i><span class="t" id="nu-txt">Connexion…</span><span class="acts"><span id="nu-btn"></span><button class="btn sm" type="button" data-nu="sync">Actualiser</button><a class="btn sm" href="./">App terrain</a></span></div>
    <div class="banner" id="nu-maj" hidden><span>L'application de l'ordinateur doit être mise à jour avant de recevoir les modifications faites ici. Tu peux consulter tes livres en attendant.</span></div>''')
# module nuage
rep('''/* ===== Exercice et périodes ===== */''', CLOUDJS + '''
/* ===== Exercice et périodes ===== */''')
# démarrage
rep('''async function boot(){
  if (!window.showDirectoryPicker){''', '''async function boot(){
  if (CLOUD) return nuBoot();
  if (!window.showDirectoryPicker){''')
rep('''async function reloadIfChanged(silent){
''', '''async function reloadIfChanged(silent){
  if (CLOUD){ nuSync(true); return false; }
''')
rep('''function mutate(fn, msg, action){
''', '''function mutate(fn, msg, action){
  if (CLOUD) return nuMutate(fn, msg, action);
''')
rep('''async function writeFile(path, content){
''', '''async function writeFile(path, content){
  if (CLOUD) return nuWrite(path, content);
''')
rep('''async function fileURL(path){
''', '''async function fileURL(path){
  if (CLOUD){ const b = await nuFile(path); return {url: URL.createObjectURL(b), type: b.type || ""}; }
''')
rep('''async function readBlob(path){ const parts''', '''async function readBlob(path){ if (CLOUD) return nuFile(path); const parts''')
rep('''async function removeFile(path){ const parts''', '''async function removeFile(path){ if (CLOUD){ nuCache.del(path); await nuEnqueue("fichier-suppr", {path}); return; } const parts''')
rep('''async function moveFile(from, to){ const f = await readBlob(from);''', '''async function moveFile(from, to){ if (CLOUD){ const h = await nuCache.get(from); if (h) { await nuCache.put(to, h); nuCache.del(from); } await nuEnqueue("deplacer", {from, to}); return to; } const f = await readBlob(from);''')
rep('''async function saveUpload(f, base){ const ext''', '''async function saveUpload(f, base){ if (CLOUD) f = await nuShrink(f); const ext''')
rep('''const winPath = p => (S.dir ? S.dir.name + "\\\\" : "") + String(p).replace(/\\//g, "\\\\");''', '''const winPath = p => CLOUD ? "Google Drive › Comptabilite › " + String(p).replace(/\\//g, " › ") : (S.dir ? S.dir.name + "\\\\" : "") + String(p).replace(/\\//g, "\\\\");''')
rep('''async function saveCSV(path, rows){ try {''', '''async function saveCSV(path, rows){ if (CLOUD){ downloadBlob(new Blob([csv(rows)], {type:"text/csv;charset=utf-8"}), path.split("/").pop()); toast("Fichier téléchargé sur ton téléphone"); return; } try {''')
# visionneuse : PDF partagé au téléphone
rep('''    const {url, type} = await fileURL(r.fichier);
    const isPdf = /pdf/.test(type) || /\\.pdf$/i.test(r.fichier);''', '''    const {url, type} = await fileURL(r.fichier);
    const isPdf = /pdf/.test(type) || /\\.pdf$/i.test(r.fichier);
    if (CLOUD && isPdf){ const b = await (await fetch(url)).blob(); await nuShare(new Blob([b], {type:"application/pdf"}), r.fichier.split("/").pop()); return; }''')
rep('''  } catch(e){ toast("Reçu introuvable dans le dossier : " + r.fichier); }''', '''  } catch(e){ toast(CLOUD ? (e.message || "Fichier introuvable") : "Reçu introuvable dans le dossier : " + r.fichier); }''')
rep('''    $("viewer").innerHTML = '<div class="row-head"><h3>' + esc(r.nom || r.fichier) + '</h3><button class="btn" type="button" id="v-close">' + ico("i-x") + 'Fermer</button></div>' + (isPdf ? '<iframe src="' + url + '" title="Reçu"></iframe>' : '<img src="' + url + '" alt="Reçu">') + '<p class="muted small">Fichier : ' + esc(S.dir.name + "\\\\" + r.fichier.replace(/\\//g, "\\\\")) + "</p>";''',
'''    $("viewer").innerHTML = '<div class="row-head"><h3>' + esc(r.nom || r.fichier) + '</h3><button class="btn" type="button" id="v-close">' + ico("i-x") + 'Fermer</button></div>' + (isPdf ? '<iframe src="' + url + '" title="Reçu"></iframe>' : '<img src="' + url + '" alt="Reçu">') + '<p class="muted small">Fichier : ' + esc(winPath(r.fichier)) + "</p>";''')
# courriel : partage du PDF au téléphone
rep('''  await mutate(d => { const x = (isF ? d.factures : d.devis).find(y => y.id === id); if (!x) return false; if (isF) x.envoyeeLe = today(); else x.envoyeLe = today(); });
  const a = document.createElement("a");''', '''  await mutate(d => { const x = (isF ? d.factures : d.devis).find(y => y.id === id); if (!x) return false; if (isF) x.envoyeeLe = today(); else x.envoyeLe = today(); });
  if (CLOUD){ try { await nuShare(new Blob([await readBlob(path)], {type:"application/pdf"}), path.split("/").pop(), body); } catch(e){ toast("Partage impossible : " + (e.message || e)); } return; }
  const a = document.createElement("a");''')
# boîte « à traiter »
rep('''async function refreshInbox(){
  if (!S.dir) return;
  try {
    const dir = await S.dir.getDirectoryHandle("a-traiter", {create:true}), out = [];
    for await (const [name, h] of dir.entries()){ if (h.kind !== "file" || !DOC_RE.test(name)) continue; const f = await h.getFile(); out.push({name, path:"a-traiter/" + name, size:f.size, mod:f.lastModified, type:f.type}); }
    out.sort''', '''async function refreshInbox(){
  if (!S.dir) return;
  try {
    let out = [];
    if (CLOUD) out = await nuInbox();
    else { const dir = await S.dir.getDirectoryHandle("a-traiter", {create:true});
    for await (const [name, h] of dir.entries()){ if (h.kind !== "file" || !DOC_RE.test(name)) continue; const f = await h.getFile(); out.push({name, path:"a-traiter/" + name, size:f.size, mod:f.lastModified, type:f.type}); } }
    out.sort''')
rep('''  for (const f of ok){
    const ext = extOf(f.name) || (f.type === "application/pdf" ? ".pdf" : ".png"), base''', '''  for (let f of ok){
    if (CLOUD) f = await nuShrink(f);
    const ext = extOf(f.name) || (f.type === "application/pdf" ? ".pdf" : ".png"), base''')
rep('''async function phoneSync(){
  if (!S.dir''', '''async function phoneSync(){
  if (CLOUD) return;
  if (!S.dir''')
open(P, "w", encoding="utf-8").write(s); print("ok")
