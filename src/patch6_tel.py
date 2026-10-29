"""v3.7 au téléphone (app terrain) : factures et soumissions complètes, envoi par PDF ou image."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)
i = s.index("/* ===== Factures et devis ===== */"); j = s.index("async function copyTxt(v){")
NEW = r'''/* ===== Factures et devis ===== */
/* Les nouveautés (types de frais, rabais, taxes incluses) attendent que l'ordinateur soit en version 3.7 */
const telDocV2 = () => { const t = (S.d && S.d.telephone) || {}; return Array.isArray(t.ops) && t.ops.includes("doc-v2"); };
function fDoc(kind, doc, p){
  p = p || {}; const isF = kind === "facture", r = R(), v2 = telDocV2(), titre = docTitre(kind);
  const lignes = doc ? clone(doc.lignes) : (p.lignes ? clone(p.lignes) : [{type:"service", description:"", qte:1, unite:"", prix:0}]);
  lignes.forEach(l => { if (!l.type) l.type = "service"; });
  const cli = S.d.clients.find(c => norm(c.nom) === norm(doc ? doc.client : p.client || "")) || {};
  const date0 = doc ? doc.date : today(), n0 = String(doc ? daysBetween(doc.date, doc.echeance || doc.date) : (isF ? (r.termes != null ? r.termes : 30) : (r.validiteDevis || 30)));
  const terms = isF ? TERMS_F : TERMS_D, termVal = terms.some(t => t[0] === n0) ? n0 : "autre";
  const code0 = doc ? doc.codeTaxe : (p.codeTaxe || (inscrit() ? defCode() : "AUCUNE"));
  const prods = S.d.produits, tfs = r.tarifs || [], ttc0 = v2 && code0 !== "AUCUNE" && !!(doc ? doc.taxesIncluses : (p.taxesIncluses != null ? p.taxesIncluses : r.docTTC)), mode0 = code0 === "AUCUNE" ? "aucune" : ttc0 ? "incl" : "plus";
  const addOpts = '<option value="">+ Ajouter une ligne…</option><optgroup label="Nouvelle ligne">' + LT.filter(t => t.k !== "rabais" || v2).map(t => '<option value="t:' + t.k + '">' + esc(t.l) + "</option>").join("") + "</optgroup>" +
    (tfs.length ? '<optgroup label="Tarifs enregistrés">' + tfs.map(t => '<option value="f:' + esc(t.id) + '">' + esc(t.description + " · " + fmt(t.prix) + (t.unite ? " / " + t.unite : "")) + "</option>").join("") + "</optgroup>" : "") +
    (prods.length ? '<optgroup label="Produits du stock">' + prods.map(x => '<option value="p:' + esc(x.id) + '">' + esc(x.nom + " (" + fq(stockOf(x)) + ")") + "</option>").join("") + "</optgroup>" : "");
  const body = '<label class="field"><span>Client</span><input class="ctl" id="d-cli" list="d-dl" maxlength="120" autocomplete="off" value="' + esc(doc ? doc.client : p.client || "") + '" placeholder="Nom du client"><datalist id="d-dl">' + S.d.clients.map(c => '<option value="' + esc(c.nom) + '">').join("") + "</datalist></label>" +
    '<details class="more"><summary>Coordonnées du client</summary><div><label class="field"><span>Téléphone</span><input class="ctl" id="d-tel" type="tel" value="' + esc(cli.telephone || "") + '"></label><label class="field"><span>Courriel</span><input class="ctl" id="d-mail" type="email" value="' + esc(cli.courriel || "") + '"></label><label class="field"><span>Adresse</span><textarea class="ctl" id="d-adr" rows="2">' + esc(cli.adresse || "") + "</textarea></label></div></details>" +
    '<div class="two"><label class="field"><span>Date</span><input class="ctl" type="date" id="d-date" value="' + esc(date0) + '"></label><label class="field"><span>' + (isF ? "Payable" : "Valide") + '</span><select class="ctl" id="d-terms">' + terms.map(([k, l]) => '<option value="' + k + '"' + (k === termVal ? " selected" : "") + ">" + esc(l) + "</option>").join("") + "</select></label></div>" +
    '<label class="field" id="d-ech-f"' + (termVal === "autre" ? "" : " hidden") + '><span>' + (isF ? "Échéance" : "Valide jusqu'au") + '</span><input class="ctl" type="date" id="d-ech" value="' + esc(doc ? doc.echeance : addDays(date0, Number(n0) || 0)) + '"></label>' +
    '<label class="field"><span>Description des travaux (facultatif)</span><textarea class="ctl" id="d-trav" rows="2" maxlength="1500" placeholder="Ex. : Émondage de 3 érables en façade et ramassage des branches">' + esc(doc ? doc.travaux || "" : p.travaux || "") + "</textarea></label>" +
    '<div class="two"><label class="field"><span>Lieu des travaux</span><input class="ctl" id="d-lieu" maxlength="200" value="' + esc(doc ? doc.lieu || "" : p.lieu || "") + '" placeholder="Si différent"></label><label class="field"><span>' + (isF ? "Date des travaux" : "Date prévue") + '</span><input class="ctl" type="date" id="d-dtrav" value="' + esc(doc ? doc.dateTravaux || "" : p.dateTravaux || "") + '"></label></div>' +
    '<div class="field"><span>Taxes</span><div class="picks" id="d-txp">' + [["plus","Taxes en plus"],["incl","Taxes incluses"],["aucune","Sans taxes"]].map(([k, l]) => '<button type="button" class="pick" data-ttc="' + k + '" aria-pressed="' + (k === mode0) + '"' + (k === "incl" && !v2 ? " disabled" : "") + ">" + l + "</button>").join("") + '</div><small id="d-txt" class="muted"></small><label class="check" style="margin-top:6px"><input type="checkbox" id="d-txl"' + ((doc ? doc.taxesLigne : (p.taxesLigne != null ? p.taxesLigne : r.docTaxesLigne)) ? " checked" : "") + '><span>Montrer les taxes de chaque ligne sur le document</span></label></div>' +
    '<div class="field"><span>Services et frais</span>' +
    '<div id="d-lines" style="display:flex;flex-direction:column;gap:8px"></div><select class="ctl" id="d-add" style="margin-top:8px">' + addOpts + "</select></div>" +
    '<div class="tot" id="d-tot"></div>' +
    '<label class="field"><span>Taxes applicables</span><select class="ctl" id="d-code">' + TAXCODES.map(c => '<option value="' + c + '"' + (code0 === c ? " selected" : "") + ">" + esc(taxLabel(c)) + "</option>").join("") + "</select></label>" +
    (isF && !doc ? '<div class="field"><span>Paiement</span><div class="picks"><button type="button" class="pick" data-dpay="" aria-pressed="true">' + ico("i-cal") + "À encaisser</button>" + S.d.comptes.filter(c => c.sorte === "banque" || c.sorte === "caisse").map(c => '<button type="button" class="pick" data-dpay="' + esc(c.id) + '" aria-pressed="false">' + ico("i-bank") + "Déjà payée : " + esc(c.nom) + "</button>").join("") + "</div></div>" : "") +
    '<label class="field"><span>Message sur le document</span><textarea class="ctl" id="d-msg" rows="2" maxlength="600">' + esc(doc ? doc.message || "" : (p.message != null ? p.message : r.messageFacture || "")) + "</textarea></label>" +
    (v2 ? "" : '<p class="hint">« Taxes incluses » et les rabais seront offerts dès que l\'application de l\'ordinateur, dans sa nouvelle version, aura été ouverte une fois.</p>') +
    '<p class="hint" id="d-hint" hidden></p>';
  const types = LT.filter(t => t.k !== "rabais" || v2 || lignes.some(l => l.type === "rabais"));
  const mtTxt = l => { const m = ligneMt(l); return (m < 0 ? "−" : "") + fmt(Math.abs(m)); };
  const linesHTML = () => S.form.lignes.map((l, i) => { const t = LTM[ligneType(l)];
    return '<div class="line' + (l.type === "rabais" ? " rabais" : "") + '" data-li="' + i + '"><div class="row" style="justify-content:space-between"><select class="ctl lt-sel" data-lf="type" aria-label="Type">' + types.map(x => '<option value="' + x.k + '"' + (x.k === t.k ? " selected" : "") + ">" + esc(x.l) + "</option>").join("") + '</select><button class="icon-btn" type="button" data-dl="rm" data-i="' + i + '" aria-label="Retirer la ligne"' + (S.form.lignes.length < 2 ? " disabled" : "") + ">" + ico("i-x") + "</button></div>" +
      '<textarea class="ctl" rows="2" data-lf="description" placeholder="' + esc(t.ph) + '" aria-label="Description">' + esc(l.description) + "</textarea>" +
      '<div class="three q3"><label class="field"><span>Qté</span><input class="ctl" data-lf="qte" inputmode="decimal" value="' + esc(fq(l.qte)) + '"></label><label class="field"><span>Unité</span><select class="ctl" data-lf="unite">' + uniteOptions(l.unite) + '</select></label><label class="field"><span>' + (S.form.ttc ? "Prix (tx incl.)" : "Prix unitaire") + '</span><input class="ctl" data-lf="prix" inputmode="decimal" value="' + (l.prix ? esc(n2s(l.prix)) : "") + '" placeholder="0,00"></label></div>' +
      '<span class="muted small" data-amt="' + i + '">' + mtTxt(l) + '</span><small class="muted" data-tax="' + i + '"></small></div>'; }).join("");
  const recalc = () => { const t = docTotals({lignes:S.form.lignes, codeTaxe:$("d-code").value, taxesIncluses:S.form.ttc});
    $("d-tot").innerHTML = "<div><span>" + (t.ttc ? "Montant avant taxes" : "Sous-total") + "</span><span>" + fmt(t.st) + "</span></div>" + taxLines($("d-code").value, t).map(([k, v]) => '<div class="muted"><span>' + esc(k) + "</span><span>" + fmt(v) + "</span></div>").join("") + '<div class="g"><span>Total' + (t.ttc ? " (taxes incl.)" : "") + "</span><span>" + fmt(t.total) + "</span></div>";
    const dd = {lignes:S.form.lignes, codeTaxe:$("d-code").value, taxesIncluses:S.form.ttc}, TX = ligneTaxes(dd);
    S.form.lignes.forEach((l, i) => { const a = document.querySelector('[data-amt="' + i + '"]'); if (a) a.textContent = mtTxt(l); const x = document.querySelector('[data-tax="' + i + '"]'); if (x){ const s = Number(l.prix) ? ligneTaxTxt(dd, TX[i]) : ""; x.textContent = s; x.hidden = !s; } });
    const msgs = []; if (isF && t.total >= 100 && (t.tx || t.tq) && (!r.noTPS || (t.tq && !r.noTVQ))) msgs.push("Ajoute tes numéros de TPS et de TVQ dans les Réglages de l'application de l'ordinateur : ils doivent figurer sur les factures de 100 $ et plus."); $("d-hint").innerHTML = msgs.map(esc).join("<br>"); $("d-hint").hidden = !msgs.length; return t; };
  const txMode = () => $("d-code").value === "AUCUNE" ? "aucune" : S.form.ttc ? "incl" : "plus";
  const txSet = () => { const m = txMode(); pressSet("[data-ttc]", "data-ttc", m); $("d-txt").textContent = m === "aucune" ? "Aucune taxe sur ce document." : m === "incl" ? "Les prix entrés comprennent déjà la TPS et la TVQ." : "Les prix entrés sont avant taxes : la TPS et la TVQ s'ajoutent."; };
  const drawLines = () => { $("d-lines").innerHTML = linesHTML(); recalc(); txSet(); };
  const prixPour = (prix, ttc) => { const [a, b] = taxRates($("d-code").value || "AUCUNE"); if (!!ttc === !!S.form.ttc || !(a || b)) return r2(prix); return ttc ? r2(prix * 100 / (100 + a + b)) : r2(prix * (100 + a + b) / 100); };
  const addLine = ln => { const L = S.form.lignes; if (L.length === 1 && !L[0].description && !L[0].prix) L[0] = ln; else L.push(ln); drawLines(); if (!ln.description){ const t = document.querySelectorAll('[data-lf="description"]'); t[t.length - 1].focus(); } };
  const title = doc ? titre + " " + doc.numero : isF ? (p.fromDevis ? "Facture " + docGenre("devis").de : "Nouvelle facture") : (titre === "Devis" ? "Nouveau devis" : "Nouvelle " + titre.toLowerCase());
  openSheet(title, body, {primary:"Enregistrer", state:{lignes, pay:"", ttc:ttc0},
    secondary:'<button class="btn" type="button" data-dsave="send">' + ico("i-send") + "Enregistrer et envoyer</button>",
    ready: drawLines,
    onInput: e => { const f = e.target.closest("[data-lf]"); if (f && f.dataset.lf !== "type"){ const l = S.form.lignes[Number(f.closest("[data-li]").dataset.li)]; if (f.dataset.lf === "description") l.description = f.value; else if (f.dataset.lf === "unite") l.unite = f.value; else { const v = num(f.value); l[f.dataset.lf] = isFinite(v) ? v : 0; } recalc(); } },
    onChange: e => { const id = e.target.id;
      if (id === "d-code"){ if (e.target.value === "AUCUNE") S.form.ttc = false; drawLines(); }
      if (e.target.dataset && e.target.dataset.lf === "type"){ const l = S.form.lignes[Number(e.target.closest("[data-li]").dataset.li)], was = LTM[ligneType(l)]; l.type = e.target.value; if (!l.unite || l.unite === was.u) l.unite = (LTM[l.type] || {}).u || ""; drawLines(); }
      if (id === "d-terms" || id === "d-date"){ const t = $("d-terms").value; $("d-ech-f").hidden = t !== "autre"; if (t !== "autre") $("d-ech").value = addDays($("d-date").value || today(), Number(t) || 0); }
      if (id === "d-cli"){ const c = S.d.clients.find(x => norm(x.nom) === norm(e.target.value)) || {}; $("d-tel").value = c.telephone || ""; $("d-mail").value = c.courriel || ""; $("d-adr").value = c.adresse || ""; }
      if (id === "d-add"){ const v = e.target.value; e.target.value = ""; if (!v) return; const k = v.slice(2);
        if (v[0] === "t") addLine({type:k, description:"", qte:1, unite:(LTM[k] || {}).u || "", prix:0});
        else if (v[0] === "f"){ const t = tfs.find(x => x.id === k); if (t) addLine({type:t.type || "service", description:t.description, qte:1, unite:t.unite || "", prix:prixPour(t.prix, t.ttc)}); }
        else if (v[0] === "p"){ const x = S.d.produits.find(q => q.id === k); if (x) addLine({type:"materiaux", description:x.nom + (x.code ? " (" + x.code + ")" : ""), qte:1, unite:x.unite || "unité", prix:prixPour(Number(x.prix) || 0, false), produit:x.id}); } } },
    onClick: e => { const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.dl === "rm"){ S.form.lignes.splice(Number(b.dataset.i), 1); drawLines(); }
      else if (b.dataset.ttc != null){ const m = b.dataset.ttc, code = $("d-code");
        if (m === "aucune"){ if (code.value !== "AUCUNE") S.form.codeAvant = code.value; code.value = "AUCUNE"; S.form.ttc = false; }
        else { if (code.value === "AUCUNE") code.value = S.form.codeAvant || (quebec() ? "QC" : defCode() !== "AUCUNE" ? defCode() : "QC"); S.form.ttc = m === "incl"; }
        drawLines(); }
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
      if ($("d-txl").checked) data.taxesLigne = true; else delete data.taxesLigne;
      ["travaux","lieu","dateTravaux"].forEach(k => { if (!data[k]) delete data[k]; });
      if (isF){ data.categorie = (doc && doc.categorie) || "ventes"; if (p.fromDevis) data.devis = p.fromDevis; if (!doc) data.paye = S.form.pay || ""; }
      else if (!doc) data.statut = "ouvert";
      const withSend = S.form.withSend; if (!withSend) closeSheet(); toast(titre + " " + data.numero + (doc ? " modifié" + (isF || titre !== "Devis" ? "e" : "") : " envoyé" + (isF || titre !== "Devis" ? "e" : "") + " à tes livres"));
      await sendOp(kind, data);
      S.vt = isF ? "factures" : "devis"; if (isF) S.vtF = "tous"; if (S.tab === "ventes") vVentes();
      if (withSend){ const fresh = (isF ? S.d.factures : S.d.devis).find(x => x.id === data.id) || Object.assign({}, data, {clientId: cli.id || ""}); sendDoc(kind, fresh); return false; } }});
}
function docBody(kind, x){
  const t = docTotals(x), isF = kind === "facture", s = isF ? facStatus(x) : devStatus(x), c = clientOf(x) || {}, G = docGroupes(x), TXL = ligneTaxes(x);
  return '<div><span class="eyebrow">' + esc(docTitre(kind) + " · " + dLong(x.date)) + "</span><h2>" + esc(x.numero + " · " + x.client) + '</h2><div class="row" style="margin-top:6px"><span class="chip ' + s.cls + '">' + esc(s.l) + '</span><span class="muted small">' + esc(isF ? (x.echeance && x.echeance > x.date ? "Payable d'ici le " + dLong(x.echeance) : "Payable à réception") : "Valide jusqu'au " + dLong(x.echeance)) + "</span></div></div>" +
    (x.travaux ? '<p class="small">' + esc(x.travaux) + "</p>" : "") + (x.lieu ? '<p class="muted small">Lieu : ' + esc(x.lieu) + "</p>" : "") +
    '<table class="doc-lines">' + G.map(g => (G.length > 1 ? '<tr><td colspan="2" class="grp">' + esc(g.t.g) + "</td></tr>" : "") + g.lignes.map(l => { const m = ligneMt(l), lt = ligneTaxTxt(x, TXL[x.lignes.indexOf(l)]); return "<tr><td>" + esc(l.description).replace(/\n/g, "<br>") + '<br><span class="muted small">' + esc(qteTxt(l) + " × " + fmt(l.prix)) + "</span>" + (lt ? '<br><span class="muted small">' + esc(lt) + "</span>" : "") + '</td><td class="n">' + (m < 0 ? "−" : "") + fmt(Math.abs(m)) + "</td></tr>"; }).join("")).join("") + "</table>" +
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
'''
s = s[:i] + NEW + s[j:]
rep('''  openSheet("Facture " + f.numero, docBody("facture", f) + '<p class="muted small">Le PDF est aussi créé sur l\\'ordinateur, dans le dossier factures, quand il reçoit la facture.</p>',
    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-pdf") + "PDF</button>" +''',
'''  openSheet("Facture " + f.numero, docBody("facture", f) + '<p class="muted small">Le PDF est aussi créé sur l\\'ordinateur, dans le dossier factures, quand il reçoit la facture.</p>',
    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-send") + "Envoyer</button>" +''')
rep('''if (x === "pdf") savePDF("facture", f);''', '''if (x === "pdf") sendDoc("facture", f);''')
rep('''  openSheet("Devis " + v.numero, docBody("devis", v)''', '''  openSheet(docTitre("devis") + " " + v.numero, docBody("devis", v)''')
rep('''    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-pdf") + "PDF</button>" + (s.k !== "facture" ?''', '''    {secondary:'<button class="btn" type="button" data-x="pdf">' + ico("i-send") + "Envoyer</button>" + (s.k !== "facture" ?''')
rep('''if (x === "pdf") savePDF("devis", v); else if (x === "mod") fDoc("devis", v); else if (x === "fac") fDoc("facture", null, {client:v.client, lignes:v.lignes, codeTaxe:v.codeTaxe, message:v.message, fromDevis:v.id});''',
    '''if (x === "pdf") sendDoc("devis", v); else if (x === "mod") fDoc("devis", v); else if (x === "fac") fDoc("facture", null, {client:v.client, lignes:v.lignes, codeTaxe:v.codeTaxe, message:v.message, fromDevis:v.id, taxesIncluses:!!v.taxesIncluses, taxesLigne:!!v.taxesLigne, travaux:v.travaux || "", lieu:v.lieu || "", dateTravaux:v.dateTravaux || ""});''')
open(P, "w", encoding="utf-8").write(s); print("ok")
