"""v3.5 : une seule application au téléphone (en-tête, barre d'onglets et menu communs à l'app terrain et aux sections complètes)."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:90]))
    s = s.replace(a, b)

CSS = r'''
/* ---------- Téléphone : une seule application (mêmes en-tête, onglets et menu que l'app terrain) ---------- */
:root{--m-tab:64px}
.m-head,.m-tabs{display:none}
.m-ov[hidden]{display:none}
@media (max-width:900px){
  body.nuage .side{display:none}
  body.nuage .main{padding:0 16px calc(var(--m-tab) + 28px + env(safe-area-inset-bottom,0px));gap:14px}
  body.nuage .m-head{display:flex}
  body.nuage .top{padding-top:2px}
  body.nuage #top-eyebrow,body.nuage #top-meta,body.nuage .top .menu-wrap{display:none}
  body.nuage .nu-bar{display:none}
  body.nuage .nu-bar.err{display:flex}
  body.nuage .m-tabs{display:block}
  body.nuage .toast{bottom:calc(var(--m-tab) + 14px + env(safe-area-inset-bottom,0px))}
  body.nuage .bulk{top:calc(68px + env(safe-area-inset-top,0px))}
}
.m-head{align-items:center;gap:10px;position:sticky;top:0;z-index:35;background:var(--surface);border-bottom:1px solid var(--line);margin:0 -16px;padding:calc(10px + env(safe-area-inset-top,0px)) 16px 10px}
.m-who{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2}
.m-who b{font-family:var(--font-display);font-size:1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.m-sync{display:inline-flex;align-items:center;gap:6px;font-size:.78rem;color:var(--muted);border:none;background:none;padding:0;cursor:pointer;text-align:left;font-family:inherit}
.m-sync i{width:8px;height:8px;border-radius:50%;background:var(--pos);flex:none}
.m-sync.wait i{background:var(--warn)}.m-sync.err i{background:var(--neg)}.m-sync.off i{background:var(--muted)}.m-sync.busy i{background:var(--accent)}
.m-ib{display:inline-grid;place-items:center;width:40px;height:40px;border:none;background:none;border-radius:10px;color:var(--ink-2);cursor:pointer;flex:none;padding:0}
.m-ib:active{background:var(--sunk)}
.m-tabs{position:fixed;left:0;right:0;bottom:0;z-index:35;background:var(--surface);border-top:1px solid var(--line);padding-bottom:env(safe-area-inset-bottom,0px)}
.m-tabs .m-wrap{display:grid;grid-template-columns:repeat(5,1fr);height:var(--m-tab);align-items:center;max-width:640px;margin:0 auto}
.m-tabs a,.m-tabs button{border:none;background:none;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:.7rem;font-weight:600;color:var(--muted);cursor:pointer;padding:6px 0;text-decoration:none;position:relative;font-family:inherit}
.m-tabs [aria-current="page"]{color:var(--accent)}
.m-tabs .m-add{justify-self:center;width:52px;height:52px;border-radius:16px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;box-shadow:0 4px 12px color-mix(in srgb,var(--accent) 40%,transparent);padding:0}
.m-tabs .m-add .ic{width:26px;height:26px;stroke-width:2.2}
.m-badge{position:absolute;top:2px;left:calc(50% + 6px);min-width:17px;height:17px;border-radius:999px;background:var(--neg);color:#fff;font-size:.66rem;display:grid;place-items:center;padding:0 4px}
.m-ov{position:fixed;inset:0;background:var(--scrim);z-index:60;display:flex;align-items:flex-end;justify-content:center}
.m-panel{background:var(--bg);width:100%;max-width:640px;max-height:92%;border-radius:18px 18px 0 0;display:flex;flex-direction:column;overflow:hidden;box-shadow:var(--shadow)}
@media (prefers-reduced-motion:no-preference){.m-panel{animation:m-up .2s ease-out}}
@keyframes m-up{from{transform:translateY(40px);opacity:.6}to{transform:none;opacity:1}}
.m-panel header{display:flex;align-items:center;gap:8px;padding:12px 16px 10px;background:var(--surface);border-bottom:1px solid var(--line)}
.m-panel header h2{flex:1;margin:0}
.m-body{overflow-y:auto;padding:14px 16px calc(18px + env(safe-area-inset-bottom,0px));display:flex;flex-direction:column;gap:10px}
.m-addgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.m-addgrid button{border:1px solid var(--line);background:var(--surface);border-radius:var(--r);padding:14px;display:flex;flex-direction:column;gap:6px;align-items:flex-start;text-align:left;cursor:pointer;min-height:96px;color:var(--ink);font-family:inherit}
.m-addgrid button .ic{width:24px;height:24px;color:var(--accent)}
.m-addgrid button small{color:var(--muted);font-size:.78rem;line-height:1.3}
.m-list{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);overflow:hidden}
.m-list button{display:flex;align-items:center;gap:12px;border:none;border-bottom:1px solid var(--line);background:none;padding:13px 14px;text-align:left;cursor:pointer;color:var(--ink);font-family:inherit;font-size:.95rem}
.m-list button:last-child{border-bottom:none}
.m-list button span{flex:1}
.m-list button .ic{color:var(--muted)}
.m-list button .ic:first-child{color:var(--accent)}
/* Tuiles du menu (mêmes dans l'app terrain) */
.mt-h{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:700;margin:8px 2px 0}
.mt-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.mt-tile{position:relative;display:flex;flex-direction:column;gap:3px;padding:14px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);color:var(--ink);text-decoration:none;min-height:108px}
.mt-tile:active{background:var(--sunk)}
.mt-ic{width:40px;height:40px;border-radius:12px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;margin-bottom:6px}
.mt-tile b{font-size:.98rem}
.mt-tile small{color:var(--muted);font-size:.8rem;line-height:1.3}
.mt-tile.on small{color:var(--warn);font-weight:600}
.mt-dot{position:absolute;top:12px;right:12px;width:9px;height:9px;border-radius:50%;background:var(--warn)}
'''
rep('</style>', CSS + '</style>', 1)
# icônes de l'app terrain
i = s.index('<symbol id="i-pdf"'); j = s.index('</symbol>', i) + len('</symbol>')
s = s[:j] + '''
  <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></symbol>
  <symbol id="i-grid" viewBox="0 0 24 24"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></symbol>''' + s[j:]

SHELL = r'''
/* ===== Menu de l'application au téléphone (partagé par l'app terrain et les sections complètes) ===== */
const MENU_TEL = [
  ["Au quotidien", [["transactions","c","i-list","Opérations","Dépenses, revenus, recherche"], ["documents","c","i-docs","Documents","Reçus à classer, envoi au comptable"]]],
  ["Achats et biens", [["fournisseurs","c","i-store","Fournisseurs","Factures à payer"], ["inventaire","c","i-box","Inventaire","Camion, équipement, entretiens, stock"]]],
  ["Argent et taxes", [["banque","c","i-bank","Banque","Soldes, rapprochement, relevés"], ["tvh","c","i-percent","Taxes de vente","TPS et TVQ à produire"], ["km","c","i-car","Kilométrage","Trajets, allocation, registre"]]],
  ["Analyse", [["projets","c","i-folder","Projets","Rentabilité par chantier"], ["rapports","c","i-chart","Rapports","Résultats, bilan, sommaire IGRF"]]],
  ["Application", [["reglages","c","i-sliders","Réglages","Entreprise, taxes, comptes, logo"], ["plus","t","i-refresh","Synchronisation","Envois en attente, compte Google"]]]
];
const ADD_TEL2 = [["transfert","i-transfer","Transfert entre comptes"], ["tvh","i-percent","Paiement de taxes"], ["dividende","i-coins","Dividende"], ["releve","i-upload","Relevé bancaire"]];
function menuTelBadges(){
  const d = S.d, b = {}; if (!d) return b;
  const ap = d.transactions.filter(t => t.type === "depense" && unpaid(t)).length; if (ap) b.fournisseurs = ap + " facture" + (ap > 1 ? "s" : "") + " à payer";
  const v = d.transactions.filter(t => t.aVerifier).length; if (v) b.transactions = v + " à vérifier";
  const km = d.km.filter(k => !k.alloc && kmPerso(k)).length; if (km) b.km = km + " trajet" + (km > 1 ? "s" : "") + " à inscrire";
  return b;
}
/* here : "t" (app terrain, index.html) ou "c" (sections complètes, complet.html) */
function menuTelHtml(here, b){
  b = b || {};
  return MENU_TEL.map(([h, items]) => '<div class="mt-h">' + esc(h) + '</div><div class="mt-grid">' + items.map(([k, p, ic, l, sub]) =>
    '<a class="mt-tile' + (b[k] ? " on" : "") + '" data-mt="' + k + '" href="' + (p === here ? "#" + k : (here === "t" ? "complet.html#" : "./#") + k) + '"><span class="mt-ic">' + ico(ic) + "</span><b>" + esc(l) + "</b><small>" + esc(b[k] || sub) + "</small>" + (b[k] ? '<i class="mt-dot"></i>' : "") + "</a>").join("") + "</div>").join("");
}
const NU_ADD = [["depense","i-camera","Reçu ou dépense","Photo du reçu et montant"], ["revenu","i-in","Revenu","Paiement reçu"], ["facture","i-invoice","Facture","Avec TPS et TVQ"], ["devis","i-quote","Devis","Chez le client"], ["note","i-cal","Événement","Rendez-vous, soumission"], ["trajet","i-car","Trajet","GPS ou à la main"], ["entretien","i-wrench","Entretien","Camion ou équipement"], ["docs","i-inbox","Documents","Photos à classer plus tard"]];
const nuMobile = () => CLOUD && !!window.matchMedia && matchMedia("(max-width: 900px)").matches;
function nuShell(){
  if ($("m-head")) return;
  document.querySelector(".main").insertAdjacentHTML("afterbegin", '<header class="m-head" id="m-head"><span class="logo">' + ico("i-book") + '</span><div class="m-who"><b id="m-nom">Comptabilité</b><button class="m-sync" id="m-sync" type="button" data-nu="synccard"><i></i><span id="m-sync-t">Connexion…</span></button></div><button class="m-ib" type="button" data-nu="search" aria-label="Rechercher">' + ico("i-search") + '</button><button class="m-ib" type="button" data-nu="sync" aria-label="Actualiser">' + ico("i-refresh") + "</button></header>");
  document.body.insertAdjacentHTML("beforeend", '<nav class="m-tabs" aria-label="Sections"><div class="m-wrap"><a href="./#accueil">' + ico("i-home") + 'Accueil</a><a href="./#agenda">' + ico("i-cal") + 'Agenda<span class="m-badge" id="mb-agenda" hidden></span></a><button type="button" class="m-add" data-nu="add" aria-label="Ajouter">' + ico("i-plus") + '</button><a href="./#ventes">' + ico("i-invoice") + 'Ventes<span class="m-badge" id="mb-ventes" hidden></span></a><button type="button" data-nu="menu" aria-current="page">' + ico("i-grid") + "Menu</button></div></nav>" +
    '<div class="m-ov" id="m-menu" hidden><div class="m-panel" role="dialog" aria-label="Menu"><header><h2>Menu</h2><button class="m-ib" type="button" data-nu="close" aria-label="Fermer">' + ico("i-x") + '</button></header><div class="m-body" id="m-menu-b"></div></div></div>' +
    '<div class="m-ov" id="m-add" hidden><div class="m-panel" role="dialog" aria-label="Ajouter"><header><h2>Ajouter</h2><button class="m-ib" type="button" data-nu="close" aria-label="Fermer">' + ico("i-x") + '</button></header><div class="m-body"><div class="m-addgrid">' +
    NU_ADD.map(([k, i, l, sub]) => '<button type="button" data-nuadd="' + k + '">' + ico(i) + "<b>" + esc(l) + "</b><small>" + esc(sub) + "</small></button>").join("") + '</div><div class="mt-h">Autres</div><div class="m-list">' +
    ADD_TEL2.map(([k, i, l]) => '<button type="button" data-nuadd="' + k + '">' + ico(i) + "<span>" + esc(l) + "</span>" + ico("i-chev") + "</button>").join("") + "</div></div></div></div>");
  ["m-menu","m-add"].forEach(id => $(id).addEventListener("click", e => { if (e.target === $(id)) nuOverlay(null); }));
  $("m-menu").addEventListener("click", e => { const t = e.target.closest("[data-mt]"); if (!t || !/^#/.test(t.getAttribute("href"))) return; e.preventDefault(); nuOverlay(null, true); history.replaceState(null, "", "#" + t.dataset.mt); route(); });
  $("m-add").addEventListener("click", e => { const b = e.target.closest("[data-nuadd]"); if (!b) return; const k = b.dataset.nuadd; nuOverlay(null); if (k === "trajet"){ location.href = "./#ajout-trajet"; return; } setTimeout(() => doNew(k), 30); });
  window.addEventListener("popstate", () => { if (NU.ov){ NU.ov = null; ["m-menu","m-add"].forEach(id => { $(id).hidden = true; }); } });
}
/* Menu ou ajout en panneau ; le bouton Retour d'Android le ferme */
function nuOverlay(id, keepHist){
  if (id){ if (NU.ov === id) return; ["m-menu","m-add"].forEach(x => { $(x).hidden = x !== id; }); if (id === "m-menu") $("m-menu-b").innerHTML = menuTelHtml("c", menuTelBadges()); if (!NU.ov) try { history.pushState({mov:1}, "", location.href); } catch(e){} NU.ov = id; return; }
  if (!NU.ov) return; ["m-menu","m-add"].forEach(x => { $(x).hidden = true; }); NU.ov = null;
  if (!keepHist && history.state && history.state.mov) history.back();
}
/* Textes pensés pour la souris et le clavier, remplacés au téléphone */
function nuTextes(){
  if (!nuMobile()) return;
  const rep = [[/Glisse-le ici, colle-le avec Ctrl\+V ou clique pour le choisir\./g, "Touche ici pour prendre une photo ou choisir un fichier."],
    [/Glisse-les ici, colle-les avec Ctrl\+V ou clique pour les choisir\. Tu peux en choisir plusieurs à la fois \(photos ou PDF\)\.[^<]*/g, "Touche ici pour prendre des photos ou choisir des fichiers (photos ou PDF), plusieurs à la fois."],
    [/Glisse-la ici ou clique pour choisir la photo ou le PDF\./g, "Touche ici pour prendre la photo ou choisir le PDF."]];
  document.querySelectorAll(".drop-cta span, .droparea span, .drop span").forEach(el => { if (el.children.length > 3) return; let h = el.innerHTML, n = h; rep.forEach(([a, b]) => { n = n.replace(a, b); }); if (n !== h) el.innerHTML = n; });
}
function nuNouveau(k){
  const v = {releve:"banque", docs:"documents", trajet:"km"}[k] || "transactions";
  history.replaceState(null, "", "#" + v); show(v);
  if (S.d) setTimeout(() => doNew(k), 60); else NU.nouveau = k;
}
function nuChrome(){
  const n = $("m-nom"); if (n && S.d) n.textContent = R().nom || "Mon entreprise";
  if (!S.d || !$("mb-agenda")) return;
  const t0 = today(), ag = agendaEvents(t0, t0).filter(e => !e.done && e.kind !== "info").length, fl = S.d.factures.filter(f => facStatus(f).k === "retard").length;
  [["mb-agenda", ag], ["mb-ventes", fl]].forEach(([id, n]) => { $(id).textContent = n; $(id).hidden = !n; });
}
'''
rep('''/* ===== Exercice et périodes ===== */''', SHELL + '''
/* ===== Exercice et périodes ===== */''')
# routage : Accueil, Agenda et Ventes sont ceux de l'app terrain ; « nouveau=… » ouvre un ajout
rep('''function route(){ const v = location.hash.slice(1); show(VIEWS[v] ? v : "accueil"); }''',
'''function route(){
  const v = location.hash.slice(1);
  if (nuMobile()){
    if (/^nouveau=\\w+$/.test(v)) return nuNouveau(v.slice(8));
    if (["accueil","agenda","ventes"].includes(v)){ location.replace("./#" + v); return; }
    if (!VIEWS[v]){ show("transactions"); if (S.d) nuOverlay("m-menu"); return; }
  }
  show(VIEWS[v] ? v : "accueil");
}''')
# démarrage, état et clics
rep('''  S.dir = {name:"Google Drive › Comptabilite", cloud:true};
  document.body.classList.add("nuage");''', '''  S.dir = {name:"Google Drive › Comptabilite", cloud:true};
  document.body.classList.add("nuage"); nuShell(); nuTextes();''')
rep('''  S.d = d; if (!S.year) S.year = fyOf(today()); rebuild(); if (!quiet) render();''', '''  S.d = d; if (!S.year) S.year = fyOf(today()); rebuild(); if (!quiet) render(); nuChrome();
  if (NU.nouveau){ const k = NU.nouveau; NU.nouveau = null; setTimeout(() => doNew(k), 60); }''')
rep('''  const el = $("nu-bar"); if (el){ el.className = "nu-bar " + cls; $("nu-txt").textContent = txt; $("nu-btn").innerHTML = btn; }''',
'''  const el = $("nu-bar"); if (el){ el.className = "nu-bar " + cls; $("nu-txt").textContent = txt; $("nu-btn").innerHTML = btn; }
  const ms = $("m-sync"); if (ms){ ms.className = "m-sync " + cls; $("m-sync-t").textContent = txt; }''')
rep('''document.addEventListener("click", e => { const b = e.target.closest("[data-nu]"); if (!b) return; const a = b.dataset.nu; if (a === "login") nuLogin(true); else if (a === "sync") nuSync(true);''',
'''document.addEventListener("click", e => { const b = e.target.closest("[data-nu]"); if (!b) return; const a = b.dataset.nu; if (a === "login") nuLogin(true); else if (a === "sync") nuSync(true); else if (a === "menu") nuOverlay(NU.ov === "m-menu" ? null : "m-menu"); else if (a === "add") nuOverlay("m-add"); else if (a === "close") nuOverlay(null); else if (a === "search") $("btn-search").click(); else if (a === "synccard") location.href = "./#plus";''')
open(P, "w", encoding="utf-8").write(s); print("ok")
