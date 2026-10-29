"""v3.9.1 : envoi depuis l'ordinateur par Gmail (compte de l'entreprise) et copie du document en image pour le coller ailleurs."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)

# Options de l'ordinateur : Gmail en premier, courriel Windows, copie en image
rep('''    (mail ? opt("mail", "i-mail", "Courriel à " + c.courriel, CLOUD ? "Le PDF est joint par le partage" : "Ton logiciel de courriel s'ouvre ; joins le PDF") : opt("mail", "i-mail", "Courriel", "Ton logiciel de courriel s'ouvre avec le message")) +''',
    '''    (!CLOUD ? opt("gmail", "i-mail", "Envoyer par Gmail", (acct ? "Depuis " + acct + ". " : "") + "Le message est prêt" + (mail ? " pour " + c.courriel : "") + " ; le PDF se télécharge pour le joindre.").replace('class="send-opt"', 'class="send-opt prim"') : "") +
    (CLOUD ? (mail ? opt("mail", "i-mail", "Courriel à " + c.courriel, "Le PDF est joint par le partage") : opt("mail", "i-mail", "Courriel", "Ton application de courriel s'ouvre avec le message"))
      : opt("mail", "i-mail", "Autre logiciel de courriel", "Outlook ou Courrier de Windows ; joins le PDF")) +''')
rep('''    opt("copy", "i-copy", "Copier le message", "Pour le coller où tu veux") + opt("files", "i-download", "Télécharger le PDF et l'image", "Pour les joindre toi-même") + "</div>", null,''',
    '''    opt("copy", "i-copy", "Copier le message", "Le texte seulement, pour le coller où tu veux") +
    opt("copyimg", "i-image", "Copier le document en image", "Colle-le (Ctrl+V) dans un courriel, Messenger ou une autre application") +
    opt("files", "i-download", "Télécharger le PDF et l'image", "Pour les joindre toi-même") + '</div><div class="banner info" id="snd-guide" hidden></div>', null,''')
rep('''  const G = docGenre(kind), c = clientOf(doc) || {}, msg = docMessage(kind, doc), canShare = !!(navigator.canShare && navigator.share);''',
    '''  const G = docGenre(kind), c = clientOf(doc) || {}, msg = docMessage(kind, doc), canShare = !!(navigator.canShare && navigator.share), acct = String(R().courriel || "").trim();''')
# Gmail : la fenêtre s'ouvre tout de suite (pas de blocage), puis le PDF se télécharge et un guide s'affiche
rep('''        try {
          b.disabled = true; const logo = await loadLogo(), sigs = await docSigs(kind, doc), name = fileSafe(doc.numero + " " + (doc.client || ""));''',
    '''        const guide = html => { const g = $("snd-guide"); g.innerHTML = html; g.hidden = false; g.scrollIntoView({block:"nearest"}); };
        if (how === "gmail"){
          const url = "https://mail.google.com/mail/?view=cm&fs=1&tf=1" + (acct ? "&authuser=" + encodeURIComponent(acct) : "") + "&to=" + encodeURIComponent(mail) + "&su=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(text);
          const w = window.open(url, "_blank");
          try { const logo = await loadLogo(), sigs = await docSigs(kind, doc), fn = fileSafe(doc.numero + " " + (doc.client || "")) + ".pdf";
            downloadBlob(new Blob([docPDF(kind, doc, logo, sigs)], {type:"application/pdf"}), fn); mark();
            guide("<span><b>" + (w ? "Gmail s'est ouvert" : "Ouvre Gmail") + "</b> avec le message prêt" + (acct ? ", dans le compte " + esc(acct) : "") + ".<br>Pour joindre le PDF <b>" + esc(fn) + "</b> : glisse-le depuis la liste des téléchargements (en haut à droite) jusque dans le courriel, ou clique sur le trombone 📎 dans Gmail et choisis-le dans <b>Téléchargements</b>." +
              (w ? "" : '<br><a href="' + esc(url) + '" target="_blank" rel="noopener">Ouvrir Gmail</a>') + "</span>");
          } catch(er){ toast("PDF non créé : " + ((er && er.message) || er)); }
          return;
        }
        try {
          b.disabled = true; const logo = await loadLogo(), sigs = await docSigs(kind, doc), name = fileSafe(doc.numero + " " + (doc.client || ""));
          if (how === "copyimg"){
            const pages = await docImages(kind, doc, logo, sigs), bms = []; for (const f of pages) bms.push(await createImageBitmap(f));
            const W = Math.max(...bms.map(x => x.width)), H = bms.reduce((t, x) => t + x.height, 0) + (bms.length - 1) * 12, cv = document.createElement("canvas"); cv.width = W; cv.height = H;
            const g = cv.getContext("2d"); g.fillStyle = "#D9DED9"; g.fillRect(0, 0, W, H); let yy = 0; bms.forEach(x => { g.drawImage(x, 0, yy); yy += x.height + 12; });
            const png = await new Promise(res => cv.toBlob(res, "image/png"));
            await navigator.clipboard.write([new ClipboardItem({"image/png": png})]);
            guide("<span><b>Le document est copié en image.</b> Va dans ton courriel, Messenger ou une autre application et colle-le avec <b>Ctrl+V</b>. Pour le message, reviens ici et clique « Copier le message ».</span>"); mark(); return;
          }''')
rep('''          if (how === "copy"){ await navigator.clipboard.writeText(text); toast("Message copié"); return; }''',
    '''          if (how === "copy"){ await navigator.clipboard.writeText(text); toast("Message copié : colle-le avec Ctrl+V"); return; }''')
rep('''.send-opt .ic{flex:none;margin-top:2px;color:var(--accent)}''', '''.send-opt .ic{flex:none;margin-top:2px;color:var(--accent)}
.send-opt span{min-width:0;overflow-wrap:anywhere}
.send-opt.prim{grid-column:1/-1;border-color:var(--accent);background:var(--accent-soft, var(--surface))}
#snd-guide{margin-top:10px}''')
open(P, "w", encoding="utf-8").write(s); print("ok")
