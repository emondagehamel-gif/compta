/* Lignes des factures et devis : un service ou un frais (location, outils, déplacement…), avec quantité, unité et prix */
const LT = [
  ["service", "Service", "Main-d'œuvre et services", "h", "Ex. : Émondage de 3 érables, 2 hommes"],
  ["location", "Location de matériel", "Location de matériel", "jour", "Ex. : Nacelle de 60 pi"],
  ["outils", "Outils et équipement", "Outils et équipement", "jour", "Ex. : Déchiqueteuse à branches"],
  ["deplacement", "Déplacement", "Déplacement", "km", "Ex. : Aller-retour au chantier"],
  ["consommables", "Consommables", "Consommables", "forfait", "Ex. : Essence, huile à chaîne"],
  ["materiaux", "Matériaux", "Matériaux", "unité", "Ex. : Haubans, paillis"],
  ["disposition", "Ramassage et disposition", "Ramassage et disposition", "voyage", "Ex. : Ramassage et transport des branches"],
  ["autre", "Autres frais", "Autres frais", "", "Ex. : Permis de coupe de la ville"],
  ["rabais", "Rabais", "Rabais", "", "Ex. : Rabais client fidèle"]
].map(([k, l, g, u, ph]) => ({k, l, g, u, ph}));
const LTM = Object.fromEntries(LT.map(t => [t.k, t]));
const LUNITES = [["", "—"], ["h", "heure (h)"], ["jour", "jour"], ["sem.", "semaine"], ["mois", "mois"], ["km", "km"], ["unité", "unité"], ["forfait", "forfait"], ["arbre", "arbre"], ["souche", "souche"], ["voyage", "voyage"], ["m³", "m³"], ["pi lin.", "pied linéaire"]];
/* Liste des unités d'une ligne (une unité ancienne ou d'un tarif s'ajoute à la liste) */
function uniteOptions(cur){ const c = String(cur || "").trim(), L = LUNITES.some(([v]) => v === c) ? LUNITES : LUNITES.concat([[c, c]]); return L.map(([v, l]) => '<option value="' + esc(v) + '"' + (v === c ? " selected" : "") + ">" + esc(l) + "</option>").join(""); }
const ligneType = l => LTM[l && l.type] ? l.type : "service";
const ligneMt = l => { const m = r2((Number(l.qte) || 0) * (Number(l.prix) || 0)); return l.type === "rabais" ? -Math.abs(m) : m; };
const qteTxt = l => { const u = String(l.unite || "").trim(), pl = Number(l.qte) >= 2 && /^[a-zà-ÿ]{3,}$/i.test(u) && !/[sx]$/i.test(u); return fq(l.qte) + (u ? " " + u + (pl ? "s" : "") : ""); };
/* Montant avant taxes d'une ligne (les prix peuvent être entrés taxes incluses) */
function ligneHT(doc, l){ const m = ligneMt(l); if (!doc.taxesIncluses) return m; const [a, b] = taxRates(doc.codeTaxe || "AUCUNE"); return r2(m * 100 / (100 + a + b)); }
/* Totaux : prix avant taxes (taxes ajoutées) ou taxes incluses (taxes extraites du total, au cent près) */
function docTotals(doc){
  const brut = r2((doc.lignes || []).reduce((s, l) => s + ligneMt(l), 0)), [a, b] = taxRates(doc.codeTaxe || "AUCUNE");
  if (doc.taxesIncluses && (a || b)){ const k = 100 + a + b, tx = r2(brut * a / k), tq = r2(brut * b / k); return {st: r2(brut - tx - tq), tx, tq, total: brut, ttc: true}; }
  const tx = r2(brut * a / 100), tq = r2(brut * b / 100); return {st: brut, tx, tq, total: r2(brut + tx + tq), ttc: false};
}
/* Taxes de chaque ligne, réparties au cent près pour que leur somme égale les taxes du document */
function ligneTaxes(doc){
  const L = doc.lignes || [], tot = docTotals(doc), [a, b] = taxRates(doc.codeTaxe || "AUCUNE"), k = tot.ttc ? 100 + a + b : 100;
  const part = (rate, cible) => { const raw = L.map(l => ligneMt(l) * rate / k), c = raw.map(v => Math.round(v * 100)); let diff = Math.round(cible * 100) - c.reduce((s, v) => s + v, 0);
    const ord = raw.map((v, i) => [v * 100 - c[i], i]).sort((x, y) => diff > 0 ? y[0] - x[0] : x[0] - y[0]);
    for (let j = 0; diff !== 0 && ord.length && j < ord.length * 3; j++){ c[ord[j % ord.length][1]] += diff > 0 ? 1 : -1; diff += diff > 0 ? -1 : 1; }
    return c.map(v => v / 100); };
  const tx = part(a, tot.tx), tq = part(b, tot.tq);
  return L.map((l, i) => { const m = ligneMt(l); return tot.ttc ? {ht: r2(m - tx[i] - tq[i]), tx: tx[i], tq: tq[i], ttc: m} : {ht: m, tx: tx[i], tq: tq[i], ttc: r2(m + tx[i] + tq[i])}; });
}
function ligneTaxTxt(doc, t){
  const [a, b] = taxRates(doc.codeTaxe || "AUCUNE"); if (!a && !b) return "";
  const parts = [a ? (doc.codeTaxe === "ON" ? "TVH " : "TPS ") + fmt(t.tx) : "", b ? "TVQ " + fmt(t.tq) : ""].filter(Boolean).join(" · ");
  return doc.taxesIncluses ? "Avant taxes " + fmt(t.ht) + " · " + parts : parts + " · Total avec taxes " + fmt(t.ttc);
}
/* Lignes regroupées par type, dans l'ordre de LT (services d'abord, rabais à la fin) */
function docGroupes(doc){
  const out = []; LT.forEach(t => { const L = (doc.lignes || []).filter(l => ligneType(l) === t.k); if (L.length) out.push({t, lignes: L, mt: r2(L.reduce((s, l) => s + ligneMt(l), 0))}); }); return out;
}
/* Texte prêt à envoyer avec le document (courriel, texto, Messenger…) */
function docMessage(kind, doc){
  const r = R(), isF = kind === "facture", t = docTotals(doc), cli = String(doc.client || "").trim(), G = docGenre(kind), lien = isF ? "" : signLien(kind, doc);
  return "Bonjour" + (cli ? " " + cli : "") + ",\n\nVoici " + G.la + " " + doc.numero + (r.nom ? (/^[aeiouyàâäéèêëîïôöûüù]/i.test(r.nom) ? " d'" : " de ") + r.nom : "") + " : " + fmt(t.total) + (t.tx || t.tq ? " taxes incluses" : "") +
    (isF ? (doc.echeance && doc.echeance > doc.date ? ", payable d'ici le " + dLong(doc.echeance) : ", payable à réception") : ", valide jusqu'au " + dLong(doc.echeance)) + "." +
    (lien ? "\n\nPour l'accepter, ouvrez le PDF joint et touchez le bouton vert « Signer en ligne » : vous signez avec le doigt, en 1 minute.\nVous pouvez aussi simplement répondre à ce message." : !isF ? "\nPour l'accepter, répondez simplement à ce message." : "") + "\n\nMerci et bonne journée,\n" + (r.nom || "") + (r.telephone ? "\n" + r.telephone : "") + (r.courriel ? "\n" + r.courriel : "");
}
/* Mise en page d'une facture ou d'une soumission : style simple et rassurant, d'après le modèle d'Émondage Hamel */
const DOC_COUL = {g:"#2F6B3B", tint:"#EDF4EE", ink:"#1E2622", mut:"#67716B", line:"#D2DBD4"};
function docTitre(kind){ return kind === "facture" ? "Facture" : (R().titreDevis || "Devis"); }
/* Accords : « la facture », « la soumission », mais « le devis » */
function docGenre(kind){ const t = docTitre(kind), f = t !== "Devis", m = t.toLowerCase(); return {t, m, la: (f ? "la " : "le ") + m, de: (f ? "de la " : "du ") + m, cette: (f ? "Cette " : "Ce ") + m, prep: f ? "préparée" : "préparé", presente: (f ? "la présente " : "le présent ") + m}; }
function docLayoutOrigine(kind, doc, logo, sigs){
  sigs = sigs || {}; const sg = doc.signature && doc.signature.nom ? doc.signature : null;
  const r = R(), P = PDF(), C = DOC_COUL, M = 54, RX = P.W - M, W = RX - M, isF = kind === "facture", tot = docTotals(doc), cli = clientOf(doc) || {};
  const G = docGenre(kind), titre = G.t, nom = String(r.nom || "Mon entreprise").trim(), BOTTOM = P.H - 74, grp = docGroupes(doc), multi = grp.length > 1;
  const XQ = M + 50, XP = RX - 168, XT = RX - 84, DW = XP - XQ - 16, TXL = doc.taxesLigne ? ligneTaxes(doc) : null;
  let y = 0, inTable = false;
  const T = (x, yy, s, o) => P.text(x, yy, s, Object.assign({color:C.ink}, o || {}));
  const h2 = (s) => { T(M, y + 13, s, {size:12.5, bold:true, color:C.g}); y += 29; };
  const label = (x, yy, s, w) => { T(x, yy, s.toUpperCase(), {size:7.8, bold:true, color:C.g, ls:1.1}); P.line(x, yy + 6, x + w, yy + 6, {color:C.line, w:0.8}); };
  const tableHead = () => { P.rect(M, y, W, 22, C.g);
    [["Qté", (M + XQ) / 2], ["Description", (XQ + XP) / 2], ["Prix unit." + (tot.ttc ? " (tx incl.)" : ""), (XP + XT) / 2], ["Total", (XT + RX) / 2]].forEach(([s, x]) => T(x, y + 14.5, s, {size:9, bold:true, color:"#FFFFFF", align:"center"}));
    y += 22; };
  const newPage = () => { P.page(); y = M; T(M, y + 10, nom.toUpperCase(), {size:10, bold:true, color:C.g, ls:0.8}); T(RX, y + 10, titre + " " + doc.numero + " (suite)", {size:9, color:C.mut, align:"right"}); y += 20; P.line(M, y, RX, y, {color:C.g, w:1}); y += 18; if (inTable) tableHead(); };
  const need = h => { if (y + h > BOTTOM) newPage(); };
  P.page();
  /* En-tête : nom et slogan à gauche, coordonnées et numéros de taxes à droite */
  let lx = M, ly = M + 18;
  if (logo){ let h = 50, w = logo.w * h / logo.h; if (w > 140){ w = 140; h = logo.h * w / logo.w; } P.image(logo, M, M, w, h); lx = M + w + 14; ly = M + Math.max(18, h / 2 + 4); }
  T(lx, ly, nom.toUpperCase(), {size:20, bold:true, color:C.g, ls:1}); ly += 17;
  if (r.slogan){ T(lx, ly, r.slogan, {size:9.5, italic:true, color:C.mut}); ly += 13; }
  String(r.adresse || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean).forEach(s => { T(lx, ly, s, {size:8.8, color:C.mut}); ly += 11.5; });
  let ry = M + 8;
  if (r.telephone){ T(RX, ry, r.telephone, {size:10, align:"right"}); ry += 13; }
  if (r.courriel){ T(RX, ry, r.courriel, {size:10, align:"right"}); ry += 14; }
  [r.noTPS ? "TPS : " + r.noTPS : "", r.noTVQ && quebec() ? "TVQ : " + r.noTVQ : "", r.neq ? "NEQ : " + r.neq : ""].filter(Boolean).forEach(s => { T(RX, ry, s, {size:8, color:C.mut, align:"right"}); ry += 10.5; });
  y = Math.max(ly, ry, logo ? M + 54 : 0) + 10; P.line(M, y, RX, y, {color:C.g, w:1.6});
  /* Titre */
  y += 36; T(P.W / 2, y, titre.toUpperCase(), {size:24, bold:true, color:C.g, align:"center", ls:3}); y += 26;
  /* Client et détails */
  const cw = (W - 30) / 2, rx2 = M + cw + 30, top = y;
  label(M, y, isF ? "Facturé à" : titre + " " + G.prep + " pour", cw); label(rx2, y, "Détails " + G.de, cw);
  let a = y + 24; T(M, a, doc.client || "", {size:11, bold:true}); a += 15;
  String(cli.adresse || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean).forEach(s => { T(M, a, s, {size:10}); a += 13; });
  [cli.telephone, cli.courriel].filter(Boolean).forEach(s => { T(M, a, s, {size:9, color:C.mut}); a += 12; });
  const det = [[titre + " n°", doc.numero], [isF ? "Date de facturation" : "Date", dLong(doc.date)]];
  if (doc.dateTravaux) det.push([isF ? "Date des travaux" : "Date prévue des travaux", dLong(doc.dateTravaux)]);
  det.push(isF ? ["Échéance", doc.echeance && doc.echeance > doc.date ? dLong(doc.echeance) : "À réception"] : ["Valide jusqu'au", dLong(doc.echeance)]);
  if (isF && doc.devis){ const v = S.d.devis.find(x => x.id === doc.devis); if (v) det.push(["Selon " + docGenre("devis").la + " n°", v.numero]); }
  let b = y + 24; det.forEach(([k, v]) => { const w = T(rx2, b, k + " :", {size:10, bold:true}); T(rx2 + w + 4, b, v, {size:10}); b += 15; });
  if (String(doc.lieu || "").trim()){ const w = T(rx2, b, "Lieu des travaux :", {size:10, bold:true}); const L = wrapText(String(doc.lieu).trim(), 10, false, cw - w - 4); L.forEach((s, i) => T(rx2 + w + 4, b + i * 13, s, {size:10})); b += L.length * 13 + 2; }
  y = Math.max(a, b) + 8;
  /* Description des travaux (texte libre) */
  if (String(doc.travaux || "").trim()){ const L = wrapText(String(doc.travaux).trim(), 10, false, W); need(36 + Math.min(L.length, 6) * 13); y += 6; h2("Description des travaux"); L.forEach(s => { need(14); T(M, y, s, {size:10}); y += 13; }); }
  /* Détail des travaux */
  need(31 + 22 + 30); y += 8; h2("Détail des travaux"); y -= 8; inTable = true; tableHead();
  const rowLines = (x1, x2) => { P.line(M, x1, M, x2, {color:C.line, w:0.6}); [XQ, XP, XT].forEach(x => P.line(x, x1, x, x2, {color:C.line, w:0.6})); P.line(RX, x1, RX, x2, {color:C.line, w:0.6}); P.line(M, x2, RX, x2, {color:C.line, w:0.6}); };
  const hdr = multi && grp.some(g => g.lignes.length > 1);
  grp.forEach(g => {
    if (hdr){ need(20 + 30); P.rect(M, y, W, 20, C.tint); T(XQ + 8, y + 13.5, g.t.g.toUpperCase(), {size:7.8, bold:true, color:C.g, ls:0.8}); T(RX - 8, y + 13.5, (g.mt < 0 ? "−" : "") + fmt(Math.abs(g.mt)), {size:8.8, bold:true, color:C.g, align:"right"}); P.line(M, y, M, y + 20, {color:C.line, w:0.6}); P.line(RX, y, RX, y + 20, {color:C.line, w:0.6}); P.line(M, y + 20, RX, y + 20, {color:C.line, w:0.6}); y += 20; }
    g.lignes.forEach(l => {
      const parts = String(l.description || "").split(/\r?\n/), main = wrapText(parts[0] || "", 10, false, DW), sub = parts.slice(1).join("\n").trim() ? wrapText(parts.slice(1).join("\n").trim(), 8.8, false, DW) : [];
      const lt = TXL ? ligneTaxTxt(doc, TXL[doc.lignes.indexOf(l)]) : "", cap = multi && !hdr ? 10.5 : 0, h = cap + Math.max(1, main.length) * 12.5 + sub.length * 11 + (lt ? 11 : 0) + 10, mt = ligneMt(l), yb = y + 14 + cap;
      need(h); const y0 = y;
      if (cap) T(XQ + 8, y + 12, g.t.g.toUpperCase(), {size:6.8, bold:true, color:C.g, ls:0.7});
      main.forEach((s, i) => T(XQ + 8, yb + i * 12.5, s, {size:10}));
      sub.forEach((s, i) => T(XQ + 8, yb + main.length * 12.5 + i * 11 - 1, s, {size:8.8, italic:true, color:C.mut}));
      if (lt) T(XQ + 8, yb + main.length * 12.5 + sub.length * 11 - 1, lt, {size:7.8, color:C.mut});
      T((M + XQ) / 2, yb, qteTxt(l), {size:10, align:"center"});
      T(XT - 8, yb, fmt(l.prix), {size:10, align:"right"});
      T(RX - 8, yb, (mt < 0 ? "−" : "") + fmt(Math.abs(mt)), {size:10, align:"right", color: mt < 0 ? C.g : C.ink});
      y += h; rowLines(y0, y);
    });
  });
  inTable = false;
  /* Sommaire */
  const t = isF && doc.transaction ? S.tmap[doc.transaction] : null, paid = t && !unpaid(t);
  const rows = [["Sous-total", tot.st], ...taxLines(doc.codeTaxe, tot)], bw = 240, bx = RX - bw, rh = 21;
  need(16 + rows.length * rh + 26 + (paid ? rh : 0)); y += 16; const sTop = y;
  const cell = (k, v, o) => { o = o || {}; if (o.fill) P.rect(bx, y, bw, o.h || rh, o.fill); P.line(bx, y, RX, y, {color:C.line, w:0.6}); P.line(bx, y, bx, y + (o.h || rh), {color:C.line, w:0.6}); P.line(RX - 96, y, RX - 96, y + (o.h || rh), {color:C.line, w:0.6}); P.line(RX, y, RX, y + (o.h || rh), {color:C.line, w:0.6});
    T(RX - 104, y + (o.h || rh) / 2 + 3.5, k + " :", {size:o.size || 10, bold:!!o.bold, align:"right", color:o.kc || C.ink}); T(RX - 8, y + (o.h || rh) / 2 + 3.5, v, {size:o.size || 10, bold:!!o.bold, align:"right", color:o.vc || C.ink}); y += o.h || rh; };
  rows.forEach(([k, v]) => cell(k, fmt(v)));
  cell(isF ? "Total à payer" : "Total", fmt(tot.total), {fill:C.tint, bold:true, size:12, vc:C.g, h:26});
  if (isF && paid) cell("Payée le " + dShort((t.paiement && t.paiement.date) || t.date) + " · Solde", fmt(0), {size:9.5, vc:C.g});
  P.line(bx, y, RX, y, {color:C.line, w:0.6});
  /* À gauche du sommaire : rappel des taxes incluses */
  let ny = sTop + 14; if (tot.ttc) wrapText((isF ? "Montant total convenu avec le client" : "Prix forfaitaire convenu avec le client") + ", taxes incluses.", 8.5, false, bx - M - 24).forEach(s => { T(M, ny, s, {size:8.5, italic:true, color:C.mut}); ny += 11; });
  y = Math.max(y, ny);
  /* Modalités */
  const pay = String(r.modePaiement || "").trim();
  const bullet = (parts) => { const full = parts.map(p => p[0]).join(""); const L = wrapText(full, 10, false, W - 16); need(L.length * 13 + 2); T(M + 4, y, "•", {size:10});
    if (L.length === 1 && parts.length > 1){ let x = M + 16; parts.forEach(([s, bo]) => { x += T(x, y, s, {size:10, bold:!!bo}); }); y += 13; } else { L.forEach(s => { T(M + 16, y, s, {size:10}); y += 13; }); } };
  if (isF){
    need(60); y += 18; h2("Modalités de paiement");
    const txt = paid ? "Cette facture a été payée le " + dLong((t.paiement && t.paiement.date) || t.date) + ". Merci!" : (doc.dateTravaux ? "Les travaux décrits ci-dessus ont été complétés le " + dLong(doc.dateTravaux) + ". " : "") + (doc.echeance && doc.echeance > doc.date ? "Le solde est payable d'ici le " + dLong(doc.echeance) + "." : "Le solde est payable à réception de la présente facture.");
    wrapText(txt, 10, false, W).forEach(s => { need(13); T(M, y, s, {size:10}); y += 13; });
    if (pay && !paid){ y += 3; const w = T(M, y, "Mode de paiement :", {size:10, bold:true}); T(M + w + 4, y, pay, {size:10}); y += 13; }
    if (sg){
      need(116); y += 14; h2("Confirmation du client");
      wrapText("Le client confirme que les travaux décrits dans la présente facture ont été effectués.", 10, false, W).forEach(s => { T(M, y, s, {size:10}); y += 13; });
      y += 6; const cw2 = (W - 30) / 2; if (sigs.client) sigImage(P, sigs.client, M + 4, y, cw2 - 8, 32); P.line(M, y + 34, M + cw2, y + 34, {color:"#8A948E", w:0.7});
      T(M, y + 46, sg.nom + " · " + dLong(sg.date) + (sg.heure ? " à " + hmTxt(sg.heure) : ""), {size:8.5, color:C.ink}); T(M, y + 58, "Signé électroniquement" + sigVia(sg), {size:7.5, italic:true, color:C.mut}); y += 62;
    }
  } else {
    need(70); y += 14; h2("Modalités");
    String(r.conditionsDevis || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean).forEach(s => bullet([[s]]));
    const nj = daysBetween(doc.date, doc.echeance || doc.date); if (nj > 0) bullet([[G.cette + " est valide pour " + nj + " jours, soit jusqu'au " + dLong(doc.echeance) + "."]]);
    if (pay) bullet([["Mode de paiement : "], [pay, true]]);
    /* Acceptation */
    const lien = sg ? "" : signLien(kind, doc);
    need(120); y += 8; h2("Acceptation " + G.de);
    wrapText("En signant ci-dessous, le client accepte les travaux et le prix décrits dans " + G.presente + ".", 10, false, W).forEach(s => { T(M, y, s, {size:10}); y += 13; });
    y += 8;
    const bloc = (x, titre, img, date, pied) => { T(x, y, titre, {size:10, bold:true}); if (img) sigImage(P, img, x + 4, y + 6, cw - 8, 32); P.line(x, y + 40, x + cw, y + 40, {color:"#8A948E", w:0.7}); T(x, y + 52, lien && x === rx2 ? "Signature (à la main, ou touchez « Signer en ligne »)" : "Signature", {size:8.5, color:C.mut});
      T(x, y + 67, "Date : " + (date ? dLong(date) : "______________________"), {size:8.5, color: date ? C.ink : C.mut}); if (pied) T(x, y + 80, pied, {size:7.5, italic:true, color:C.mut}); };
    const sc = doc.signatureCie && doc.signatureCie.nom ? doc.signatureCie : null;
    bloc(M, nom, sigs.cie || null, sc ? sc.date : (sigs.cie ? doc.date : ""), sc ? "Signé pour l'entreprise par " + sc.nom : "");
    bloc(rx2, sg ? "Client : " + sg.nom : "Client", sg && sigs.client ? sigs.client : null, sg ? sg.date : "", sg ? sigPied(sg) : "");
    if (lien) sigBoutonPDF(P, rx2 + 4, y + 9, lien, C.g);
    y += sg || sc ? 84 : 72;
  }
  /* Remerciements */
  const msg = String(doc.message || "").trim(), extra = msg && !/^merci de votre confiance\s*[.!]?$/i.test(msg) ? wrapText(msg, 9, false, W - 40) : [];
  if (y + 30 + extra.length * 12 > P.H - 56) newPage(); y += 16; T(P.W / 2, y, "Merci de votre confiance.", {size:11, bold:true, color:C.g, align:"center"}); y += 15;
  extra.forEach(s => { T(P.W / 2, y, s, {size:9, italic:true, color:C.mut, align:"center"}); y += 12; });
  /* Pied de page */
  const pied = [nom, r.telephone, r.courriel].filter(Boolean).join("  |  ");
  P.pages.forEach((_, i) => { P.at(i); P.line(M, P.H - 50, RX, P.H - 50, {color:C.line, w:0.6}); T(P.W / 2, P.H - 36, pied + (P.pages.length > 1 ? "   ·   Page " + (i + 1) + " de " + P.pages.length : ""), {size:8.5, color:C.mut, align:"center"}); });
  return P;
}
function docPDF(kind, doc, logo, sigs){ return docLayout(kind, doc, logo, sigs).bytes(); }
/* Signature : image centrée dans sa case, sans la déformer */
function sigImage(P, img, x, y, w, h){ let iw = img.w, ih = img.h, k = Math.min(w / iw, h / ih); iw *= k; ih *= k; P.image(img, x, y + (h - ih), iw, ih); }
const hmTxt = h => { const m = String(h || "").match(/^(\d{1,2}):(\d{2})/); return m ? Number(m[1]) + " h " + m[2] : ""; };
/* Image JPEG prête pour le PDF (une autre sorte d'image est convertie) */
async function jpegObj(blob){
  const bm = await createImageBitmap(blob); let data;
  if (blob.type === "image/jpeg") data = new Uint8Array(await blob.arrayBuffer());
  else { const c = document.createElement("canvas"); c.width = bm.width; c.height = bm.height; const g = c.getContext("2d"); g.fillStyle = "#FFFFFF"; g.fillRect(0, 0, c.width, c.height); g.drawImage(bm, 0, 0); data = new Uint8Array(await (await new Promise(r => c.toBlob(r, "image/jpeg", 0.9))).arrayBuffer()); }
  return {w: bm.width, h: bm.height, data};
}
/* Signature à l'écran : le client signe avec le doigt, un stylet ou la souris. Rend {blob, img, nom, date, heure, signeLe} ou null. */
function sigPad(o){
  o = o || {};
  return new Promise(resolve => {
    const ov = document.createElement("div"); ov.className = "sig-ov"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", o.titre || "Signature");
    ov.innerHTML = '<div class="sig-box"><div class="sig-h"><b>' + esc(o.titre || "Signature") + '</b><button type="button" class="sig-x" aria-label="Fermer">×</button></div>' + (o.texte ? '<p class="sig-t">' + esc(o.texte) + "</p>" : "") +
      '<div class="sig-zone"><canvas></canvas><span class="sig-ph">Signez ici</span><span class="sig-l"></span></div>' +
      (o.nom !== false ? '<label class="sig-n"><span>Nom de la personne qui signe</span><input type="text" maxlength="80" autocomplete="off" value="' + esc(o.nom || "") + '"></label>' : "") +
      '<div class="sig-f"><button type="button" class="sig-b sig-clear">Effacer</button><span style="flex:1"></span><button type="button" class="sig-b sig-cancel">Annuler</button><button type="button" class="sig-b sig-ok" disabled>' + esc(o.ok || "Signer") + "</button></div></div>";
    document.body.appendChild(ov); document.body.classList.add("sig-open");
    const cv = ov.querySelector("canvas"), zone = ov.querySelector(".sig-zone"), g = cv.getContext("2d"), okB = ov.querySelector(".sig-ok"), nomI = ov.querySelector(".sig-n input"), dpr = Math.max(1, window.devicePixelRatio || 1);
    let strokes = [], cur = null;
    const draw = () => { g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, cv.width, cv.height); g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = "#17244D"; g.lineWidth = 2.6;
      strokes.forEach(st => { g.beginPath(); st.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); if (st.length === 1) g.lineTo(st[0][0] + 0.5, st[0][1] + 0.5); g.stroke(); });
      ov.querySelector(".sig-ph").hidden = strokes.length > 0; okB.disabled = !strokes.length || (nomI ? !nomI.value.trim() : false); };
    const size = () => { const r = zone.getBoundingClientRect(); cv.width = Math.max(1, Math.round(r.width * dpr)); cv.height = Math.max(1, Math.round(r.height * dpr)); cv.style.width = r.width + "px"; cv.style.height = r.height + "px"; draw(); };
    const pt = e => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    cv.addEventListener("pointerdown", e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch(er){} cur = [pt(e)]; strokes.push(cur); draw(); });
    cv.addEventListener("pointermove", e => { if (!cur) return; e.preventDefault(); cur.push(pt(e)); draw(); });
    const up = () => { cur = null; }; cv.addEventListener("pointerup", up); cv.addEventListener("pointercancel", up); cv.addEventListener("lostpointercapture", up);
    if (nomI) nomI.addEventListener("input", draw);
    const close = v => { window.removeEventListener("resize", size); document.removeEventListener("keydown", key, true); ov.remove(); document.body.classList.remove("sig-open"); resolve(v); };
    const key = e => { if (e.key === "Escape"){ e.stopPropagation(); e.preventDefault(); close(null); } };
    document.addEventListener("keydown", key, true); window.addEventListener("resize", size);
    ov.querySelector(".sig-x").onclick = () => close(null); ov.querySelector(".sig-cancel").onclick = () => close(null);
    ov.querySelector(".sig-clear").onclick = () => { strokes = []; draw(); };
    okB.onclick = async () => {
      okB.disabled = true;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity; strokes.forEach(st => st.forEach(([a, b]) => { x0 = Math.min(x0, a); y0 = Math.min(y0, b); x1 = Math.max(x1, a); y1 = Math.max(y1, b); }));
      const pad = 6, k = Math.min(2, 900 / Math.max(1, x1 - x0 + pad * 2)), w = Math.max(1, Math.round((x1 - x0 + pad * 2) * k)), h = Math.max(1, Math.round((y1 - y0 + pad * 2) * k));
      const c = document.createElement("canvas"); c.width = w; c.height = h; const gx = c.getContext("2d"); gx.fillStyle = "#FFFFFF"; gx.fillRect(0, 0, w, h);
      gx.setTransform(k, 0, 0, k, (pad - x0) * k, (pad - y0) * k); gx.lineCap = "round"; gx.lineJoin = "round"; gx.strokeStyle = "#17244D"; gx.lineWidth = 2.6;
      strokes.forEach(st => { gx.beginPath(); st.forEach((q, i) => i ? gx.lineTo(q[0], q[1]) : gx.moveTo(q[0], q[1])); if (st.length === 1) gx.lineTo(st[0][0] + 0.5, st[0][1] + 0.5); gx.stroke(); });
      const blob = await new Promise(r => c.toBlob(r, "image/jpeg", 0.88)); if (!blob){ okB.disabled = false; return; }
      const now = new Date(), pad2 = n => String(n).padStart(2, "0");
      close({blob, img: {w, h, data: new Uint8Array(await blob.arrayBuffer())}, nom: nomI ? nomI.value.trim() : "", date: today(), heure: pad2(now.getHours()) + ":" + pad2(now.getMinutes()), signeLe: now.toISOString()});
    };
    requestAnimationFrame(size);
  });
}
function sigTexte(kind, doc){
  const G = docGenre(kind), t = docTotals(doc);
  return kind === "facture" ? "En signant, je confirme que les travaux décrits dans la facture " + doc.numero + " ont été effectués (total : " + fmt(t.total) + ")."
    : "En signant, j'accepte les travaux et le prix décrits dans " + G.la + " " + doc.numero + " : total de " + fmt(t.total) + (t.tx || t.tq ? ", taxes incluses" : "") + ".";
}
/* Les mêmes pages en images JPEG (pour Snapchat, Messenger, les textos) */
async function pdfImages(P, scale){
  scale = scale || 2.5; const out = [];
  for (const list of P.draws){
    const c = document.createElement("canvas"); c.width = Math.round(P.W * scale); c.height = Math.round(P.H * scale);
    const g = c.getContext("2d"); g.fillStyle = "#FFFFFF"; g.fillRect(0, 0, c.width, c.height); g.scale(scale, scale); g.textBaseline = "alphabetic";
    for (const o of list){
      if (o.k === "t"){ g.fillStyle = o.color || "#000000"; g.font = (o.bold ? "bold " : "") + o.size + "px Helvetica, Arial, sans-serif"; g.textAlign = o.align || "left"; g.fillText(o.s, o.x, o.y); }
      else if (o.k === "l"){ g.strokeStyle = o.color; g.lineWidth = o.w; g.beginPath(); g.moveTo(o.x1, o.y1); g.lineTo(o.x2, o.y2); g.stroke(); }
      else if (o.k === "r"){ g.fillStyle = o.color; g.fillRect(o.x, o.y, o.w, o.h); }
      else if (o.k === "p"){ g.lineCap = "round"; g.lineJoin = "round"; g.beginPath(); o.cmds.forEach(c => c[0] === "M" ? g.moveTo(c[1], c[2]) : c[0] === "L" ? g.lineTo(c[1], c[2]) : c[0] === "C" ? g.bezierCurveTo(c[1], c[2], c[3], c[4], c[5], c[6]) : g.closePath()); if (o.fill){ g.fillStyle = o.fill; g.fill(); } if (o.stroke){ g.strokeStyle = o.stroke; g.lineWidth = o.w; g.stroke(); } }
      else if (o.k === "i"){ try { const bm = await createImageBitmap(new Blob([o.img.data], {type:"image/jpeg"})); g.drawImage(bm, o.x, o.y, o.w, o.h); } catch(e){} }
    }
    out.push(await new Promise(res => c.toBlob(res, "image/jpeg", 0.9)));
  }
  return out;
}
async function docImages(kind, doc, logo, sigs){
  const P = docLayout(kind, doc, logo, sigs), blobs = await pdfImages(P), base = fileSafe(doc.numero + " " + (doc.client || ""));
  return blobs.filter(Boolean).map((b, i) => new File([b], base + (blobs.length > 1 ? "-page-" + (i + 1) : "") + ".jpg", {type:"image/jpeg"}));
}
