"""v3.9 : styles des factures et soumissions (Nature, Moderne, Épuré), formes arrondies dans le moteur PDF, choix et aperçu dans les Réglages."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); STYLE = open(sys.argv[2], encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)
# Moteur PDF : chemins, rectangles arrondis, cercles
rep('''    image(img, x, y, w, h){ if (!imgs.includes(img)) imgs.push(img);''', '''    path(cmds, o){ o = o || {}; let p = ""; cmds.forEach(c => { if (c[0] === "M") p += n(c[1]) + " " + n(H - c[2]) + " m "; else if (c[0] === "L") p += n(c[1]) + " " + n(H - c[2]) + " l "; else if (c[0] === "C") p += n(c[1]) + " " + n(H - c[2]) + " " + n(c[3]) + " " + n(H - c[4]) + " " + n(c[5]) + " " + n(H - c[6]) + " c "; else if (c[0] === "Z") p += "h "; });
      ops.push((o.fill ? col(o.fill) + " rg " : "") + (o.stroke ? col(o.stroke) + " RG " + n(o.w || 0.8) + " w 1 J 1 j " : "") + p + (o.fill && o.stroke ? "B" : o.fill ? "f" : "S") + " 0 0 0 rg 0 0 0 RG 0 J 0 j");
      cv.push({k:"p", cmds, fill:o.fill || null, stroke:o.stroke || null, w:o.w || 0.8}); },
    rrect(x, y, w, h, r, o){ r = Math.max(0, Math.min(r, w / 2, h / 2)); const k = 0.5523 * r;
      P.path([["M", x + r, y], ["L", x + w - r, y], ["C", x + w - r + k, y, x + w, y + r - k, x + w, y + r], ["L", x + w, y + h - r], ["C", x + w, y + h - r + k, x + w - r + k, y + h, x + w - r, y + h], ["L", x + r, y + h], ["C", x + r - k, y + h, x, y + h - r + k, x, y + h - r], ["L", x, y + r], ["C", x, y + r - k, x + r - k, y, x + r, y], ["Z"]], o); },
    circle(cx, cy, r, o){ const k = 0.5523 * r; P.path([["M", cx + r, cy], ["C", cx + r, cy + k, cx + k, cy + r, cx, cy + r], ["C", cx - k, cy + r, cx - r, cy + k, cx - r, cy], ["C", cx - r, cy - k, cx - k, cy - r, cx, cy - r], ["C", cx + k, cy - r, cx + r, cy - k, cx + r, cy], ["Z"]], o); },
    image(img, x, y, w, h){ if (!imgs.includes(img)) imgs.push(img);''')
# Les styles, juste après la mise en page d'origine
i = s.index("function docPDF(kind, doc, logo, sigs){")
s = s[:i] + STYLE + s[i:]
# Réglages : choix du style et aperçu
rep('''slogan:"", neq:"", modePaiement:"", signatureCie:"",''', '''slogan:"", neq:"", modePaiement:"", signatureCie:"", styleDoc:"nature",''')
rep('''          <label class="field"><span>Titre des devis sur le document</span>''', '''          <div class="field full"><span>Style des factures et soumissions</span><div class="inline-form"><select id="r-style" class="ctl auto"></select><button class="btn sm" type="button" id="r-style-voir"><svg class="ic"><use href="#i-pdf"/></svg>Voir un aperçu</button></div></div>
          <label class="field"><span>Titre des devis sur le document</span>''')
rep('''  $("r-slogan").value = r.slogan || "";''', '''  setOptions($("r-style"), Object.entries(DOC_STYLES), DOC_STYLES[r.styleDoc] ? r.styleDoc : "origine");
  $("r-slogan").value = r.slogan || "";''')
rep('''    slogan:$("r-slogan").value.trim(),''', '''    styleDoc:$("r-style").value, slogan:$("r-slogan").value.trim(),''')
rep('''$("r-sigcie-rm").addEventListener("click",''', '''/* Aperçu d'un style : une soumission d'exemple, sans rien enregistrer */
$("r-style-voir").addEventListener("click", async () => {
  const r = R(), was = r.styleDoc; r.styleDoc = $("r-style").value;
  try {
    const ex = {id:"apercu", numero:"D-" + new Date().getFullYear() + "-000", date:today(), echeance:addDays(today(), Number(r.validiteDevis) || 30), dateTravaux:addDays(today(), 7), client:"Client exemple", lieu:"123, rue des Érables, Québec", codeTaxe: inscrit() ? defCode() : "AUCUNE", taxesIncluses:false,
      travaux:"Émondage de 2 érables en façade et ramassage complet des branches.", message:r.messageFacture || "",
      lignes:[{type:"service", description:"Émondage de 2 érables", qte:6, unite:"h", prix:85}, {type:"location", description:"Nacelle de 60 pi", qte:1, unite:"jour", prix:450}, {type:"deplacement", description:"Aller-retour au chantier", qte:40, unite:"km", prix:1.25}]};
    const blob = new Blob([docPDF("devis", ex, await loadLogo(), {cie: r.signatureCie ? await loadJpeg(r.signatureCie) : null})], {type:"application/pdf"});
    if (CLOUD) await nuShare(blob, "apercu-style.pdf", ""); else { const u = URL.createObjectURL(blob); const w = window.open(u, "_blank"); if (!w) downloadBlob(blob, "apercu-style.pdf"); setTimeout(() => URL.revokeObjectURL(u), 120000); }
  } catch(e){ toast("Aperçu impossible : " + (e.message || e)); }
  finally { r.styleDoc = was; }
});
$("r-sigcie-rm").addEventListener("click",''')
open(P, "w", encoding="utf-8").write(s); print("ok")
