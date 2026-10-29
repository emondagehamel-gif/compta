"""v3.6 : module « Impôts de fin d'année » (préparation du T2 et de la CO-17)."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); JS = open(sys.argv[2], encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:90]))
    s = s.replace(a, b)
rep('</style>', '''
/* Impôts de fin d'année */
#fa-body .card{display:flex;flex-direction:column;gap:10px}
#fa-body h3{margin:6px 0 0;font-size:.95rem}
#fa-body .kv .v input{text-align:right}
#fa-body details.more{padding-bottom:4px}
.fa-list{display:flex;flex-direction:column}
.fa-list .item{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--line)}
.fa-list .item:last-child{border-bottom:none}
.fa-list .t{display:flex;flex-direction:column;gap:2px;min-width:0}
.fa-list .t small{color:var(--muted);font-size:.82rem}
.fa-list .v{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.fa-biens{display:flex;flex-direction:column;gap:10px}
.fa-bien{border:1px solid var(--line);border-radius:var(--r);padding:10px 12px;display:flex;flex-direction:column;gap:6px}
.fa-bien.off{opacity:.6}
.fa-bien .row{display:flex;gap:10px;align-items:baseline}
.fa-sel{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fa-sel select{max-width:100%}
</style>''')
i = s.index('<symbol id="i-pdf"'); j = s.index('</symbol>', i) + len('</symbol>')
s = s[:j] + '\n  <symbol id="i-calc" viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8.5 11h.01M12 11h.01M15.5 11h.01M8.5 14.5h.01M12 14.5h.01M8.5 18h.01M12 18h.01M15.5 14.5V18"/></symbol>' + s[j:]
rep('''      <button data-view="km"><svg class="ic"><use href="#i-car"/></svg><span class="lbl">Kilométrage</span></button>''',
'''      <button data-view="km"><svg class="ic"><use href="#i-car"/></svg><span class="lbl">Kilométrage</span></button>
      <button data-view="impots"><svg class="ic"><use href="#i-calc"/></svg><span class="lbl">Impôts de fin d'année</span></button>''')
rep('''    <!-- Rapports -->''', '''    <!-- Impôts de fin d'année -->
    <section class="view" id="view-impots" hidden><div class="stack" id="fa-body"></div></section>

    <!-- Rapports -->''')
rep('''km:"Kilométrage", projets:"Projets", rapports:"Rapports", reglages:"Réglages"};''', '''km:"Kilométrage", impots:"Impôts de fin d'année", projets:"Projets", rapports:"Rapports", reglages:"Réglages"};''')
rep('''km:"i-car", projets:"i-folder",''', '''km:"i-car", impots:"i-calc", projets:"i-folder",''')
rep('''km:renderKm, projets:renderProjets,''', '''km:renderKm, impots:renderImpots, projets:renderProjets,''')
rep('''  if (!d.reglages.onboarding || typeof d.reglages.onboarding !== "object") d.reglages.onboarding = {};''', '''  if (!d.reglages.onboarding || typeof d.reglages.onboarding !== "object") d.reglages.onboarding = {};
  if (!d.reglages.fiscal || typeof d.reglages.fiscal !== "object") d.reglages.fiscal = {};''')
rep('''["tvh","c","i-percent","Taxes de vente","TPS et TVQ à produire"], ["km","c","i-car","Kilométrage","Trajets, allocation, registre"]]],''',
'''["tvh","c","i-percent","Taxes de vente","TPS et TVQ à produire"], ["km","c","i-car","Kilométrage","Trajets, allocation, registre"], ["impots","c","i-calc","Impôts de fin d'année","T2, CO-17, amortissement, impôt estimé"]]],''')
rep('''/* ----- Projets ----- */''', JS + '''
/* ----- Projets ----- */''')
open(P, "w", encoding="utf-8").write(s); print("ok")
