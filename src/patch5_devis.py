"""v3.7 : factures et soumissions complètes (types de frais, unités, prix taxes incluses, tarifs enregistrés,
description et lieu des travaux), nouvelle mise en page d'après le modèle d'Émondage Hamel, partage (PDF ou image)."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); CORE = open(sys.argv[2], encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

# ---------- Moteur PDF : italique, espacement des lettres, et enregistrement des tracés pour les images ----------
rep('''const WIN = {"€":128,"‚":130,"„":132,"…":133,"‘":145,"’":146,"“":147,"”":148,"•":149,"–":150,"—":151,"™":153,"œ":156,"Œ":140};''',
    '''const WIN = {"€":128,"‚":130,"„":132,"…":133,"‘":145,"’":146,"“":147,"”":148,"•":149,"–":150,"—":151,"™":153,"œ":156,"Œ":140,"‹":139,"›":155};''')
rep('''const WIN_W = {128:556,''', '''const WIN_W = {139:333,155:333,128:556,''')
rep('''  const W = 612, H = 792, pages = [], imgs = [];
  let ops = null;''', '''  const W = 612, H = 792, pages = [], imgs = [], draws = [];
  let ops = null, cv = null;''')
rep('''    W, H, pages,
    page(){ ops = []; pages.push(ops); return P; },
    at(i){ ops = pages[i]; return P; },
    text(x, y, s, o){ o = o || {}; const size = o.size || 10, bold = !!o.bold, w = textW(s, size, bold); let tx = x; if (o.align === "right") tx = x - w; else if (o.align === "center") tx = x - w / 2;
      ops.push((o.color ? col(o.color) + " rg " : "") + "BT /" + (bold ? "F2" : "F1") + " " + n(size) + " Tf " + n(tx) + " " + n(H - y) + " Td (" + pdfStr(s) + ") Tj ET" + (o.color ? " 0 0 0 rg" : "")); return w; },
    line(x1, y1, x2, y2, o){ o = o || {}; ops.push(col(o.color || "#000000") + " RG " + n(o.w || 0.6) + " w " + n(x1) + " " + n(H - y1) + " m " + n(x2) + " " + n(H - y2) + " l S"); },
    rect(x, y, w, h, color){ ops.push(col(color) + " rg " + n(x) + " " + n(H - y - h) + " " + n(w) + " " + n(h) + " re f 0 0 0 rg"); },
    image(img, x, y, w, h){ if (!imgs.includes(img)) imgs.push(img); ops.push("q " + n(w) + " 0 0 " + n(h) + " " + n(x) + " " + n(H - y - h) + " cm /Im" + (imgs.indexOf(img) + 1) + " Do Q"); },''',
'''    W, H, pages, draws,
    page(){ ops = []; pages.push(ops); cv = []; draws.push(cv); return P; },
    at(i){ ops = pages[i]; cv = draws[i]; return P; },
    text(x, y, s, o){ o = o || {}; const size = o.size || 10, bold = !!o.bold, ls = Number(o.ls) || 0, nc = [...pdfChars(s)].length, w = textW(s, size, bold) + (nc > 1 ? ls * (nc - 1) : 0); let tx = x; if (o.align === "right") tx = x - w; else if (o.align === "center") tx = x - w / 2;
      ops.push((o.color ? col(o.color) + " rg " : "") + "BT /" + (bold ? "F2" : o.italic ? "F3" : "F1") + " " + n(size) + " Tf " + (ls ? n(ls) + " Tc " : "") + n(tx) + " " + n(H - y) + " Td (" + pdfStr(s) + ") Tj " + (ls ? "0 Tc " : "") + "ET" + (o.color ? " 0 0 0 rg" : ""));
      cv.push({k:"t", x:tx, y, s:pdfChars(s), size, bold, italic:!!o.italic, ls, color:o.color || "#000000"}); return w; },
    line(x1, y1, x2, y2, o){ o = o || {}; ops.push(col(o.color || "#000000") + " RG " + n(o.w || 0.6) + " w " + n(x1) + " " + n(H - y1) + " m " + n(x2) + " " + n(H - y2) + " l S"); cv.push({k:"l", x1, y1, x2, y2, color:o.color || "#000000", w:o.w || 0.6}); },
    rect(x, y, w, h, color){ ops.push(col(color) + " rg " + n(x) + " " + n(H - y - h) + " " + n(w) + " " + n(h) + " re f 0 0 0 rg"); cv.push({k:"r", x, y, w, h, color}); },
    image(img, x, y, w, h){ if (!imgs.includes(img)) imgs.push(img); ops.push("q " + n(w) + " 0 0 " + n(h) + " " + n(x) + " " + n(H - y - h) + " cm /Im" + (imgs.indexOf(img) + 1) + " Do Q"); cv.push({k:"i", img, x, y, w, h}); },''')
rep('''      const first = 5 + imgs.length;''', '''      const first = 6 + imgs.length;''')
rep('''      obj(4, ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]);
      imgs.forEach((im, i) => obj(5 + i,''', '''      obj(4, ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]);
      obj(5, ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>"]);
      imgs.forEach((im, i) => obj(6 + i,''')
rep('''imgs.map((_, i) => "/Im" + (i + 1) + " " + (5 + i) + " 0 R")''', '''imgs.map((_, i) => "/Im" + (i + 1) + " " + (6 + i) + " 0 R")''')
rep('''/Resources << /Font << /F1 3 0 R /F2 4 0 R >>" + xo''', '''/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >>" + xo''')

# ---------- Mise en page, totaux, images : remplacés par le nouveau module ----------
i = s.index("/* Mise en page d'une facture ou d'un devis */\nfunction docPDF(kind, doc, logo){"); j = s.index("\n/* ----- ZIP (sans compression) ----- */")
s = s[:i] + CORE + s[j:]
rep('''function docTotals(doc){
  const st = r2((doc.lignes || []).reduce((s, l) => s + r2((Number(l.qte) || 0) * (Number(l.prix) || 0)), 0)), [a, b] = taxRates(doc.codeTaxe || "AUCUNE");
  const tx = r2(st * a / 100), tq = r2(st * b / 100); return {st, tx, tq, total: r2(st + tx + tq)};
}
''', "")
# texte du canevas : italique et espacement
rep('''      if (o.k === "t"){ g.fillStyle = o.color || "#000000"; g.font = (o.bold ? "bold " : "") + o.size + "px Helvetica, Arial, sans-serif"; g.textAlign = o.align || "left"; g.fillText(o.s, o.x, o.y); }''',
    '''      if (o.k === "t"){ g.fillStyle = o.color || "#000000"; g.font = (o.italic ? "italic " : "") + (o.bold ? "bold " : "") + o.size + "px Helvetica, Arial, sans-serif"; g.textAlign = "left"; try { g.letterSpacing = (o.ls || 0) + "px"; } catch(e){} g.fillText(o.s, o.x, o.y); }''')

# ---------- Réglages : nouveaux champs ----------
rep('''termes:30, validiteDevis:30, messageFacture:"Merci de votre confiance!", logo:""};''',
    '''termes:30, validiteDevis:30, messageFacture:"Merci de votre confiance!", logo:"",
  slogan:"", neq:"", modePaiement:"", titreDevis:"Devis", conditionsDevis:"Paiement dû à la fin des travaux (sauf entente différente).", tarifs:[], docTTC:false};''')
rep('''  if (!d.reglages.obligations || typeof d.reglages.obligations !== "object") d.reglages.obligations = {};''',
    '''  if (!d.reglages.obligations || typeof d.reglages.obligations !== "object") d.reglages.obligations = {};
  if (!Array.isArray(d.reglages.tarifs)) d.reglages.tarifs = [];''')
rep('''          <label class="field full"><span>Message au bas des factures</span><textarea id="r-msg" class="ctl" rows="2" maxlength="400"></textarea></label>''',
'''          <label class="field"><span>Slogan (sous le nom)</span><input id="r-slogan" class="ctl" type="text" maxlength="80" placeholder="Élagage · Abattage · Entretien d'arbres"></label>
          <label class="field"><span>NEQ (Registraire des entreprises)</span><input id="r-neq" class="ctl" type="text" maxlength="20" placeholder="1234567890"></label>
          <label class="field"><span>Mode de paiement</span><input id="r-paiement" class="ctl" type="text" maxlength="120" placeholder="virement Interac à courriel@exemple.com"></label>
          <label class="field"><span>Titre des devis sur le document</span><select id="r-titredevis" class="ctl"><option value="Soumission">Soumission</option><option value="Devis">Devis</option></select></label>
          <label class="field full"><span>Modalités des soumissions (une par ligne)</span><textarea id="r-condev" class="ctl" rows="2" maxlength="600"></textarea></label>
          <label class="field full"><span>Message au bas des factures et soumissions</span><textarea id="r-msg" class="ctl" rows="2" maxlength="400"></textarea><small>Il s'affiche en italique sous « Merci de votre confiance. »</small></label>
          <div class="field full"><span>Tarifs enregistrés</span><div id="r-tarifs" class="tarifs"></div>
            <div class="inline-form tarif-add"><select id="r-tf-type" class="ctl auto"></select><input id="r-tf-desc" class="ctl" type="text" maxlength="200" placeholder="Description, ex. : Taux horaire, émondeur"><select id="r-tf-unite" class="ctl auto" aria-label="Unité"></select><input id="r-tf-prix" class="ctl fig" type="text" inputmode="decimal" placeholder="Prix" style="width:100px"><label class="check"><input id="r-tf-ttc" type="checkbox"><span>Taxes incluses</span></label><button class="btn sm" type="button" id="r-tf-ok"><svg class="ic"><use href="#i-plus"/></svg>Ajouter</button></div>
            <small>Tes prix habituels (taux horaire, location, déplacement…) : ils s'ajoutent en un clic dans une facture ou une soumission. Tu peux aussi enregistrer une ligne avec l'étoile dans l'éditeur.</small></div>''')
rep('''  $("r-validite").value = String(r.validiteDevis || 30); $("r-msg").value = r.messageFacture || "";''',
    '''  $("r-validite").value = String(r.validiteDevis || 30); $("r-msg").value = r.messageFacture || "";
  $("r-slogan").value = r.slogan || ""; $("r-neq").value = r.neq || ""; $("r-paiement").value = r.modePaiement || ""; $("r-titredevis").value = r.titreDevis === "Soumission" ? "Soumission" : "Devis"; $("r-condev").value = r.conditionsDevis || "";
  setOptions($("r-tf-type"), LT.map(t => [t.k, t.l])); if (!$("r-tf-unite").options.length){ $("r-tf-unite").innerHTML = uniteOptions("h"); } renderTarifsReglages();''')
rep('''validiteDevis: Math.max(1, Math.round(num($("r-validite").value)) || 30), messageFacture:$("r-msg").value.trim()});''',
    '''validiteDevis: Math.max(1, Math.round(num($("r-validite").value)) || 30), messageFacture:$("r-msg").value.trim(),
    slogan:$("r-slogan").value.trim(), neq:$("r-neq").value.trim(), modePaiement:$("r-paiement").value.trim(), titreDevis:$("r-titredevis").value, conditionsDevis:$("r-condev").value.trim()});''')
rep('''$("r-logo-rm").addEventListener("click", () => mutate(d => { d.reglages.logo = ""; }, "Logo retiré"));''',
'''$("r-logo-rm").addEventListener("click", () => mutate(d => { d.reglages.logo = ""; }, "Logo retiré"));
/* Tarifs enregistrés */
const tarifTxt = t => (LTM[t.type] || LTM.service).l + " · " + t.description + " · " + fmt(t.prix) + (t.unite ? " / " + t.unite : "") + (t.ttc ? " (taxes incl.)" : "");
function renderTarifsReglages(){
  const T = R().tarifs || [];
  put($("r-tarifs"), T.length ? T.map(t => '<div class="tarif"><span>' + esc(tarifTxt(t)) + '</span><button class="btn link" type="button" data-tf-del="' + esc(t.id) + '">Retirer</button></div>').join("") : '<p class="muted small">Aucun tarif pour l\\'instant.</p>');
}
$("r-tarifs").addEventListener("click", e => { const b = e.target.closest("[data-tf-del]"); if (!b) return; const id = b.dataset.tfDel; mutate(d => { d.reglages.tarifs = (d.reglages.tarifs || []).filter(t => t.id !== id); }, "Tarif retiré"); });
$("r-tf-ok").addEventListener("click", () => {
  const desc = $("r-tf-desc").value.trim(), prix = num($("r-tf-prix").value), type = $("r-tf-type").value;
  if (!desc || !isFinite(prix) || prix <= 0) return toast("Entre la description et le prix du tarif.");
  const t = {id: uid("tf"), type, description: desc, unite: $("r-tf-unite").value || "", prix: r2(prix), ttc: $("r-tf-ttc").checked};
  mutate(d => { d.reglages.tarifs = (d.reglages.tarifs || []).concat([t]); }, "Tarif ajouté").then(ok => { if (ok){ $("r-tf-desc").value = ""; $("r-tf-prix").value = ""; $("r-tf-unite").value = ""; } });
});
$("r-tf-type").addEventListener("change", () => { $("r-tf-unite").value = (LTM[$("r-tf-type").value] || {}).u || "";
});''')

# ---------- Éditeur : champs de la facture ou de la soumission ----------
rep('''        <label class="field"><span id="d-ech-lbl">Échéance</span><input id="d-ech" class="ctl" type="date"></label>
      </div>''', '''        <label class="field"><span id="d-ech-lbl">Échéance</span><input id="d-ech" class="ctl" type="date"></label>
        <label class="field"><span id="d-dtrav-lbl">Date des travaux</span><input id="d-dtrav" class="ctl" type="date"></label>
        <label class="field" style="grid-column:span 2"><span>Lieu des travaux</span><input id="d-lieu" class="ctl" type="text" maxlength="200" placeholder="Si différent de l'adresse du client"></label>
      </div>''')
rep('''      <div class="field"><span>Produits et services</span>
        <div class="lines-ed" id="d-lines"></div>
        <div class="inline-form" style="margin-top:8px">
          <button class="btn sm" type="button" id="d-add-line"><svg class="ic"><use href="#i-plus"/></svg>Ajouter une ligne</button>
          <select id="d-add-prod" class="ctl auto" hidden></select>
        </div>
      </div>''', '''      <label class="field full"><span>Description des travaux (sur le document, facultatif)</span><textarea id="d-travaux" class="ctl" rows="2" maxlength="1500" placeholder="Ex. : Émondage de 3 érables argentés en façade, dégagement de la toiture et ramassage des branches."></textarea></label>
      <div class="field"><div class="lines-top"><span>Services et frais</span><div class="seg" id="d-ttc" role="group" aria-label="Taxes"><button type="button" data-ttc="plus">Taxes en plus</button><button type="button" data-ttc="incl">Taxes incluses</button><button type="button" data-ttc="aucune">Sans taxes</button></div></div>
        <p class="muted small" id="d-ttc-txt" style="margin:0 0 4px"></p>
        <label class="check" style="margin:0 0 8px"><input type="checkbox" id="d-txl"><span>Montrer aussi les taxes de chaque ligne sur le document</span></label>
        <div class="lines-ed" id="d-lines"></div>
        <div class="lt-add" id="d-lt-add"></div>
        <div class="inline-form" style="margin-top:8px">
          <select id="d-add-tarif" class="ctl auto" hidden></select>
          <select id="d-add-prod" class="ctl auto" hidden></select>
        </div>
      </div>''')
rep('''      <button class="btn" type="button" id="d-save-pdf"><svg class="ic"><use href="#i-pdf"/></svg>Enregistrer et créer le PDF</button>''',
    '''      <button class="btn" type="button" id="d-save-pdf"><svg class="ic"><use href="#i-pdf"/></svg>Enregistrer et voir le PDF</button>
      <button class="btn" type="button" id="d-save-send"><svg class="ic"><use href="#i-mail"/></svg>Enregistrer et envoyer</button>''')

# ---------- Éditeur : logique ----------
rep('''  S.doc = {kind, orig: doc || null, lignes: doc ? clone(doc.lignes) : (p.lignes ? clone(p.lignes) : [{description:"", qte:1, prix:0}]), numAuto: !doc, fromDevis: p.fromDevis || "", pay:"", confirm:null};
  if (!S.doc.lignes.length) S.doc.lignes.push({description:"", qte:1, prix:0});''',
'''  S.doc = {kind, orig: doc || null, lignes: doc ? clone(doc.lignes) : (p.lignes ? clone(p.lignes) : [{type:"service", description:"", qte:1, unite:"", prix:0}]), numAuto: !doc, fromDevis: p.fromDevis || "", pay:"", confirm:null,
    ttc: docV2() && !!(doc ? doc.taxesIncluses : (p.taxesIncluses != null ? p.taxesIncluses : r.docTTC))};
  if (!S.doc.lignes.length) S.doc.lignes.push({type:"service", description:"", qte:1, unite:"", prix:0});
  S.doc.lignes.forEach(l => { if (!l.type) l.type = "service"; });
  $("d-travaux").value = doc ? (doc.travaux || "") : (p.travaux || ""); $("d-lieu").value = doc ? (doc.lieu || "") : (p.lieu || ""); $("d-dtrav").value = doc ? (doc.dateTravaux || "") : (p.dateTravaux || "");
  $("d-dtrav-lbl").textContent = isF ? "Date des travaux" : "Date prévue des travaux";
  $("d-ttc").querySelector('[data-ttc="incl"]').disabled = !docV2(); $("d-ttc").querySelector('[data-ttc="incl"]').title = docV2() ? "" : "Ouvre une fois l'application de l'ordinateur (nouvelle version) pour l'activer";
  $("d-txl").checked = !!(doc ? doc.taxesLigne : (p.taxesLigne != null ? p.taxesLigne : r.docTaxesLigne));
  $("d-lt-add").innerHTML = LT.filter(t => t.k !== "rabais" || docV2()).map(t => '<button type="button" class="chip-btn' + (t.k === "rabais" ? " alt" : "") + '" data-addlt="' + t.k + '">' + ico("i-plus") + esc(t.k === "service" ? "Service" : t.l) + "</button>").join("");
  const tfs = (r.tarifs || []);
  $("d-add-tarif").hidden = !tfs.length;
  $("d-add-tarif").innerHTML = '<option value="">+ Ajouter un tarif enregistré</option>' + LT.map(t => { const L = tfs.filter(x => (x.type || "service") === t.k); return L.length ? '<optgroup label="' + esc(t.l) + '">' + L.map(x => '<option value="' + esc(x.id) + '">' + esc(x.description + " · " + fmt(x.prix) + (x.unite ? " / " + x.unite : "")) + "</option>").join("") + "</optgroup>" : ""; }).join("");''')
rep('''  $("d-kind").textContent = isF ? "Facture" : "Devis";
  $("d-title").textContent = doc ? doc.numero + " · " + doc.client : (isF ? (p.fromDevis ? "Facture à partir du devis " + ((S.d.devis.find(v => v.id === p.fromDevis) || {}).numero || "") : "Nouvelle facture") : "Nouveau devis");''',
'''  $("d-kind").textContent = isF ? "Facture" : docTitre("devis");
  $("d-title").textContent = doc ? doc.numero + " · " + doc.client : (isF ? (p.fromDevis ? "Facture à partir " + docGenre("devis").de + " " + ((S.d.devis.find(v => v.id === p.fromDevis) || {}).numero || "") : "Nouvelle facture") : (docTitre("devis") === "Devis" ? "Nouveau devis" : "Nouvelle soumission"));''')
rep('''function renderLines(){
  const L = S.doc.lignes, pm = {}; S.d.produits.forEach(x => pm[x.id] = x);
  $("d-lines").innerHTML = '<div class="le-row head"><span>Description</span><span class="num-h">Qté</span><span class="num-h">Prix unitaire</span><span class="num-h">Montant</span><span></span></div>' +
    L.map((l, i) => { const pr = l.produit ? pm[l.produit] : null;
      return '<div class="le-row" data-l="' + i + '"><input class="ctl" data-f="description" value="' + esc(l.description) + '" maxlength="300" placeholder="Ex. : Main-d\\'œuvre, installation" aria-label="Description de la ligne ' + (i + 1) + '"><input class="ctl fig" data-f="qte" inputmode="decimal" value="' + esc(fq(l.qte)) + '" aria-label="Quantité"><input class="ctl fig" data-f="prix" inputmode="decimal" value="' + (l.prix ? esc(n2s(l.prix)) : "") + '" placeholder="0,00" aria-label="Prix unitaire"><span class="amt" data-amt="' + i + '">' + fmt(r2((Number(l.qte) || 0) * (Number(l.prix) || 0))) + '</span><button type="button" class="icon-btn sm" data-rmline="' + i + '" aria-label="Retirer la ligne"' + (L.length < 2 ? " disabled" : "") + ">" + ico("i-x") + "</button>" +
        (pr ? '<small data-stock="' + i + '">' + ico("i-box") + " Produit du stock : " + esc(fq(stockOf(pr, S.doc.orig ? S.doc.orig.id : null))) + " " + esc(pr.unite || "unité(s)") + " disponible(s)</small>" : "") + "</div>"; }).join("");
}''', '''function renderLines(){
  const L = S.doc.lignes, pm = {}, types = LT.filter(t => t.k !== "rabais" || docV2() || L.some(l => l.type === "rabais")); S.d.produits.forEach(x => pm[x.id] = x);
  $("d-lines").innerHTML = L.map((l, i) => { const pr = l.produit ? pm[l.produit] : null, t = LTM[ligneType(l)], mt = ligneMt(l);
      return '<div class="le-row le2' + (l.type === "rabais" ? " rabais" : "") + '" data-l="' + i + '">' +
        '<textarea class="ctl le-desc" data-f="description" rows="1" maxlength="600" placeholder="' + esc(t.ph) + '" aria-label="Description de la ligne ' + (i + 1) + '">' + esc(l.description) + "</textarea>" +
        '<select class="ctl le-type" data-f="type" aria-label="Type">' + types.map(x => '<option value="' + x.k + '"' + (x.k === t.k ? " selected" : "") + ">" + esc(x.l) + "</option>").join("") + "</select>" +
        '<label class="le-mini"><span>Qté</span><input class="ctl fig" data-f="qte" inputmode="decimal" value="' + esc(fq(l.qte)) + '"></label>' +
        '<label class="le-mini"><span>Unité</span><select class="ctl" data-f="unite">' + uniteOptions(l.unite) + "</select></label>" +
        '<label class="le-mini"><span>' + (S.doc.ttc ? "Prix (tx incl.)" : "Prix unitaire") + '</span><input class="ctl fig" data-f="prix" inputmode="decimal" value="' + (l.prix ? esc(n2s(l.prix)) : "") + '" placeholder="0,00"></label>' +
        '<span class="amt" data-amt="' + i + '">' + (mt < 0 ? "−" : "") + fmt(Math.abs(mt)) + "</span>" +
        '<span class="le-acts"><button type="button" class="icon-btn sm" data-tfsave="' + i + '" title="Garder comme tarif" aria-label="Garder comme tarif">' + ico("i-star") + '</button><button type="button" class="icon-btn sm" data-rmline="' + i + '" aria-label="Retirer la ligne"' + (L.length < 2 ? " disabled" : "") + ">" + ico("i-x") + "</button></span>" +
        '<small class="le-tax" data-tax="' + i + '"></small>' + (pr ? '<small data-stock="' + i + '">' + ico("i-box") + " Produit du stock : " + esc(fq(stockOf(pr, S.doc.orig ? S.doc.orig.id : null))) + " " + esc(pr.unite || "unité(s)") + " disponible(s)</small>" : "") + "</div>"; }).join("");
  $("d-lines").querySelectorAll(".le-desc").forEach(autoGrow);
}
const autoGrow = el => { el.style.height = "auto"; el.style.height = Math.min(220, el.scrollHeight + 2) + "px"; };
/* Les nouveautés des factures (types de frais, rabais, taxes incluses) demandent que l'ordinateur soit en version 3.7 */
const docV2 = () => { if (!CLOUD) return true; const t = (NU.base && NU.base.telephone) || (S.d && S.d.telephone) || {}; return Array.isArray(t.ops) && t.ops.includes("doc-v2"); };
/* Taxes : en plus du prix, incluses dans le prix, ou aucune */
const docTxMode = () => $("d-code").value === "AUCUNE" ? "aucune" : S.doc.ttc ? "incl" : "plus";
function docTTCset(){ const m = docTxMode(); $("d-ttc").querySelectorAll("[data-ttc]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.ttc === m)));
  $("d-ttc-txt").textContent = m === "aucune" ? "Aucune taxe sur ce document." : m === "incl" ? "Les prix entrés comprennent déjà la TPS et la TVQ : elles sont calculées à l'intérieur du total." : "Les prix entrés sont avant taxes : la TPS et la TVQ s'ajoutent au total."; }
function ligneDe(type, extra){ return Object.assign({type, description:"", qte:1, unite:(LTM[type] || {}).u || "", prix:0}, extra || {}); }
function addLigne(line){ const L = S.doc.lignes, empty = L.length === 1 && !L[0].description && !L[0].prix; if (empty) L[0] = line; else L.push(line); renderLines(); docRecalc(); const ins = $("d-lines").querySelectorAll('[data-f="description"]'); const el = ins[empty ? 0 : ins.length - 1]; if (el && !line.description) el.focus(); }''')
rep('''  const doc = {lignes:S.doc.lignes, codeTaxe:$("d-code").value}, t = docTotals(doc);
  $("d-tot").innerHTML = '<div><span>Sous-total</span><span>' + fmt(t.st) + "</span></div>" + taxLines(doc.codeTaxe, t).map(([k, v]) => '<div class="muted"><span>' + esc(k) + "</span><span>" + fmt(v) + "</span></div>").join("") + '<div class="grand"><span>Total</span><span>' + fmt(t.total) + "</span></div>";
  S.doc.lignes.forEach((l, i) => { const el = $("d-lines").querySelector('[data-amt="' + i + '"]'); if (el) el.textContent = fmt(r2((Number(l.qte) || 0) * (Number(l.prix) || 0))); });''',
'''  const doc = {lignes:S.doc.lignes, codeTaxe:$("d-code").value, taxesIncluses:S.doc.ttc}, t = docTotals(doc), G = docGroupes(doc);
  $("d-tot").innerHTML = (G.length > 1 ? G.map(g => '<div class="muted small"><span>' + esc(g.t.g) + "</span><span>" + (g.mt < 0 ? "−" : "") + fmt(Math.abs(g.mt)) + "</span></div>").join("") + '<div class="sep"></div>' : "") +
    '<div><span>' + (t.ttc ? "Montant avant taxes" : "Sous-total") + "</span><span>" + fmt(t.st) + "</span></div>" + taxLines(doc.codeTaxe, t).map(([k, v]) => '<div class="muted"><span>' + esc(k) + "</span><span>" + fmt(v) + "</span></div>").join("") + '<div class="grand"><span>Total' + (t.ttc ? " (taxes incluses)" : "") + "</span><span>" + fmt(t.total) + "</span></div>";
  const TX = ligneTaxes(doc);
  S.doc.lignes.forEach((l, i) => { const el = $("d-lines").querySelector('[data-amt="' + i + '"]'); if (el){ const m = ligneMt(l); el.textContent = (m < 0 ? "−" : "") + fmt(Math.abs(m)); }
    const tx = $("d-lines").querySelector('[data-tax="' + i + '"]'); if (tx){ const s = Number(l.prix) ? ligneTaxTxt(doc, TX[i]) : ""; tx.textContent = s; tx.hidden = !s; } });''')
rep('''$("d-add-line").addEventListener("click", () => { S.doc.lignes.push({description:"", qte:1, prix:0}); renderLines(); docRecalc(); const ins = $("d-lines").querySelectorAll('[data-f="description"]'); ins[ins.length - 1].focus(); });
$("d-add-prod").addEventListener("change", e => {
  const pr = S.d.produits.find(x => x.id === e.target.value); e.target.value = ""; if (!pr) return;
  const L = S.doc.lignes, empty = L.length === 1 && !L[0].description && !L[0].prix ? 0 : -1, line = {description: pr.nom + (pr.code ? " (" + pr.code + ")" : ""), qte:1, prix: Number(pr.prix) || 0, produit: pr.id};
  if (empty === 0) L[0] = line; else L.push(line);
  renderLines(); docRecalc();
});
$("d-lines").addEventListener("input", e => {
  const el = e.target.closest("[data-f]"), row = e.target.closest("[data-l]"); if (!el || !row) return;
  const l = S.doc.lignes[Number(row.dataset.l)], f = el.dataset.f;
  if (f === "description") l.description = el.value; else { const v = num(el.value); l[f] = isFinite(v) ? v : 0; }
  docRecalc();
});''', '''$("d-lt-add").addEventListener("click", e => { const b = e.target.closest("[data-addlt]"); if (b) addLigne(ligneDe(b.dataset.addlt)); });
$("d-ttc").addEventListener("click", e => { const b = e.target.closest("[data-ttc]"); if (!b || b.disabled) return; const m = b.dataset.ttc, code = $("d-code");
  if (m === "aucune"){ if (code.value !== "AUCUNE") S.doc.codeAvant = code.value; code.value = "AUCUNE"; S.doc.ttc = false; }
  else { if (code.value === "AUCUNE") code.value = S.doc.codeAvant || (quebec() ? "QC" : defCode() !== "AUCUNE" ? defCode() : "QC"); S.doc.ttc = m === "incl"; }
  docTTCset(); renderLines(); docRecalc(); });
$("d-code").addEventListener("change", () => { if ($("d-code").value === "AUCUNE") S.doc.ttc = false; docTTCset(); renderLines(); docRecalc(); });
/* Prix d'un tarif ou d'un produit dans le mode de prix de la facture (avant taxes ou taxes incluses) */
function prixPour(prix, ttc){ const [a, b] = taxRates($("d-code").value || "AUCUNE"); if (!!ttc === !!S.doc.ttc || !(a || b)) return r2(prix); return ttc ? r2(prix * 100 / (100 + a + b)) : r2(prix * (100 + a + b) / 100); }
$("d-add-tarif").addEventListener("change", e => {
  const t = (R().tarifs || []).find(x => x.id === e.target.value); e.target.value = ""; if (!t) return;
  addLigne(ligneDe(t.type || "service", {description: t.description, unite: t.unite || "", prix: prixPour(t.prix, t.ttc)}));
});
$("d-add-prod").addEventListener("change", e => {
  const pr = S.d.produits.find(x => x.id === e.target.value); e.target.value = ""; if (!pr) return;
  addLigne(ligneDe("materiaux", {description: pr.nom + (pr.code ? " (" + pr.code + ")" : ""), unite: pr.unite || "unité", prix: prixPour(Number(pr.prix) || 0, false), produit: pr.id}));
});
$("d-lines").addEventListener("input", e => {
  const el = e.target.closest("[data-f]"), row = e.target.closest("[data-l]"); if (!el || !row) return;
  const l = S.doc.lignes[Number(row.dataset.l)], f = el.dataset.f;
  if (f === "description"){ l.description = el.value; autoGrow(el); } else if (f === "unite") l.unite = el.value; else if (f !== "type"){ const v = num(el.value); l[f] = isFinite(v) ? v : 0; }
  docRecalc();
});
$("d-lines").addEventListener("change", e => {
  const el = e.target.closest('[data-f="type"]'), row = e.target.closest("[data-l]"); if (!el || !row) return;
  const l = S.doc.lignes[Number(row.dataset.l)], was = LTM[ligneType(l)]; l.type = el.value; if (!l.unite || l.unite === was.u) l.unite = (LTM[l.type] || {}).u || "";
  renderLines(); docRecalc();
});''')
rep('''$("d-lines").addEventListener("keydown", e => {
  if (e.key !== "Enter" || !e.target.closest("[data-f]")) return;''', '''$("d-lines").addEventListener("keydown", e => {
  if (e.key !== "Enter" || !e.target.closest("[data-f]") || e.target.tagName === "SELECT" || (e.target.tagName === "TEXTAREA" && e.shiftKey)) return;''')
rep('''  if (i === S.doc.lignes.length - 1) $("d-add-line").click(); else''', '''  if (i === S.doc.lignes.length - 1) addLigne(ligneDe(ligneType(S.doc.lignes[i]))); else''')
rep('''$("d-lines").addEventListener("click", e => { const b = e.target.closest("[data-rmline]"); if (!b) return; S.doc.lignes.splice(Number(b.dataset.rmline), 1); if (!S.doc.lignes.length) S.doc.lignes.push({description:"", qte:1, prix:0}); renderLines(); docRecalc(); });''',
'''$("d-lines").addEventListener("click", e => {
  const sv = e.target.closest("[data-tfsave]");
  if (sv){ const l = S.doc.lignes[Number(sv.dataset.tfsave)]; if (!l || !String(l.description || "").trim() || !(Number(l.prix) > 0)) return toast("Entre la description et le prix de la ligne avant de la garder comme tarif.");
    const t = {id: uid("tf"), type: ligneType(l), description: String(l.description).trim(), unite: l.unite || "", prix: r2(l.prix), ttc: !!S.doc.ttc};
    if ((R().tarifs || []).some(x => norm(x.description) === norm(t.description) && x.prix === t.prix)) return toast("Ce tarif est déjà enregistré.");
    mutate(d => { d.reglages.tarifs = (d.reglages.tarifs || []).concat([t]); }, "Tarif enregistré : il est dans la liste « Ajouter un tarif enregistré »").then(ok => { if (ok && S.doc){ const tfs = R().tarifs; $("d-add-tarif").hidden = false; $("d-add-tarif").innerHTML = '<option value="">+ Ajouter un tarif enregistré</option>' + LT.map(x => { const L = tfs.filter(y => (y.type || "service") === x.k); return L.length ? '<optgroup label="' + esc(x.l) + '">' + L.map(y => '<option value="' + esc(y.id) + '">' + esc(y.description + " · " + fmt(y.prix) + (y.unite ? " / " + y.unite : "")) + "</option>").join("") + "</optgroup>" : ""; }).join(""); } });
    return; }
  const b = e.target.closest("[data-rmline]"); if (!b) return; S.doc.lignes.splice(Number(b.dataset.rmline), 1); if (!S.doc.lignes.length) S.doc.lignes.push(ligneDe("service")); renderLines(); docRecalc(); });''')
rep('''$("d-save-pdf").addEventListener("click", () => { S.doc.withPdf = true; $("doc-form").requestSubmit(); });''',
    '''$("d-save-pdf").addEventListener("click", () => { S.doc.withPdf = true; $("doc-form").requestSubmit(); });
$("d-save-send").addEventListener("click", () => { S.doc.withSend = true; $("doc-form").requestSubmit(); });''')
rep('''  const withPdf = S.doc.withPdf; S.doc.withPdf = false;''', '''  const withPdf = S.doc.withPdf, withSend = S.doc.withSend; S.doc.withPdf = false; S.doc.withSend = false;''')
rep('''  const lignes = S.doc.lignes.map(l => { const x = {description:String(l.description || "").trim(), qte: Number(l.qte) || 0, prix: r2(l.prix)}; if (l.produit) x.produit = l.produit; return x; }).filter(l => l.description || l.prix);''',
    '''  const lignes = S.doc.lignes.map(l => { const x = {type: ligneType(l), description:String(l.description || "").trim(), qte: Number(l.qte) || 0, unite: String(l.unite || "").trim(), prix: r2(l.prix)}; if (l.produit) x.produit = l.produit; return x; }).filter(l => l.description || l.prix);''')
rep('''client, lignes, codeTaxe: $("d-code").value, projet: $("d-proj").value, message: $("d-msg").value.trim(), note: $("d-note").value.trim(), modifieLe: now});''',
    '''client, lignes, codeTaxe: $("d-code").value, projet: $("d-proj").value, message: $("d-msg").value.trim(), note: $("d-note").value.trim(), modifieLe: now,
    taxesIncluses: !!S.doc.ttc, taxesLigne: $("d-txl").checked, travaux: $("d-travaux").value.trim(), lieu: $("d-lieu").value.trim(), dateTravaux: $("d-dtrav").value || ""});
  if (!doc.taxesIncluses) delete doc.taxesIncluses; if (!doc.taxesLigne) delete doc.taxesLigne; ["travaux","lieu","dateTravaux"].forEach(k => { if (!doc[k]) delete doc[k]; });''')
rep('''    if (isF) syncFactureTx(d, doc, pay);
  }, o ?''', '''    if (isF) syncFactureTx(d, doc, pay);
    if (docV2() && !!d.reglages.docTTC !== !!doc.taxesIncluses) d.reglages.docTTC = !!doc.taxesIncluses;
    if (docV2() && !!d.reglages.docTaxesLigne !== !!doc.taxesLigne) d.reglages.docTaxesLigne = !!doc.taxesLigne;
  }, o ?''')
rep('''  if (withPdf || doc.pdf) await makeDocPDF(kind, doc.id, withPdf);
});''', '''  if (withSend){ await shareDoc(kind, doc.id); return; }
  if (withPdf || doc.pdf) await makeDocPDF(kind, doc.id, withPdf);
});''')
rep('''  openDoc("facture", null, {client:v.client, lignes:v.lignes, codeTaxe:v.codeTaxe, projet:v.projet, message:v.message, fromDevis:v.id});''',
    '''  openDoc("facture", null, {client:v.client, lignes:v.lignes, codeTaxe:v.codeTaxe, projet:v.projet, message:v.message, fromDevis:v.id, taxesIncluses:!!v.taxesIncluses, taxesLigne:!!v.taxesLigne, travaux:v.travaux || "", lieu:v.lieu || "", dateTravaux:v.dateTravaux || ""});''')
rep('''  setOptions($("d-code"), TAXCODES.map(c => [c, taxLabel(c)]), doc ? doc.codeTaxe : (p.codeTaxe || (inscrit() ? defCode() : "AUCUNE")));''',
    '''  setOptions($("d-code"), TAXCODES.map(c => [c, taxLabel(c)]), doc ? doc.codeTaxe : (p.codeTaxe || (inscrit() ? defCode() : "AUCUNE")));
  if ($("d-code").value === "AUCUNE") S.doc.ttc = false; S.doc.codeAvant = ""; docTTCset();''')

# ---------- Envoi : courriel, texto, Messenger, Snapchat… ----------
rep('''async function mailDoc(kind, id){''', '''/* Envoyer une facture ou une soumission : PDF ou image par le partage du téléphone ou de Windows, courriel, texte à copier */
async function shareDoc(kind, id){
  const isF = kind === "facture", doc = (isF ? S.d.factures : S.d.devis).find(x => x.id === id); if (!doc) return;
  const G = docGenre(kind), c = clientOf(doc) || {}, msg = docMessage(kind, doc), canShare = !!(navigator.canShare && navigator.share);
  const tel = String(c.telephone || "").replace(/[^\\d+]/g, ""), mail = String(c.courriel || "").replace(/[^\\w.@+-]/g, "");
  const opt = (k, icon, t, s) => '<button type="button" class="send-opt" data-send="' + k + '">' + ico(icon) + "<span><b>" + esc(t) + "</b><small>" + esc(s) + "</small></span></button>";
  openForm("Envoyer " + G.la + " " + doc.numero, '<p class="muted small">' + esc(doc.client) + " · " + esc(fmt(docTotals(doc).total)) + '</p><label class="field full"><span>Message</span><textarea id="snd-msg" class="ctl" rows="7">' + esc(msg) + "</textarea></label>" +
    '<div class="send-opts">' + (canShare ? opt("pdf", "i-pdf", "Envoyer le PDF", "Courriel, Messenger, WhatsApp, Outlook…") + opt("img", "i-image", "Envoyer en image", "Texto, Snapchat, Messenger, Instagram…") : "") +
    (mail ? opt("mail", "i-mail", "Courriel à " + c.courriel, CLOUD ? "Le PDF est joint par le partage" : "Ton logiciel de courriel s'ouvre ; joins le PDF") : opt("mail", "i-mail", "Courriel", "Ton logiciel de courriel s'ouvre avec le message")) +
    (tel && CLOUD ? opt("sms", "i-phone", "Texto à " + c.telephone, "Le message seulement, sans pièce jointe") : "") +
    opt("copy", "i-copy", "Copier le message", "Pour le coller où tu veux") + opt("files", "i-download", "Télécharger le PDF et l'image", "Pour les joindre toi-même") + "</div>", null,
    {cancel:"Fermer", wide:true, ready: f => {
      f.onclick = async e => {
        const b = e.target.closest("[data-send]"); if (!b) return; const how = b.dataset.send, text = $("snd-msg").value, subj = docTitre(kind) + " " + doc.numero + (R().nom ? " · " + R().nom : "");
        const mark = () => mutate(d => { const x = (isF ? d.factures : d.devis).find(y => y.id === id); if (!x) return false; const t = today(); if ((isF ? x.envoyeeLe : x.envoyeLe) === t) return false; if (isF) x.envoyeeLe = t; else x.envoyeLe = t; });
        try {
          b.disabled = true; const logo = await loadLogo(), name = fileSafe(doc.numero + " " + (doc.client || ""));
          if (how === "copy"){ await navigator.clipboard.writeText(text); toast("Message copié"); return; }
          if (how === "sms"){ location.href = "sms:" + tel + "?body=" + encodeURIComponent(text); mark(); return; }
          if (how === "pdf" || how === "img" || (how === "mail" && CLOUD && canShare)){
            const files = how === "img" ? await docImages(kind, doc, logo) : [new File([docPDF(kind, doc, logo)], name + ".pdf", {type:"application/pdf"})];
            if (how === "mail" && mail){ try { await navigator.clipboard.writeText(c.courriel); toast("Courriel du client copié : colle-le dans « À »"); } catch(er){} }
            if (!navigator.canShare({files})) throw new Error("ce navigateur ne partage pas les fichiers");
            await navigator.share({files, title: subj, text}); mark(); closeForm(); return;
          }
          if (how === "mail"){ const path = await makeDocPDF(kind, id, false, true); location.href = "mailto:" + mail + "?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(text); mark();
            if (path && !CLOUD) toast("Joins le PDF : dossier " + winPath(path.split("/").slice(0, -1).join("/")) + ", fichier " + path.split("/").pop()); return; }
          if (how === "files"){ const all = [new File([docPDF(kind, doc, logo)], name + ".pdf", {type:"application/pdf"}), ...await docImages(kind, doc, logo)];
            all.forEach((f, k) => setTimeout(() => { const u = URL.createObjectURL(f), a = document.createElement("a"); a.href = u; a.download = f.name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 60000); }, k * 400));
            toast("PDF et image enregistrés dans Téléchargements"); return; }
        } catch(er){ if (er && er.name === "AbortError") return; toast("Envoi impossible : " + ((er && er.message) || er)); }
        finally { b.disabled = false; }
      };
    }});
}
async function mailDoc(kind, id){''')
rep('''  else if (ds.fmail) mailDoc("facture", ds.fmail);
  else if (ds.dmail) mailDoc("devis", ds.dmail);''', '''  else if (ds.fmail) shareDoc("facture", ds.fmail);
  else if (ds.dmail) shareDoc("devis", ds.dmail);''')
rep('''title="Envoyer par courriel" aria-label="Envoyer par courriel">' + ico("i-mail") + "</button>") + "</div></td></tr>"; }).join("") +''',
    '''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + "</button>") + "</div></td></tr>"; }).join("") +''')
rep('''title="Envoyer par courriel" aria-label="Envoyer par courriel">' + ico("i-mail") + "</button></div></td></tr>").join("") + "</tbody></table>"''',
    '''title="Envoyer (courriel, texto, Messenger…)" aria-label="Envoyer">' + ico("i-send") + "</button></div></td></tr>").join("") + "</tbody></table>"''')

rep('''        <label class="field"><span>Taxes</span><select id="d-code" class="ctl"></select></label>''', '''        <label class="field"><span>Taxes applicables</span><select id="d-code" class="ctl"></select></label>''')
# ---------- Divers ----------
i = s.index('<symbol id="i-pdf"'); j = s.index('</symbol>', i) + len('</symbol>')
s = s[:j] + '''
  <symbol id="i-star" viewBox="0 0 24 24"><path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z"/></symbol>
  <symbol id="i-send" viewBox="0 0 24 24"><path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4z"/></symbol>
  <symbol id="i-image" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.5"/><path d="M21 16l-5-5-9 9"/></symbol>
  <symbol id="i-phone" viewBox="0 0 24 24"><rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18h2"/></symbol>''' + s[j:]
rep('''"patch","fichier","deplacer","fichier-suppr"];''', '''"patch","fichier","deplacer","fichier-suppr","doc-v2"];''')
rep('''(f.lignes || []).forEach(l => { if (l.produit) salesAmt += r2((Number(l.qte) || 0) * (Number(l.prix) || 0)); }); });''', '''(f.lignes || []).forEach(l => { if (l.produit) salesAmt += ligneHT(f, l); }); });''')
rep('''</style>''', '''/* Éditeur de factures et soumissions : lignes sur deux rangées */
.lines-top{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.lines-top>span{font-size:.8rem;font-weight:600;color:var(--muted)}
.seg{display:inline-flex;border:1px solid var(--line-strong);border-radius:999px;overflow:hidden}
.seg button{border:0;background:var(--surface);padding:6px 12px;font:inherit;font-size:.82rem;font-weight:600;color:var(--muted);cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
.seg button+button{border-left:1px solid var(--line-strong)}
.seg button:disabled{opacity:.45;cursor:not-allowed}
.le-row.le2{grid-template-columns:176px 70px 96px 124px minmax(0,1fr) 64px;grid-template-areas:"desc desc desc desc desc desc" "type qte unit prix amt acts";row-gap:6px;align-items:end}
.le2 .le-desc{grid-area:desc;resize:none;min-height:36px;line-height:1.35}
.le2 .le-type{grid-area:type}
.le2 .le-mini:nth-of-type(1){grid-area:qte}.le2 .le-mini:nth-of-type(2){grid-area:unit}.le2 .le-mini:nth-of-type(3){grid-area:prix}
.le2 .amt{grid-area:amt;align-self:center;padding-top:14px}
.le2 .le-acts{grid-area:acts;display:flex;gap:2px;justify-content:flex-end;align-self:center;padding-top:14px}
.le-mini{display:flex;flex-direction:column;gap:2px;min-width:0}
.le-mini span{font-size:.68rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}
.le2.rabais .amt{color:var(--pos)}
.le2 small{grid-column:1/-1}
.le2 .le-tax{color:var(--muted);font-size:.78rem;margin-top:-2px;text-align:right}
@media (max-width:620px){.le-row.le2{grid-template-columns:1fr 1fr 1fr;grid-template-areas:"desc desc desc" "type type type" "qte unit prix" "amt amt acts"}.le2 .amt{display:block;text-align:left;padding-top:0}.le2 .le-acts{padding-top:0}}
.lt-add{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip-btn{display:inline-flex;align-items:center;gap:4px;border:1px dashed var(--line-strong);background:var(--surface);border-radius:999px;padding:5px 10px;font:inherit;font-size:.8rem;font-weight:600;color:var(--ink);cursor:pointer}
.chip-btn .ic{width:14px;height:14px}
.chip-btn:hover{border-style:solid;border-color:var(--accent);color:var(--accent)}
.chip-btn.alt{color:var(--pos)}
.doc-tot .sep{border-top:1px dashed var(--line);padding:0;margin:4px 0}
.send-opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px;margin-top:10px}
.send-opt{display:flex;gap:10px;align-items:flex-start;text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:var(--r);padding:10px 12px;font:inherit;cursor:pointer;color:var(--ink)}
.send-opt:hover{border-color:var(--accent)}
.send-opt span{display:flex;flex-direction:column;gap:2px}
.send-opt small{color:var(--muted);font-size:.78rem}
.send-opt .ic{flex:none;margin-top:2px;color:var(--accent)}
.tarifs{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:var(--r);margin-bottom:8px}
.tarifs .tarif{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:6px 10px;border-top:1px solid var(--line);font-size:.88rem}
.tarifs .tarif:first-child{border-top:0}
.tarifs p{padding:8px 10px;margin:0}
.tarif-add{flex-wrap:wrap}
.tarif-add #r-tf-desc{flex:1;min-width:180px}
</style>''')
open(P, "w", encoding="utf-8").write(s); print("ok")
