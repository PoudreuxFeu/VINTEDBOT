👗 CrowBot — Vinted Scraper

L'outil ultime de surveillance Vinted — Rapide, précis et automatisé

Surveillance Temps Réel • Achat Direct • Filtres Avancés • Multi-Salons • Persistance

📖 Table des matières

✨ Présentation

🎯 Fonctionnalités

⚙️ Installation

🔑 Configuration

🚀 Lancement

📜 Commandes

💡 Conseils d'utilisation

❓ FAQ

✨ Présentation

CrowBot Vinted Scraper est une extension spécialisée de l'écosystème CrowBot. Ce module est conçu pour les utilisateurs exigeants (resellers, collectionneurs) qui souhaitent être alertés d'une nouvelle annonce avant même qu'elle n'apparaisse dans les recherches classiques sur l'application.

⚡ Vitesse de pointe : Cycle de scan toutes les 3 secondes.

💳 Snipe facilité : Boutons d'achat direct pour griller la priorité aux autres acheteurs.

💾 Zéro perte : Sauvegarde automatique de vos surveillances (résiste aux redémarrages).

🏷️ Précision chirurgicale : Filtres par catégories officielles et par marques spécifiques.

🎯 Fonctionnalités

Catégorie

Détails

🔍 Scanning

Analyse asynchrone des flux Vinted, gestion des en-têtes Mozilla récents.

🏷️ Filtrage

Support de +50 catégories (Hommes, Femmes, Enfants, Électronique, Maison).

💳 Achat Rapide

Génération de liens de paiement direct (/transaction/buy/new).

🖼️ Notifications

Embeds riches avec prix en couleur selon le montant, photos HD, et compteur de favoris.

🛠️ Gestion

Menu déroulant interactif pour stopper les recherches sans taper de texte.

🔄 Session

Rotation automatique des cookies pour éviter les bannissements d'IP.

⚙️ Installation

Prérequis

Python 3.10+ : Téléchargeable sur python.org.

Discord Token : À récupérer sur le Portail Développeur.

Étape 1 — Préparation

# Clonez ou créez un dossier pour le projet
mkdir vinted-scraper && cd vinted-scraper


Étape 2 — Installer les dépendances

pip install discord.py aiohttp python-dotenv Brotli


🔑 Configuration

Créez un fichier .env à la racine :

DISCORD_TOKEN=votre_token_secret_ici


🚀 Lancement

Dans votre terminal :

python vinted_bot.py


Une fois en ligne :

Utilisez /vinted pour lancer votre première recherche.

Le bot créera un embed de confirmation et commencera le scan immédiatement.

📜 Commandes

🛰️ Surveillance

Commande

Description

Permission

/vinted

Démarrer un scan (Catégorie, Salon, Marque optionnelle)

Membre

/vinted_stop

Arrêter un scan via un menu déroulant

Membre

/vinted_list

Voir tous les scans actifs sur le serveur

Membre

/vinted_test

Faire un test rapide (3 articles) sans démarrer de scan

Membre

🛠️ Administration & Aide

Commande

Description

Permission

/vinted_stop_all

Arrête absolument tous les scans du serveur

Administrateur

/vinted_categories

Liste toutes les catégories disponibles

Membre

/help

Affiche l'interface d'aide CrowBot

Membre

💡 Conseils d'utilisation

Évitez le spam : Ne lancez pas plus de 5 surveillances simultanées sur la même IP pour éviter le "Rate Limit".

Marques : Soyez précis. Tapez Nike au lieu de nk.

Salons dédiés : Créez un salon par catégorie (ex: #vinted-nike, #vinted-robes) pour une meilleure organisation.

❓ FAQ

Le bot ne poste plus rien ? Vérifiez vos logs. Vinted a peut-être bloqué votre IP temporairement (Erreur 429). Attendez 5 minutes.

Comment ajouter une catégorie ? Les catégories sont codées en dur dans le dictionnaire CATEGORIES. Vous pouvez en ajouter avec leurs IDs Vinted respectifs.

Les boutons ne fonctionnent pas ? Assurez-vous que le bot a la permission "Envoyer des messages" et "Intégrer des liens".

<p align="center">
<b>Développé pour la performance par l'équipe CrowBot.</b>




<i>Vitesse • Précision • Succès</i>
</p>
