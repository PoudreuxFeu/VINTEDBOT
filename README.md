👗 CrowBot — Vinted Scraper

<p align="center">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Version-2.0.0-purple%3Fstyle%3Dfor-the-badge" alt="Version">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Python-3.10%252B-blue%3Fstyle%3Dfor-the-badge" alt="Python">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Discord.py-2.3%252B-orange%3Fstyle%3Dfor-the-badge" alt="Discord.py">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Status-Stable-success%3Fstyle%3Dfor-the-badge" alt="Status">
</p>

🚀 Présentation

CrowBot Vinted est un outil de monitoring ultra-rapide conçu pour détecter les nouvelles annonces Vinted dès leur mise en ligne. Idéal pour le resell ou pour dénicher des pépites avant tout le monde grâce à une réactivité inégalée.

✨ Fonctionnalités clés

⚡ Ultra Rapide Cycle de scan optimisé toutes les 3 secondes pour ne rater aucune annonce.

🛍️ Achat Direct Bouton intégré pour accéder directement à la page de paiement Vinted.

🏷️ Filtre par Marque Ciblez précisément une marque (Nike, Adidas, Stone Island...) au sein d'une catégorie.

📋 Multi-Surveillance Gérez plusieurs salons et plusieurs filtres simultanément sur un même serveur.

💾 Persistance des données Vos surveillances sont sauvegardées et redémarrent automatiquement avec le bot.

🔍 Autocomplete intelligent Système de recherche de catégories fluide via les commandes Slash de Discord.

🛡️ Gestion simplifiée Commandes intuitives pour lister, tester et arrêter les surveillances sans spam.

🛠️ Installation

1️⃣ Prérequis

Python 3.10 ou version supérieure.

Un compte Discord Developer pour générer votre Token.

2️⃣ Installation des dépendances

Ouvrez votre terminal et exécutez la commande suivante :

pip install discord.py aiohttp python-dotenv Brotli


3️⃣ Configuration

Créez un fichier .env à la racine de votre projet et ajoutez votre token :

DISCORD_TOKEN=votre_token_ici


🚀 Utilisation

Lancez le bot avec la commande suivante :

python vinted_bot.py


📋 Commandes disponibles

Commande

Description

`` /vinted

Lance une nouvelle surveillance (Catégorie + Salon + Marque).

`` /vinted_list

Liste toutes les surveillances actives sur le serveur.

`` /vinted_categories

Affiche la liste complète des catégories supportées.

[Image of /help] /help

Affiche le menu d'aide détaillé.

💡 Comment ça marche ?

Système de Catégories : Le bot utilise les catalog_id officiels de Vinted pour une précision chirurgicale.

Gestion des Sessions : Récupération automatique des cookies Vinted pour contourner les blocages (rotation de session).

Anti-Doublon : Stockage intelligent dans une liste seen_ids pour éviter les notifications répétitives.

Embeds Premium : Notifications riches incluant prix, état, taille, marque, favoris et image haute résolution.

⚠️ Notes importantes

🛑 Rate Limiting : L'intervalle est réglé sur 3 secondes. Un nombre excessif de surveillances peut entraîner un blocage temporaire de votre IP par Vinted (Erreur 429).

👤 Usage : Ce bot est destiné à un usage personnel ou communautaire. Respectez les conditions d'utilisation de la plateforme.

<p align="center">
<b>Développé pour la performance par l'équipe CrowBot.</b>
</p>
