# Sources de l'application téléphone

- `ui.js` : interface et synchronisation (Google Drive v3 + connexion Google par redirection, file d'attente hors réseau, photos dans IndexedDB).
- `sw.js` : service worker (l'application s'ouvre sans réseau).
- `head.html`, `body.html` : gabarit. Les fonctions de calcul (`core.js`) sont extraites de `Comptabilite.html` (application de l'ordinateur) par `extract.py` selon `names.txt`.
- `build.py` : construit la page à la racine du dépôt. Il attend l'arborescence de travail de Claude (`phone/`, `pwa/`, `Comptabilite/Comptabilite.html`).
- `mock.py`, `test_pwa.py`, `test_integ_pwa.py` : tests avec un faux Google (hors réseau, retour du réseau, jeton expiré, refus, intégration sur l'ordinateur). `fixture.json` contient des données fictives.

Format des changements déposés dans `Comptabilite/telephone/` : voir `POUR-CLAUDE.md` dans le dossier Comptabilite.
