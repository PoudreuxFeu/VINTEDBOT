Vinted est un outil de monitoring ultra-rapide conçu pour détecter les nouvelles annonces Vinted dès leur mise en ligne. Idéal pour le "resell" ou pour dénicher des pépites avant tout le monde.

✨ Fonctionnalités clés

⚡ Ultra Rapide : Cycle de scan toutes les 3 secondes pour ne rater aucune annonce.

🛍️ Achat Direct : Bouton intégré pour accéder directement à la page de paiement.

🏷️ Filtre par Marque : Ciblez précisément une marque (Nike, Adidas, Stone Island...) dans une catégorie.

📋 Multi-Surveillance : Gérez plusieurs salons et plusieurs filtres simultanément.

💾 Persistance : Vos surveillances sont sauvegardées et redémarrent automatiquement avec le bot.

🔍 Autocomplete : Système de recherche de catégories intelligent via les commandes Slash.

🛡️ Gestion Propre : Commandes pour lister, tester et arrêter les surveillances sans spam.

🛠️ Installation

1. Prérequis

Python 3.10+

Un compte Discord Developer pour créer votre bot.

2. Installation des dépendances

pip install discord.py aiohttp python-dotenv Brotli


3. Configuration

Créez un fichier .env à la racine du projet :

DISCORD_TOKEN=votre_token_ici


🚀 Utilisation

Lancez le bot avec :

python vinted_bot.py


Commandes disponibles

Commande

Description

/vinted

Lance une nouvelle surveillance (Catégorie + Salon + Marque optionnelle).

/vinted_stop

Affiche un menu déroulant pour choisir quelle surveillance arrêter.

/vinted_list

Liste toutes les surveillances actives sur le serveur.

/vinted_test

Teste instantanément une recherche pour vérifier les résultats.

/vinted_categories

Affiche la liste complète des catégories supportées.

/vinted_stop_all

Arrête toutes les surveillances du serveur (Admin uniquement).

/help

Affiche le menu d'aide détaillé.

💡 Comment ça marche ?

Catégories : Le bot utilise des catalog_id officiels de Vinted pour une précision maximale.

Session & Cookies : Il gère automatiquement la récupération des cookies Vinted pour éviter les blocages (système de rotation de session).

Anti-Doublon : Chaque article est stocké temporairement dans une liste seen_ids pour ne jamais vous notifier deux fois pour le même objet.

Embeds Dynamiques : Les notifications incluent le prix, l'état, la taille, la marque, le nombre de favoris et la photo de l'article.

⚠️ Notes importantes

Rate Limiting : L'intervalle est réglé sur 3 secondes. Si vous lancez trop de surveillances simultanées, Vinted peut temporairement bloquer votre IP (429).

Usage : Ce bot est destiné à un usage personnel ou communautaire.

Développé pour la performance. Vinted Scraper.
