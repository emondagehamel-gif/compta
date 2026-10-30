#!/bin/bash
# Reconstruit l'application de l'ordinateur, l'app du téléphone et la PWA (depuis le dossier app)
set -e
W=$(mktemp -d)
cp nuage/Comptabilite-v3.6.html $W/c.html
python3 nuage/patch5_devis.py $W/c.html nuage/devis_core.js
python3 nuage/patch7_signature.py $W/c.html
python3 nuage/patch9_style.py $W/c.html nuage/style_core.js
python3 nuage/patch10_envoi.py $W/c.html
python3 nuage/patch11_logo.py $W/c.html logo/favicon.txt
python3 nuage/patch12_gmail.py $W/c.html
python3 nuage/patch13_signer.py $W/c.html nuage/signer_core.js nuage/signer.gs
python3 nuage/patch14_sigcie.py $W/c.html nuage/sigcie_core.js nuage/polices
cp $W/c.html Comptabilite/Comptabilite.html
cp nuage/ui-v3.6.js $W/u.js
python3 nuage/patch6_tel.py $W/u.js
python3 nuage/patch8_tel_sig.py $W/u.js
python3 nuage/patch12_tel_gmail.py $W/u.js
python3 nuage/patch15_tel_sigcie.py $W/u.js
cp $W/u.js pwa/ui.js
python3 pwa/build.py 426079109504-mnl3la1a49q52rdb98i2as6pulnllt3e.apps.googleusercontent.com
