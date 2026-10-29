
## Version 3.11 : envoi par Gmail avec le PDF joint

- À l'ordinateur, « Envoyer par Gmail » envoie maintenant le courriel avec le PDF déjà joint. Il n'y a plus de PDF à télécharger puis à joindre.
- Comment ça marche :
  - l'application ouvre la page d'envoi `https://emondagehamel-gif.github.io/compta/envoi.html` dans une petite fenêtre ;
  - elle lui passe le message, le sujet, le destinataire et le PDF par `postMessage` (messages `envoi-pret`, `envoi`, `envoi-fait`) ;
  - la page affiche le courriel (De, À, Objet, Message, pièce jointe). Rien ne part avant que l'utilisateur clique « Envoyer » ;
  - l'envoi passe par l'API Gmail (`users.messages.send`, portée `gmail.send`) avec le compte Google connecté. Une copie reste dans « Messages envoyés » ;
  - quand c'est envoyé, la page prévient l'application, qui met `envoyeLe` (devis) ou `envoyeeLe` (facture) à la date du jour.
- Connexion Google : elle passe par la page principale (`index.html?auth=3&retour=envoi.html&mail=1`), seule adresse de retour autorisée. Google demande la permission d'envoyer des courriels la première fois seulement.
- À faire une seule fois dans Google Cloud (projet `comptabilite-513021`) : activer l'API Gmail. Sans ça, la page affiche « L'envoi par Gmail n'est pas encore activé » avec le lien.
- Si la fenêtre ne répond pas, ou en dépannage, le bouton « Autre façon : ouvrir Gmail et télécharger le PDF » garde l'ancienne méthode (v3.9.1).
- Le courriel en attente est gardé dans le navigateur (IndexedDB `compta-envoi`) pendant la connexion à Google, puis effacé après l'envoi ou l'annulation.

## Version 3.12 : signature en ligne des soumissions

- Le client signe la soumission sur son cellulaire, sans rien installer. Il reçoit un lien « Signer en ligne » :
  - dans le message du courriel (ordinateur et téléphone) ;
  - sur un bouton vert dans la case « Client » du PDF (lien cliquable).
- La page de signature est `https://emondagehamel-gif.github.io/compta/signer.html`. Elle montre le numéro, le client, le total et la date de validité. Le client écrit son nom, signe avec le doigt, coche « J'accepte… » et clique « Signer et accepter ».
- La signature passe par un service Google Apps Script dans le compte emondagehamel@gmail.com (code : `signer.gs`). Ce service :
  - vérifie le lien ;
  - dépose dans `telephone/` une op `signature` (avec `data.appareil: "en ligne"`) et la photo de la signature ;
  - envoie un courriel d'avis à `reglages.courriel`.
- L'application applique l'op comme une signature du téléphone. La signature est rangée dans `signatures/`, la soumission passe à `accepte`, et le PDF porte « Signé électroniquement en ligne à … ». Une signature en ligne n'écrase jamais une signature existante. Si la soumission n'est pas encore arrivée du téléphone, l'op attend, jusqu'à 3 jours.
- Réglages :
  - `reglages.signerUrl` : l'adresse `…/macros/s/ID/exec` du service ;
  - `reglages.signerCle` : la clé secrète (hex) qui signe les liens (HMAC-SHA256 de `v1|id|numero|client|totalCents|echeance|nom`, 32 premiers caractères hex). Ne pas la changer : les liens déjà envoyés ne marcheraient plus.
- Mise en place : Réglages › Factures et devis › « Signature en ligne des soumissions » › Activer. On y trouve le code à copier, les étapes dans script.google.com et la vérification du service.
- Pas de lien pour une soumission déjà signée, facturée ou refusée. Le service refuse :
  - un lien modifié ;
  - une soumission expirée ;
  - une soumission déjà signée.
