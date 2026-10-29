/* ===== Signature en ligne des soumissions (v3.12) =====
   Le client reçoit un lien (dans le courriel et sur un bouton du PDF). La page signer.html lui montre la soumission,
   il signe avec le doigt, et le service Google Apps Script de l'entreprise dépose la signature dans le dossier
   « telephone » (op « signature », appareil « en ligne »). Le lien est protégé par une clé secrète (reglages.signerCle) :
   on ne peut pas changer le montant ni signer une autre soumission. */
const SIGN_PAGE = (typeof window !== "undefined" && window.__SIGNER) || "https://emondagehamel-gif.github.io/compta/signer.html";
const SCRIPT_BASE = (typeof window !== "undefined" && window.__SCRIPT) || "https://script.google.com/macros/s/";
/* SHA-256 et HMAC (calcul immédiat, pour garder docMessage et docPDF simples) */
const SHA256 = (() => {
  const primes = []; for (let n = 2; primes.length < 64; n++){ if (primes.every(p => n % p)) primes.push(n); }
  const frac = x => (x - Math.floor(x)) * 4294967296 >>> 0;
  const K = primes.map(p => frac(Math.cbrt(p))), H0 = primes.slice(0, 8).map(p => frac(Math.sqrt(p)));
  return bytes => {
    const l = bytes.length, nb = ((l + 9 + 63) >> 6) << 6, m = new Uint8Array(nb); m.set(bytes); m[l] = 0x80;
    const dv = new DataView(m.buffer); dv.setUint32(nb - 4, (l * 8) >>> 0); dv.setUint32(nb - 8, Math.floor(l / 536870912));
    const h = H0.slice(), w = new Uint32Array(64), r = (x, k) => (x >>> k) | (x << (32 - k));
    for (let o = 0; o < nb; o += 64){
      for (let i = 0; i < 16; i++) w[i] = dv.getUint32(o + i * 4);
      for (let i = 16; i < 64; i++){ const a = w[i - 15], b = w[i - 2]; w[i] = (w[i - 16] + (r(a, 7) ^ r(a, 18) ^ (a >>> 3)) + w[i - 7] + (r(b, 17) ^ r(b, 19) ^ (b >>> 10))) >>> 0; }
      let [a, b, c, d, e, f, g, hh] = h;
      for (let i = 0; i < 64; i++){
        const t1 = (hh + (r(e, 6) ^ r(e, 11) ^ r(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) >>> 0, t2 = ((r(a, 2) ^ r(a, 13) ^ r(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      [a, b, c, d, e, f, g, hh].forEach((v, i) => { h[i] = (h[i] + v) >>> 0; });
    }
    const out = new Uint8Array(32), ov = new DataView(out.buffer); h.forEach((v, i) => ov.setUint32(i * 4, v)); return out;
  };
})();
function hmacHex(key, msg){
  const enc = new TextEncoder(); let k = enc.encode(key); if (k.length > 64) k = SHA256(k);
  const kb = new Uint8Array(64); kb.set(k); const m = enc.encode(msg), a = new Uint8Array(64 + m.length), b = new Uint8Array(96);
  a.set(kb.map(x => x ^ 0x36)); a.set(m, 64); b.set(kb.map(x => x ^ 0x5c)); b.set(SHA256(a), 64);
  return Array.from(SHA256(b), x => x.toString(16).padStart(2, "0")).join("");
}
/* Identifiant du service (adresse « …/macros/s/IDENTIFIANT/exec » collée dans Réglages) */
function signerId(url){
  const u = String(url == null ? R().signerUrl || "" : url).trim(), b = SCRIPT_BASE.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const m = u.match(new RegExp("^" + b + "([\\w-]{20,200})/exec/?(?:[?#].*)?$")); return m ? m[1] : "";
}
const signerPret = () => !!(signerId() && /^[0-9a-f]{32,}$/.test(String(R().signerCle || "")));
const signMsg = o => ["v1", o.i, o.n, encodeURIComponent(o.c), o.t, o.e, encodeURIComponent(o.en)].join("|");
/* Lien de signature d'une soumission ouverte, ou "" (déjà signée, facturée, refusée, ou service pas activé) */
function signLien(kind, doc){
  if (kind !== "devis" || !doc || !doc.id || doc.signature || ["facture", "refuse"].includes(doc.statut) || !signerPret()) return "";
  const r = R(), o = {i: String(doc.id), n: String(doc.numero || ""), c: String(doc.client || "").trim(), t: String(Math.round(docTotals(doc).total * 100)), e: String(doc.echeance || ""), en: String(r.nom || "").trim()};
  const q = new URLSearchParams({s: signerId(), i: o.i, n: o.n, c: o.c, t: o.t, e: o.e, en: o.en, k: hmacHex(String(r.signerCle), signMsg(o)).slice(0, 32)});
  return SIGN_PAGE + "#" + q.toString();
}
/* Mention sous la signature : « Signé électroniquement en ligne » ou « …, sur téléphone » */
const sigVia = sg => sg && sg.appareil ? (sg.appareil === "en ligne" ? " en ligne" : ", sur " + sg.appareil) : "";
const sigPied = sg => "Signé électroniquement" + (sg.appareil === "en ligne" ? " en ligne" : "") + (sg.heure ? " à " + hmTxt(sg.heure) : "") + (sg.appareil && sg.appareil !== "en ligne" ? ", sur " + sg.appareil : "");
/* Bouton vert « Signer en ligne » (lien cliquable du PDF), dans la case de signature du client */
function sigBoutonPDF(P, x, y, url, g){
  const w = 152, h = 26;
  P.rrect(x, y, w, h, 6, {fill: g}); P.text(x + w / 2, y + 17, "Signer en ligne  ›", {size: 10.5, bold: true, color: "#FFFFFF", align: "center"}); P.link(x, y, w, h, url);
}
