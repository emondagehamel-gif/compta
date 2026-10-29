# Sources de l'application téléphone

- `ui.js` : interface et synchronisation (Google Drive v3 + connexion Google par redirection, file d'attente hors réseau, photos dans IndexedDB).
- `sw.js` : service worker (l'application s'ouvre sans réseau).
- `head.html`, `body.html` : gabarit. Les fonctions de calcul (`core.js`) sont extraites de `Comptabilite.html` (application de l'ordinateur) par `extract.py` selon `names.txt`.
- `build.py` : construit la page à la racine du dépôt. Il attend l'arborescence de travail de Claude (`phone/`, `pwa/`, `Comptabilite/Comptabilite.html`).
- `mock.py`, `test_pwa.py`, `test_integ_pwa.py` : tests avec un faux Google (hors réseau, retour du réseau, jeton expiré, refus, intégration sur l'ordinateur). `fixture.json` contient des données fictives.

Format des changements déposés dans `Comptabilite/telephone/` : voir `POUR-CLAUDE.md` dans le dossier Comptabilite.

## Version complète (`complet.html`)

`complet.html` est l'application de l'ordinateur (`Comptabilite.html`) en « mode nuage » : elle lit les livres dans Google Drive et envoie chaque modification comme changement `patch` (et `fichier`, `deplacer`, `fichier-suppr` pour les fichiers). Le code du mode nuage est dans `cloud.js` (inséré dans `Comptabilite.html` par `patch2_cloud.py`). La connexion Google passe par `index.html?auth=1&retour=complet.html`, la seule adresse autorisée dans Google Cloud.
