🛍️  — Vinted Scraper

<div align="center">

Surveille les nouvelles annonces Vinted en temps réel directement dans ton serveur Discord.

</div>

✨ Fonctionnalités

🔍 Surveillance en temps réel — Nouvelles annonces détectées toutes les ~8 secondes.

🏷️ Filtre par marque — Cherche uniquement Nike, Zara, Adidas...

💰 Filtre par prix — Définit un prix minimum et/ou maximum.

📦 50+ catégories — Femmes, Hommes, Enfants, Tech, Maison...

💾 Persistance — Les surveillances survivent aux redémarrages (JSON Storage).

🔄 Retry automatique — Relance automatiquement en cas d'erreur réseau.

🛡️ Anti-ban — Rotation de User-Agent + Rate limiting intelligent.

📊 Statistiques — Suivi du nombre d'articles envoyés par surveillance.

🎛️ Multi-surveillance — Jusqu'à 10 surveillances simultanées par serveur.

📸 Aperçu

┌─────────────────────────────────────────────┐
│ 🛍️ Nike Air Max 90 — Taille 42              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ## 35 €                                     │
│                                             │
│ 👤 Vendeur      💶 Prix         🏷️ Marque    │
│ john_doe       35 €            Nike         │
│                                             │
│ 📏 Taille       ✨ État         ❤️ Favoris   │
│ 42             Bon état        12           │
│                                             │
│ [🛍️ Voir l'article] [💳 Acheter]             │
│ [📋 Copier les liens]                        │
└─────────────────────────────────────────────┘


🚀 Installation

Prérequis

Python 3.11 ou supérieur.

Un bot Discord avec les permissions nécessaires.

Un Token Discord.

1. Cloner le projet

git clone [https://github.com/ton-user/crowbot-vinted.git](https://github.com/ton-user/crowbot-vinted.git)
cd crowbot-vinted


2. Installer les dépendances

pip install discord.py aiohttp python-dotenv Brotli


Ou via le fichier requirements :

pip install -r requirements.txt


3. Configurer le fichier .env

Crée un fichier .env à la racine du projet :

DISCORD_TOKEN=ton_token_discord_ici


💡 Où trouver ton token ? Rendez-vous sur le Discord Developer Portal, crée une application → Bot → Reset Token.

4. Lancer le bot

python vinted_bot.py


📁 Structure du projet

crowbot-vinted/
│
├── vinted_bot.py          # Bot principal
├── vinted_watchers.json   # Données persistantes (auto-généré)
├── vinted_bot.log         # Logs (auto-généré)
├── .env                   # Token Discord (à créer)
├── requirements.txt       # Dépendances
└── README.md              # Ce fichier


⚙️ Configuration

Les constantes configurables se trouvent en haut de vinted_bot.py :

Constante

Défaut

Description

SCRAPE_INTERVAL

8

Secondes entre chaque cycle de scraping

REQUEST_DELAY

1.5

Délai minimum entre chaque requête Vinted

MAX_RETRIES

3

Tentatives avant abandon sur erreur réseau

COOKIE_TTL

300

Durée de vie du cookie en secondes

MAX_SEEN_IDS

300

Nombre d'IDs mémorisés par surveillance

MAX_WATCHERS_GUILD

10

Surveillances simultanées max par serveur

🎮 Commandes

Commande

Description

Permissions

/vinted

Démarrer une surveillance

Tout le monde

/vinted_stop

Arrêter une surveillance (menu)

Tout le monde

/vinted_stop_all

Arrêter toutes les surveillances

Administrateur

/vinted_list

Voir les surveillances actives

Tout le monde

/vinted_stats

Statistiques du scraper

Tout le monde

/vinted_categories

Voir toutes les catégories

Tout le monde

/vinted_test

Tester une catégorie (aperçu)

Tout le monde

/help

Aide et informations

Tout le monde

Détail des options /vinted

categorie (Texte) : ✅ Catégorie Vinted (autocomplétion)

salon (Salon) : ✅ Salon Discord de destination

marque (Texte) : ❌ Filtrer par marque (ex: Nike)

prix_min (Nombre) : ❌ Prix minimum en €

prix_max (Nombre) : ❌ Prix maximum en €

🛡️ Sécurité & Anti-ban

Le bot intègre plusieurs mécanismes pour éviter les blocages :

┌─────────────────────────────────────────────────────┐
│               Mécanismes Anti-ban                    │
├─────────────────┬───────────────────────────────────┤
│ User-Agent Pool │ 6 navigateurs différents en        │
│                 │ rotation aléatoire                 │
├─────────────────┼───────────────────────────────────┤
│ Rate Limiting   │ 1.5s minimum entre chaque requête │
├─────────────────┼───────────────────────────────────┤
│ Backoff expo.   │ Délai croissant sur erreurs        │
│                 │ répétées (max 30s)                 │
├─────────────────┼───────────────────────────────────┤
│ Cookie TTL      │ Renouvellement auto toutes les 5mn │
├─────────────────┼───────────────────────────────────┤
│ 429 Handler     │ Pause automatique si rate limited  │
└─────────────────┴───────────────────────────────────┘


🐛 Dépannage

<details>
<summary><b>❌ "DISCORD_TOKEN manquant dans .env"</b></summary>
Assure-toi que le fichier .env existe à la racine, contient bien la variable sans espaces autour du =.
</details>

<details>
<summary><b>❌ Les commandes slash n'apparaissent pas</b></summary>
La synchronisation peut prendre jusqu'à 1 heure. Redémarrez votre client Discord.
</details>

<details>
<summary><b>⚠️ Aucun article ne s'affiche</b></summary>
Utilisez /vinted_test. Si rien ne sort, Vinted a peut-être bloqué votre IP temporairement (Erreur 429).
</details>

⚖️ Avertissement légal

Ce projet est développé à des fins éducatives uniquement. L'utilisation d'un scraper peut être contraire aux CGU de Vinted. Utilisez ce bot de manière responsable.

<div align="center">

Fait avec ❤️ par PoudreuxFeu
⭐ Si ce projet t'a aidé, laisse une étoile ! ⭐

</div>
