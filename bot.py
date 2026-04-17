"""
╔══════════════════════════════════════════════════════════════════╗
║                     — VINTED SCRAPER v2.0                        ║
║         Surveillance d'articles Vinted en temps réel             ║
║                                                                   ║
║  Améliorations v2:                                                ║
║  • Rate limiting intelligent                                      ║
║  • Retry automatique sur erreurs réseau                           ║
║  • Lock asyncio pour thread-safety                                ║
║  • Rotation de User-Agent                                         ║
║  • Métriques et monitoring                                        ║
║  • Gestion propre shutdown                                        ║
║  • Filtre prix min/max                                            ║
║  • Notifications d'erreur Discord                                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import datetime
import os
import json
import time
import random
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional
from dotenv import load_dotenv

# ─────────────────────────────────────────────
#  CONFIGURATION & LOGGING
# ─────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("vinted_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("VintedBot")

TOKEN     = os.getenv("DISCORD_TOKEN")
DATA_FILE = "vinted_watchers.json"

# Délais de sécurité
SCRAPE_INTERVAL   = 8    # secondes entre chaque cycle complet
REQUEST_DELAY     = 1.5  # secondes entre chaque requête Vinted
MAX_RETRIES       = 3    # tentatives avant abandon
COOKIE_TTL        = 300  # secondes avant renouvellement cookie
MAX_SEEN_IDS      = 300  # IDs conservés par watcher
MAX_WATCHERS_GUILD = 10  # limite par serveur

# ─────────────────────────────────────────────
#  USER-AGENT POOL (rotation anti-ban)
# ─────────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

VINTED_BASE = "https://www.vinted.fr"

# ─────────────────────────────────────────────
#  CATÉGORIES
# ─────────────────────────────────────────────

CATEGORIES = {
    # Femmes
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
    # Hommes
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
    # Enfants
    "bebe":              280,
    "enfant_fille":      281,
    "enfant_garcon":     282,
    "jouets":            220,
    # Tech
    "smartphones":       2,
    "ordinateurs":       594,
    "tablettes":         595,
    "consoles":          596,
    "jeux_video":        597,
    "casques":           598,
    "photo":             599,
    "tv":                600,
    # Maison
    "decoration":        8,
    "cuisine":           9,
    "linge":             10,
    "meubles":           11,
    "jardin":            12,
    # Divers
    "livres":            5,
    "musique":           6,
    "films":             7,
    "sport":             15,
    "beaute":            218,
    "animaux":           302,
    "voiture":           17,
    "collection":        3,
}

CATEGORIES_GROUPS = {
    "👗 Femmes":       ["robes","hauts","manteaux","vestes","jeans","pantalons",
                        "jupes","pulls","chaussures_femme","sacs","bijoux",
                        "lingerie","sport_femme","maillots"],
    "👕 Hommes":       ["t-shirts","chemises","sweats","vestes_homme","manteaux_homme",
                        "pantalons_homme","jeans_homme","shorts","chaussures_homme",
                        "accessoires","sport_homme"],
    "👶 Enfants":      ["bebe","enfant_fille","enfant_garcon","jouets"],
    "📱 Électronique": ["smartphones","ordinateurs","tablettes","consoles",
                        "jeux_video","casques","photo","tv"],
    "🏠 Maison":       ["decoration","cuisine","linge","meubles","jardin"],
    "📚 Autres":       ["livres","musique","films","sport","beaute",
                        "animaux","voiture","collection"],
}

# ─────────────────────────────────────────────
#  DATACLASS WATCHER (structure typée)
# ─────────────────────────────────────────────

@dataclass
class Watcher:
    """Représente une surveillance Vinted active."""
    guild_id:   int
    channel_id: int
    categorie:  str
    catalog_id: int
    marque:     Optional[str]     = None
    prix_min:   Optional[float]   = None
    prix_max:   Optional[float]   = None
    seen_ids:   list              = field(default_factory=list)
    added_by:   str               = ""
    started_at: str               = field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat()
    )
    # Métriques
    total_sent:    int = 0
    last_activity: str = ""
    error_count:   int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Watcher":
        # Compatibilité avec ancienne version (sans prix_min/prix_max)
        d.setdefault("prix_min", None)
        d.setdefault("prix_max", None)
        d.setdefault("total_sent", 0)
        d.setdefault("last_activity", "")
        d.setdefault("error_count", 0)
        return Watcher(**{k: v for k, v in d.items() if k in Watcher.__dataclass_fields__})

# ─────────────────────────────────────────────
#  STOCKAGE AMÉLIORÉ
# ─────────────────────────────────────────────

class WatcherStorage:
    """Gestion thread-safe du stockage des watchers."""

    def __init__(self, filepath: str):
        self.filepath    = filepath
        self._lock       = asyncio.Lock()
        self._watchers:  dict[str, Watcher] = {}
        self._stopped:   set[str]           = set()
        self._load()

    def _load(self):
        """Charge depuis le fichier JSON."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for key, data in raw.get("watchers", {}).items():
                try:
                    self._watchers[key] = Watcher.from_dict(data)
                except Exception as e:
                    log.warning(f"[Storage] Skip watcher '{key}': {e}")
            self._stopped = set(raw.get("stopped", []))
            log.info(f"[Storage] {len(self._watchers)} watcher(s) chargé(s)")
        except Exception as e:
            log.error(f"[Storage] Erreur chargement: {e}")

    async def save(self):
        """Sauvegarde asynchrone (avec lock)."""
        async with self._lock:
            try:
                data = {
                    "watchers": {k: w.to_dict() for k, w in self._watchers.items()},
                    "stopped":  list(self._stopped),
                    "saved_at": datetime.datetime.utcnow().isoformat(),
                }
                # Écriture atomique via fichier temporaire
                tmp = self.filepath + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, self.filepath)
            except Exception as e:
                log.error(f"[Storage] Erreur sauvegarde: {e}")

    def get_all(self) -> dict[str, Watcher]:
        return dict(self._watchers)

    def get(self, key: str) -> Optional[Watcher]:
        return self._watchers.get(key)

    def add(self, key: str, watcher: Watcher):
        self._watchers[key] = watcher
        self._stopped.discard(key)

    def remove(self, key: str):
        """Suppression atomique : stopped_keys PUIS suppression."""
        self._stopped.add(key)
        self._watchers.pop(key, None)
        log.info(f"[Storage] Watcher '{key}' supprimé")

    def is_stopped(self, key: str) -> bool:
        return key in self._stopped or key not in self._watchers

    def clear_stopped(self, key: str):
        self._stopped.discard(key)

    def guild_watchers(self, guild_id: int) -> dict[str, Watcher]:
        return {k: w for k, w in self._watchers.items() if w.guild_id == guild_id}

    def guild_count(self, guild_id: int) -> int:
        return sum(1 for w in self._watchers.values() if w.guild_id == guild_id)

# ─────────────────────────────────────────────
#  HTTP CLIENT AMÉLIORÉ
# ─────────────────────────────────────────────

class VintedHTTPClient:
    """Client HTTP avec gestion cookie, retry et rate limiting."""

    def __init__(self):
        self._session:      Optional[aiohttp.ClientSession] = None
        self._cookie:       str   = ""
        self._cookie_ts:    float = 0.0
        self._request_lock        = asyncio.Lock()
        self._last_request_ts:float = 0.0
        self._consecutive_errors: int = 0
        self._backoff:      float = 1.0  # délai croissant sur erreurs

    def _random_headers(self) -> dict:
        """Headers avec User-Agent aléatoire."""
        return {
            "User-Agent":      random.choice(USER_AGENTS),
            "Accept":          "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer":         f"{VINTED_BASE}/catalog",
            "Origin":          VINTED_BASE,
            "DNT":             "1",
            "Connection":      "keep-alive",
            "Sec-Fetch-Dest":  "empty",
            "Sec-Fetch-Mode":  "cors",
            "Sec-Fetch-Site":  "same-origin",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector    = aiohttp.TCPConnector(
                limit=5,
                ssl=False,
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=15, connect=5),
            )
        return self._session

    async def _rate_limit(self):
        """Respecte le délai minimum entre requêtes."""
        async with self._request_lock:
            elapsed = time.monotonic() - self._last_request_ts
            if elapsed < REQUEST_DELAY:
                await asyncio.sleep(REQUEST_DELAY - elapsed)
            self._last_request_ts = time.monotonic()

    async def refresh_cookie(self) -> str:
        """Renouvelle le cookie de session Vinted."""
        session = await self._get_session()
        try:
            headers = self._random_headers()
            async with session.get(
                VINTED_BASE,
                headers=headers,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                cookies = session.cookie_jar.filter_cookies(VINTED_BASE)
                self._cookie    = "; ".join(f"{k}={v.value}" for k, v in cookies.items())
                self._cookie_ts = time.monotonic()
                log.debug(f"[HTTP] Cookie renouvelé ({len(self._cookie)} chars)")
                return self._cookie
        except Exception as e:
            log.warning(f"[HTTP] Échec renouvellement cookie: {e}")
            return self._cookie

    async def get_cookie(self) -> str:
        """Retourne le cookie, le renouvelle si nécessaire."""
        if not self._cookie or (time.monotonic() - self._cookie_ts) > COOKIE_TTL:
            await self.refresh_cookie()
        return self._cookie

    async def get_brand_id(self, brand_name: str) -> Optional[str]:
        """Recherche l'ID d'une marque par son nom."""
        await self._rate_limit()
        session = await self._get_session()
        cookie  = await self.get_cookie()
        headers = {**self._random_headers(), "Cookie": cookie}

        try:
            async with session.get(
                f"{VINTED_BASE}/api/v2/brands/by_name",
                headers=headers,
                params={"brand_name": brand_name},
            ) as resp:
                if resp.status == 200:
                    data  = await resp.json(content_type=None)
                    brand = data.get("brand")
                    if brand:
                        return str(brand.get("id", ""))
        except Exception as e:
            log.debug(f"[HTTP] get_brand_id '{brand_name}': {e}")
        return None

    async def fetch_items(
        self,
        catalog_id:  int,
        marque:      Optional[str] = None,
        per_page:    int = 20,
        retries:     int = MAX_RETRIES,
    ) -> list[dict]:
        """
        Fetch les articles Vinted avec retry automatique.
        Retourne [] si échec définitif.
        """
        await self._rate_limit()
        session = await self._get_session()
        cookie  = await self.get_cookie()

        params = {
            "per_page":    str(per_page),
            "catalog_ids": str(catalog_id),
            "order":       "newest_first",
            "page":        "1",
        }

        # Résolution marque → ID
        if marque:
            brand_id = await self.get_brand_id(marque)
            if brand_id:
                params["brand_ids"] = brand_id
                log.debug(f"[HTTP] Marque '{marque}' → ID {brand_id}")
            else:
                params["search_text"] = marque
                log.debug(f"[HTTP] Marque '{marque}' non trouvée, search_text utilisé")

        for attempt in range(retries):
            headers = {**self._random_headers(), "Cookie": cookie}
            try:
                async with session.get(
                    f"{VINTED_BASE}/api/v2/catalog/items",
                    headers=headers,
                    params=params,
                ) as resp:

                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        items = data.get("items", [])
                        self._consecutive_errors = 0
                        self._backoff = 1.0
                        return items

                    elif resp.status == 401:
                        log.warning("[HTTP] 401 — renouvellement cookie forcé")
                        self._cookie_ts = 0
                        cookie = await self.refresh_cookie()
                        await asyncio.sleep(2)

                    elif resp.status == 429:
                        wait = self._backoff * (2 ** attempt)
                        log.warning(f"[HTTP] 429 Rate Limited — attente {wait:.1f}s")
                        await asyncio.sleep(wait)

                    elif resp.status in (503, 502, 504):
                        wait = self._backoff * (attempt + 1)
                        log.warning(f"[HTTP] {resp.status} — retry dans {wait:.1f}s")
                        await asyncio.sleep(wait)

                    else:
                        log.warning(f"[HTTP] Status inattendu: {resp.status}")
                        break

            except asyncio.TimeoutError:
                log.warning(f"[HTTP] Timeout (tentative {attempt+1}/{retries})")
                await asyncio.sleep(self._backoff)

            except aiohttp.ClientConnectorError as e:
                log.warning(f"[HTTP] Connexion impossible: {e}")
                await asyncio.sleep(self._backoff * 2)
                break

            except Exception as e:
                log.error(f"[HTTP] Erreur inattendue: {e}")
                break

        self._consecutive_errors += 1
        # Backoff exponentiel sur erreurs répétées
        self._backoff = min(30.0, 1.0 * (1.5 ** self._consecutive_errors))
        return []

    async def close(self):
        """Ferme proprement la session HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
            log.info("[HTTP] Session fermée")

# ─────────────────────────────────────────────
#  HELPERS PRIX
# ─────────────────────────────────────────────

CURRENCY_SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "PLN": "zł", "CZK": "Kč"}

def parse_price(raw_price) -> tuple[float, str]:
    if isinstance(raw_price, dict):
        amount   = raw_price.get("amount", 0)
        currency = raw_price.get("currency_code", "EUR")
        try:
            return float(str(amount).replace(",", ".")), CURRENCY_SYMBOLS.get(currency, currency)
        except Exception:
            return 0.0, "€"
    try:
        return float(str(raw_price).replace(",", ".")), "€"
    except Exception:
        return 0.0, "€"

def format_price(raw_price) -> str:
    value, symbol = parse_price(raw_price)
    return f"{int(value)} {symbol}" if value == int(value) else f"{value:.2f} {symbol}"

def price_in_range(
    raw_price,
    prix_min: Optional[float],
    prix_max: Optional[float]
) -> bool:
    """Vérifie si un prix est dans la plage souhaitée."""
    if prix_min is None and prix_max is None:
        return True
    value, _ = parse_price(raw_price)
    if prix_min is not None and value < prix_min:
        return False
    if prix_max is not None and value > prix_max:
        return False
    return True

# ─────────────────────────────────────────────
#  EMBED & VIEW
# ─────────────────────────────────────────────

def build_item_embed(item: dict, watcher: Watcher) -> discord.Embed:
    """Construit l'embed Discord pour un article Vinted."""
    title    = item.get("title", "Article sans titre")
    url      = item.get("url", "")
    if url and not url.startswith("http"):
        url = VINTED_BASE + url

    raw_price    = item.get("price")
    price_str    = format_price(raw_price)
    price_val, _ = parse_price(raw_price)

    # Photo
    photos    = item.get("photos", [])
    photo_url = None
    if photos:
        p         = photos[0]
        photo_url = p.get("full_size_url") or p.get("url") or p.get("thumb_url")

    # Vendeur
    user     = item.get("user", {})
    username = user.get("login", "Inconnu")
    user_url = f"{VINTED_BASE}/member/{user.get('id', '')}"

    # Infos article
    size_title   = item.get("size_title", "")
    status_title = item.get("status", "")
    brand_title  = item.get("brand_title", "")
    fav_count    = item.get("favourite_count", 0)
    view_count   = item.get("view_count", 0)

    # Couleur selon prix
    if price_val <= 5:    color = discord.Color.green()
    elif price_val <= 15: color = discord.Color.gold()
    elif price_val <= 50: color = discord.Color.orange()
    else:                 color = discord.Color.red()

    e = discord.Embed(
        title=f"🛍️ {title[:250]}",
        url=url,
        color=color,
        description=f"## {price_str}",
    )

    if photo_url:
        e.set_image(url=photo_url)

    e.add_field(name="👤 Vendeur", value=f"[{username}]({user_url})", inline=True)
    e.add_field(name="💶 Prix",    value=f"**{price_str}**",          inline=True)

    if brand_title:
        e.add_field(name="🏷️ Marque",  value=brand_title,  inline=True)
    if size_title:
        e.add_field(name="📏 Taille",  value=size_title,   inline=True)
    if status_title:
        e.add_field(name="✨ État",    value=status_title, inline=True)
    if fav_count:
        e.add_field(name="❤️ Favoris", value=str(fav_count), inline=True)
    if view_count:
        e.add_field(name="👁️ Vues",    value=str(view_count), inline=True)

    # Tags footer
    tags = f"`{watcher.categorie}`"
    if watcher.marque:
        tags += f" • `{watcher.marque}`"
    if watcher.prix_min or watcher.prix_max:
        prix_range = ""
        if watcher.prix_min:
            prix_range += f"≥{watcher.prix_min}€"
        if watcher.prix_max:
            prix_range += f" ≤{watcher.prix_max}€"
        tags += f" • {prix_range.strip()}"

    e.set_footer(text=f"Vinted • {tags} • {datetime.datetime.now().strftime('%H:%M:%S')}")
    e.timestamp = datetime.datetime.utcnow()
    return e


class ArticleView(discord.ui.View):
    """Boutons d'action sur chaque article."""

    def __init__(self, item_url: str, item_id: int):
        super().__init__(timeout=None)
        self.item_url = item_url
        self.item_id  = item_id

        if item_url:
            self.add_item(discord.ui.Button(
                label="🛍️ Voir l'article",
                url=item_url,
                style=discord.ButtonStyle.link,
                row=0,
            ))

        checkout_url = f"{VINTED_BASE}/transaction/buy/new?item_id={item_id}"
        self.add_item(discord.ui.Button(
            label="💳 Acheter",
            url=checkout_url,
            style=discord.ButtonStyle.link,
            row=0,
        ))

    @discord.ui.button(
        label="📋 Copier les liens",
        style=discord.ButtonStyle.secondary,
        custom_id="copy_link_v2",
        row=1,
    )
    async def copy_link(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        checkout = f"{VINTED_BASE}/transaction/buy/new?item_id={self.item_id}"
        await interaction.response.send_message(
            f"🔗 **Article :** {self.item_url}\n"
            f"💳 **Achat direct :** {checkout}",
            ephemeral=True,
        )

# ─────────────────────────────────────────────
#  BOT
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot     = commands.Bot(command_prefix="!", intents=intents, help_command=None)
storage = WatcherStorage(DATA_FILE)
http    = VintedHTTPClient()

# ─────────────────────────────────────────────
#  AUTOCOMPLETE
# ─────────────────────────────────────────────

async def categorie_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    lower = current.lower()
    return [
        app_commands.Choice(name=c, value=c)
        for c in CATEGORIES
        if lower in c.lower()
    ][:25]

# ─────────────────────────────────────────────
#  TÂCHE DE SCRAPING v2
# ─────────────────────────────────────────────

# File de métriques pour monitoring
_metrics: deque = deque(maxlen=100)

@tasks.loop(seconds=SCRAPE_INTERVAL)
async def scrape_task():
    """Cycle principal de scraping — s'exécute toutes les N secondes."""
    all_watchers = storage.get_all()
    if not all_watchers:
        return

    cycle_start  = time.monotonic()
    items_sent   = 0
    errors       = 0

    for key, watcher in all_watchers.items():

        # ── Vérification active avant chaque watcher ──
        if storage.is_stopped(key):
            storage.clear_stopped(key)
            continue

        channel = None
        try:
            guild = bot.get_guild(watcher.guild_id)
            if not guild:
                continue

            channel = guild.get_channel(watcher.channel_id)
            if not channel:
                continue

            # Fetch avec retry intégré
            items = await http.fetch_items(
                watcher.catalog_id,
                watcher.marque,
                per_page=20,
            )

            # ── Vérification post-fetch ──
            if storage.is_stopped(key):
                storage.clear_stopped(key)
                continue

            if not items:
                continue

            seen_ids = set(watcher.seen_ids)
            new_items = []

            for item in items:
                item_id = item.get("id")
                if not item_id or item_id in seen_ids:
                    continue

                # Filtre prix
                if not price_in_range(item.get("price"), watcher.prix_min, watcher.prix_max):
                    seen_ids.add(item_id)  # marque comme vu pour ne pas retester
                    continue

                new_items.append(item)
                seen_ids.add(item_id)

            # Envoi dans l'ordre chronologique (plus ancien → plus récent)
            for item in reversed(new_items):

                # ── Vérification avant chaque envoi ──
                if storage.is_stopped(key):
                    storage.clear_stopped(key)
                    log.info(f"[Scrape] Envoi interrompu pour '{key}'")
                    break

                try:
                    embed    = build_item_embed(item, watcher)
                    item_url = item.get("url", "")
                    if item_url and not item_url.startswith("http"):
                        item_url = VINTED_BASE + item_url
                    item_id  = item.get("id", 0)
                    view     = ArticleView(item_url, item_id)

                    await channel.send(embed=embed, view=view)
                    items_sent += 1

                    # Mise à jour métriques watcher
                    watcher.total_sent    += 1
                    watcher.last_activity  = datetime.datetime.utcnow().isoformat()
                    watcher.error_count    = 0

                    await asyncio.sleep(0.5)  # anti-spam Discord

                except discord.Forbidden:
                    log.warning(f"[Discord] Permissions insuffisantes dans #{channel.name}")
                    errors += 1
                    break

                except discord.HTTPException as e:
                    log.warning(f"[Discord] HTTPException: {e}")
                    errors += 1
                    await asyncio.sleep(2)

                except Exception as e:
                    log.error(f"[Discord] Erreur envoi: {e}")
                    errors += 1

            # ── Mise à jour seen_ids (atomique) ──
            if not storage.is_stopped(key):
                watcher.seen_ids = list(seen_ids)[-MAX_SEEN_IDS:]

        except Exception as e:
            log.error(f"[Scrape] Erreur critique watcher '{key}': {e}")
            errors += 1
            if watcher:
                watcher.error_count = watcher.error_count + 1

    # Sauvegarde en fin de cycle
    await storage.save()

    # Métriques cycle
    cycle_time = time.monotonic() - cycle_start
    _metrics.append({
        "ts":        datetime.datetime.utcnow().isoformat(),
        "items":     items_sent,
        "errors":    errors,
        "duration":  round(cycle_time, 2),
        "watchers":  len(all_watchers),
    })

    if items_sent > 0:
        log.info(f"[Scrape] Cycle: {items_sent} article(s) envoyé(s) en {cycle_time:.2f}s")


@scrape_task.before_loop
async def before_scrape():
    await bot.wait_until_ready()
    log.info(f"[Scrape] Démarré — cycle toutes les {SCRAPE_INTERVAL}s")
    # Préchauffage du cookie
    await http.refresh_cookie()

# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

@bot.event
async def on_ready():
    await bot.tree.sync()
    scrape_task.start()
    log.info(f"✅ VintedBot prêt : {bot.user} ({bot.user.id})")
    log.info(f"   Serveurs : {len(bot.guilds)}")
    log.info(f"   Watchers : {len(storage.get_all())}")


@bot.event
async def on_disconnect():
    log.warning("[Bot] Déconnecté de Discord")


async def shutdown():
    """Arrêt propre du bot."""
    log.info("[Bot] Arrêt en cours...")
    scrape_task.cancel()
    await http.close()
    await storage.save()

# ─────────────────────────────────────────────
#  COMMANDES SLASH
# ─────────────────────────────────────────────

@bot.tree.command(
    name="vinted",
    description="Surveiller les nouvelles annonces Vinted en temps réel"
)
@app_commands.describe(
    categorie="Catégorie à surveiller",
    salon="Salon Discord où envoyer les articles",
    marque="Marque spécifique (ex: Nike, Zara...)",
    prix_min="Prix minimum en € (optionnel)",
    prix_max="Prix maximum en € (optionnel)",
)
@app_commands.autocomplete(categorie=categorie_autocomplete)
async def vinted_cmd(
    inter:     discord.Interaction,
    categorie: str,
    salon:     discord.TextChannel,
    marque:    Optional[str]   = None,
    prix_min:  Optional[float] = None,
    prix_max:  Optional[float] = None,
):
    await inter.response.defer(ephemeral=True)

    # Validation catégorie
    categorie  = categorie.lower().strip()
    catalog_id = CATEGORIES.get(categorie)

    if not catalog_id:
        suggestions = [c for c in CATEGORIES if categorie[:3] in c][:5]
        msg = f"❌ Catégorie `{categorie}` introuvable."
        if suggestions:
            msg += "\n**Suggestions :** " + " • ".join(f"`{s}`" for s in suggestions)
        return await inter.followup.send(msg, ephemeral=True)

    # Validation prix
    if prix_min is not None and prix_max is not None and prix_min >= prix_max:
        return await inter.followup.send(
            "❌ `prix_min` doit être inférieur à `prix_max`.", ephemeral=True)

    # Limite par serveur
    guild_count = storage.guild_count(inter.guild.id)
    if guild_count >= MAX_WATCHERS_GUILD:
        return await inter.followup.send(
            f"❌ Limite de **{MAX_WATCHERS_GUILD} surveillances** par serveur atteinte.\n"
            f"Arrêtez-en une avec `/vinted_stop`.",
            ephemeral=True,
        )

    # Clé unique
    marque_key = (marque or "").lower().strip() or "none"
    prix_key   = f"{prix_min or 0}-{prix_max or 0}"
    key        = f"{inter.guild.id}:{salon.id}:{categorie}:{marque_key}:{prix_key}"

    if storage.get(key) is not None:
        return await inter.followup.send(
            f"⚠️ Cette surveillance existe déjà dans {salon.mention} !\n"
            f"Utilise `/vinted_stop` pour l'arrêter.",
            ephemeral=True,
        )

    # Permissions
    perms = salon.permissions_for(inter.guild.me)
    if not (perms.send_messages and perms.embed_links):
        return await inter.followup.send(
            f"❌ Permissions insuffisantes dans {salon.mention}.\n"
            f"J'ai besoin de : **Envoyer des messages** + **Intégrer des liens**",
            ephemeral=True,
        )

    # Création
    watcher = Watcher(
        guild_id=   inter.guild.id,
        channel_id= salon.id,
        categorie=  categorie,
        catalog_id= catalog_id,
        marque=     marque.strip() if marque else None,
        prix_min=   prix_min,
        prix_max=   prix_max,
        added_by=   str(inter.user),
    )
    storage.add(key, watcher)
    await storage.save()

    # Embed confirmation
    e = discord.Embed(
        title="✅ Surveillance démarrée !",
        color=discord.Color.green(),
    )
    e.add_field(name="📦 Catégorie",  value=f"`{categorie}`",          inline=True)
    e.add_field(name="📣 Salon",      value=salon.mention,              inline=True)
    e.add_field(name="⏱️ Intervalle", value=f"~{SCRAPE_INTERVAL}s",    inline=True)

    if marque:
        e.add_field(name="🏷️ Marque",   value=f"`{marque}`",  inline=True)
    if prix_min is not None:
        e.add_field(name="💰 Prix min",  value=f"{prix_min} €", inline=True)
    if prix_max is not None:
        e.add_field(name="💰 Prix max",  value=f"{prix_max} €", inline=True)

    e.set_footer(text=f"Démarré par {inter.user} • {guild_count + 1}/{MAX_WATCHERS_GUILD} surveillances")
    e.timestamp = datetime.datetime.utcnow()
    await inter.followup.send(embed=e, ephemeral=True)

    # Annonce dans le salon cible
    announce = discord.Embed(
        title="🔍 Surveillance Vinted activée",
        description=(
            f"Nouvelles annonces **{categorie}**"
            f"{f' — **{marque}**' if marque else ''}"
            f"{f' — entre **{prix_min}€** et **{prix_max}€**' if prix_min and prix_max else ''}"
            f" toutes les ~{SCRAPE_INTERVAL} secondes."
        ),
        color=discord.Color.blurple(),
    )
    announce.set_footer(text="CrowBot Vinted Scraper")
    await salon.send(embed=announce)


@bot.tree.command(
    name="vinted_stop",
    description="Arrêter une surveillance (menu de sélection)"
)
async def vinted_stop(inter: discord.Interaction):
    guild_watchers = storage.guild_watchers(inter.guild.id)

    if not guild_watchers:
        return await inter.response.send_message(
            "📭 Aucune surveillance active sur ce serveur.", ephemeral=True)

    options = []
    for k, w in list(guild_watchers.items())[:25]:
        ch      = inter.guild.get_channel(w.channel_id)
        ch_name = ch.name if ch else "supprimé"
        mrq     = w.marque or "toutes marques"
        prix    = ""
        if w.prix_min or w.prix_max:
            prix = f" • {w.prix_min or '?'}€→{w.prix_max or '?'}€"

        options.append(discord.SelectOption(
            label=f"{w.categorie} — #{ch_name}"[:100],
            description=f"Marque: {mrq}{prix} • {w.total_sent} articles"[:100],
            value=k,
        ))

    select = discord.ui.Select(
        placeholder="Choisir la surveillance à arrêter...",
        options=options,
        min_values=1,
        max_values=1,
    )

    async def on_select(interaction: discord.Interaction):
        chosen = select.values[0]
        w      = storage.get(chosen)

        if w is None:
            return await interaction.response.send_message(
                "❌ Cette surveillance n'existe plus.", ephemeral=True)

        storage.remove(chosen)
        await storage.save()

        ch     = interaction.guild.get_channel(w.channel_id)
        ch_ref = ch.mention if ch else "#supprimé"

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⏹️ Surveillance arrêtée",
                description=(
                    f"✅ **{w.categorie}** dans {ch_ref} — arrêtée.\n"
                    f"📊 {w.total_sent} article(s) envoyé(s) au total."
                ),
                color=discord.Color.red(),
            ),
            view=None,
        )

    select.callback = on_select
    view = discord.ui.View(timeout=60)
    view.add_item(select)

    await inter.response.send_message(
        embed=discord.Embed(
            title="⏹️ Arrêter une surveillance",
            description=f"**{len(guild_watchers)}** surveillance(s) active(s).",
            color=discord.Color.orange(),
        ),
        view=view,
        ephemeral=True,
    )


@bot.tree.command(
    name="vinted_list",
    description="Voir toutes les surveillances actives sur ce serveur"
)
async def vinted_list(inter: discord.Interaction):
    guild_watchers = storage.guild_watchers(inter.guild.id)

    if not guild_watchers:
        return await inter.response.send_message(
            "📭 Aucune surveillance active.\nUtilise `/vinted` pour en démarrer une !",
            ephemeral=True,
        )

    e = discord.Embed(
        title=f"🔍 Surveillances actives ({len(guild_watchers)}/{MAX_WATCHERS_GUILD})",
        color=discord.Color.blurple(),
    )

    for key, w in guild_watchers.items():
        channel = inter.guild.get_channel(w.channel_id)
        ch_name = channel.mention if channel else "#supprimé"
        marque  = w.marque or "Toutes"
        started = w.started_at[:10] if w.started_at else "?"

        prix_info = ""
        if w.prix_min or w.prix_max:
            prix_info = f"\n💰 {w.prix_min or '?'}€ → {w.prix_max or '?'}€"

        e.add_field(
            name=f"📦 {w.categorie}",
            value=(
                f"📣 {ch_name}\n"
                f"🏷️ `{marque}`{prix_info}\n"
                f"📊 {w.total_sent} articles\n"
                f"📅 {started}"
            ),
            inline=True,
        )

    e.set_footer(text="Utilise /vinted_stop pour arrêter une surveillance")
    await inter.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(
    name="vinted_stop_all",
    description="Arrêter TOUTES les surveillances (Administrateur uniquement)"
)
@app_commands.checks.has_permissions(administrator=True)
async def vinted_stop_all(inter: discord.Interaction):
    keys = list(storage.guild_watchers(inter.guild.id).keys())

    if not keys:
        return await inter.response.send_message(
            "📭 Aucune surveillance active.", ephemeral=True)

    for k in keys:
        storage.remove(k)
    await storage.save()

    await inter.response.send_message(
        embed=discord.Embed(
            title="⏹️ Tout arrêté",
            description=f"**{len(keys)}** surveillance(s) arrêtée(s).",
            color=discord.Color.red(),
        ),
        ephemeral=True,
    )


@bot.tree.command(
    name="vinted_stats",
    description="Statistiques du scraper (dernier cycle)"
)
async def vinted_stats(inter: discord.Interaction):
    all_w = storage.get_all()
    guild_w = storage.guild_watchers(inter.guild.id)

    e = discord.Embed(
        title="📊 Statistiques VintedBot",
        color=discord.Color.blurple(),
    )
    e.add_field(name="🌍 Total watchers",   value=str(len(all_w)),                     inline=True)
    e.add_field(name="🏠 Watchers serveur", value=f"{len(guild_w)}/{MAX_WATCHERS_GUILD}", inline=True)
    e.add_field(name="⏱️ Intervalle",       value=f"{SCRAPE_INTERVAL}s",               inline=True)

    # Dernier cycle
    if _metrics:
        last = _metrics[-1]
        e.add_field(name="📦 Dernier cycle",
                    value=f"{last['items']} article(s) • {last['duration']}s",
                    inline=False)

    # Stats par watcher de cette guilde
    total_sent = sum(w.total_sent for w in guild_w.values())
    e.add_field(name="📨 Articles envoyés (serveur)", value=str(total_sent), inline=True)

    e.set_footer(text=f"VintedBot v2.0")
    e.timestamp = datetime.datetime.utcnow()
    await inter.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(
    name="vinted_categories",
    description="Voir toutes les catégories disponibles"
)
async def vinted_categories(inter: discord.Interaction):
    e = discord.Embed(
        title="📋 Catégories disponibles",
        description="Utilise l'autocomplétion dans `/vinted categorie:` pour chercher rapidement !",
        color=discord.Color.blurple(),
    )
    for group, cats in CATEGORIES_GROUPS.items():
        e.add_field(
            name=group,
            value="\n".join(f"`{c}`" for c in cats),
            inline=True,
        )
    e.set_footer(text="CrowBot Vinted Scraper v2.0")
    await inter.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(
    name="vinted_test",
    description="Tester le scraping — aperçu des derniers articles"
)
@app_commands.describe(
    categorie="Catégorie à tester",
    marque="Marque (optionnel)",
)
@app_commands.autocomplete(categorie=categorie_autocomplete)
async def vinted_test(
    inter: discord.Interaction,
    categorie: str,
    marque: Optional[str] = None,
):
    await inter.response.defer(ephemeral=True)
    categorie  = categorie.lower().strip()
    catalog_id = CATEGORIES.get(categorie)

    if not catalog_id:
        return await inter.followup.send(
            f"❌ Catégorie `{categorie}` introuvable.", ephemeral=True)

    items = await http.fetch_items(catalog_id, marque, per_page=3)

    if not items:
        return await inter.followup.send(
            "❌ Aucun article trouvé. Réessaie dans quelques instants.", ephemeral=True)

    await inter.followup.send(
        f"✅ **{len(items)} article(s)** pour `{categorie}`"
        f"{f' • `{marque}`' if marque else ''}. Aperçu ci-dessous :",
        ephemeral=True,
    )

    # Créer un watcher temporaire pour build_item_embed
    fake_watcher = Watcher(
        guild_id=0, channel_id=0,
        categorie=categorie, catalog_id=catalog_id,
        marque=marque,
    )

    for item in items[:3]:
        embed    = build_item_embed(item, fake_watcher)
        item_url = item.get("url", "")
        if item_url and not item_url.startswith("http"):
            item_url = VINTED_BASE + item_url
        item_id = item.get("id", 0)
        view    = ArticleView(item_url, item_id)

        await inter.channel.send(embed=embed, view=view)
        await asyncio.sleep(0.5)


@bot.tree.command(name="help", description="Aide CrowBot Vinted")
async def help_cmd(inter: discord.Interaction):
    e = discord.Embed(
        title="🛍️ CrowBot — Vinted Scraper v2.0",
        description="Surveille les nouvelles annonces Vinted en temps réel !",
        color=discord.Color.blurple(),
    )
    e.add_field(
        name="📌 Commandes",
        value=(
            "`/vinted` — Démarrer une surveillance\n"
            "`/vinted_stop` — Arrêter via menu déroulant\n"
            "`/vinted_stop_all` — Tout arrêter (Admin)\n"
            "`/vinted_list` — Voir les surveillances actives\n"
            "`/vinted_stats` — Statistiques du scraper\n"
            "`/vinted_categories` — Toutes les catégories\n"
            "`/vinted_test` — Tester une catégorie"
        ),
        inline=False,
    )
    e.add_field(
        name="🆕 Nouveautés v2.0",
        value=(
            "• **Filtre prix** min/max par surveillance\n"
            "• **Retry automatique** sur erreurs réseau\n"
            "• **Rate limiting** intelligent (anti-ban)\n"
            "• **Rotation User-Agent** anti-détection\n"
            "• **Statistiques** par watcher\n"
            f"• **Limite** {MAX_WATCHERS_GUILD} surveillances/serveur"
        ),
        inline=False,
    )
    e.add_field(name="⏱️ Fréquence",   value=f"~{SCRAPE_INTERVAL} secondes", inline=True)
    e.add_field(name="💾 Persistance", value="Survit aux redémarrages",       inline=True)
    e.add_field(name="🔄 Retry",       value=f"{MAX_RETRIES} tentatives",     inline=True)
    e.set_footer(text="CrowBot Vinted Scraper v2.0")
    await inter.response.send_message(embed=e, ephemeral=True)


# Gestion erreurs commandes
@vinted_stop_all.error
async def stop_all_error(inter: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await inter.response.send_message(
            "❌ Commande réservée aux **administrateurs**.", ephemeral=True)

# ─────────────────────────────────────────────
#  LANCEMENT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        log.critical("❌ DISCORD_TOKEN manquant dans .env")
        exit(1)

    try:
        bot.run(TOKEN, log_handler=None)  # on gère le logging nous-mêmes
    except KeyboardInterrupt:
        log.info("Arrêt demandé (Ctrl+C)")
    finally:
        # Nettoyage asynchrone
        asyncio.get_event_loop().run_until_complete(shutdown())
