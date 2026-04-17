"""
╔══════════════════════════════════════════════════════════════════╗
║                    CROWBOT — VINTED SCRAPER                      ║
║         Surveillance d'articles Vinted en temps réel             ║
╚══════════════════════════════════════════════════════════════════╝

Installation:
    pip install discord.py aiohttp python-dotenv Brotli

Fichier .env:
    DISCORD_TOKEN=ton_token_ici

Lancement:
    python vinted_bot.py
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN     = os.getenv("DISCORD_TOKEN")
DATA_FILE = "vinted_watchers.json"

VINTED_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Referer":         "https://www.vinted.fr/",
    "Origin":          "https://www.vinted.fr",
    "DNT":             "1",
    "Connection":      "keep-alive",
    "Sec-Fetch-Dest":  "empty",
    "Sec-Fetch-Mode":  "cors",
    "Sec-Fetch-Site":  "same-origin",
}

VINTED_BASE = "https://www.vinted.fr"

CATEGORIES = {
    "robes":             1904,
    "hauts":             1903,
    "manteaux":          1909,
    "vestes":            1232,
    "jeans":             1905,
    "pantalons":         1906,
    "jupes":             1907,
    "pulls":             1908,
    "chaussures_femme":  16,
    "sacs":              54,
    "bijoux":            231,
    "lingerie":          42,
    "sport_femme":       213,
    "maillots":          209,
    "t-shirts":          370,
    "chemises":          371,
    "sweats":            372,
    "vestes_homme":      373,
    "manteaux_homme":    374,
    "pantalons_homme":   375,
    "jeans_homme":       376,
    "shorts":            377,
    "chaussures_homme":  24,
    "accessoires":       378,
    "sport_homme":       379,
    "bebe":              280,
    "enfant_fille":      281,
    "enfant_garcon":     282,
    "jouets":            220,
    "smartphones":       2,
    "ordinateurs":       594,
    "tablettes":         595,
    "consoles":          596,
    "jeux_video":        597,
    "casques":           598,
    "photo":             599,
    "tv":                600,
    "decoration":        8,
    "cuisine":           9,
    "linge":             10,
    "meubles":           11,
    "jardin":            12,
    "livres":            5,
    "musique":           6,
    "films":             7,
    "sport":             15,
    "beaute":            218,
    "animaux":           302,
    "voiture":           17,
    "collection":        3,
}

# ─────────────────────────────────────────────
#  HELPERS PRIX
# ─────────────────────────────────────────────

def parse_price(raw_price) -> tuple[float, str]:
    currency_symbols = {"EUR": "€", "GBP": "£", "USD": "$", "PLN": "zł", "CZK": "Kč"}
    if isinstance(raw_price, dict):
        amount   = raw_price.get("amount", 0)
        currency = raw_price.get("currency_code", "EUR")
        try:
            return float(str(amount).replace(",", ".")), currency_symbols.get(currency, currency)
        except Exception:
            return 0.0, "€"
    try:
        return float(str(raw_price).replace(",", ".")), "€"
    except Exception:
        return 0.0, "€"

def format_price(raw_price) -> str:
    value, symbol = parse_price(raw_price)
    if value == int(value):
        return f"{int(value)} {symbol}"
    return f"{value:.2f} {symbol}"

# ─────────────────────────────────────────────
#  STOCKAGE
# ─────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"watchers": {}, "stopped": []}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "watchers": watchers,
                "stopped":  list(stopped_keys)
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Save] Erreur: {e}")

_data = load_data()

# ── watchers actifs ──────────────────────────
# clé → dict watcher
watchers: dict = _data.get("watchers", {})

# ── clés à ignorer dans le prochain cycle ───
# Quand on stop un watcher, on l'ajoute ici
# Le cycle scrape vérifie cette liste AVANT d'envoyer
stopped_keys: set = set(_data.get("stopped", []))

# ─────────────────────────────────────────────
#  BOT
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─────────────────────────────────────────────
#  AUTOCOMPLETE
# ─────────────────────────────────────────────

async def categorie_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    current_lower = current.lower()
    results = []
    for cat in CATEGORIES.keys():
        if current_lower in cat.lower():
            results.append(app_commands.Choice(name=cat, value=cat))
        if len(results) >= 25:
            break
    return results

# ─────────────────────────────────────────────
#  SESSION PERSISTANTE
# ─────────────────────────────────────────────

_session: aiohttp.ClientSession | None = None
_vinted_cookie: str   = ""
_cookie_ts: float     = 0.0
COOKIE_TTL            = 300

async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        _session  = aiohttp.ClientSession(connector=connector)
    return _session

async def get_vinted_cookie(session: aiohttp.ClientSession) -> str:
    global _vinted_cookie, _cookie_ts
    import time
    if _vinted_cookie and (time.time() - _cookie_ts) < COOKIE_TTL:
        return _vinted_cookie
    try:
        async with session.get(
            VINTED_BASE,
            headers=VINTED_HEADERS,
            timeout=aiohttp.ClientTimeout(total=10),
            allow_redirects=True
        ) as resp:
            cookies    = session.cookie_jar.filter_cookies(VINTED_BASE)
            cookie_str = "; ".join(f"{k}={v.value}" for k, v in cookies.items())
            _vinted_cookie = cookie_str
            _cookie_ts     = time.time()
            return cookie_str
    except Exception as ex:
        print(f"[Cookie] Erreur: {ex}")
        return _vinted_cookie

# ─────────────────────────────────────────────
#  FONCTIONS VINTED
# ─────────────────────────────────────────────

async def get_brand_id(
    session: aiohttp.ClientSession,
    brand_name: str,
    cookie_str: str
) -> str | None:
    url     = f"{VINTED_BASE}/api/v2/brands/by_name"
    params  = {"brand_name": brand_name}
    headers = {**VINTED_HEADERS, "Cookie": cookie_str}
    try:
        async with session.get(
            url, headers=headers, params=params,
            timeout=aiohttp.ClientTimeout(total=8)
        ) as resp:
            if resp.status == 200:
                data  = await resp.json(content_type=None)
                brand = data.get("brand")
                if brand:
                    return str(brand.get("id", ""))
    except Exception:
        pass
    return None


async def fetch_vinted_items(
    session: aiohttp.ClientSession,
    catalog_id: int,
    marque: str | None = None,
    per_page: int = 30
) -> list[dict]:
    cookie_str = await get_vinted_cookie(session)
    params = {
        "per_page":    str(per_page),
        "catalog_ids": str(catalog_id),
        "order":       "newest_first",
        "page":        "1",
    }
    if marque:
        brand_id = await get_brand_id(session, marque, cookie_str)
        if brand_id:
            params["brand_ids"] = brand_id
        else:
            params["search_text"] = marque

    headers = {**VINTED_HEADERS, "Cookie": cookie_str}
    url     = f"{VINTED_BASE}/api/v2/catalog/items"

    try:
        async with session.get(
            url, headers=headers, params=params,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 401:
                global _cookie_ts
                _cookie_ts = 0
                return []
            if resp.status != 200:
                print(f"[Vinted] Status: {resp.status}")
                return []
            data = await resp.json(content_type=None)
            return data.get("items", [])
    except asyncio.TimeoutError:
        print("[Vinted] Timeout")
        return []
    except Exception as ex:
        print(f"[Vinted] Erreur: {ex}")
        return []

# ─────────────────────────────────────────────
#  VIEW ARTICLE
# ─────────────────────────────────────────────

class ArticleView(discord.ui.View):
    def __init__(self, item_url: str, item_id: int, price_str: str):
        super().__init__(timeout=None)
        self.item_url  = item_url
        self.item_id   = item_id
        self.price_str = price_str

        if item_url:
            self.add_item(discord.ui.Button(
                label="🛍️ Voir sur Vinted",
                url=item_url,
                style=discord.ButtonStyle.link,
            ))

        checkout_url = f"{VINTED_BASE}/transaction/buy/new?item_id={item_id}"
        self.add_item(discord.ui.Button(
            label="💳 Acheter directement",
            url=checkout_url,
            style=discord.ButtonStyle.link,
        ))

    @discord.ui.button(
        label="📋 Copier le lien",
        style=discord.ButtonStyle.secondary,
        emoji="📋",
        custom_id="copy_link"
    )
    async def copy_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔗 **Article :** {self.item_url}\n"
            f"💳 **Achat direct :** {VINTED_BASE}/transaction/buy/new?item_id={self.item_id}",
            ephemeral=True
        )


def build_item_embed(item: dict, categorie: str, marque: str | None) -> discord.Embed:
    title = item.get("title", "Article sans titre")
    url   = item.get("url", "")
    if url and not url.startswith("http"):
        url = VINTED_BASE + url

    raw_price        = item.get("price")
    price_str        = format_price(raw_price)
    price_val, _     = parse_price(raw_price)

    photos    = item.get("photos", [])
    photo_url = None
    if photos:
        photo     = photos[0]
        photo_url = (
            photo.get("full_size_url") or
            photo.get("url") or
            photo.get("thumb_url")
        )

    user     = item.get("user", {})
    username = user.get("login", "Inconnu")
    user_url = f"{VINTED_BASE}/member/{user.get('id', '')}"

    size_title   = item.get("size_title", "")
    status_title = item.get("status", "")
    brand_title  = item.get("brand_title", "")
    fav_count    = item.get("favourite_count", 0)

    if price_val <= 5:     color = discord.Color.green()
    elif price_val <= 15:  color = discord.Color.gold()
    elif price_val <= 50:  color = discord.Color.orange()
    else:                  color = discord.Color.red()

    e = discord.Embed(
        title=f"🛍️ {title}",
        url=url,
        color=color,
        description=f"## {price_str}"
    )
    if photo_url:
        e.set_image(url=photo_url)

    e.add_field(name="👤 Vendeur",     value=f"[{username}]({user_url})", inline=True)
    e.add_field(name="💶 Prix",        value=f"**{price_str}**",          inline=True)
    if brand_title:
        e.add_field(name="🏷️ Marque",  value=brand_title,    inline=True)
    if size_title:
        e.add_field(name="📏 Taille",  value=size_title,      inline=True)
    if status_title:
        e.add_field(name="✨ État",    value=status_title,    inline=True)
    if fav_count:
        e.add_field(name="❤️ Favoris", value=str(fav_count),  inline=True)

    tags = f"`{categorie}`"
    if marque:
        tags += f" • `{marque}`"

    e.set_footer(text=f"Vinted • {tags} • {datetime.datetime.now().strftime('%H:%M:%S')}")
    e.timestamp = datetime.datetime.utcnow()
    return e

# ─────────────────────────────────────────────
#  HELPER — Supprimer proprement un watcher
# ─────────────────────────────────────────────

def remove_watcher(key: str):
    """
    Supprime un watcher de façon sûre.
    1. L'ajoute dans stopped_keys → le cycle en cours l'ignorera immédiatement
    2. Le retire de watchers → les cycles suivants ne le verront plus
    3. Sauvegarde
    """
    stopped_keys.add(key)          # ← stoppe immédiatement le cycle en cours
    watchers.pop(key, None)        # ← retire pour les cycles suivants
    save_data()
    print(f"[Stop] Watcher '{key}' arrêté et supprimé.")

# ─────────────────────────────────────────────
#  TÂCHE DE SCRAPING
# ─────────────────────────────────────────────

@tasks.loop(seconds=3)
async def scrape_task():
    if not watchers:
        return

    session = await get_session()

    # On prend un snapshot des clés actives AU DÉBUT du cycle
    # pour éviter les modifications du dict pendant l'itération
    active_keys = list(watchers.keys())

    for key in active_keys:

        # ── VÉRIFICATION IMMÉDIATE ──
        # Si le watcher a été stoppé PENDANT ce cycle, on skip
        if key in stopped_keys or key not in watchers:
            stopped_keys.discard(key)   # nettoie la liste des stoppés
            continue

        watcher = watchers[key]

        guild = bot.get_guild(watcher["guild_id"])
        if not guild:
            continue

        channel = guild.get_channel(watcher["channel_id"])
        if not channel:
            continue

        catalog_id = watcher["catalog_id"]
        marque     = watcher.get("marque")
        seen_ids   = set(watcher.get("seen_ids", []))

        items = await fetch_vinted_items(session, catalog_id, marque, per_page=30)

        # ── VÉRIFICATION APRÈS FETCH ──
        # Le watcher a peut-être été stoppé pendant le fetch (peut prendre 1-2s)
        if key in stopped_keys or key not in watchers:
            stopped_keys.discard(key)
            continue

        if not items:
            continue

        new_items = []
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                new_items.append(item)
                seen_ids.add(item_id)

        for item in reversed(new_items):

            # ── VÉRIFICATION AVANT CHAQUE ENVOI ──
            # Si l'utilisateur stoppe pendant qu'on envoie les articles,
            # on arrête immédiatement l'envoi
            if key in stopped_keys or key not in watchers:
                stopped_keys.discard(key)
                print(f"[Scrape] Envoi interrompu pour '{key}' (watcher stoppé pendant l'envoi)")
                break

            try:
                embed     = build_item_embed(item, watcher["categorie"], marque)
                item_url  = item.get("url", "")
                if item_url and not item_url.startswith("http"):
                    item_url = VINTED_BASE + item_url
                item_id   = item.get("id", 0)
                price_str = format_price(item.get("price"))
                view      = ArticleView(item_url, item_id, price_str)

                await channel.send(embed=embed, view=view)
                await asyncio.sleep(0.3)

            except discord.Forbidden:
                print(f"[Discord] Permission refusée dans {channel.name}")
                break
            except Exception as ex:
                print(f"[Discord] Erreur: {ex}")

        # Mise à jour des IDs vus (seulement si le watcher est encore actif)
        if key in watchers and key not in stopped_keys:
            watcher["seen_ids"] = list(seen_ids)[-500:]
            watchers[key]       = watcher

    save_data()


@scrape_task.before_loop
async def before_scrape():
    await bot.wait_until_ready()
    print("[Scrape] Démarré — cycle toutes les 3 secondes")

# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

@bot.event
async def on_ready():
    await bot.tree.sync()
    scrape_task.start()
    print(f"✅ VintedBot prêt : {bot.user}")
    print(f"   {len(watchers)} watcher(s) chargé(s)")

# ─────────────────────────────────────────────
#  COMMANDES
# ─────────────────────────────────────────────

@bot.tree.command(
    name="vinted",
    description="Surveiller les nouveaux articles Vinted dans un salon"
)
@app_commands.describe(
    categorie="Catégorie à surveiller (tape pour chercher)",
    salon="Salon où envoyer les articles",
    marque="Marque spécifique (optionnel, ex: Nike, Zara...)"
)
@app_commands.autocomplete(categorie=categorie_autocomplete)
async def vinted_cmd(
    inter: discord.Interaction,
    categorie: str,
    salon: discord.TextChannel,
    marque: str = None
):
    await inter.response.defer(ephemeral=True)

    categorie  = categorie.lower().strip()
    catalog_id = CATEGORIES.get(categorie)

    if not catalog_id:
        suggestions = [c for c in CATEGORIES if categorie[:3] in c][:5]
        msg = f"❌ Catégorie `{categorie}` introuvable."
        if suggestions:
            msg += "\n\n**Peut-être :** " + " • ".join(f"`{s}`" for s in suggestions)
        msg += "\n\nUtilise `/vinted_categories` pour tout voir."
        return await inter.followup.send(msg, ephemeral=True)

    marque_key = marque.lower().strip() if marque else "none"
    key        = f"{inter.guild.id}:{salon.id}:{categorie}:{marque_key}"

    if key in watchers:
        return await inter.followup.send(
            f"⚠️ Un watcher pour `{categorie}`"
            f"{f' • {marque}' if marque else ''} "
            f"existe déjà dans {salon.mention} !\n"
            f"Utilise `/vinted_stop_select` pour l'arrêter.",
            ephemeral=True
        )

    perms = salon.permissions_for(inter.guild.me)
    if not perms.send_messages or not perms.embed_links:
        return await inter.followup.send(
            f"❌ Je n'ai pas les permissions dans {salon.mention}.",
            ephemeral=True
        )

    watchers[key] = {
        "guild_id":   inter.guild.id,
        "channel_id": salon.id,
        "categorie":  categorie,
        "marque":     marque.strip() if marque else None,
        "catalog_id": catalog_id,
        "seen_ids":   [],
        "added_by":   str(inter.user),
        "started_at": datetime.datetime.utcnow().isoformat(),
    }
    # S'assure que la clé n'est pas dans stopped_keys (edge case redémarrage)
    stopped_keys.discard(key)
    save_data()

    e = discord.Embed(
        title="✅ Surveillance Vinted démarrée !",
        color=discord.Color.green()
    )
    e.add_field(name="📦 Catégorie",  value=f"`{categorie}`",        inline=True)
    e.add_field(name="📣 Salon",      value=salon.mention,            inline=True)
    e.add_field(name="🔄 Intervalle", value="Toutes les 3 secondes", inline=True)
    if marque:
        e.add_field(name="🏷️ Marque", value=f"`{marque}`", inline=True)
    e.add_field(
        name="ℹ️ Boutons sur chaque article",
        value=(
            "🛍️ **Voir sur Vinted** → Page article\n"
            "💳 **Acheter directement** → Page paiement\n"
            "📋 **Copier le lien** → Liens en privé"
        ),
        inline=False
    )
    e.set_footer(text=f"Démarré par {inter.user}")
    e.timestamp = datetime.datetime.utcnow()
    await inter.followup.send(embed=e, ephemeral=True)

    salon_e = discord.Embed(
        title="🔍 Surveillance Vinted activée",
        description=(
            f"Surveillance des nouvelles annonces **{categorie}**"
            f"{f' de la marque **{marque}**' if marque else ''} "
            f"toutes les 3 secondes."
        ),
        color=discord.Color.blurple()
    )
    salon_e.set_footer(text="CrowBot Vinted Scraper")
    await salon.send(embed=salon_e)


@bot.tree.command(
    name="vinted_stop",
    description="Arrêter une surveillance en la choisissant dans une liste"
)
async def vinted_stop(inter: discord.Interaction):
    """Menu déroulant pour choisir quelle surveillance arrêter."""
    guild_watchers = {k: v for k, v in watchers.items() if v["guild_id"] == inter.guild.id}

    if not guild_watchers:
        return await inter.response.send_message(
            "📭 Aucune surveillance active.", ephemeral=True)

    options = []
    for k, w in list(guild_watchers.items())[:25]:
        ch      = inter.guild.get_channel(w["channel_id"])
        ch_name = ch.name if ch else "supprimé"
        mrq     = w.get("marque") or "toutes marques"
        label   = f"{w['categorie']} — #{ch_name}"
        desc    = f"Marque: {mrq}"
        options.append(discord.SelectOption(
            label=label[:100],
            description=desc[:100],
            value=k
        ))

    select = discord.ui.Select(
        placeholder="Choisir la surveillance à arrêter...",
        options=options,
        min_values=1,
        max_values=1
    )

    async def select_callback(interaction: discord.Interaction):
        chosen_key = select.values[0]
        if chosen_key in watchers:
            w = watchers[chosen_key]

            # ── SUPPRESSION PROPRE ──
            remove_watcher(chosen_key)

            ch     = interaction.guild.get_channel(w["channel_id"])
            ch_ref = ch.mention if ch else "#supprimé"
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="⏹️ Surveillance arrêtée",
                    description=(
                        f"✅ Surveillance **{w['categorie']}** dans {ch_ref} arrêtée.\n"
                        f"Les articles ont immédiatement arrêté d'être envoyés."
                    ),
                    color=discord.Color.red()
                ),
                view=None
            )
        else:
            await interaction.response.send_message(
                "❌ Cette surveillance n'existe plus.", ephemeral=True)

    select.callback = select_callback
    view = discord.ui.View(timeout=60)
    view.add_item(select)

    e = discord.Embed(
        title="⏹️ Arrêter une surveillance",
        description=f"**{len(guild_watchers)}** surveillance(s) active(s). Laquelle arrêter ?",
        color=discord.Color.orange()
    )
    await inter.response.send_message(embed=e, view=view, ephemeral=True)


@bot.tree.command(
    name="vinted_list",
    description="Voir toutes les surveillances actives sur ce serveur"
)
async def vinted_list(inter: discord.Interaction):
    guild_watchers = {k: v for k, v in watchers.items() if v["guild_id"] == inter.guild.id}

    if not guild_watchers:
        return await inter.response.send_message(
            "📭 Aucune surveillance active.\nUtilise `/vinted` pour en démarrer une !",
            ephemeral=True
        )

    e = discord.Embed(
        title=f"🔍 Surveillances actives ({len(guild_watchers)})",
        color=discord.Color.blurple()
    )
    for key, w in guild_watchers.items():
        channel = inter.guild.get_channel(w["channel_id"])
        ch_name = channel.mention if channel else "#supprimé"
        marque  = w.get("marque") or "Toutes"
        started = w.get("started_at", "?")[:10]
        e.add_field(
            name=f"📦 {w['categorie']}",
            value=(
                f"📣 {ch_name}\n"
                f"🏷️ `{marque}`\n"
                f"👤 {w.get('added_by', '?')}\n"
                f"📅 {started}"
            ),
            inline=True
        )
    e.set_footer(text="/vinted_stop pour arrêter une surveillance")
    await inter.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(
    name="vinted_stop_all",
    description="Arrêter TOUTES les surveillances sur ce serveur (Admin)"
)
@app_commands.checks.has_permissions(administrator=True)
async def vinted_stop_all(inter: discord.Interaction):
    keys = [k for k, v in watchers.items() if v["guild_id"] == inter.guild.id]
    if not keys:
        return await inter.response.send_message("📭 Aucune surveillance active.", ephemeral=True)

    for k in keys:
        remove_watcher(k)   # ← suppression propre pour chaque clé

    await inter.response.send_message(
        embed=discord.Embed(
            title="⏹️ Tout arrêté",
            description=f"**{len(keys)}** surveillance(s) arrêtée(s) immédiatement.",
            color=discord.Color.red()
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="vinted_categories",
    description="Voir toutes les catégories disponibles"
)
async def vinted_categories(inter: discord.Interaction):
    cats_by_group = {
        "👗 Femmes":       ["robes","hauts","manteaux","vestes","jeans","pantalons","jupes","pulls","chaussures_femme","sacs","bijoux","lingerie","sport_femme","maillots"],
        "👕 Hommes":       ["t-shirts","chemises","sweats","vestes_homme","manteaux_homme","pantalons_homme","jeans_homme","shorts","chaussures_homme","accessoires","sport_homme"],
        "👶 Enfants":      ["bebe","enfant_fille","enfant_garcon","jouets"],
        "📱 Électronique": ["smartphones","ordinateurs","tablettes","consoles","jeux_video","casques","photo","tv"],
        "🏠 Maison":       ["decoration","cuisine","linge","meubles","jardin"],
        "📚 Autres":       ["livres","musique","films","sport","beaute","animaux","voiture","collection"],
    }
    e = discord.Embed(
        title="📋 Catégories disponibles",
        description="Tape directement dans `/vinted categorie:` pour chercher !",
        color=discord.Color.blurple()
    )
    for group, cats in cats_by_group.items():
        e.add_field(name=group, value="\n".join(f"`{c}`" for c in cats), inline=True)
    e.set_footer(text="CrowBot Vinted Scraper")
    await inter.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(
    name="vinted_test",
    description="Tester le scraping — aperçu des derniers articles"
)
@app_commands.describe(categorie="Catégorie à tester", marque="Marque (optionnel)")
@app_commands.autocomplete(categorie=categorie_autocomplete)
async def vinted_test(inter: discord.Interaction, categorie: str, marque: str = None):
    await inter.response.defer(ephemeral=True)
    categorie  = categorie.lower().strip()
    catalog_id = CATEGORIES.get(categorie)
    if not catalog_id:
        return await inter.followup.send(f"❌ Catégorie `{categorie}` introuvable.", ephemeral=True)

    session = await get_session()
    items   = await fetch_vinted_items(session, catalog_id, marque, per_page=3)

    if not items:
        return await inter.followup.send(
            "❌ Aucun article trouvé. Réessaie dans quelques secondes.", ephemeral=True)

    await inter.followup.send(
        f"✅ **Test réussi !** {len(items)} article(s) pour `{categorie}`"
        f"{f' • `{marque}`' if marque else ''}. Aperçu :",
        ephemeral=True
    )
    for item in items[:3]:
        embed     = build_item_embed(item, categorie, marque)
        item_url  = item.get("url", "")
        if item_url and not item_url.startswith("http"):
            item_url = VINTED_BASE + item_url
        item_id   = item.get("id", 0)
        price_str = format_price(item.get("price"))
        view      = ArticleView(item_url, item_id, price_str)
        await inter.channel.send(embed=embed, view=view)
        await asyncio.sleep(0.3)


@bot.tree.command(name="help", description="Aide CrowBot Vinted")
async def help_cmd(inter: discord.Interaction):
    e = discord.Embed(
        title="🛍️ CrowBot — Vinted Scraper",
        description="Surveille les nouvelles annonces Vinted en temps réel !",
        color=discord.Color.blurple()
    )
    e.add_field(
        name="📌 Commandes",
        value=(
            "`/vinted` — Démarrer une surveillance\n"
            "`/vinted_stop` — Arrêter via menu déroulant ✅\n"
            "`/vinted_stop_all` — Tout arrêter (Admin)\n"
            "`/vinted_list` — Voir les surveillances actives\n"
            "`/vinted_categories` — Voir toutes les catégories\n"
            "`/vinted_test` — Tester une catégorie"
        ),
        inline=False
    )
    e.add_field(
        name="🛍️ Boutons sur chaque article",
        value=(
            "**🛍️ Voir sur Vinted** → Page de l'article\n"
            "**💳 Acheter directement** → Page de paiement\n"
            "**📋 Copier le lien** → Liens en message privé"
        ),
        inline=False
    )
    e.add_field(name="⏱️ Fréquence",  value="Toutes les **3 secondes**", inline=True)
    e.add_field(name="💾 Persistance", value="Survit aux redémarrages",   inline=True)
    e.set_footer(text="CrowBot Vinted Scraper")
    await inter.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────
#  LANCEMENT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("❌ DISCORD_TOKEN manquant dans .env")
        exit(1)
    bot.run(TOKEN)