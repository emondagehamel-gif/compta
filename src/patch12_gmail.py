"""v3.11 : « Envoyer par Gmail » depuis l'ordinateur avec le PDF déjà joint.
L'application ouvre la page d'envoi (envoi.html, sur le même site que l'app du téléphone), lui passe le message et le PDF,
et la page envoie le courriel par Gmail quand tu cliques « Envoyer ». Quand c'est envoyé, la page prévient l'application,
qui note la date d'envoi. L'ancienne façon (Gmail s'ouvre et le PDF se télécharge) reste en dépannage."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

rep('''const PHONE_URL = "https://emondagehamel-gif.github.io/compta/";''',
    '''const PHONE_URL = "https://emondagehamel-gif.github.io/compta/";
/* Page d'envoi par Gmail : elle reçoit le PDF par message entre fenêtres et l'envoie avec ton compte Gmail */
const ENVOI_URL = window.__ENVOI || PHONE_URL + "envoi.html";
const ENVOI = {w:null, ori:"", data:null, cb:null, got:false, timer:0, tries:0,
  start(w, cb){ Object.assign(this, {w, cb, ori:new URL(ENVOI_URL).origin, data:null, got:false, tries:0}); this.arm(); },
  set(d){ this.data = d; if (this.got) this.post(); },
  post(){ if (this.w && this.data && !this.w.closed) try { this.w.postMessage(this.data, this.ori); } catch(e){} },
  /* La page ne répond pas (ancienne version gardée par le navigateur) : on la recharge deux fois, puis on propose l'autre façon */
  arm(){ clearTimeout(this.timer); this.timer = setTimeout(() => { if (this.got || !this.w || this.w.closed) return;
    if (++this.tries <= 2){ try { this.w.location.href = ENVOI_URL + "?essai=" + this.tries; } catch(e){} this.arm(); } else if (this.cb) this.cb.late(); }, 9000); }
};
window.addEventListener("message", e => {
  const E = ENVOI, m = e.data; if (!E.w || e.source !== E.w || e.origin !== E.ori || !m || typeof m !== "object") return;
  if (m.t === "envoi-pret"){ E.got = true; clearTimeout(E.timer); E.post(); }
  else if (m.t === "envoi-fait" && E.data && m.id === E.data.id && E.cb){ const cb = E.cb; E.cb = null; cb.done(m); }
});''')

# Option principale : le PDF est joint automatiquement
rep('''    (!CLOUD ? opt("gmail", "i-mail", "Envoyer par Gmail", (acct ? "Depuis " + acct + ". " : "") + "Le message est prêt" + (mail ? " pour " + c.courriel : "") + " ; le PDF se télécharge pour le joindre.").replace('class="send-opt"', 'class="send-opt prim"') : "") +''',
    '''    (!CLOUD ? opt("gmail", "i-mail", "Envoyer par Gmail", (acct ? "Depuis " + acct + ", " : "") + "avec le PDF déjà joint" + (mail ? ", à " + c.courriel : "") + ". Tu vérifies, puis tu cliques Envoyer.").replace('class="send-opt"', 'class="send-opt prim"') : "") +''')

rep('''        if (how === "gmail"){
          const url = "https://mail.google.com/mail/?view=cm&fs=1&tf=1"''',
    '''        const fnPdf = fileSafe(doc.numero + " " + (doc.client || "")) + ".pdf";
        const manuel = '<div class="snd-acts"><button type="button" class="btn sm" data-send="gmailm">' + ico("i-download") + "Autre façon : ouvrir Gmail et télécharger le PDF</button></div>";
        if (how === "gmail"){
          const w = window.open(ENVOI_URL, "compta-envoi", "popup,width=780,height=900");
          if (!w){ guide("<span><b>La fenêtre d'envoi a été bloquée par le navigateur.</b> Clique sur l'icône de fenêtre bloquée à droite de la barre d'adresse, choisis « Toujours autoriser », puis clique de nouveau « Envoyer par Gmail ».</span>" + manuel); return; }
          ENVOI.start(w, {
            done: m => { mark(); toast("Courriel envoyé à " + (m.to || "ton client"));
              if ($("snd-guide")) guide('<span><b>✓ Courriel envoyé</b> à ' + esc(m.to || "") + (m.de ? ", depuis " + esc(m.de) : "") + ", avec le PDF " + esc(fnPdf) + ". Tu le retrouves dans Gmail, dans « Messages envoyés ».</span>"); },
            late: () => { if ($("snd-guide")) guide("<span><b>La fenêtre d'envoi ne répond pas.</b> Vérifie ta connexion Internet et réessaie, ou utilise l'autre façon.</span>" + manuel); }
          });
          guide("<span><b>Une fenêtre Gmail s'ouvre</b> avec le message et le PDF <b>" + esc(fnPdf) + "</b> déjà joint. Vérifie le courriel, puis clique <b>Envoyer</b>." +
            "<br><small>La première fois, Google te demande la permission d'envoyer des courriels avec ton compte" + (acct ? " " + esc(acct) : "") + ".</small></span>" + manuel);
          try { const logo = await loadLogo(), sigs = await docSigs(kind, doc), pdf = docPDF(kind, doc, logo, sigs);
            ENVOI.set({t:"envoi", v:1, id:doc.id, kind, numero:doc.numero, client:doc.client || "", to:mail, subject:subj, body:text, filename:fnPdf, pdf:new Uint8Array(pdf), de:acct, nom:R().nom || ""});
          } catch(er){ toast("PDF non créé : " + ((er && er.message) || er)); try { w.close(); } catch(e){} }
          return;
        }
        if (how === "gmailm"){
          const url = "https://mail.google.com/mail/?view=cm&fs=1&tf=1"''')
rep('''.send-opt.prim{grid-column:1/-1;border-color:var(--accent);background:var(--accent-soft, var(--surface))}''',
    '''.send-opt.prim{grid-column:1/-1;border-color:var(--accent);background:var(--accent-soft, var(--surface))}
#snd-guide{flex-direction:column;align-items:stretch}#snd-guide small{color:var(--muted)}.snd-acts{margin-top:8px}''')
open(P, "w", encoding="utf-8").write(s); print("ok")
