"""v3.11 (téléphone / page principale) : connexion Google pour la page d'envoi par Gmail (envoi.html).
La page principale est la seule adresse de retour autorisée : elle demande la permission « envoyer des courriels »
(en plus de ce qui est déjà accordé), garde le jeton avec ses permissions, puis retourne à envoi.html."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

rep('''const SCOPE = "https://www.googleapis.com/auth/drive";''',
    '''const SCOPE = "https://www.googleapis.com/auth/drive", MAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send";''')
# Connexion : permission Gmail seulement pour la page d'envoi ; « auto » = Google ne demande que si nécessaire
rep('''  const p = new URLSearchParams({client_id:clientId(), redirect_uri:redirectUri(), response_type:"token", scope:SCOPE, include_granted_scopes:"true", state:st, prompt: interactive ? "select_account" : "none"});
  const hint = LS.get("email", ""); if (hint) p.set("login_hint", hint);''',
    '''  const p = new URLSearchParams({client_id:clientId(), redirect_uri:redirectUri(), response_type:"token", scope:LS.get("authMail", 0) ? MAIL_SCOPE : SCOPE, include_granted_scopes:"true", state:st, prompt: interactive === true ? "select_account" : "none"});
  if (interactive === "auto") p.delete("prompt");
  const hint = LS.get("authHint", "") || LS.get("email", ""); if (hint) p.set("login_hint", hint);''')
rep('''    TOK = {t:p.get("access_token"), exp:Date.now() + (Number(p.get("expires_in")) || 3600) * 1000};''',
    '''    TOK = {t:p.get("access_token"), exp:Date.now() + (Number(p.get("expires_in")) || 3600) * 1000, scope:p.get("scope") || ""};''')
rep('''  if (qp.get("auth")){
    const r = qp.get("retour") || ""; LS.set("retour", /^complet\\.html(#[\\w-]*)?$/.test(r) ? r : "");
    try { history.replaceState(null, "", location.pathname); } catch(e){}
    if (online() && clientId()){ authRedirect(qp.get("auth") === "2"); return; }
  }
  const auth = readAuthHash();
  if (auth && auth.ok && LS.get("retour", "")){ const r = LS.get("retour", ""); LS.set("retour", ""); location.replace(r); return; }''',
    '''  if (qp.get("auth")){
    const r = qp.get("retour") || "", a = qp.get("auth"), hint = qp.get("hint") || "";
    LS.set("retour", /^(complet|envoi)\\.html(#[\\w-]*)?$/.test(r) ? r : "");
    LS.set("authMail", qp.get("mail") && /^envoi/.test(r) ? 1 : 0); LS.set("authHint", /^[^@\\s]+@[^@\\s]+$/.test(hint) ? hint : "");
    try { history.replaceState(null, "", location.pathname); } catch(e){}
    if (online() && clientId()){ authRedirect(a === "2" ? true : a === "3" ? "auto" : false); return; }
  }
  const auth = readAuthHash(); LS.set("authMail", 0); LS.set("authHint", "");
  if (auth && LS.get("retour", "")){ const r = LS.get("retour", "");
    /* page d'envoi : on y retourne même si Google a refusé, pour qu'elle l'explique */
    if (auth.ok || /^envoi/.test(r)){ LS.set("retour", ""); location.replace(r + (auth.ok ? "" : "#erreur=" + encodeURIComponent(auth.err || "erreur"))); return; } }''')
open(P, "w", encoding="utf-8").write(s); print("ok")
