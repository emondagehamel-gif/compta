"""v3.12 : signature en ligne des soumissions.
Le client reçoit un bouton « Signer en ligne » (courriel et PDF) qui ouvre signer.html ; le service Google Apps Script
de l'entreprise (signer.gs) dépose la signature dans telephone/ (op « signature », appareil « en ligne »).
Ce patch : cœur (lien signé HMAC, bouton du PDF), liens cliquables dans le moteur PDF, op « signature » en ligne,
et la mise en place dans Réglages (code à copier, adresse du service, vérification)."""
import sys, json
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); CORE = open(sys.argv[2], encoding="utf-8").read(); GS = open(sys.argv[3], encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

# 1. Cœur partagé (aussi extrait pour le téléphone)
rep('''function docPDF(kind, doc, logo, sigs){''', CORE.rstrip() + '''\nfunction docPDF(kind, doc, logo, sigs){''')
rep('''  slogan:"", neq:"", modePaiement:"", signatureCie:"",''', '''  slogan:"", neq:"", modePaiement:"", signatureCie:"", signerUrl:"", signerCle:"",''')

# 2. Moteur PDF : zones cliquables (liens) par page
rep('''  const W = 612, H = 792, pages = [], imgs = [], draws = [];
  let ops = null, cv = null;''', '''  const W = 612, H = 792, pages = [], imgs = [], draws = [], links = [];
  let ops = null, cv = null, lk = null;''')
rep('''    page(){ ops = []; pages.push(ops); cv = []; draws.push(cv); return P; },
    at(i){ ops = pages[i]; cv = draws[i]; return P; },''', '''    page(){ ops = []; pages.push(ops); cv = []; draws.push(cv); lk = []; links.push(lk); return P; },
    at(i){ ops = pages[i]; cv = draws[i]; lk = links[i]; return P; },
    link(x, y, w, h, url){ if (lk && url) lk.push({x, y, w, h, url:String(url)}); },''')
rep('''      const xo = imgs.length ? " /XObject << " + imgs.map((_, i) => "/Im" + (i + 1) + " " + (6 + i) + " 0 R").join(" ") + " >>" : "";
      pages.forEach((o, i) => { const pn = first + i * 2, c = o.join("\\n");
        obj(pn, ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + W + " " + H + "] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >>" + xo + " >> /Contents " + (pn + 1) + " 0 R >>"]);
        obj(pn + 1, ["<< /Length " + c.length + " >>\\nstream\\n" + c + "\\nendstream"]); });
      const total = first + pages.length * 2, xref = len;''', '''      const xo = imgs.length ? " /XObject << " + imgs.map((_, i) => "/Im" + (i + 1) + " " + (6 + i) + " 0 R").join(" ") + " >>" : "";
      const annBase = first + pages.length * 2, ann = []; links.forEach((L, i) => L.forEach(l => ann.push({i, l})));
      pages.forEach((o, i) => { const pn = first + i * 2, c = o.join("\\n"), my = ann.map((a, k) => a.i === i ? (annBase + k) + " 0 R" : "").filter(Boolean);
        obj(pn, ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + W + " " + H + "] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >>" + xo + " >>" + (my.length ? " /Annots [" + my.join(" ") + "]" : "") + " /Contents " + (pn + 1) + " 0 R >>"]);
        obj(pn + 1, ["<< /Length " + c.length + " >>\\nstream\\n" + c + "\\nendstream"]); });
      ann.forEach((a, k) => { const l = a.l, u = l.url.replace(/[^\\x21-\\x7e]/g, ch => encodeURIComponent(ch)).replace(/[\\\\()]/g, "\\\\$&");
        obj(annBase + k, ["<< /Type /Annot /Subtype /Link /Rect [" + [l.x, H - l.y - l.h, l.x + l.w, H - l.y].map(n).join(" ") + "] /Border [0 0 0] /F 4 /A << /Type /Action /S /URI /URI (" + u + ") >> >>"]); });
      const total = annBase + ann.length, xref = len;''')

# 3. Signature reçue en ligne : « en ligne », jamais par-dessus une signature existante ; attend la soumission si elle n'est pas encore arrivée du téléphone
rep('''      const L = x.kind === "devis" ? d.devis : d.factures, e = L.find(v => v.id === x.id); if (!e || !photos[0]) break;''',
    '''      const L = x.kind === "devis" ? d.devis : d.factures, e = L.find(v => v.id === x.id), web = x.appareil === "en ligne";
      if (!e && web && photos[0] && Date.now() - new Date(now).getTime() < 3 * 864e5){ res.attendre = true; break; }
      if (!e || !photos[0]) break;
      if (web && e.signature){ res.msg = "Signature en ligne ignorée : " + e.numero + " était déjà signée"; break; }''')
rep('''signeLe: x.signeLe || now, appareil: "téléphone"};''', '''signeLe: x.signeLe || now, appareil: web ? "en ligne" : "téléphone"};''')
rep('''res.msg = "Signature du client : " + e.numero + " (" + e.signature.nom + ")"; break; }''',
    '''res.msg = (web ? "Signée en ligne par le client : " : "Signature du client : ") + e.numero + " (" + e.signature.nom + ")"; break; }''')
rep('''        if (r.unknown){ unknown.add(o.name); continue; }''', '''        if (r.unknown){ unknown.add(o.name); continue; }
        if (r.attendre){ unknown.add(o.name); later.add(o.name); continue; }   // la soumission n'est pas encore arrivée : on réessaie plus tard''')
rep('''    const msgs = [], pdfs = [], unknown = new Set(); let count = 0;''', '''    const msgs = [], pdfs = [], unknown = new Set(), later = new Set(); let count = 0;''')
rep('''    if (unknown.size) toast(unknown.size + " changement(s) du téléphone attendent une mise à jour de cette application");''',
    '''    if (unknown.size > later.size) toast((unknown.size - later.size) + " changement(s) du téléphone attendent une mise à jour de cette application");''')

# 4. Réglages : mise en place du service de signature
rep('''          <div class="field full"><span>Logo (facultatif)</span>''', '''          <div class="field full"><span>Signature en ligne des soumissions (facultatif)</span><div class="inline-form"><span class="muted small" id="r-sg-st">Pas activée</span><button class="btn sm" type="button" id="r-sg"><svg class="ic"><use href="#i-pen"/></svg>Activer</button><button class="btn link" type="button" id="r-sg-rm" hidden>Désactiver</button></div><small>Le client reçoit un bouton « Signer en ligne » dans le courriel et dans le PDF. Il signe avec le doigt sur son cellulaire, et la soumission passe à « acceptée » toute seule.</small></div>
          <div class="field full"><span>Logo (facultatif)</span>''')
rep('''  $("r-sigcie-st").textContent = r.signatureCie ?''', '''  { const ok = signerPret(); $("r-sg-st").textContent = ok ? "Activée : le bouton « Signer en ligne » est dans les soumissions" : (r.signerUrl ? "À vérifier" : "Pas activée"); $("r-sg-rm").hidden = !r.signerUrl; $("r-sg").lastChild.textContent = ok ? "Vérifier" : "Activer"; }
  $("r-sigcie-st").textContent = r.signatureCie ?''')
rep('''$("r-sigcie-rm").addEventListener("click", () => mutate(d => { d.reglages.signatureCie = ""; }, "Signature de l'entreprise retirée"));''',
    '''$("r-sigcie-rm").addEventListener("click", () => mutate(d => { d.reglages.signatureCie = ""; }, "Signature de l'entreprise retirée"));
/* Signature en ligne : code du service Google Apps Script à coller dans script.google.com */
const SIGNER_GS = ''' + json.dumps(GS, ensure_ascii=False) + ''';
async function signerPing(url){
  try { const r = await fetch(url.replace(/[?#].*$/, "") + "?a=ping", {cache:"no-store"}); if (!r.ok) return {ok:false, err:"http", code:r.status}; return await r.json(); }
  catch(e){ return {ok:false, err:"reseau"}; }
}
function openSigner(){
  const r = R(), compte = r.courriel ? "<b>" + esc(r.courriel) + "</b>" : "le compte Google de l'entreprise";
  openForm("Signature en ligne des soumissions", '<p class="muted small">Un petit service Google, dans ton propre compte, reçoit les signatures de tes clients et les dépose dans ton dossier Comptabilite. C\\'est gratuit. À faire une seule fois, environ 3 minutes.</p>' +
    '<ol class="sg-steps">' +
    '<li><b>Copie le code du service.</b><div><button class="btn sm" type="button" id="sg-copy">' + ico("i-copy") + "Copier le code</button></div></li>" +
    '<li><b>Ouvre Google Apps Script</b> avec ' + compte + ' : <a href="https://script.google.com/home/projects/create" target="_blank" rel="noopener">nouveau projet sur script.google.com</a>. Efface le texte déjà écrit, colle le code (Ctrl+V), puis clique sur l\\'icône 💾 <b>Enregistrer</b>.</li>' +
    '<li><b>Mets-le en ligne.</b> En haut à droite : <b>Déployer</b> › <b>Nouveau déploiement</b>. Clique la roue dentée ⚙ à côté de « Sélectionner le type » › <b>Application Web</b>. « Exécuter en tant que » : <b>Moi</b>. « Qui a accès » : <b>Tout le monde</b>. Clique <b>Déployer</b>, puis <b>Autoriser l\\'accès</b> : choisis ton compte, clique <b>Paramètres avancés</b> › <b>Accéder à … (non sécurisé)</b> › <b>Autoriser</b>. C\\'est ton propre service.</li>' +
    '<li><b>Copie l\\'URL de l\\'application Web</b> (elle se termine par <code>/exec</code>) et colle-la ici :<input id="sg-url" class="ctl" type="url" spellcheck="false" placeholder="https://script.google.com/macros/s/…/exec"></li></ol>' +
    '<div class="banner info" id="sg-res" hidden></div>',
    async () => {
      const url = $("sg-url").value.trim(), res = $("sg-res"), say = h => { res.innerHTML = "<span>" + h + "</span>"; res.hidden = false; };
      if (!signerId(url)) return "Colle l'URL de l'application Web : elle commence par https://script.google.com/macros/s/ et se termine par /exec.";
      const ok = await mutate(d => { d.reglages.signerUrl = url; if (!/^[0-9a-f]{32,}$/.test(String(d.reglages.signerCle || ""))) d.reglages.signerCle = Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2, "0")).join(""); });
      if (!ok) return "Enregistrement impossible.";
      say("Vérification du service…");
      const p = await signerPing(url);
      if (p && p.ok && p.cle){ toast("Signature en ligne activée"); say("<b>✓ Service vérifié.</b> Les prochaines soumissions envoyées auront le bouton « Signer en ligne »."); return false; }
      if (p && p.ok) { say("<b>✓ Service trouvé.</b> Google Drive est en train d'enregistrer la clé dans tes livres : le service sera prêt dans une minute. Les prochaines soumissions auront le bouton « Signer en ligne »."); toast("Signature en ligne activée"); return false; }
      say(p && p.err === "dossier" ? "<b>Le service ne trouve pas ton dossier Comptabilite.</b> Vérifie qu'il est déployé avec le compte Google où se trouve ton dossier Comptabilite (Google Drive)." :
        "<b>Le service ne répond pas encore.</b> Vérifie l'étape 3 : « Qui a accès » doit être <b>Tout le monde</b>. L'adresse est quand même enregistrée ; reviens cliquer « Vérifier » dans un moment.");
      return false;
    }, {wide:true, ok:"Vérifier et activer", cancel:"Fermer", ready: () => {
      $("sg-url").value = r.signerUrl || "";
      $("sg-copy").onclick = async () => { try { await navigator.clipboard.writeText(SIGNER_GS); toast("Code copié : colle-le dans Apps Script avec Ctrl+V"); } catch(e){ toast("Copie impossible"); } };
    }});
}
$("r-sg").addEventListener("click", openSigner);
$("r-sg-rm").addEventListener("click", () => mutate(d => { d.reglages.signerUrl = ""; }, "Signature en ligne désactivée : les soumissions n'auront plus le bouton"));''')
rep('''#snd-guide{flex-direction:column;align-items:stretch}''', '''.sg-steps{margin:4px 0 12px;padding-left:22px;display:flex;flex-direction:column;gap:12px}.sg-steps li{line-height:1.45}.sg-steps li>div,.sg-steps li>input{margin-top:6px}.sg-steps code{font-size:.85em;background:var(--sunk);padding:1px 4px;border-radius:4px}
#snd-guide{flex-direction:column;align-items:stretch}''')
open(P, "w", encoding="utf-8").write(s); print("ok")
