
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
