# 🛍️  — Vinted Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**Surveille les nouvelles annonces Vinted en temps réel directement dans ton serveur Discord.**

</div>

---

## ✨ Fonctionnalités

- 🔍 **Surveillance en temps réel** — nouvelles annonces détectées automatiquement
- 🏷️ **Filtre par marque** — Nike, Zara, Adidas...
- 💰 **Filtre par prix** — minimum / maximum
- 📦 **50+ catégories** — mode, tech, maison, jeux...
- 💾 **Persistance** — les surveillances survivent aux redémarrages
- 🔄 **Retry automatique** — relance après erreur réseau
- 🛡️ **Anti-ban intelligent** — rotation User-Agent + rate limiting
- 📊 **Statistiques** — nombre d’articles envoyés
- 🎛️ **Multi-surveillance** — jusqu’à 10 surveillances par serveur

---

## 📸 Aperçu

```text
┌─────────────────────────────────────────────┐
│ 🛍️ Nike Air Max 90 — Taille 42            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 💶 35 €                                   │
│ 👤 john_doe   🏷️ Nike   ❤️ 12 favoris     │
│ 📏 Taille 42   ✨ Bon état                │
│ [🛍️ Voir l'article] [💳 Acheter]         │
└─────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prérequis

- Python **3.11** ou supérieur
- Un bot Discord
- Token Discord valide

### 1. Cloner le projet

```bash
git clone https://github.com/ton-user/crowbot-vinted.git
cd crowbot-vinted
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer `.env`

```env
DISCORD_TOKEN=ton_token_discord_ici
```

### 4. Lancer le bot

```bash
python vinted_bot.py
```

---

## 📁 Structure du projet

```text
crowbot-vinted/
├── vinted_bot.py
├── vinted_watchers.json
├── vinted_bot.log
├── .env
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration

| Constante | Défaut | Description |
|---|---:|---|
| SCRAPE_INTERVAL | 8 | Intervalle entre cycles |
| REQUEST_DELAY | 1.5 | Délai minimum entre requêtes |
| MAX_RETRIES | 3 | Tentatives réseau |
| COOKIE_TTL | 300 | Durée cookie |
| MAX_SEEN_IDS | 300 | IDs mémorisés |
| MAX_WATCHERS_GUILD | 10 | Surveillances max |

---

## 🎮 Commandes

| Commande | Description |
|---|---|
| `/vinted` | Démarrer une surveillance |
| `/vinted_stop` | Arrêter une surveillance |
| `/vinted_stop_all` | Tout arrêter |
| `/vinted_list` | Voir les surveillances |
| `/vinted_stats` | Statistiques |
| `/vinted_categories` | Voir les catégories |
| `/vinted_test` | Tester une catégorie |
| `/help` | Aide |

---

## 🛡️ Sécurité & Anti-ban

- Rotation automatique de User-Agent
- Limitation intelligente du rythme des requêtes
- Backoff exponentiel en cas d’erreur
- Gestion automatique des erreurs `429`
- Renouvellement périodique des cookies

---

## 🐛 Dépannage

### Les commandes slash n'apparaissent pas
Les commandes globales peuvent prendre jusqu’à 1 heure à apparaître.

### Aucun article détecté
- Vérifie les logs
- Teste avec `/vinted_test`
- Vérifie la catégorie / marque

### Erreurs 429
Augmente `SCRAPE_INTERVAL` pour ralentir les requêtes.

---

## 📝 Logs

```text
2026-04-17 14:23:01 [INFO] Bot prêt : Vinted#1234
2026-04-17 14:23:09 [INFO] 3 article(s) envoyé(s)
2026-04-17 14:23:17 [WARNING] 429 Rate Limited
```

---

## ⚖️ Avertissement légal

Projet fourni à des fins éducatives.  
Vérifie les CGU de Vinted avant utilisation.

---

## 📜 License

MIT License — libre d’utilisation, modification et distribution.

<div align="center">

Fait avec ❤️ par Poudreux

⭐ Si ce projet t'a aidé, laisse une étoile ! ⭐

</div>
