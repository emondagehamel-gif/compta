# Sources de l'application téléphone

- `ui.js` : interface et synchronisation (Google Drive v3 + connexion Google par redirection, file d'attente hors réseau, photos dans IndexedDB).
- `sw.js` : service worker (l'application s'ouvre sans réseau).
- `head.html`, `body.html` : gabarit. Les fonctions de calcul (`core.js`) sont extraites de `Comptabilite.html` (application de l'ordinateur) par `extract.py` selon `names.txt`.
- `build.py` : construit la page à la racine du dépôt. Il attend l'arborescence de travail de Claude (`phone/`, `pwa/`, `Comptabilite/Comptabilite.html`).
- `mock.py`, `test_pwa.py`, `test_integ_pwa.py` : tests avec un faux Google (hors réseau, retour du réseau, jeton expiré, refus, intégration sur l'ordinateur). `fixture.json` contient des données fictives.

Format des changements déposés dans `Comptabilite/telephone/` : voir `POUR-CLAUDE.md` dans le dossier Comptabilite.

## Version complète (`complet.html`)

`complet.html` est l'application de l'ordinateur (`Comptabilite.html`) en « mode nuage » : elle lit les livres dans Google Drive et envoie chaque modification comme changement `patch` (et `fichier`, `deplacer`, `fichier-suppr` pour les fichiers). Le code du mode nuage est dans `cloud.js` (inséré dans `Comptabilite.html` par `patch2_cloud.py`). La connexion Google passe par `index.html?auth=1&retour=complet.html`, la seule adresse autorisée dans Google Cloud.

## Impôts de fin d'année (v3.6)

`impots.js` (inséré dans `Comptabilite.html` par `patch4_impots.py`) : section qui prépare les montants du T2 et de la CO-17 (DPA, annexe 1, impôt estimé, dividendes T5 et RL-3, dates, dossier PDF). Les saisies sont gardées dans `reglages.fiscal["AAAA"]`. Ce sont des estimations : la transmission se fait avec un logiciel homologué. Tests : `test_impots.py` (calculs vérifiés à la main) et `test_impots_tel.py` (téléphone).

## Soumissions et factures complètes (v3.7)

`devis_core.js` (inséré dans `Comptabilite.html` par `patch5_devis.py`) : lignes par type de frais avec unité, prix taxes incluses, tarifs enregistrés, nouvelle mise en page (`docLayout`, d'après le modèle d'Émondage Hamel) et images JPEG des documents (`docImages`) pour l'envoi par texto, Messenger ou Snapchat. `patch6_tel.py` met à jour le formulaire et l'envoi de l'app terrain (`ui.js`). Tests : `test_devis.py`, `test_devis_tel.py`, `test_integ_devis.py`.

## Signature du client (v3.8)

`sigPad` (dans `devis_core.js`) : pavé de signature à l'écran (doigt, stylet, souris) qui rend une image JPEG. `patch7_signature.py` l'ajoute à l'ordinateur et à la version complète (signature du client, signature de l'entreprise, op `signature`) ; `patch8_tel_sig.py` à l'app terrain. Tests : `test_signature.py`, `test_signature_tel.py`, `test_integ_signature.py`.

## Styles des documents (v3.9)

`style_core.js` (inséré par `patch9_style.py`) : styles « Nature » (par défaut), « Moderne » et « Épuré » des factures et soumissions, en plus du modèle d'origine (`docLayoutOrigine`). Le moteur PDF dessine maintenant des chemins, des rectangles arrondis et des cercles (emblème feuille). Le style se choisit dans Réglages (`reglages.styleDoc`), avec un aperçu.

## Envoi par Gmail avec le PDF joint (v3.11)

`envoi.html` (copiée telle quelle à la racine par `build.py`) : page d'envoi ouverte par l'application de l'ordinateur. Elle reçoit le message et le PDF par `postMessage` (`envoi-pret` → `envoi` → `envoi-fait`), montre le courriel et l'envoie par l'API Gmail (`users.messages.send`, téléversement `message/rfc822`, portée `gmail.send`) quand on clique « Envoyer ». La connexion Google passe par `index.html?auth=3&retour=envoi.html&mail=1` (`patch12_tel_gmail.py`), puisque `/compta/` est la seule adresse de retour autorisée. `patch12_gmail.py` branche le bouton « Envoyer par Gmail » de l'ordinateur et garde l'ancienne façon en dépannage. Il faut activer l'API Gmail une fois dans le projet Google Cloud. Test : `test_gmail.py` (faux Gmail dans `mock.py`).

## Signature en ligne des soumissions (v3.12)

`signer_core.js` (inséré par `patch13_signer.py`, aussi extrait pour le téléphone) : lien de signature protégé par HMAC-SHA256 (`reglages.signerCle`), bouton cliquable « Signer en ligne » dans la case du client du PDF (annotations `/Link` ajoutées au moteur PDF), lien dans le message. `signer.html` : page où le client signe avec le doigt. `signer.gs` : service Google Apps Script que l'entreprise installe dans son compte (Réglages › Signature en ligne). Il vérifie le lien, dépose une op `signature` (`appareil: "en ligne"`) et la photo dans `Comptabilite/telephone`, et envoie un courriel d'avis. Tests : `test_sha.js` (SHA-256/HMAC contre Node), `test_signer.py` (de bout en bout, avec `fake_gas.js` qui exécute `signer.gs` dans Node avec un faux Drive), `test_signer_tel.py`. `build_all.sh` reconstruit tout.
