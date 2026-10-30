"""Construit l'application installable (PWA) dans pwa/dist à partir des sources du téléphone.
Usage : python3 pwa/build.py [CLIENT_ID] [VERSION]   (depuis le dossier app)"""
import subprocess, sys, json, os, hashlib
client = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "__CLIENT_ID__"
subprocess.run(['python3', 'phone/extract.py', open('phone/names.txt').read().strip(), 'phone/core.js'], check=True)
src = open('Comptabilite/Comptabilite.html', encoding='utf-8').read()
i = src.index('<svg width="0" height="0"'); sprite = src[i:src.index('</svg>', i)]
for sym in ['<symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></symbol>', '<symbol id="i-grid" viewBox="0 0 24 24"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></symbol>']:
    if sym.split('"')[1] not in sprite: sprite += '  ' + sym + '\n'
sprite += '</svg>'
head = open('phone/head.html', encoding='utf-8').read()
head = head.replace('<title>Comptabilité mobile</title>', '<title>Comptabilité</title>').replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
ui = open('pwa/ui.js', encoding='utf-8').read().replace('"__CLIENT_ID__"', json.dumps(client))
js = '(function(){\n"use strict";\n' + open('phone/core.js', encoding='utf-8').read() + '\n' + ui + '\n})();\n'
full = src.replace('<meta name="viewport" content="width=device-width,initial-scale=1">', '<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">\n<meta name="theme-color" content="#151D19" media="(prefers-color-scheme: dark)">\n<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" href="icon-feuille-192.png" type="image/png">\n<link rel="apple-touch-icon" href="apple-touch-icon-feuille.png">', 1)
assert full != src, "en-tête de la version complète introuvable"
envoi = open('pwa/envoi.html', encoding='utf-8').read(); signer = open('pwa/signer.html', encoding='utf-8').read()
ver = hashlib.sha1((head + js + sprite + full + envoi + signer).encode()).hexdigest()[:10]
html = '''<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151D19" media="(prefers-color-scheme: dark)">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Comptabilité">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-feuille-192.png" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon-feuille.png">
''' + head + '''<style>html,body{margin:0}body{min-height:100dvh;overscroll-behavior-y:contain}[hidden]{display:none!important}.sync.off i{background:var(--muted)}img{max-width:100%}
.full-link{flex-direction:row;align-items:center;gap:12px;text-decoration:none;color:inherit;border-color:color-mix(in srgb,var(--accent) 35%,var(--line));background:var(--accent-soft)}
.full-link .fl-ic{width:40px;height:40px;border-radius:10px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;flex:none}
.mt-h{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:700;margin:8px 2px 0}
.mt-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.mt-tile{position:relative;display:flex;flex-direction:column;gap:3px;padding:14px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);color:var(--ink);text-decoration:none;min-height:108px}
.mt-tile:active{background:var(--sunk)}
.mt-ic{width:40px;height:40px;border-radius:12px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;margin-bottom:6px}
.mt-tile b{font-size:.98rem}.mt-tile small{color:var(--muted);font-size:.8rem;line-height:1.3}.mt-tile.on small{color:var(--warn);font-weight:600}
.mt-dot{position:absolute;top:12px;right:12px;width:9px;height:9px;border-radius:50%;background:var(--warn)}
.m-list{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);overflow:hidden}
.m-list a{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding:13px 14px;color:var(--ink);text-decoration:none;font-size:.95rem}
.m-list a:last-child{border-bottom:none}.m-list a span{flex:1}.m-list a .ic{color:var(--muted)}.m-list a .ic:first-child{color:var(--accent)}</style>
</head>
<body>
''' + sprite + '\n' + open('phone/body.html', encoding='utf-8').read() + '<script>\n' + js + '</script>\n</body>\n</html>\n'
os.makedirs('pwa/dist', exist_ok=True)
open('pwa/dist/index.html', 'w', encoding='utf-8').write(html)
open('pwa/dist/complet.html', 'w', encoding='utf-8').write(full)
open('pwa/dist/envoi.html', 'w', encoding='utf-8').write(envoi)
# Page de signature : avec les calculs et la mise en page des soumissions (aperçu complet et copie signée en PDF)
import re
core_sig = re.sub(r'(?m)^const SIG_FONTS = .*$', 'const SIG_FONTS = {};', open('phone/core.js', encoding='utf-8').read())   # pas besoin des polices pour signer
core_bundle = 'const CORE = (function(){\n"use strict";\nconst S = {d:null, tmap:{}};\n' + core_sig + '\nreturn {S, docPDF, docImages, jpegObj};\n})();'
assert '/*__CORE__*/' in signer
open('pwa/dist/signer.html', 'w', encoding='utf-8').write(signer.replace('/*__CORE__*/', core_bundle.replace('</script', '<\\/script')))
open('pwa/all.js', 'w', encoding='utf-8').write(js)
manifest = {"name": "Comptabilité", "short_name": "Comptabilité", "description": "Comptabilité de l'entreprise sur le terrain : reçus, factures, devis, agenda, trajets et entretiens, même sans réseau.",
  "lang": "fr-CA", "id": "./", "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
  "background_color": "#F2F5F1", "theme_color": "#FFFFFF",
  "icons": [{"src": "icon-feuille-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-feuille-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-feuille-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
open('pwa/dist/manifest.webmanifest', 'w', encoding='utf-8').write(json.dumps(manifest, ensure_ascii=False, indent=2))
sw = open('pwa/sw.js', encoding='utf-8').read().replace('__VERSION__', ver)
open('pwa/dist/sw.js', 'w', encoding='utf-8').write(sw)
open('pwa/dist/.nojekyll', 'w').write('')
print('built', len(html), 'version', ver, 'client', client[:12])
