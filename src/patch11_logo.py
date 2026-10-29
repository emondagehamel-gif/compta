"""v3.10 : nouveau logo de l'application (la feuille des factures, blanche sur vert), dans la barre latérale, l'en-tête du téléphone et l'onglet."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read(); FAV = open(sys.argv[2], encoding="utf-8").read().strip()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:110]))
    s = s.replace(a, b)
i = s.index('<link rel="icon" href="data:image/svg+xml,'); j = s.index(">", i) + 1
s = s[:i] + '<link rel="icon" href="' + FAV.replace('"', "%22") + '">' + s[j:]
k = s.index('<symbol id="i-pdf"'); e = s.index('</symbol>', k) + len('</symbol>')
s = s[:e] + '''
  <symbol id="i-feuille" viewBox="0 0 100 100"><g transform="translate(50 50) scale(1.42) translate(-48 -52)"><path d="M30 70C17.6 40 55.9 29.9 74 26C70.1 44.1 60 82.4 30 70Z" fill="currentColor" stroke="none"/><path d="M30.5 69.5L21 79" fill="none" stroke="currentColor" stroke-width="4.6" stroke-linecap="round"/><path d="M33 67C44 56 55 45 66.5 33.5" fill="none" stroke="var(--leaf-vein, #2C6B39)" stroke-width="3.2" stroke-linecap="round"/></g></symbol>''' + s[e:]
rep('''      <span class="logo"><svg class="ic"><use href="#i-book"/></svg></span>''', '''      <span class="logo"><svg class="ic feuille"><use href="#i-feuille"/></svg></span>''')
rep('''<header class="m-head" id="m-head"><span class="logo">' + ico("i-book") + '</span>''', '''<header class="m-head" id="m-head"><span class="logo"><svg class="ic feuille"><use href="#i-feuille"/></svg></span>''')
rep('''.logo{width:34px;height:34px;border-radius:10px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;flex:none}''',
    '''.logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(160deg,#3F8C4D,#235A2F);color:#FFFFFF;--leaf-vein:#2C6B39;display:grid;place-items:center;flex:none;box-shadow:0 1px 2px rgba(20,60,30,.25)}
.logo .ic.feuille{width:26px;height:26px;stroke-width:0}
.splash .box .logo{width:52px;height:52px;border-radius:14px}
.splash .box .logo .ic.feuille{width:40px;height:40px}''')
rep('''function splash(html){ $("splash-box").innerHTML = html;''', '''function splash(html){ $("splash-box").innerHTML = '<span class="logo"><svg class="ic feuille"><use href="#i-feuille"/></svg></span>' + html;''')
rep('''  <div class="box" id="splash-box">
    <span class="eyebrow">Comptabilité</span>''', '''  <div class="box" id="splash-box">
    <span class="logo"><svg class="ic feuille"><use href="#i-feuille"/></svg></span>
    <span class="eyebrow">Comptabilité</span>''')
open(P, "w", encoding="utf-8").write(s); print("ok")
