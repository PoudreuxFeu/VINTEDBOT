

# 🛍️ CrowBot — Vinted Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**Surveille les nouvelles annonces Vinted en temps réel directement dans ton serveur Discord.**

</div>

---

## ✨ Fonctionnalités

- 🔍 **Surveillance en temps réel** — Nouvelles annonces détectées toutes les ~8 secondes
- 🏷️ **Filtre par marque** — Cherche uniquement Nike, Zara, Adidas...
- 💰 **Filtre par prix** — Définit un prix minimum et/ou maximum
- 📦 **50+ catégories** — Femmes, Hommes, Enfants, Tech, Maison...
- 💾 **Persistance** — Les surveillances survivent aux redémarrages
- 🔄 **Retry automatique** — Relance automatiquement en cas d'erreur réseau
- 🛡️ **Anti-ban** — Rotation de User-Agent + Rate limiting intelligent
- 📊 **Statistiques** — Suivi du nombre d'articles envoyés par surveillance
- 🎛️ **Multi-surveillance** — Jusqu'à 10 surveillances simultanées par serveur

---

## 📸 Aperçu
┌─────────────────────────────────────────────┐
│ 🛍️ Nike Air Max 90 — Taille 42 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ## 35 € │
│ │
│ 👤 Vendeur 💶 Prix 🏷️ Marque │
│ john_doe 35 € Nike │
│ │
│ 📏 Taille ✨ État ❤️ Favoris │
│ 42 Bon état 12 │
│ │
│ [🛍️ Voir l'article] [💳 Acheter] │
│ [📋 Copier les liens] │
└─────────────────────────────────────────────┘

text


---

## 🚀 Installation

### Prérequis

- Python **3.11** ou supérieur
- Un bot Discord avec les permissions nécessaires
- Token Discord

### 1. Cloner le projet

```bash
git clone https://github.com/ton-user/crowbot-vinted.git
cd crowbot-vinted
2. Installer les dépendances
Bash

pip install discord.py aiohttp python-dotenv Brotli
Ou via le fichier requirements :

Bash

pip install -r requirements.txt
3. Configurer le fichier .env
Crée un fichier .env à la racine du projet :

env

DISCORD_TOKEN=ton_token_discord_ici
💡 Où trouver ton token ?
Rendez-vous sur le Discord Developer Portal,
crée une application → Bot → Reset Token.

4. Inviter le bot sur ton serveur
Dans le Developer Portal :

OAuth2 → URL Generator
Scopes : bot + applications.commands
Permissions : Send Messages + Embed Links + View Channels
5. Lancer le bot
Bash

python vinted_bot.py
📁 Structure du projet
text

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

Constante	Défaut	Description
SCRAPE_INTERVAL	8	Secondes entre chaque cycle de scraping
REQUEST_DELAY	1.5	Délai minimum entre chaque requête Vinted
MAX_RETRIES	3	Tentatives avant abandon sur erreur réseau
COOKIE_TTL	300	Durée de vie du cookie en secondes
MAX_SEEN_IDS	300	Nombre d'IDs mémorisés par surveillance
MAX_WATCHERS_GUILD	10	Surveillances simultanées max par serveur
🎮 Commandes
Commande	Description	Permissions
/vinted	Démarrer une surveillance	Tout le monde
/vinted_stop	Arrêter une surveillance (menu)	Tout le monde
/vinted_stop_all	Arrêter toutes les surveillances	Administrateur
/vinted_list	Voir les surveillances actives	Tout le monde
/vinted_stats	Statistiques du scraper	Tout le monde
/vinted_categories	Voir toutes les catégories	Tout le monde
/vinted_test	Tester une catégorie (aperçu)	Tout le monde
/help	Aide et informations	Tout le monde
Détail des options /vinted
Option	Type	Requis	Description
categorie	Texte	✅	Catégorie Vinted (autocomplétion)
salon	Salon	✅	Salon Discord de destination
marque	Texte	❌	Filtrer par marque (ex: Nike)
prix_min	Nombre	❌	Prix minimum en €
prix_max	Nombre	❌	Prix maximum en €
📦 Catégories disponibles
<details> <summary><b>👗 Femmes</b></summary>
robes hauts manteaux vestes jeans pantalons
jupes pulls chaussures_femme sacs bijoux
lingerie sport_femme maillots

</details><details> <summary><b>👕 Hommes</b></summary>
t-shirts chemises sweats vestes_homme manteaux_homme
pantalons_homme jeans_homme shorts chaussures_homme
accessoires sport_homme

</details><details> <summary><b>👶 Enfants</b></summary>
bebe enfant_fille enfant_garcon jouets

</details><details> <summary><b>📱 Électronique</b></summary>
smartphones ordinateurs tablettes consoles
jeux_video casques photo tv

</details><details> <summary><b>🏠 Maison</b></summary>
decoration cuisine linge meubles jardin

</details><details> <summary><b>📚 Autres</b></summary>
livres musique films sport beaute
animaux voiture collection

</details>
🛡️ Sécurité & Anti-ban
Le bot intègre plusieurs mécanismes pour éviter les blocages :

text

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
📊 Fonctionnement interne
text

Discord (Slash Command)
        │
        ▼
   /vinted start
        │
        ▼
  WatcherStorage ──── vinted_watchers.json
        │
        ▼
  scrape_task (loop toutes les 8s)
        │
        ├──► VintedHTTPClient
        │         │
        │         ├──► Refresh cookie si expiré
        │         ├──► Rotation User-Agent
        │         ├──► GET /api/v2/catalog/items
        │         └──► Retry x3 si erreur
        │
        ├──► Filtre seen_ids (déjà vus)
        ├──► Filtre prix min/max
        │
        └──► Discord Channel
                  │
                  └──► Embed + Boutons (ArticleView)
🐛 Dépannage
<details> <summary><b>❌ "DISCORD_TOKEN manquant dans .env"</b></summary>
Assure-toi que :

Le fichier .env existe à la racine du projet
Il contient bien DISCORD_TOKEN=ton_token
Il n'y a pas d'espaces autour du =
env

# ✅ Correct
DISCORD_TOKEN=OTk4...abc

# ❌ Incorrect
DISCORD_TOKEN = OTk4...abc
</details><details> <summary><b>❌ Les commandes slash n'apparaissent pas</b></summary>
Les commandes peuvent mettre jusqu'à 1 heure à se synchroniser globalement.

Pour forcer la synchronisation sur un serveur spécifique, modifie temporairement :

Python

await bot.tree.sync(guild=discord.Object(id=TON_GUILD_ID))
</details><details> <summary><b>❌ "Permissions insuffisantes"</b></summary>
Le bot a besoin dans le salon cible :

✅ Voir le salon
✅ Envoyer des messages
✅ Intégrer des liens (Embed Links)
</details><details> <summary><b>⚠️ Aucun article ne s'affiche</b></summary>
Utilise /vinted_test pour vérifier que le scraping fonctionne
Vérifie les logs dans vinted_bot.log
Vinted peut bloquer temporairement — attends quelques minutes
Vérifie que la catégorie/marque existe bien sur Vinted
</details><details> <summary><b>⚠️ Le bot reçoit des 429 (Rate Limited)</b></summary>
Réduis le nombre de surveillances simultanées ou augmente SCRAPE_INTERVAL
dans la configuration :

Python

SCRAPE_INTERVAL = 15  # Passe de 8s à 15s
</details>
📝 Logs
Les logs sont enregistrés dans vinted_bot.log et affichés en console :

text

2024-01-15 14:23:01 [INFO] VintedBot: ✅ VintedBot prêt : CrowBot#1234
2024-01-15 14:23:01 [INFO] VintedBot:    Serveurs : 3
2024-01-15 14:23:01 [INFO] VintedBot:    Watchers : 5
2024-01-15 14:23:09 [INFO] VintedBot: [Scrape] Cycle: 3 article(s) envoyé(s) en 2.34s
2024-01-15 14:23:17 [WARNING] VintedBot: [HTTP] 429 Rate Limited — attente 2.0s
📋 requirements.txt
text

discord.py>=2.3.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
Brotli>=1.1.0
⚖️ Avertissement légal
Ce projet est développé à des fins éducatives uniquement.
L'utilisation d'un scraper peut être contraire aux
CGU de Vinted.
Utilise ce bot de manière responsable et à tes propres risques.
Les auteurs ne sont pas responsables d'une utilisation abusive.

📜 License
text

MIT License — Libre d'utilisation, modification et distribution.
<div align="center">
Fait avec ❤️ par CrowBot

⭐ Si ce projet t'a aidé, laisse une étoile ! ⭐

</div> 
