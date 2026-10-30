/* ===== Signature de l'entreprise en lettres attachées (v3.13) =====
   Le nom de la personne qui signe pour l'entreprise, écrit dans une police manuscrite, devient une image JPEG
   (comme une signature). On l'ajoute soumission par soumission, quand on le choisit (doc.signatureCie).
   Polices sous licence SIL Open Font License 1.1 : Great Vibes (2010 The Great Vibes Pro Project Authors),
   Allura (2010 The Allura Project Authors), Dancing Script (2016 The Dancing Script Project Authors). */
const SIG_FONTS = __SIG_FONTS__;
const SIG_STYLES = {elegante: "Élégante", classique: "Classique", simple: "Simple"};
const SIG_ENCRE = "#22356F";
const sigPolicesOK = new Set();
async function sigPolice(style){
  const st = SIG_FONTS[style] ? style : "elegante", fam = "Signature " + SIG_STYLES[st];
  if (!sigPolicesOK.has(st)){ const ff = new FontFace(fam, "url(data:font/woff2;base64," + SIG_FONTS[st] + ")"); await ff.load(); document.fonts.add(ff); sigPolicesOK.add(st); }
  return fam;
}
/* Image du nom en lettres attachées : {blob, img:{w, h, data}} */
async function sigNomImage(nom, style){
  const fam = await sigPolice(style), size = 110, c = document.createElement("canvas"), m = c.getContext("2d"); m.font = size + "px '" + fam + "'";
  /* cadre serré autour de l'écriture (les boucles dépassent un peu de la mesure de la police) */
  const tm = m.measureText(nom), asc = Math.max(tm.actualBoundingBoxAscent || size * 0.8, size * 0.6), desc = Math.max(tm.actualBoundingBoxDescent || size * 0.3, size * 0.15), pad = size * 0.12;
  const left = Math.max(tm.actualBoundingBoxLeft || 0, 0) + pad, w = Math.ceil(left + Math.max(tm.width, tm.actualBoundingBoxRight || 0) + pad * 2), h = Math.ceil(asc + desc + pad * 2); c.width = w; c.height = h;
  const g = c.getContext("2d"); g.fillStyle = "#FFFFFF"; g.fillRect(0, 0, w, h); g.font = size + "px '" + fam + "'"; g.fillStyle = SIG_ENCRE; g.textBaseline = "alphabetic"; g.fillText(nom, left, pad + asc);
  const blob = await new Promise(r => c.toBlob(r, "image/jpeg", 0.92));
  return {blob, img: {w, h, data: new Uint8Array(await blob.arrayBuffer())}};
}
/* Fenêtre : nom de la personne qui signe pour l'entreprise et style d'écriture. Rend {blob, img, nom, style, date, heure, signeLe} ou null. */
function sigNomPad(o){
  o = o || {};
  return new Promise(async resolve => {
    const st0 = SIG_FONTS[o.style] ? o.style : "elegante";
    const ov = document.createElement("div"); ov.className = "sig-ov"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", o.titre || "Signature de l'entreprise");
    ov.innerHTML = '<div class="sig-box"><div class="sig-h"><b>' + esc(o.titre || "Signature de l'entreprise") + '</b><button type="button" class="sig-x" aria-label="Fermer">×</button></div>' +
      (o.texte ? '<p class="sig-t">' + esc(o.texte) + "</p>" : "") +
      '<label class="sig-n"><span>Ton nom, comme il doit apparaître</span><input type="text" maxlength="60" autocomplete="name" value="' + esc(o.nom || "") + '" placeholder="Prénom Nom"></label>' +
      '<div class="sig-styles" role="radiogroup" aria-label="Style d\'écriture" style="display:grid;gap:8px;margin:10px 0 4px">' +
      Object.keys(SIG_STYLES).map(k => '<button type="button" role="radio" class="sig-style" data-style="' + k + '" aria-checked="' + (k === st0) + '" style="display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;padding:8px 14px;border-radius:10px;border:2px solid ' + (k === st0 ? "#2F6B3B" : "#D6DED8") + ';background:#FFFFFF;color:' + SIG_ENCRE + ';cursor:pointer;min-height:64px;text-align:left">' +
        '<span class="sig-apercu" style="font-size:34px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></span><small style="color:#68736C;font:600 .78rem system-ui,sans-serif;flex:none">' + SIG_STYLES[k] + "</small></button>").join("") + "</div>" +
      '<div class="sig-f"><span style="flex:1"></span><button type="button" class="sig-b sig-cancel">Annuler</button><button type="button" class="sig-b sig-ok" disabled>' + esc(o.ok || "Signer") + "</button></div></div>";
    document.body.appendChild(ov); document.body.classList.add("sig-open");
    const nomI = ov.querySelector(".sig-n input"), okB = ov.querySelector(".sig-ok"); let style = st0;
    const maj = () => { const v = nomI.value.trim() || "Ton nom"; ov.querySelectorAll(".sig-style").forEach(b => { b.querySelector(".sig-apercu").textContent = v; const on = b.dataset.style === style; b.setAttribute("aria-checked", on); b.style.borderColor = on ? "#2F6B3B" : "#D6DED8"; }); okB.disabled = !nomI.value.trim(); };
    const close = v => { document.removeEventListener("keydown", key, true); ov.remove(); document.body.classList.remove("sig-open"); resolve(v); };
    const key = e => { if (e.key === "Escape"){ e.stopPropagation(); e.preventDefault(); close(null); } };
    document.addEventListener("keydown", key, true);
    ov.querySelector(".sig-x").onclick = () => close(null); ov.querySelector(".sig-cancel").onclick = () => close(null);
    ov.querySelectorAll(".sig-style").forEach(b => { b.onclick = () => { style = b.dataset.style; maj(); }; });
    nomI.addEventListener("input", maj); nomI.addEventListener("keydown", e => { if (e.key === "Enter" && !okB.disabled){ e.preventDefault(); okB.click(); } });
    okB.onclick = async () => {
      okB.disabled = true; const nom = nomI.value.replace(/\s+/g, " ").trim();
      try { const r = await sigNomImage(nom, style), now = new Date(), pad2 = n => String(n).padStart(2, "0");
        close(Object.assign(r, {nom, style, date: today(), heure: pad2(now.getHours()) + ":" + pad2(now.getMinutes()), signeLe: now.toISOString()})); }
      catch(e){ okB.disabled = false; }
    };
    maj(); setTimeout(() => nomI.focus(), 30);
    try { for (const k of Object.keys(SIG_STYLES)){ const fam = await sigPolice(k); const b = ov.querySelector('[data-style="' + k + '"] .sig-apercu'); if (b) b.style.fontFamily = "'" + fam + "', cursive"; } } catch(e){}
  });
}
