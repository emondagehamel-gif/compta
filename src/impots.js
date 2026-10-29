/* ----- Fin d'année : préparation des déclarations T2 et CO-17 ----- */
/* Règles vérifiées en octobre 2026 (sources dans le dossier et dans POUR-CLAUDE.md). Ce sont des estimations :
   la déclaration se transmet avec un logiciel homologué, qui refait les calculs. */
const FISC = {
  fedPME: 0.09, fedGen: 0.15, plafond: 500000, seuilAcomptes: 3000,
  qcGen: 0.115,
  qcDpe: debut => debut > "2026-04-29" ? 0.093 : 0.083,          // année qui commence après le 29 avril 2026 : 9,3 % (taux net 2,2 %), sinon 8,3 % (3,2 %)
  div: y => ({majo: 0.15, fed: 0.090301, qc: y >= 2027 ? 0.0269 : 0.0342}),   // dividendes ordinaires (autres que déterminés)
  plafond101: y => y >= 2026 ? 39000 : 38000
};
const DPA_CAT = {
  "8": {l:"Catégorie 8", d:"Machines, matériel et outils de 500 $ et plus", t:0.20},
  "10": {l:"Catégorie 10", d:"Camions, remorques et véhicules de travail", t:0.30},
  "10.1": {l:"Catégorie 10.1", d:"Voiture de tourisme au-dessus du plafond", t:0.30},
  "12": {l:"Catégorie 12", d:"Petits outils de moins de 500 $, logiciels", t:1.00},
  "50": {l:"Catégorie 50", d:"Ordinateurs et matériel informatique", t:0.55}
};
const DPA_1RE = [["acc","Accélérée : 1,5 × le taux (acquis après 2024)"], ["demi","Demi-année : moitié du taux"], ["sans","Taux normal, sans demi-année"], ["imm","100 % la première année"]];
const dpaFact = k => ({acc:1.5, demi:0.5, sans:1, imm:Infinity})[k] || 1;
function faCfg(y){ const f = R().fiscal; return (f && typeof f === "object" && f[String(y)]) || {}; }
const faPct = v => (Math.round(v * 100) / 100).toLocaleString("fr-CA", {maximumFractionDigits: 2}) + " %";
const faOuvert = k => (S.faOpen || {})[k] ? " open" : "";
/* Après une saisie, les nouveaux calculs s'affichent tout de suite, sans perdre le champ où se trouve le curseur */
function faFlush(){
  const el = $("fa-body"); if (!el || el._pending == null) return;
  const a = document.activeElement, inside = !!a && el.contains(a);
  const sel = !inside ? null : a.dataset.fa ? '[data-fa="' + a.dataset.fa + '"]' : a.dataset.faBien ? '[data-fa-bien="' + a.dataset.faBien + '"][data-fa-k="' + a.dataset.faK + '"]' : a.id ? "#" + a.id : null;
  if (inside && !sel) return;
  const typed = inside && a.tagName !== "SELECT" && a.value !== a.defaultValue, val = inside ? a.value : "";
  let s0 = null, s1 = null; try { if (inside){ s0 = a.selectionStart; s1 = a.selectionEnd; } } catch(e){}
  const h = el._pending; el._pending = null; el.innerHTML = h; el._html = h;
  const n = sel && el.querySelector(sel);
  if (n){ if (typed) n.value = val; n.focus({preventScroll:true}); try { if (s0 != null) n.setSelectionRange(s0, s1); } catch(e){} }
}
function faSave(y, fn, msg){
  return Promise.resolve(mutate(d => { const r = d.reglages; r.fiscal = r.fiscal && typeof r.fiscal === "object" ? clone(r.fiscal) : {}; const c = r.fiscal[String(y)] = Object.assign({}, r.fiscal[String(y)] || {}); if (fn(c) === false) return false; }, msg)).then(r => { faFlush(); return r; });
}
/* Exercice réel : la première année commence à la date de constitution */
function faRange(y){
  const fr = fyRange(y), dc = R().dateConstitution, start = dc && dc > fr.start && dc <= fr.end ? dc : fr.start;
  return {start, end: fr.end, debut: fr.start, jours: Math.round((new Date(fr.end) - new Date(start)) / 864e5) + 1};
}
const faAnnee0 = () => fyOf(R().dateConstitution || R().dateOuverture || today());
/* Biens amortissables acquis pendant l'exercice : achats inscrits en immobilisation, inventaire avec coût d'achat, ajouts à la main */
function faBiens(y){
  const fr = fyRange(y), cfg = faCfg(y), choix = cfg.biens || {}, out = [];
  const coutTx = t => r2((Number(t.montant) || 0) + (inscrit() ? 0 : Number(t.taxe) || 0) + (inscritQ() ? 0 : Number(t.tvq) || 0));
  S.d.transactions.forEach(t => {
    const c = t.type === "depense" ? cat("depense", t.categorie) : null; if (!c || c.grp !== "immo" || t.date < fr.start || t.date > fr.end) return;
    const eq = t.equipement ? S.d.equipements.find(e => e.id === t.equipement) : null, cout = coutTx(t);
    out.push({key:"t:" + t.id, desc: t.description || t.tiers || c.l, date: t.date, cout, eq: eq ? eq.id : "", defCat: t.categorie === "equipement-info" ? "50" : eq && isRoad(eq) ? "10" : cout < 500 ? "12" : "8", source:"Opération"});
  });
  S.d.equipements.forEach(e => {
    if (!(Number(e.coutAchat) > 0) || !e.dateAchat || e.dateAchat < fr.start || e.dateAchat > fr.end || out.some(b => b.eq === e.id)) return;
    out.push({key:"e:" + e.id, desc: e.nom, date: e.dateAchat, cout: r2(Number(e.coutAchat)), defCat: isRoad(e) ? "10" : e.type === "informatique" ? "50" : "8", source:"Inventaire", horsLivres:true, vehicule: e.type === "vehicule"});
  });
  (cfg.ajouts || []).forEach(a => out.push({key:"m:" + a.id, id:a.id, desc: a.desc || "Bien ajouté", date: a.date || fr.end, cout: r2(Number(a.cout) || 0), defCat: a.cat || "8", source:"Ajouté ici", manuel:true}));
  return out.map(b => { const o = choix[b.key] || {}, an = Number(String(b.date).slice(0, 4)); return Object.assign(b, {cat: o.cat || b.defCat, premiere: o.premiere || (an >= 2025 && an <= 2029 ? "acc" : "demi"), exclu: !!o.exclu}); });
}
/* Déduction pour amortissement par catégorie (annexe 8) */
function faDPA(y, depth){
  depth = depth || 0;
  const cfg = faCfg(y), r0 = faRange(y), prorata = Math.min(1, r0.jours / 365), cats = {};
  const get = k => cats[k] || (cats[k] = {cat:k, debut:0, ajouts:0, liste:[], dispo:0});
  let prev = null; if (y > faAnnee0() && depth < 30) prev = faDPA(y - 1, depth + 1);
  Object.keys(DPA_CAT).forEach(k => {
    const man = cfg.fnacc && cfg.fnacc[k] !== undefined && cfg.fnacc[k] !== "" ? Number(cfg.fnacc[k]) : null;
    const v = man != null && isFinite(man) ? man : (prev ? ((prev.cats.find(c => c.cat === k) || {}).fin || 0) : 0);
    if (v) get(k).debut = r2(v); if (man != null) get(k).debutManuel = true;
  });
  faBiens(y).filter(b => !b.exclu && DPA_CAT[b.cat]).forEach(b => {
    const c = get(b.cat), cout = b.cat === "10.1" ? Math.min(b.cout, FISC.plafond101(Number(String(b.date).slice(0, 4)))) : b.cout;
    c.ajouts = r2(c.ajouts + cout); c.liste.push(Object.assign({}, b, {coutDpa: cout}));
  });
  (cfg.ventes || []).forEach(v => { if (DPA_CAT[v.cat]) get(v.cat).dispo = r2(get(v.cat).dispo + (Number(v.produit) || 0)); });
  let total = 0, recup = 0, perteF = 0;
  Object.values(cats).forEach(c => {
    const t = DPA_CAT[c.cat].t;
    c.avant = r2(c.debut + c.ajouts - c.dispo);
    if (c.avant < 0){ c.recup = r2(-c.avant); recup += c.recup; c.max = 0; c.dpa = 0; c.fin = 0; return; }
    const net = Math.max(0, c.ajouts - c.dispo), ratio = c.ajouts > 0 ? net / c.ajouts : 0, base = Math.max(0, c.avant - net);
    let imm = 0, autres = 0;
    c.liste.forEach(b => { const v = b.coutDpa * ratio, f = dpaFact(b.premiere); if (f === Infinity) imm += v; else autres += Math.min(v, v * t * f); });
    c.max = r2(Math.min(c.avant, (base * t + autres) * prorata + imm));
    const dem = cfg.dpaDemandee && cfg.dpaDemandee[c.cat] !== undefined && cfg.dpaDemandee[c.cat] !== "" ? Number(cfg.dpaDemandee[c.cat]) : null;
    c.demandeeManuelle = dem != null && isFinite(dem);
    c.dpa = r2(c.demandeeManuelle ? Math.max(0, Math.min(c.max, dem)) : c.max);
    c.fin = r2(c.avant - c.dpa);
    if (c.avant > 0 && c.debut + c.ajouts > 0 && cfg.vide && cfg.vide[c.cat]){ perteF += c.fin; c.perteFinale = c.fin; c.dpa = 0; c.fin = 0; }
    total += c.dpa;
  });
  return {cats: Object.values(cats).sort((a, b) => parseFloat(a.cat) - parseFloat(b.cat)), total: r2(total), recup: r2(recup), perteFinale: r2(perteF), prorata};
}
/* Revenu imposable (annexe 1) */
function faRevenu(y){
  const fr = fyRange(y), p = pnl(fr.start, fr.end), cfg = faCfg(y), dp = faDPA(y), L = [];
  L.push({l:"Bénéfice net selon les livres", v: r2(p.net), ligne:"Annexe 1, ligne 101"});
  if (p.repasND > 0.004) L.push({l:"Ajouter : 50 % des repas et frais de représentation", v: r2(p.repasND), ligne:"ligne 121"});
  if (dp.recup) L.push({l:"Ajouter : récupération d'amortissement", v: dp.recup, ligne:"ligne 107"});
  (cfg.ajust || []).forEach(a => { const v = Number(a.v) || 0; if (Math.abs(v) > 0.004) L.push({l:(v > 0 ? "Ajouter : " : "Déduire : ") + (a.l || "ajustement"), v: r2(v), id: a.id, manuel: true}); });
  L.push({l:"Déduire : déduction pour amortissement (DPA)", v: -dp.total, ligne:"ligne 403"});
  if (dp.perteFinale) L.push({l:"Déduire : perte finale", v: -dp.perteFinale, ligne:"ligne 404"});
  const net = r2(L.reduce((s, x) => s + x.v, 0)), pertes = r2(Math.max(0, Math.min(Number(cfg.pertes) || 0, Math.max(0, net))));
  return {L, net, pertes, imposable: r2(Math.max(0, net - pertes)), perte: net < 0 ? r2(-net) : 0, p, dp, placements: r2(p.rev.placements || 0)};
}
/* Impôt estimé : fédéral et Québec, déduction pour petite entreprise */
function faImpot(y){
  const rv = faRevenu(y), cfg = faCfg(y), r0 = faRange(y), prorata = Math.min(1, r0.jours / 365);
  const base = rv.imposable, plaf = r2(FISC.plafond * prorata), pme = r2(Math.min(base, plaf));
  const fed = r2(pme * FISC.fedPME + (base - pme) * FISC.fedGen);
  const h = Number(cfg.heures) || 0, pr = Number(cfg.primaire) || 0, s0 = 5000 * prorata, s1 = 5500 * prorata;
  const fH = Math.max(0, Math.min(1, (h - s0) / (s1 - s0))), fP = Math.max(0, Math.min(1, (pr - 25) / 25)), fq = Math.max(fH, fP), tq = FISC.qcDpe(r0.debut);
  const qc = r2(base * FISC.qcGen - pme * tq * fq);
  const af = Number(cfg.acomptesFed) || 0, aq = Number(cfg.acomptesQc) || 0;
  return {rv, base, pme, plaf, fed, qc, total: r2(fed + qc), fH, fP, fq, tq, h, pr, seuilH: Math.round(s1), soldeFed: r2(fed - af), soldeQc: r2(qc - aq), af, aq,
    taux: base > 0 ? (fed + qc) / base : 0, acomptes: {fed: fed > FISC.seuilAcomptes, qc: qc > FISC.seuilAcomptes}};
}
/* Dividendes de l'année civile : feuillets T5 et RL-3 (dividendes ordinaires d'une SPCC) */
function faDividendes(cy){
  const a = cy + "-01-01", b = cy + "-12-31", L = S.d.transactions.filter(t => t.type === "dividende" && t.date >= a && t.date <= b);
  const reel = r2(L.reduce((s, t) => s + (Number(t.montant) || 0), 0)), P = FISC.div(cy), imp = r2(reel * (1 + P.majo));
  return {n: L.length, reel, imposable: imp, creditFed: r2(imp * P.fed), creditQc: r2(imp * P.qc), P};
}
function faDates(y){
  const e = fyRange(y).end, [ey, em] = e.split("-").map(Number), fin = n => iso(lastDay(ey, em - 1 + n));
  return {solde3: fin(3), solde2: fin(2), t2: fin(6), cy: ey, feuillets: iso(lastDay(ey + 1, 1))};
}
/* Liste de vérification de fin d'exercice */
function faVerifs(y){
  const fr = fyRange(y), d = S.d, out = [], cfg = faCfg(y), coch = cfg.coches || {};
  const tx = d.transactions.filter(t => t.date >= fr.start && t.date <= fr.end), s = n => n > 1 ? "s" : "";
  const av = tx.filter(t => t.aVerifier).length; out.push({k:"verif", st: av ? "todo" : "ok", l:"Opérations marquées « à vérifier »", s: av ? av + " opération" + s(av) + " à revoir" : "Aucune", go:"transactions"});
  const sr = tx.filter(needsReceipt).length; out.push({k:"recus", st: sr ? "todo" : "ok", l:"Reçus des dépenses de 100 $ et plus", s: sr ? sr + " dépense" + s(sr) + " sans reçu" : "Tous joints", go:"transactions"});
  d.comptes.filter(c => c.sorte === "banque" || c.sorte === "carte").forEach(c => { const last = d.rapprochements.filter(r => r.compte === c.id).map(r => r.dateReleve).sort().pop() || ""; out.push({k:"rap:" + c.id, st: last >= fr.end ? "ok" : "todo", l:"Rapprochement : " + c.nom, s: last ? "Dernier relevé rapproché : " + dShort(last) : "Aucun rapprochement", go:"banque"}); });
  const km = d.km.filter(k => kmPerso(k) && !k.alloc && k.date >= fr.start && k.date <= fr.end).length; out.push({k:"km", st: km ? "todo" : "ok", l:"Allocation de kilométrage inscrite", s: km ? km + " trajet" + s(km) + " sans allocation" : "À jour", go:"km"});
  const per = periods(y).filter(p => p.end <= today() && !R().declarations[p.key]).length; out.push({k:"tps", st: per ? "todo" : "ok", l:"Déclarations de TPS et de TVQ de l'exercice", s: per ? per + " période" + s(per) + " à marquer comme produite" + s(per) : "Produites", go:"tvh"});
  const ar = d.transactions.filter(t => t.type === "revenu" && unpaid(t) && t.date <= fr.end).length, ap = d.transactions.filter(t => t.type === "depense" && unpaid(t) && t.date <= fr.end).length;
  out.push({k:"arap", st: coch.arap ? "ok" : "info", l:"Montants à recevoir et à payer révisés", s: ar + " à recevoir, " + ap + " à payer à la fin de l'exercice", go:"fournisseurs", manuel:true});
  const hl = faBiens(y).filter(b => b.horsLivres).length; out.push({k:"immo", st: hl ? "todo" : "ok", l:"Achats d'équipement inscrits aux livres", s: hl ? hl + " bien" + s(hl) + " de l'inventaire sans opération d'achat" : "Rien à signaler", go:"inventaire"});
  if (d.produits.length) out.push({k:"stock", st: coch.stock ? "ok" : "info", l:"Stock compté au " + dShort(fr.end), s:"Valeur du stock au coût à la fin de l'exercice", go:"inventaire", manuel:true});
  const sal = pnl(fr.start, fr.end).exp.salaires || 0; if (sal > 0) out.push({k:"paie", st: coch.paie ? "ok" : "info", l:"Salaires : feuillets T4 et RL-1", s:"La paie demande les retenues à la source et les feuillets ; un service de paie ou ton comptable s'en occupe habituellement.", manuel:true});
  out.push({k:"remun", st: coch.remun ? "ok" : "info", l:"Ta rémunération de l'année décidée", s:"Salaire ou dividendes : à décider avant la fin de l'exercice (avec ton comptable au besoin)", manuel:true});
  return out;
}
const faNum = v => v == null || v === "" ? "" : String(v).replace(".", ",");
function renderImpots(){
  const y = S.year, fr = fyRange(y), r0 = faRange(y), cfg = faCfg(y), V = faVerifs(y), I = faImpot(y), rv = I.rv, dp = rv.dp, D = faDates(y), dv = faDividendes(D.cy), biens = faBiens(y);
  const done = V.filter(v => v.st === "ok").length, chip = st => st === "ok" ? '<span class="chip ok">Fait</span>' : st === "todo" ? '<span class="chip due">À faire</span>' : '<span class="chip open">À vérifier</span>';
  const row = (l, v, cls, sub) => "<div><span>" + l + (sub ? '<br><small class="muted">' + sub + "</small>" : "") + '</span><span class="v' + (cls ? " " + cls : "") + '">' + v + "</span></div>";
  const inp = (id, v, ph, w) => '<input class="ctl fig" inputmode="decimal" data-fa="' + id + '" value="' + esc(faNum(v)) + '" placeholder="' + esc(ph || "0") + '" style="width:' + (w || 120) + 'px">';
  let h = '<div class="banner info"><span>Ce dossier prépare tes déclarations <b>T2</b> (fédéral) et <b>CO-17</b> (Québec) pour l\'' + esc(fyLabel(y).toLowerCase()) + (r0.start !== fr.start ? " (du " + dLong(r0.start) + " au " + dLong(r0.end) + ")" : "") + '. Les montants sont des <b>estimations</b> à reporter dans un logiciel homologué ou à remettre à ton comptable : la déclaration se transmet avec ce logiciel.</span><button class="btn sm" type="button" id="btn-fa-pdf">' + ico("i-pdf") + "Dossier PDF</button></div>";
  /* 1. Vérifications */
  h += '<div class="card"><div class="card-h"><h2>1. Avant de fermer l\'exercice</h2><span class="muted small">' + done + " sur " + V.length + '</span></div><div class="list fa-list">' +
    V.map(v => '<div class="item"><span class="t"><b>' + esc(v.l) + "</b><small>" + esc(v.s) + '</small></span><span class="v">' + chip(v.st) + (v.manuel ? '<label class="check" style="font-size:.8rem"><input type="checkbox" data-fa-coche="' + v.k + '"' + (v.st === "ok" ? " checked" : "") + "> Fait</label>" : "") + (v.go && v.st !== "ok" ? '<button class="btn sm" type="button" data-goto="' + v.go + '">Voir</button>' : "") + "</span></div>").join("") + "</div></div>";
  /* 2. États financiers */
  const p = rv.p;
  h += '<div class="card"><div class="card-h"><h2>2. États financiers (annexes 100 et 125)</h2></div><div class="kv">' + row("Revenus", fmt(p.totRev)) + row("Dépenses", fmt(p.totCv + p.totExp)) + row("<b>Bénéfice net comptable</b>", "<b>" + fmt(p.net) + "</b>") + "</div>" +
    '<p class="note">Le bilan et l\'état des résultats avec les codes IGRF sont les montants des annexes 100 et 125 du T2. Ils servent aussi pour la CO-17.</p><div class="actions"><button class="btn sm" type="button" data-fa-rp="igrf">Sommaire IGRF</button><button class="btn sm" type="button" data-fa-rp="resultats">État des résultats</button><button class="btn sm" type="button" data-fa-rp="bilan">Bilan</button></div>' +
    (rv.placements > 0.004 ? '<p class="err">Revenus de placement de ' + fmt(rv.placements) + " : ils sont imposés autrement (impôt remboursable). Fais vérifier cette partie par ton comptable.</p>" : "") + "</div>";
  /* 3. DPA */
  const optCat = cur => Object.entries(DPA_CAT).map(([k, c]) => '<option value="' + k + '"' + (k === cur ? " selected" : "") + ">" + c.l + " (" + Math.round(c.t * 100) + " %)</option>").join("");
  h += '<div class="card"><div class="card-h"><h2>3. Amortissement fiscal (DPA, annexe 8)</h2><span class="muted small">Total : ' + fmt(dp.total) + "</span></div>" +
    '<p class="note">Le camion, la remorque, les outils et l\'ordinateur ne sont pas déduits d\'un coup : chaque année, une partie de leur coût (la DPA) est déduite selon leur catégorie.' + (dp.prorata < 1 ? " Exercice de " + r0.jours + " jours : la DPA est réduite en proportion." : "") + "</p>" +
    '<h3>Biens achetés pendant l\'exercice</h3>' + (biens.length ? '<div class="fa-biens">' + biens.map(b => '<div class="fa-bien' + (b.exclu ? " off" : "") + '"><div class="row"><b style="flex:1">' + esc(b.desc) + '</b><span class="fig">' + fmt(b.cout) + '</span></div><small class="muted">' + esc(dShort(b.date) + " · " + b.source) + "</small>" +
      (b.horsLivres ? '<small class="err">Cet achat n\'est pas inscrit aux livres. Ajoute-le comme dépense « Machines et matériel (immobilisation) » pour qu\'il paraisse au bilan.</small>' : "") +
      (b.vehicule && b.cout > FISC.plafond101(Number(b.date.slice(0, 4))) && b.cat !== "10.1" ? '<small class="muted">Si c\'est une voiture de tourisme plutôt qu\'un camion de travail, choisis la catégorie 10.1 : le coût admissible est limité à ' + fmt(FISC.plafond101(Number(b.date.slice(0, 4)))) + " avant taxes.</small>" : "") +
      '<div class="fa-sel"><select class="ctl" data-fa-bien="' + esc(b.key) + '" data-fa-k="cat">' + optCat(b.cat) + '</select><select class="ctl" data-fa-bien="' + esc(b.key) + '" data-fa-k="premiere">' + DPA_1RE.map(([k, l]) => '<option value="' + k + '"' + (k === b.premiere ? " selected" : "") + ">" + l + "</option>").join("") + '</select><label class="check"><input type="checkbox" data-fa-bien="' + esc(b.key) + '" data-fa-k="exclu"' + (b.exclu ? " checked" : "") + "> Ne pas amortir</label>" + (b.manuel ? '<button class="btn link" type="button" data-fa-ajout-del="' + esc(b.id) + '">Retirer</button>' : "") + "</div></div>").join("") + "</div>"
      : '<p class="muted small">Aucun achat d\'équipement inscrit pendant l\'exercice.</p>') +
    '<details class="more" data-fa-d="aj"' + faOuvert("aj") + '><summary>Ajouter un bien acheté sans opération (ex. : camion apporté à la compagnie)</summary><div class="filters"><label class="grow">Description<input class="ctl" id="fa-aj-desc" maxlength="80"></label><label>Date<input class="ctl" type="date" id="fa-aj-date" value="' + esc(fr.end) + '"></label><label>Coût ($)<input class="ctl fig" id="fa-aj-cout" inputmode="decimal" style="width:110px"></label><label>Catégorie<select class="ctl" id="fa-aj-cat">' + optCat("10") + '</select></label><button class="btn" type="button" id="fa-aj-ok">Ajouter</button></div></details>' +
    '<h3>Par catégorie</h3><div class="sheet"><table><thead><tr><th>Catégorie</th><th class="num">Solde au début (FNACC)</th><th class="num">Achats</th><th class="num">Ventes</th><th class="num">DPA maximale</th><th class="num">DPA demandée</th><th class="num">Solde à la fin</th></tr></thead><tbody>' +
    (dp.cats.length ? dp.cats.map(c => '<tr><td><b>' + esc(DPA_CAT[c.cat].l) + '</b><br><small class="muted">' + esc(DPA_CAT[c.cat].d) + ", " + Math.round(DPA_CAT[c.cat].t * 100) + ' %</small></td><td class="num">' + inp("fnacc|" + c.cat, c.debutManuel ? (cfg.fnacc || {})[c.cat] : "", fmt(c.debut).replace(/\s?\$/, ""), 110) + '</td><td class="num">' + fmt(c.ajouts) + '</td><td class="num">' + fmt(c.dispo) + '</td><td class="num">' + fmt(c.max) + (c.recup ? '<br><small class="err">Récupération : ' + fmt(c.recup) + "</small>" : "") + '</td><td class="num">' + inp("dpaDemandee|" + c.cat, c.demandeeManuelle ? (cfg.dpaDemandee || {})[c.cat] : "", fmt(c.max).replace(/\s?\$/, ""), 110) + '</td><td class="num">' + fmt(c.fin) + "</td></tr>").join("") : '<tr><td colspan="7" class="muted">Aucun bien amortissable. Si la compagnie en avait déjà, entre leur solde de début (FNACC) ci-dessous.</td></tr>') + "</tbody></table></div>" +
    '<details class="more" data-fa-d="fn"' + faOuvert("fn") + '><summary>Solde de début d\'une autre catégorie, ou vente d\'un bien</summary><div class="filters"><label>Catégorie<select class="ctl" id="fa-fn-cat">' + optCat("8") + '</select></label><label>Solde au début ($)<input class="ctl fig" id="fa-fn-v" inputmode="decimal" style="width:110px"></label><button class="btn" type="button" id="fa-fn-ok">Enregistrer le solde</button></div>' +
    '<div class="filters"><label>Catégorie<select class="ctl" id="fa-ve-cat">' + optCat("10") + '</select></label><label>Prix de vente ($)<input class="ctl fig" id="fa-ve-v" inputmode="decimal" style="width:110px"></label><button class="btn" type="button" id="fa-ve-ok">Ajouter la vente</button></div>' +
    ((cfg.ventes || []).length ? '<div class="kv">' + cfg.ventes.map(v => row(esc(DPA_CAT[v.cat] ? DPA_CAT[v.cat].l : v.cat) + " : vente", fmt(v.produit) + ' <button class="btn link" type="button" data-fa-vente-del="' + esc(v.id) + '">Retirer</button>')).join("") + "</div>" : "") +
    '<p class="note">Le solde de début (FNACC) d\'une année est le solde de fin de l\'année précédente, repris de ta déclaration T2 de l\'an dernier. La DPA demandée peut être plus petite que la maximale si tu veux la garder pour plus tard. Règles 2026 : déduction accélérée de 1,5 fois le taux pour les biens acquis après 2024 et prêts avant 2030 ; une « mégadéduction » de 100 % est proposée pour certains biens acquis après le 14 septembre 2026 (projet de loi) ; plafond de 39 000 $ pour une voiture de tourisme achetée en 2026.</p></details></div>';
  /* 4. Revenu imposable */
  h += '<div class="card"><div class="card-h"><h2>4. Revenu imposable (annexe 1)</h2></div><div class="kv">' +
    rv.L.map(x => row(esc(x.l) + (x.manuel ? ' <button class="btn link" type="button" data-fa-ajust-del="' + esc(x.id) + '">Retirer</button>' : ""), fmt(x.v), "", x.ligne ? esc(x.ligne) : "")).join("") +
    row("<b>Revenu net aux fins de l'impôt</b>", "<b>" + fmt(rv.net) + "</b>") +
    row("Pertes des années précédentes à utiliser", inp("pertes", cfg.pertes, "0", 110), "", "Pertes autres qu'en capital reportées (annexe 4)") +
    row("<b>Revenu imposable</b>", "<b>" + fmt(rv.imposable) + "</b>") + (rv.perte ? row("Perte de l'année (reportable)", fmt(rv.perte), "neg") : "") + "</div>" +
    '<details class="more" data-fa-d="ad"' + faOuvert("ad") + '><summary>Ajouter un ajustement (amendes, frais de club, impôts passés en dépense…)</summary><div class="filters"><label class="grow">Description<input class="ctl" id="fa-ad-l" maxlength="80" placeholder="Ex. : Pénalités et intérêts sur impôts"></label><label>Montant ($)<input class="ctl fig" id="fa-ad-v" inputmode="decimal" style="width:110px" placeholder="+ ajoute, − déduit"></label><button class="btn" type="button" id="fa-ad-ok">Ajouter</button></div></details></div>';
  /* 5. Impôt estimé */
  h += '<div class="card"><div class="card-h"><h2>5. Impôt estimé de la compagnie</h2><span class="muted small">Taux moyen : ' + faPct(I.taux * 100) + "</span></div>" +
    '<div class="kv">' + row("Fédéral", fmt(I.fed), "", fmt(I.pme) + " au taux des petites entreprises (9 %)" + (I.base > I.pme ? ", " + fmt(I.base - I.pme) + " au taux général (15 %)" : "")) +
    row("Québec", fmt(I.qc), "", I.fq >= 1 ? "Déduction pour petite entreprise complète : taux de " + faPct((FISC.qcGen - I.tq) * 100) : I.fq > 0 ? "Déduction pour petite entreprise partielle (" + Math.round(I.fq * 100) + " %)" : "Taux général de 11,5 % : pas de déduction pour petite entreprise au Québec (voir les heures ci-dessous)") +
    row("<b>Total estimé</b>", "<b>" + fmt(I.total) + "</b>") + "</div>" +
    '<h3>Déduction pour petite entreprise du Québec</h3><p class="note">Au Québec, la déduction exige au moins ' + I.seuilH.toLocaleString("fr-CA") + ' heures rémunérées dans l\'année (employés, y compris toi si tu te verses un salaire), sinon elle diminue puis disparaît sous ' + Math.round(I.seuilH * 10 / 11).toLocaleString("fr-CA") + ' heures. Les entreprises surtout dans les secteurs primaire ou manufacturier y ont droit autrement.</p>' +
    '<div class="kv">' + row("Heures rémunérées dans l'exercice", inp("heures", cfg.heures, "0", 110)) + row("Part des activités primaires ou manufacturières (%)", inp("primaire", cfg.primaire, "0", 110)) + "</div>" +
    '<h3>Paiements</h3><div class="kv">' + row("Acomptes déjà versés au fédéral", inp("acomptesFed", cfg.acomptesFed, "0", 110)) + row("Acomptes déjà versés au Québec", inp("acomptesQc", cfg.acomptesQc, "0", 110)) +
    row("Solde à payer au fédéral", fmt(Math.max(0, I.soldeFed)), I.soldeFed > 0 ? "neg" : "", I.soldeFed < 0 ? "Remboursement attendu : " + fmt(-I.soldeFed) : "") + row("Solde à payer au Québec", fmt(Math.max(0, I.soldeQc)), I.soldeQc > 0 ? "neg" : "", I.soldeQc < 0 ? "Remboursement attendu : " + fmt(-I.soldeQc) : "") + "</div>" +
    ((I.acomptes.fed || I.acomptes.qc) ? '<p class="note"><b>Acomptes l\'an prochain :</b> quand l\'impôt dépasse 3 000 $, des acomptes sont exigés l\'année suivante. Une petite SPCC admissible paie par trimestre : environ ' + fmt(r2(I.fed / 4)) + " au fédéral et " + fmt(r2(I.qc / 4)) + " au Québec par trimestre, selon l'impôt de cette année.</p>" : "") +
    '<p class="note">Hypothèses : société privée sous contrôle canadien, non associée, revenu d\'entreprise exploitée activement seulement, capital imposable de moins de 10 M$. Taux 2026 : fédéral 9 % sur les premiers 500 000 $ et 15 % au-delà ; Québec 11,5 %, réduit à 3,2 % avec la déduction pour petite entreprise (2,2 % pour un exercice qui commence après le 29 avril 2026).</p></div>';
  /* 6. Dividendes */
  h += '<div class="card"><div class="card-h"><h2>6. Dividendes versés en ' + D.cy + ' (T5 et RL-3)</h2></div>' + (dv.reel > 0 ?
    '<div class="kv">' + row("Dividendes ordinaires versés", fmt(dv.reel), "", dv.n + " versement" + (dv.n > 1 ? "s" : "")) + "</div>" +
    '<div class="grid2"><div><h3>Feuillet T5 (fédéral)</h3><div class="kv">' + row("Case 10 : montant réel", fmt(dv.reel)) + row("Case 11 : montant imposable (+15 %)", fmt(dv.imposable)) + row("Case 12 : crédit d'impôt pour dividendes", fmt(dv.creditFed)) + '</div></div><div><h3>Relevé 3 (Québec)</h3><div class="kv">' + row("Case A2 : montant réel des dividendes ordinaires", fmt(dv.reel)) + row("Case B : montant imposable", fmt(dv.imposable)) + row("Case C : crédit d'impôt pour dividendes", fmt(dv.creditQc)) + "</div></div></div>" +
    '<p class="note">Feuillets à remettre à l\'actionnaire et à produire au plus tard le ' + dLong(D.feuillets) + ". Dividendes ordinaires (autres que déterminés), habituels pour une petite entreprise imposée au taux réduit.</p>"
    : '<p class="muted small">Aucun dividende inscrit en ' + D.cy + ". S'il y en a, inscris-les avec « + › Dividende » : les montants des feuillets T5 et RL-3 apparaîtront ici.</p>") + "</div>";
  /* 7. Dates */
  h += '<div class="card"><div class="card-h"><h2>7. Dates à retenir</h2></div><div class="kv">' + row("Solde d'impôt à payer (fédéral et Québec)", dLong(D.solde3), "", "3 mois après la fin de l'exercice pour une SPCC qui a droit à la déduction pour petite entreprise (sinon " + dLong(D.solde2) + ")") +
    row("Déclarations T2 et CO-17", dLong(D.t2), "", "6 mois après la fin de l'exercice, avec un logiciel homologué") + row("Feuillets T4, RL-1, T5 et RL-3", dLong(D.feuillets)) + "</div></div>";
  put($("fa-body"), h);
}
async function faPDFsave(){
  const y = S.year, path = "exports/fin-annee-" + y + ".pdf";
  try { await writeFile(path, new Blob([faPDF(y)], {type:"application/pdf"})); delete S.thumbs[path]; viewFile({fichier:path, nom:"Dossier de fin d'année " + y}); }
  catch(e){ console.error(e); toast("Création du PDF impossible : " + (e.message || e)); }
}
/* Dossier de fin d'année en PDF : à garder et à utiliser avec le logiciel homologué ou le comptable */
function faPDF(y){
  const r = R(), P = PDF(), M = 48, RX = P.W - M, ACC = "#2347A6", MUT = "#5F6F67", LINE = "#C7D1C9", BAND = "#EEF2FA", BOTTOM = P.H - 64;
  const I = faImpot(y), rv = I.rv, dp = rv.dp, D = faDates(y), dv = faDividendes(D.cy), V = faVerifs(y), r0 = faRange(y), fr = fyRange(y);
  let yy = 0;
  const page = () => { P.page(); yy = M; };
  const need = h => { if (yy + h > BOTTOM){ page(); P.text(M, yy + 8, (r.nom || "") + " · Dossier de fin d'année " + y + " (suite)", {size:9, color:MUT}); yy += 24; } };
  const titre = t => { need(40); yy += 10; P.text(M, yy + 10, t, {size:12.5, bold:true, color:ACC}); yy += 20; P.line(M, yy, RX, yy, {color:LINE, w:0.6}); yy += 6; };
  const ligne = (l, v, o) => { o = o || {}; const lines = wrapText(l, o.size || 9.5, !!o.bold, RX - M - 130); need(lines.length * 12 + 4); lines.forEach((s, i) => P.text(M + (o.ind || 0), yy + 11 + i * 12, s, {size:o.size || 9.5, bold:!!o.bold, color:o.color})); if (v !== undefined) P.text(RX, yy + 11, String(v), {size:o.size || 9.5, bold:!!o.bold, align:"right"}); yy += lines.length * 12 + 3; };
  const note = t => { const lines = wrapText(t, 8.5, false, RX - M); need(lines.length * 11 + 4); lines.forEach((s, i) => P.text(M, yy + 10 + i * 11, s, {size:8.5, color:MUT})); yy += lines.length * 11 + 6; };
  page();
  P.text(M, yy + 14, "Dossier de fin d'année " + y, {size:19, bold:true, color:ACC}); yy += 30;
  P.text(M, yy, r.nom || "", {size:11.5, bold:true}); yy += 14;
  [r.numero ? "NEQ : " + r.numero : "", r.noTPS ? "TPS : " + r.noTPS : "", r.noTVQ ? "TVQ : " + r.noTVQ : ""].filter(Boolean).forEach(s => { P.text(M, yy, s, {size:9, color:MUT}); yy += 11; });
  P.text(M, yy, "Exercice du " + dLong(r0.start) + " au " + dLong(r0.end) + " · Produit le " + dLong(today()), {size:9, color:MUT}); yy += 16;
  note("Estimations préparées à partir des livres de l'application, à reporter dans un logiciel homologué (T2 et CO-17) ou à remettre au comptable. Les logiciels homologués refont les calculs officiels.");
  titre("1. Liste de vérification");
  V.forEach(v => ligne(v.l + " — " + v.s, v.st === "ok" ? "Fait" : v.st === "todo" ? "À faire" : "À vérifier", {size:9}));
  titre("2. États financiers");
  ligne("Revenus", fmt(rv.p.totRev)); ligne("Dépenses", fmt(rv.p.totCv + rv.p.totExp)); ligne("Bénéfice net comptable", fmt(rv.p.net), {bold:true});
  note("Le détail par code IGRF (annexes 100 et 125) est dans Rapports, rapport « Sommaire IGRF », exportable en CSV.");
  titre("3. Déduction pour amortissement (annexe 8)");
  if (dp.cats.length) dp.cats.forEach(c => { ligne(DPA_CAT[c.cat].l + " (" + Math.round(DPA_CAT[c.cat].t * 100) + " %) — " + DPA_CAT[c.cat].d, "", {bold:true}); ligne("Solde au début (FNACC)", fmt(c.debut), {ind:12}); ligne("Achats", fmt(c.ajouts), {ind:12}); if (c.dispo) ligne("Ventes", fmt(c.dispo), {ind:12}); ligne("DPA demandée (maximale : " + fmt(c.max) + ")", fmt(c.dpa), {ind:12}); ligne("Solde à la fin", fmt(c.fin), {ind:12}); if (c.recup) ligne("Récupération d'amortissement", fmt(c.recup), {ind:12}); c.liste.forEach(b => ligne("• " + b.desc + " (" + dShort(b.date) + ", " + (DPA_1RE.find(x => x[0] === b.premiere) || ["", ""])[1] + ")", fmt(b.coutDpa), {ind:20, size:8.5})); });
  else ligne("Aucun bien amortissable", "");
  ligne("Total de la DPA", fmt(dp.total), {bold:true});
  titre("4. Revenu imposable (annexe 1)");
  rv.L.forEach(x => ligne(x.l + (x.ligne ? " (" + x.ligne + ")" : ""), fmt(x.v)));
  ligne("Revenu net aux fins de l'impôt", fmt(rv.net), {bold:true}); if (rv.pertes) ligne("Pertes des années précédentes utilisées", fmt(-rv.pertes)); ligne("Revenu imposable", fmt(rv.imposable), {bold:true});
  titre("5. Impôt estimé");
  ligne("Fédéral (" + fmt(I.pme) + " à 9 %" + (I.base > I.pme ? ", " + fmt(I.base - I.pme) + " à 15 %" : "") + ")", fmt(I.fed));
  ligne("Québec (taux général 11,5 %" + (I.fq > 0 ? ", déduction pour petite entreprise à " + Math.round(I.fq * 100) + " %" : ", sans déduction pour petite entreprise") + ")", fmt(I.qc));
  ligne("Total estimé", fmt(I.total), {bold:true});
  ligne("Heures rémunérées déclarées", (Number(faCfg(y).heures) || 0).toLocaleString("fr-CA")); if (I.af || I.aq) ligne("Acomptes versés (fédéral / Québec)", fmt(I.af) + " / " + fmt(I.aq));
  ligne("Solde à payer : fédéral", fmt(Math.max(0, I.soldeFed))); ligne("Solde à payer : Québec", fmt(Math.max(0, I.soldeQc)));
  note("Hypothèses : SPCC non associée, revenu d'entreprise exploitée activement, capital imposable de moins de 10 M$. Taux 2026 : fédéral 9 % (premiers 500 000 $) et 15 % ; Québec 11,5 %, 3,2 % avec la déduction pour petite entreprise (2,2 % pour un exercice qui commence après le 29 avril 2026), qui exige 5 500 heures rémunérées (ou des activités surtout primaires ou manufacturières).");
  titre("6. Dividendes " + D.cy + " (feuillets T5 et RL-3)");
  if (dv.reel > 0){ ligne("T5 case 10 — montant réel", fmt(dv.reel)); ligne("T5 case 11 — montant imposable", fmt(dv.imposable)); ligne("T5 case 12 — crédit d'impôt pour dividendes", fmt(dv.creditFed)); ligne("RL-3 case A2 — montant réel des dividendes ordinaires", fmt(dv.reel)); ligne("RL-3 case B — montant imposable", fmt(dv.imposable)); ligne("RL-3 case C — crédit d'impôt pour dividendes", fmt(dv.creditQc)); }
  else ligne("Aucun dividende inscrit", "");
  titre("7. Dates");
  ligne("Solde d'impôt (SPCC avec déduction pour petite entreprise)", dLong(D.solde3)); ligne("Solde d'impôt (autres cas)", dLong(D.solde2)); ligne("Déclarations T2 et CO-17", dLong(D.t2)); ligne("Feuillets T4, RL-1, T5 et RL-3", dLong(D.feuillets));
  P.pages.forEach((_, i) => { P.at(i); P.line(M, P.H - 42, RX, P.H - 42, {color:LINE, w:0.5}); P.text(M, P.H - 30, "Estimations à valider avec un logiciel homologué ou un comptable.", {size:7.5, color:MUT}); P.text(RX, P.H - 30, "Page " + (i + 1) + " de " + P.pages.length, {size:7.5, color:MUT, align:"right"}); });
  return P.bytes();
}
/* Saisies du dossier */
$("view-impots").addEventListener("change", e => {
  const t = e.target, y = S.year;
  if (t.dataset.fa){
    const [k, sub] = t.dataset.fa.split("|"), raw = t.value.trim(), v = raw === "" ? "" : num(raw);
    if (raw !== "" && !isFinite(v)){ toast("Entre un nombre, par exemple 1250,50"); return; }
    faSave(y, c => { if (sub){ c[k] = Object.assign({}, c[k] || {}); if (v === "") delete c[k][sub]; else c[k][sub] = r2(v); } else { if (v === "") delete c[k]; else c[k] = r2(v); } }, "Dossier d'impôt mis à jour");
  } else if (t.dataset.faBien){
    const key = t.dataset.faBien, k = t.dataset.faK, v = t.type === "checkbox" ? t.checked : t.value;
    faSave(y, c => { c.biens = Object.assign({}, c.biens || {}); c.biens[key] = Object.assign({}, c.biens[key] || {}, {[k]: v}); }, "DPA mise à jour");
  } else if (t.dataset.faCoche){
    const k = t.dataset.faCoche, v = t.checked; faSave(y, c => { c.coches = Object.assign({}, c.coches || {}, {[k]: v}); }, v ? "Marqué comme fait" : "Marqué à faire");
  }
});
$("view-impots").addEventListener("toggle", e => { const d = e.target; if (d.dataset && d.dataset.faD){ S.faOpen = Object.assign({}, S.faOpen || {}, {[d.dataset.faD]: d.open}); } }, true);
$("view-impots").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return; const y = S.year;
  if (b.id === "btn-fa-pdf") faPDFsave();
  else if (b.dataset.faRp){ go("rapports", () => { $("rp-type").value = b.dataset.faRp; $("rp-per").value = "exercice"; setReportRange(); }); }
  else if (b.id === "fa-aj-ok"){
    const desc = $("fa-aj-desc").value.trim(), cout = num($("fa-aj-cout").value), date = $("fa-aj-date").value || fyRange(y).end, ct = $("fa-aj-cat").value;
    if (!desc || !isFinite(cout) || cout <= 0) return toast("Entre la description et le coût du bien.");
    faSave(y, c => { c.ajouts = (c.ajouts || []).concat([{id: uid("b"), desc, cout: r2(cout), date, cat: ct}]); }, "Bien ajouté à la DPA");
  }
  else if (b.dataset.faAjoutDel){ const id = b.dataset.faAjoutDel; faSave(y, c => { c.ajouts = (c.ajouts || []).filter(a => a.id !== id); }, "Bien retiré"); }
  else if (b.id === "fa-fn-ok"){ const k = $("fa-fn-cat").value, v = num($("fa-fn-v").value); if (!isFinite(v) || v < 0) return toast("Entre le solde de début, par exemple 12500"); faSave(y, c => { c.fnacc = Object.assign({}, c.fnacc || {}, {[k]: r2(v)}); }, "Solde de début enregistré"); }
  else if (b.id === "fa-ve-ok"){ const k = $("fa-ve-cat").value, v = num($("fa-ve-v").value); if (!isFinite(v) || v <= 0) return toast("Entre le prix de vente."); faSave(y, c => { c.ventes = (c.ventes || []).concat([{id: uid("v"), cat: k, produit: r2(v)}]); }, "Vente ajoutée"); }
  else if (b.dataset.faVenteDel){ const id = b.dataset.faVenteDel; faSave(y, c => { c.ventes = (c.ventes || []).filter(v => v.id !== id); }); }
  else if (b.id === "fa-ad-ok"){ const l = $("fa-ad-l").value.trim(), v = num($("fa-ad-v").value); if (!l || !isFinite(v) || !v) return toast("Entre la description et le montant (négatif pour une déduction)."); faSave(y, c => { c.ajust = (c.ajust || []).concat([{id: uid("a"), l, v: r2(v)}]); }, "Ajustement ajouté"); }
  else if (b.dataset.faAjustDel){ const id = b.dataset.faAjustDel; faSave(y, c => { c.ajust = (c.ajust || []).filter(a => a.id !== id); }); }
});
