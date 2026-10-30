/* Styles des factures et soumissions : « Nature » (cartes douces), « Moderne » (bandeau vert), « Épuré » (sobre). Le modèle d'origine reste offert. */
const DOC_STYLES = {origine: "Modèle d'origine", nature: "Nature : doux et rassurant", moderne: "Moderne : bandeau vert", epure: "Épuré : sobre et aéré"};
function docLayout(kind, doc, logo, sigs){ const st = R().styleDoc; return DOC_STYLES[st] && st !== "origine" ? docLayoutStyle(kind, doc, logo, sigs, st) : docLayoutOrigine(kind, doc, logo, sigs); }
/* Emblème : une feuille dans un cercle (quand il n'y a pas de logo) */
function docEmbleme(P, cx, cy, R0, fond, feuille){
  /* Même feuille que le logo de l'application (dessin sur 100 unités, centré sur 48,52) */
  P.circle(cx, cy, R0, {fill: fond});
  const k = R0 / 50 * 1.02, X = u => cx + (u - 48) * k, Y = v => cy + (v - 52) * k;
  P.path([["M", X(30), Y(70)], ["C", X(17.6), Y(40), X(55.9), Y(29.9), X(74), Y(26)], ["C", X(70.1), Y(44.1), X(60), Y(82.4), X(30), Y(70)], ["Z"]], {fill: feuille});
  P.path([["M", X(30.5), Y(69.5)], ["L", X(21), Y(79)]], {stroke: feuille, w: 4.6 * k});
  P.path([["M", X(33), Y(67)], ["C", X(44), Y(56), X(55), Y(45), X(66.5), Y(33.5)]], {stroke: fond, w: 3.2 * k});
}
function docLayoutStyle(kind, doc, logo, sigs, st){
  sigs = sigs || {}; const sg = doc.signature && doc.signature.nom ? doc.signature : null, MOD = st === "moderne", EPU = st === "epure";
  const C = Object.assign({g:"#2F6B3B", g2:"#4C8B57", tint:"#EDF5EE", soft:"#F7FAF7", ink:"#1E2622", mut:"#68736C", line:"#DCE4DE", pale:"#CFE3D3"},
    MOD ? {g:"#235C37", tint:"#E8F2EA", soft:"#F5F9F6"} : EPU ? {tint:"#F3F5F3", soft:"#FAFBFA", line:"#E2E5E3", ink:"#1B1E1C"} : {});
  const r = R(), P = PDF(), M = 50, RX = P.W - M, W = RX - M, isF = kind === "facture", tot = docTotals(doc), cli = clientOf(doc) || {};
  const G = docGenre(kind), titre = G.t, nom = String(r.nom || "Mon entreprise").trim(), grp = docGroupes(doc), multi = grp.length > 1, TXL = doc.taxesLigne ? ligneTaxes(doc) : null;
  const BOTTOM = P.H - (MOD ? 62 : 66), XD = M + 10, XQ = RX - 196, XP = RX - 92, DW = XQ - 34 - XD;
  let y = 0, inTable = false, zebra = 0;
  const T = (x, yy, s, o) => P.text(x, yy, s, Object.assign({color:C.ink}, o || {}));
  const h2 = s => { if (EPU){ T(M, y + 10, s.toUpperCase(), {size:8.5, bold:true, color:C.g, ls:1.6}); y += 23; } else { T(M, y + 12, s, {size:12.5, bold:true, color:C.g}); y += 25; } };
  const caps = (x, yy, s, col) => T(x, yy, s.toUpperCase(), {size:7.4, bold:true, color:col || (EPU ? C.mut : C.g), ls:1.1});
  const tableHead = () => {
    if (EPU){ caps(XD, y + 12, "Description", C.mut); T(XQ, y + 12, "QTÉ", {size:7.4, bold:true, color:C.mut, ls:1.1, align:"center"}); T(XP, y + 12, (tot.ttc ? "Prix (tx incl.)" : "Prix unit.").toUpperCase(), {size:7.4, bold:true, color:C.mut, ls:1.1, align:"right"}); T(RX - 10, y + 12, "TOTAL", {size:7.4, bold:true, color:C.mut, ls:1.1, align:"right"}); P.line(M, y + 19, RX, y + 19, {color:C.ink, w:0.9}); y += 22; }
    else { const fill = MOD ? C.tint : C.g, tc = MOD ? C.g : "#FFFFFF"; P.rrect(M, y, W, 24, 5, {fill});
      T(XD, y + 15.5, "Description", {size:9, bold:true, color:tc}); T(XQ, y + 15.5, "Qté", {size:9, bold:true, color:tc, align:"center"}); T(XP, y + 15.5, tot.ttc ? "Prix (tx incl.)" : "Prix unit.", {size:9, bold:true, color:tc, align:"right"}); T(RX - 10, y + 15.5, "Total", {size:9, bold:true, color:tc, align:"right"}); y += 26; }
    zebra = 0; };
  const newPage = () => { P.page(); y = M; T(M, y + 10, nom.toUpperCase(), {size:9.5, bold:true, color:C.g, ls:0.9}); T(RX, y + 10, titre + " " + doc.numero + " (suite)", {size:9, color:C.mut, align:"right"}); y += 18; P.line(M, y, RX, y, {color:EPU ? C.line : C.g, w:0.8}); y += 18; if (inTable) tableHead(); };
  const need = h => { if (y + h > BOTTOM) newPage(); };
  P.page();
  /* ---------- En-tête ---------- */
  const contact = [r.telephone, r.courriel].filter(Boolean), nos = [r.noTPS ? "TPS " + r.noTPS : "", r.noTVQ && quebec() ? "TVQ " + r.noTVQ : "", r.neq ? "NEQ " + r.neq : ""].filter(Boolean);
  if (MOD){
    const BH = 98; P.rect(0, 0, P.W, BH, C.g);
    let lx = M; if (logo){ let h = 46, w = logo.w * h / logo.h; if (w > 120){ w = 120; h = logo.h * w / logo.w; } P.rrect(M - 4, BH / 2 - h / 2 - 4, w + 8, h + 8, 6, {fill:"#FFFFFF"}); P.image(logo, M, BH / 2 - h / 2, w, h); lx = M + w + 18; }
    else { docEmbleme(P, M + 24, BH / 2, 24, "#FFFFFF", C.g); lx = M + 62; }
    T(lx, BH / 2 + 1, nom.toUpperCase(), {size:20, bold:true, color:"#FFFFFF", ls:1.2}); if (r.slogan) T(lx, BH / 2 + 17, r.slogan, {size:9.5, italic:true, color:C.pale});
    let ry = BH / 2 - (contact.length * 13 + nos.length * 10.5) / 2 + 9; contact.forEach(s => { T(RX, ry, s, {size:10, bold:true, color:"#FFFFFF", align:"right"}); ry += 13; }); ry += 2; nos.forEach(s => { T(RX, ry, s, {size:7.8, color:C.pale, align:"right"}); ry += 10.5; });
    y = BH + 36;
  } else {
    let lx = M, top = M - 6;
    if (logo){ let h = 46, w = logo.w * h / logo.h; if (w > 130){ w = 130; h = logo.h * w / logo.w; } P.image(logo, M, top, w, h); lx = M + w + 14; }
    else if (EPU){ docEmbleme(P, M + 12, top + 15, 12, C.g, "#FFFFFF"); lx = M + 32; }
    else { docEmbleme(P, M + 23, top + 23, 23, C.g, "#FFFFFF"); lx = M + 58; }
    T(lx, top + (EPU ? 20 : 21), nom.toUpperCase(), {size:EPU ? 15 : 19, bold:true, color:EPU ? C.ink : C.g, ls:EPU ? 2.4 : 0.9});
    if (r.slogan) T(lx, top + (EPU ? 34 : 37), r.slogan, {size:9.2, italic:!EPU, color:C.mut});
    let ry = top + 8; contact.forEach(s => { T(RX, ry, s, {size:9.8, align:"right"}); ry += 12.5; }); ry += 1; nos.forEach(s => { T(RX, ry, s, {size:7.6, color:C.mut, align:"right"}); ry += 10; });
    y = Math.max(top + 50, ry) + 10;
    if (EPU) P.line(M, y, RX, y, {color:C.line, w:0.8}); else { P.line(M, y, RX, y, {color:C.g, w:1.4}); }
    y += 32;
  }
  /* ---------- Titre et détails ---------- */
  const det = [[isF ? "Date de facturation" : "Date", dLong(doc.date)]];
  if (doc.dateTravaux) det.push([isF ? "Date des travaux" : "Travaux prévus le", dLong(doc.dateTravaux)]);
  det.push(isF ? ["Échéance", doc.echeance && doc.echeance > doc.date ? dLong(doc.echeance) : "À réception"] : ["Valide jusqu'au", dLong(doc.echeance)]);
  if (isF && doc.devis){ const v = S.d.devis.find(x => x.id === doc.devis); if (v) det.push(["Selon " + docGenre("devis").la, v.numero]); }
  const cw = (W - 18) / 2, x2 = M + cw + 18, lieu = String(doc.lieu || "").trim();
  const cliL = [[doc.client || "", {size:11.5, bold:true, h:15}]].concat(String(cli.adresse || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean).map(s => [s])).concat([cli.telephone, cli.courriel].filter(Boolean).map(s => [s, {size:9, color:C.mut, h:12}]));
  const lieuL = lieu ? wrapText(lieu, 10, false, cw - 28) : [];
  if (EPU){
    caps(M, y - 8, titre, C.g); T(M, y + 14, doc.numero, {size:22, bold:true}); let dy = y - 8;
    det.forEach(([k, v]) => { T(RX - 150, dy, k, {size:8.8, color:C.mut, align:"right"}); T(RX, dy, v, {size:9.2, bold:true, align:"right"}); dy += 13.5; });
    y = Math.max(y + 32, dy + 8);
    const col = (x, label, lignes) => { P.line(x, y, x + cw, y, {color:C.line, w:0.8}); caps(x, y + 15, label); let yy = y + 30; lignes.forEach(([s, o]) => { T(x, yy, s, Object.assign({size:10}, o || {})); yy += (o && o.h) || 13; }); return yy - y; };
    const ha = col(M, isF ? "Facturé à" : titre + " " + G.prep + " pour", cliL), hb = lieu ? col(x2, "Lieu des travaux", lieuL.map(s => [s])) : 0;
    y += Math.max(ha, hb) + 12;
  } else {
    /* Titre, numéro et montant total bien en vue */
    if (MOD){ T(M, y, titre, {size:26, bold:true}); const tw = textW(titre, 26, true), no = "N° " + doc.numero, nw = textW(no, 10, true) + 20; P.rrect(M + tw + 12, y - 16, nw, 21, 10.5, {fill:C.tint}); T(M + tw + 12 + nw / 2, y - 2, no, {size:10, bold:true, color:C.g, align:"center"}); }
    else { T(M, y, titre.toUpperCase(), {size:24, bold:true, color:C.g, ls:2.4}); T(M, y + 16, "N° " + doc.numero, {size:10.5, bold:true, color:C.mut}); }
    T(RX, y - 17, (isF ? "Total à payer" : "Montant total").toUpperCase(), {size:7.4, bold:true, color:C.mut, ls:1.1, align:"right"}); T(RX, y + 4, fmt(tot.total), {size:20, bold:true, color:C.g, align:"right"});
    y += MOD ? 18 : 30;
    /* Deux cartes : client (et lieu des travaux), détails */
    const hc = 30 + cliL.reduce((t, [, o]) => t + ((o && o.h) || 13), 0) + (lieu ? 22 + lieuL.length * 13 : 0), hd = 30 + det.length * 15, h = Math.max(hc, hd);
    const fond = (x, w) => { if (MOD){ P.rrect(x, y, w, h, 8, {fill:C.soft}); P.rect(x, y + 8, 3, h - 16, C.g2); } else P.rrect(x, y, w, h, 8, {fill:C.soft, stroke:C.line, w:0.6}); };
    fond(M, cw); caps(M + 14, y + 17, isF ? "Facturé à" : titre + " " + G.prep + " pour"); let yy = y + 33;
    cliL.forEach(([s, o]) => { T(M + 14, yy, s, Object.assign({size:10}, o || {})); yy += (o && o.h) || 13; });
    if (lieu){ yy += 6; caps(M + 14, yy, "Lieu des travaux"); yy += 14; lieuL.forEach(s => { T(M + 14, yy, s, {size:10}); yy += 13; }); }
    if (MOD) P.rrect(x2, y, cw, h, 8, {fill:C.tint}); else P.rrect(x2, y, cw, h, 8, {fill:C.tint});
    caps(x2 + 14, y + 17, "Détails " + G.de); let dy = y + 34;
    det.forEach(([k, v]) => { T(x2 + 14, dy, k, {size:9.2, color:C.mut}); T(x2 + cw - 14, dy, v, {size:9.6, bold:true, align:"right"}); dy += 15; });
    y += h + 16;
  }
  /* ---------- Description des travaux ---------- */
  if (String(doc.travaux || "").trim()){
    const L = wrapText(String(doc.travaux).trim(), 10, false, W - 16); need(30 + Math.min(L.length, 6) * 13); h2("Description des travaux");
    const y0 = y - 10; L.forEach(s => { need(14); T(M + (EPU ? 0 : 14), y, s, {size:10}); y += 13; }); if (!EPU) P.rect(M, y0, 3, y - y0 - 6, C.g2); y += 8;
  }
  /* ---------- Détail des travaux ---------- */
  need(27 + 26 + 30); h2("Détail des travaux"); y -= 6; inTable = true; tableHead();
  const hdr = multi && grp.some(g => g.lignes.length > 1);
  grp.forEach(g => {
    if (hdr){ need(22 + 30); y += 2; T(XD, y + 13, g.t.g.toUpperCase(), {size:7.6, bold:true, color:C.g, ls:0.9}); T(RX - 10, y + 13, (g.mt < 0 ? "−" : "") + fmt(Math.abs(g.mt)), {size:8.6, bold:true, color:C.g, align:"right"}); y += 19; P.line(M, y, RX, y, {color:C.pale, w:0.6}); zebra = 0; }
    g.lignes.forEach(l => {
      const parts = String(l.description || "").split(/\r?\n/), main = wrapText(parts[0] || "", 10, false, DW), sub = parts.slice(1).join("\n").trim() ? wrapText(parts.slice(1).join("\n").trim(), 8.8, false, DW) : [];
      const lt = TXL ? ligneTaxTxt(doc, TXL[doc.lignes.indexOf(l)]) : "", cap = multi && !hdr ? 10.5 : 0, h = cap + Math.max(1, main.length) * 12.5 + sub.length * 11 + (lt ? 11 : 0) + 12, mt = ligneMt(l), yb = y + 15 + cap;
      need(h); if (!EPU && zebra++ % 2 === 1) P.rect(M, y, W, h, C.soft);
      if (cap) T(XD, y + 12, g.t.g.toUpperCase(), {size:6.8, bold:true, color:C.g, ls:0.7});
      main.forEach((s, i) => T(XD, yb + i * 12.5, s, {size:10}));
      sub.forEach((s, i) => T(XD, yb + main.length * 12.5 + i * 11 - 1, s, {size:8.8, italic:true, color:C.mut}));
      if (lt) T(XD, yb + main.length * 12.5 + sub.length * 11 - 1, lt, {size:7.8, color:C.mut});
      T(XQ, yb, qteTxt(l), {size:10, align:"center"}); T(XP, yb, fmt(l.prix), {size:10, align:"right"});
      T(RX - 10, yb, (mt < 0 ? "−" : "") + fmt(Math.abs(mt)), {size:10, bold:!EPU, align:"right", color: mt < 0 ? C.g : C.ink});
      y += h; P.line(M, y, RX, y, {color:C.line, w:0.6});
    });
  });
  inTable = false;
  /* ---------- Sommaire ---------- */
  const t = isF && doc.transaction ? S.tmap[doc.transaction] : null, paid = t && !unpaid(t);
  const rows = [["Sous-total", tot.st], ...taxLines(doc.codeTaxe, tot)], bw = 232, bx = RX - bw, rh = 19;
  need(18 + rows.length * rh + 40 + (paid ? 18 : 0)); y += 18; const sTop = y;
  if (MOD) P.rrect(bx, y - 4, bw, rows.length * rh + 52, 8, {fill:C.tint});
  rows.forEach(([k, v]) => { T(bx + 14, y + 12, k, {size:9.5, color:C.mut}); T(RX - 12, y + 12, fmt(v), {size:10, align:"right"}); y += rh; });
  y += 6; const lab = isF ? "Total à payer" : "Total";
  if (EPU){ P.line(bx, y, RX, y, {color:C.ink, w:0.9}); T(bx + 14, y + 20, lab, {size:12, bold:true}); T(RX - 12, y + 20, fmt(tot.total), {size:14, bold:true, align:"right"}); P.rect(RX - 12 - textW(fmt(tot.total), 14, true), y + 25, textW(fmt(tot.total), 14, true), 2, C.g); y += 34; }
  else if (MOD){ T(bx + 14, y + 20, lab, {size:12, bold:true, color:C.g}); T(RX - 12, y + 21, fmt(tot.total), {size:16, bold:true, color:C.g, align:"right"}); y += 40; }
  else { P.rrect(bx, y, bw, 34, 7, {fill:C.g}); T(bx + 14, y + 22, lab.toUpperCase(), {size:10, bold:true, color:"#FFFFFF", ls:1}); T(RX - 12, y + 23, fmt(tot.total), {size:15, bold:true, color:"#FFFFFF", align:"right"}); y += 42; }
  if (isF && paid){ T(RX - 12, y + 4, "Payée le " + dLong((t.paiement && t.paiement.date) || t.date) + " · solde : " + fmt(0), {size:9, bold:true, color:C.g, align:"right"}); y += 16; }
  let ny = sTop + 12; if (tot.ttc) wrapText((isF ? "Montant total convenu avec le client" : "Prix forfaitaire convenu avec le client") + ", taxes incluses.", 8.5, false, bx - M - 24).forEach(s => { T(M, ny, s, {size:8.5, italic:true, color:C.mut}); ny += 11; });
  y = Math.max(y, ny);
  /* ---------- Modalités, acceptation, signatures ---------- */
  const pay = String(r.modePaiement || "").trim();
  const bullet = parts => { const full = parts.map(p => p[0]).join(""), L = wrapText(full, 10, false, W - 16); need(L.length * 13 + 2); T(M + 3, y, "•", {size:10, bold:true, color:C.g});
    if (L.length === 1 && parts.length > 1){ let x = M + 15; parts.forEach(([s, bo]) => { x += T(x, y, s, {size:10, bold:!!bo}); }); y += 13.5; } else { L.forEach(s => { T(M + 15, y, s, {size:10}); y += 13.5; }); } };
  const ligneSig = (x, yy, w) => P.line(x, yy, x + w, yy, {color:"#8A948E", w:0.7});
  if (isF){
    need(60); y += 8; h2("Modalités de paiement");
    const txt = paid ? "Cette facture a été payée le " + dLong((t.paiement && t.paiement.date) || t.date) + ". Merci!" : (doc.dateTravaux ? "Les travaux décrits ci-dessus ont été complétés le " + dLong(doc.dateTravaux) + ". " : "") + (doc.echeance && doc.echeance > doc.date ? "Le solde est payable d'ici le " + dLong(doc.echeance) + "." : "Le solde est payable à réception de la présente facture.");
    wrapText(txt, 10, false, W).forEach(s => { need(13); T(M, y, s, {size:10}); y += 13.5; });
    if (pay && !paid){ y += 3; const w = T(M, y, "Mode de paiement :", {size:10, bold:true}); T(M + w + 4, y, pay, {size:10}); y += 13; }
    if (sg){
      need(112); y += 12; h2("Confirmation du client");
      wrapText("Le client confirme que les travaux décrits dans la présente facture ont été effectués.", 10, false, W).forEach(s => { T(M, y, s, {size:10}); y += 13; });
      y += 6; if (sigs.client) sigImage(P, sigs.client, M + 4, y, cw - 8, 32); ligneSig(M, y + 34, cw);
      T(M, y + 46, sg.nom + " · " + dLong(sg.date) + (sg.heure ? " à " + hmTxt(sg.heure) : ""), {size:8.5}); T(M, y + 58, "Signé électroniquement" + sigVia(sg), {size:7.5, italic:true, color:C.mut}); y += 62;
    }
  } else {
    need(64); y += 8; h2("Modalités");
    String(r.conditionsDevis || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean).forEach(s => bullet([[s]]));
    const nj = daysBetween(doc.date, doc.echeance || doc.date); if (nj > 0) bullet([[G.cette + " est valide pour " + nj + " jours, soit jusqu'au " + dLong(doc.echeance) + "."]]);
    if (pay) bullet([["Mode de paiement : "], [pay, true]]);
    const lien = sg ? "" : signLien(kind, doc);
    need(114); y += 6; h2("Acceptation " + G.de);
    wrapText("En signant ci-dessous, le client accepte les travaux et le prix décrits dans " + G.presente + ".", 10, false, W).forEach(s => { T(M, y, s, {size:10}); y += 13; });
    y += 8;
    const bloc = (x, tt, img, date, pied) => { T(x, y, tt, {size:10, bold:true}); if (img) sigImage(P, img, x + 4, y + 6, cw - 8, 32); ligneSig(x, y + 40, cw); T(x, y + 52, lien && x === x2 ? "Signature (à la main, ou touchez « Signer en ligne »)" : "Signature", {size:8.5, color:C.mut});
      T(x, y + 66, "Date : " + (date ? dLong(date) : "______________________"), {size:8.5, color: date ? C.ink : C.mut}); if (pied) T(x, y + 79, pied, {size:7.5, italic:true, color:C.mut}); };
    const sc = doc.signatureCie && doc.signatureCie.nom ? doc.signatureCie : null;
    bloc(M, nom, sigs.cie || null, sc ? sc.date : (sigs.cie ? doc.date : ""), sc ? "Signé pour l'entreprise par " + sc.nom : "");
    bloc(x2, sg ? "Client : " + sg.nom : "Client", sg && sigs.client ? sigs.client : null, sg ? sg.date : "", sg ? sigPied(sg) : "");
    if (lien) sigBoutonPDF(P, x2 + 4, y + 9, lien, C.g);
    y += sg || sc ? 84 : 72;
  }
  /* ---------- Remerciements ---------- */
  const msg = String(doc.message || "").trim(), extra = msg && !/^merci de votre confiance\s*[.!]?$/i.test(msg) ? wrapText(msg, 9, false, W - 40) : [];
  if (y + 26 + extra.length * 12 > P.H - (MOD ? 44 : 52)) newPage(); y += 12;
  T(P.W / 2, y, "Merci de votre confiance.", {size:11, bold:true, color:C.g, align:"center"}); y += 14; extra.forEach(s => { T(P.W / 2, y, s, {size:9, italic:true, color:C.mut, align:"center"}); y += 12; });
  /* ---------- Pied de page ---------- */
  const pied = [nom, r.telephone, r.courriel].filter(Boolean).join("   |   ");
  P.pages.forEach((_, i) => { P.at(i); const pg = P.pages.length > 1 ? "Page " + (i + 1) + " de " + P.pages.length : "";
    if (MOD){ P.rect(0, P.H - 34, P.W, 34, C.g); T(P.W / 2, P.H - 14, pied, {size:8.5, color:"#FFFFFF", align:"center"}); if (pg) T(RX, P.H - 14, pg, {size:7.5, color:C.pale, align:"right"}); }
    else { if (!EPU) P.line(M, P.H - 46, RX, P.H - 46, {color:C.pale, w:0.8}); T(P.W / 2, P.H - 30, pied, {size:8.3, color:C.mut, align:"center"}); if (pg) T(RX, P.H - 30, pg, {size:7.5, color:C.mut, align:"right"}); } });
  return P;
}
