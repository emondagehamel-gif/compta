"""Construit l'application installable (PWA) dans pwa/dist à partir des sources du téléphone.
Usage : python3 pwa/build.py [CLIENT_ID] [VERSION]   (depuis le dossier app)"""
import subprocess, sys, json, os, hashlib
client = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "__CLIENT_ID__"
subprocess.run(['python3', 'phone/extract.py', open('phone/names.txt').read().strip(), 'phone/core.js'], check=True)
src = open('Comptabilite/Comptabilite.html', encoding='utf-8').read()
i = src.index('<svg width="0" height="0"'); sprite = src[i:src.index('</svg>', i)]
sprite += '''  <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></symbol>
  <symbol id="i-grid" viewBox="0 0 24 24"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></symbol>
  <symbol id="i-map" viewBox="0 0 24 24"><path d="M12 21s-6-5.4-6-11a6 6 0 1 1 12 0c0 5.6-6 11-6 11z"/><path d="M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z"/></symbol>
</svg>'''
head = open('phone/head.html', encoding='utf-8').read()
head = head.replace('<title>Comptabilité mobile</title>', '<title>Comptabilité</title>').replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
ui = open('pwa/ui.js', encoding='utf-8').read().replace('"__CLIENT_ID__"', json.dumps(client))
js = '(function(){\n"use strict";\n' + open('phone/core.js', encoding='utf-8').read() + '\n' + ui + '\n})();\n'
ver = hashlib.sha1((head + js + sprite).encode()).hexdigest()[:10]
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
<link rel="icon" href="icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
''' + head + '''<style>html,body{margin:0}body{min-height:100dvh;overscroll-behavior-y:contain}[hidden]{display:none!important}.sync.off i{background:var(--muted)}img{max-width:100%}</style>
</head>
<body>
''' + sprite + '\n' + open('phone/body.html', encoding='utf-8').read() + '<script>\n' + js + '</script>\n</body>\n</html>\n'
os.makedirs('pwa/dist', exist_ok=True)
open('pwa/dist/index.html', 'w', encoding='utf-8').write(html)
open('pwa/all.js', 'w', encoding='utf-8').write(js)
manifest = {"name": "Comptabilité", "short_name": "Comptabilité", "description": "Comptabilité de l'entreprise sur le terrain : reçus, factures, devis, agenda, trajets et entretiens, même sans réseau.",
  "lang": "fr-CA", "id": "./", "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
  "background_color": "#F2F5F1", "theme_color": "#FFFFFF",
  "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
open('pwa/dist/manifest.webmanifest', 'w', encoding='utf-8').write(json.dumps(manifest, ensure_ascii=False, indent=2))
sw = open('pwa/sw.js', encoding='utf-8').read().replace('__VERSION__', ver)
open('pwa/dist/sw.js', 'w', encoding='utf-8').write(sw)
open('pwa/dist/.nojekyll', 'w').write('')
print('built', len(html), 'version', ver, 'client', client[:12])
