import re
import json
import os
import asyncio
import traceback
import logging
import sys
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError, RetryAfter

# ─────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  HARDCODED CREDENTIALS  (no env vars needed)
# ─────────────────────────────────────────────────────────────
BOT_TOKEN     = "8678706957:AAFhh-j91XA7_fcu_Be6SE6REkyisDHVXAA"
IVAS_EMAIL    = "tawandamahachi07@gmail.com"
IVAS_PASSWORD = "mahachi2007"
ADMIN_IDS     = ["8339856952"]
INITIAL_CHATS = ["-1003854641278"]

# ─────────────────────────────────────────────────────────────
#  SITE URLS
# ─────────────────────────────────────────────────────────────
BASE_URL     = "https://www.ivasms.com"
LOGIN_URL    = "https://www.ivasms.com/login"
PORTAL_URL   = "https://www.ivasms.com/portal/sms/received"
SMS_URL      = "https://www.ivasms.com/portal/sms/received/getsms"
NUMBERS_URL  = "https://www.ivasms.com/portal/sms/received/getsms/number"
SMS_DETAIL   = "https://www.ivasms.com/portal/sms/received/getsms/number/sms"

# ─────────────────────────────────────────────────────────────
#  FILE PATHS
# ─────────────────────────────────────────────────────────────
DATA_DIR      = "/data" if os.path.isdir("/data") else "."
STATE_FILE    = os.path.join(DATA_DIR, "seen.json")
CHATS_FILE    = os.path.join(DATA_DIR, "chats.json")
PROFILE_DIR   = os.path.join(DATA_DIR, "chrome_profile")

# ─────────────────────────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────────────────────────
POLL_INTERVAL = 30   # seconds between each SMS check

# ─────────────────────────────────────────────────────────────
#  TELEGRAM BUTTONS  (shown on every message)
# ─────────────────────────────────────────────────────────────
BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 NUMBER CHANNEL", url="https://t.me/mrafrixtech")],
    [InlineKeyboardButton("📡 BACKUP CHANNEL",  url="https://t.me/auroratechinc")],
    [InlineKeyboardButton("🔑 OTP GROUP",        url="https://t.me/afrixotpgc")],
    [InlineKeyboardButton("👨‍💻 CONTACT DEV",     url="https://t.me/jaden_afrix")],
])

# ─────────────────────────────────────────────────────────────
#  COUNTRY FLAGS
# ─────────────────────────────────────────────────────────────
COUNTRY_FLAGS = {
    "Afghanistan": "🇦🇫", "Albania": "🇦🇱", "Algeria": "🇩🇿", "Angola": "🇦🇴",
    "Argentina": "🇦🇷", "Armenia": "🇦🇲", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Azerbaijan": "🇦🇿", "Bahrain": "🇧🇭", "Bangladesh": "🇧🇩", "Belarus": "🇧🇾",
    "Belgium": "🇧🇪", "Benin": "🇧🇯", "Bolivia": "🇧🇴", "Brazil": "🇧🇷",
    "Bulgaria": "🇧🇬", "Cambodia": "🇰🇭", "Cameroon": "🇨🇲", "Canada": "🇨🇦",
    "Chad": "🇹🇩", "Chile": "🇨🇱", "China": "🇨🇳", "Colombia": "🇨🇴",
    "Congo": "🇨🇬", "Croatia": "🇭🇷", "Cuba": "🇨🇺", "Cyprus": "🇨🇾",
    "Czech Republic": "🇨🇿", "Denmark": "🇩🇰", "Egypt": "🇪🇬", "Estonia": "🇪🇪",
    "Ethiopia": "🇪🇹", "Finland": "🇫🇮", "France": "🇫🇷", "Gabon": "🇬🇦",
    "Gambia": "🇬🇲", "Georgia": "🇬🇪", "Germany": "🇩🇪", "Ghana": "🇬🇭",
    "Greece": "🇬🇷", "Guatemala": "🇬🇹", "Guinea": "🇬🇳", "Haiti": "🇭🇹",
    "Honduras": "🇭🇳", "Hong Kong": "🇭🇰", "Hungary": "🇭🇺", "Iceland": "🇮🇸",
    "India": "🇮🇳", "Indonesia": "🇮🇩", "Iran": "🇮🇷", "Iraq": "🇮🇶",
    "Ireland": "🇮🇪", "Israel": "🇮🇱", "Italy": "🇮🇹", "Ivory Coast": "🇨🇮",
    "IVORY COAST": "🇨🇮", "Jamaica": "🇯🇲", "Japan": "🇯🇵", "Jordan": "🇯🇴",
    "Kazakhstan": "🇰🇿", "Kenya": "🇰🇪", "Kuwait": "🇰🇼", "Kyrgyzstan": "🇰🇬",
    "Laos": "🇱🇦", "Latvia": "🇱🇻", "Lebanon": "🇱🇧", "Liberia": "🇱🇷",
    "Libya": "🇱🇾", "Lithuania": "🇱🇹", "Luxembourg": "🇱🇺", "Madagascar": "🇲🇬",
    "Malaysia": "🇲🇾", "Mali": "🇲🇱", "Malta": "🇲🇹", "Mexico": "🇲🇽",
    "Moldova": "🇲🇩", "Monaco": "🇲🇨", "Mongolia": "🇲🇳", "Montenegro": "🇲🇪",
    "Morocco": "🇲🇦", "Mozambique": "🇲🇿", "Myanmar": "🇲🇲", "Namibia": "🇳🇦",
    "Nepal": "🇳🇵", "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Nicaragua": "🇳🇮",
    "Niger": "🇳🇪", "Nigeria": "🇳🇬", "North Korea": "🇰🇵", "North Macedonia": "🇲🇰",
    "Norway": "🇳🇴", "Oman": "🇴🇲", "Pakistan": "🇵🇰", "Panama": "🇵🇦",
    "Paraguay": "🇵🇾", "Peru": "🇵🇪", "Philippines": "🇵🇭", "Poland": "🇵🇱",
    "Portugal": "🇵🇹", "Qatar": "🇶🇦", "Romania": "🇷🇴", "Russia": "🇷🇺",
    "Rwanda": "🇷🇼", "Saudi Arabia": "🇸🇦", "Senegal": "🇸🇳", "Serbia": "🇷🇸",
    "Sierra Leone": "🇸🇱", "Singapore": "🇸🇬", "Slovakia": "🇸🇰", "Slovenia": "🇸🇮",
    "Somalia": "🇸🇴", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸",
    "Sri Lanka": "🇱🇰", "Sudan": "🇸🇩", "Sweden": "🇸🇪", "Switzerland": "🇨🇭",
    "Syria": "🇸🇾", "Taiwan": "🇹🇼", "Tajikistan": "🇹🇯", "Tanzania": "🇹🇿",
    "Thailand": "🇹🇭", "Togo": "🇹🇬", "TOGO": "🇹🇬", "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷", "Turkmenistan": "🇹🇲", "Uganda": "🇺🇬", "Ukraine": "🇺🇦",
    "United Arab Emirates": "🇦🇪", "United Kingdom": "🇬🇧", "United States": "🇺🇸",
    "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿", "Venezuela": "🇻🇪", "Vietnam": "🇻🇳",
    "Yemen": "🇾🇪", "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼",
}

# ─────────────────────────────────────────────────────────────
#  SERVICE DETECTION
# ─────────────────────────────────────────────────────────────
SERVICE_KEYWORDS = {
    "Facebook":     ["facebook"],
    "Google":       ["google", "gmail"],
    "WhatsApp":     ["whatsapp"],
    "Telegram":     ["telegram"],
    "Instagram":    ["instagram"],
    "Amazon":       ["amazon"],
    "Netflix":      ["netflix"],
    "LinkedIn":     ["linkedin"],
    "Microsoft":    ["microsoft", "outlook", "live.com"],
    "Apple":        ["apple", "icloud"],
    "Twitter":      ["twitter", "x.com"],
    "Snapchat":     ["snapchat"],
    "TikTok":       ["tiktok"],
    "Discord":      ["discord"],
    "Signal":       ["signal"],
    "Viber":        ["viber"],
    "IMO":          ["imo"],
    "PayPal":       ["paypal"],
    "Binance":      ["binance"],
    "Uber":         ["uber"],
    "Bolt":         ["bolt"],
    "Airbnb":       ["airbnb"],
    "Yahoo":        ["yahoo"],
    "Steam":        ["steam"],
    "Foodpanda":    ["foodpanda"],
    "Messenger":    ["messenger", "meta"],
    "YouTube":      ["youtube"],
    "eBay":         ["ebay"],
    "AliExpress":   ["aliexpress"],
    "Alibaba":      ["alibaba"],
    "Flipkart":     ["flipkart"],
    "Skype":        ["skype"],
    "Spotify":      ["spotify"],
    "Stripe":       ["stripe"],
    "Cash App":     ["cash app", "cashapp"],
    "Venmo":        ["venmo"],
    "Zelle":        ["zelle"],
    "Wise":         ["wise", "transferwise"],
    "Coinbase":     ["coinbase"],
    "KuCoin":       ["kucoin"],
    "Bybit":        ["bybit"],
    "OKX":          ["okx"],
    "Huobi":        ["huobi"],
    "Kraken":       ["kraken"],
    "MetaMask":     ["metamask"],
    "Epic Games":   ["epic games", "epicgames"],
    "PlayStation":  ["playstation", "psn"],
    "Xbox":         ["xbox"],
    "Twitch":       ["twitch"],
    "Reddit":       ["reddit"],
    "ProtonMail":   ["protonmail", "proton"],
    "Zoho":         ["zoho"],
    "Indeed":       ["indeed"],
    "Upwork":       ["upwork"],
    "Fiverr":       ["fiverr"],
    "Booking.com":  ["booking.com"],
    "Careem":       ["careem"],
    "Swiggy":       ["swiggy"],
    "Zomato":       ["zomato"],
    "McDonald's":   ["mcdonalds", "mcdonald's"],
    "KFC":          ["kfc"],
    "Shein":        ["shein"],
    "OnlyFans":     ["onlyfans"],
    "Tinder":       ["tinder"],
    "Bumble":       ["bumble"],
    "Line":         ["line app", "line:"],
    "WeChat":       ["wechat"],
    "VK":           ["vk.com", "vkontakte"],
}

SERVICE_EMOJIS = {
    "Telegram": "📩", "WhatsApp": "🟢", "Facebook": "📘", "Instagram": "📸",
    "Messenger": "💬", "Google": "🔍", "YouTube": "▶️", "Twitter": "🐦",
    "TikTok": "🎵", "Snapchat": "👻", "Amazon": "🛒", "eBay": "📦",
    "AliExpress": "📦", "Alibaba": "🏭", "Flipkart": "📦", "Microsoft": "🪟",
    "Outlook": "📧", "Skype": "📞", "Netflix": "🎬", "Spotify": "🎶",
    "Apple": "🍏", "PayPal": "💰", "Stripe": "💳", "Cash App": "💵",
    "Venmo": "💸", "Zelle": "🏦", "Wise": "🌐", "Binance": "🪙",
    "Coinbase": "🪙", "KuCoin": "🪙", "Bybit": "📈", "OKX": "🟠",
    "Huobi": "🔥", "Kraken": "🐙", "MetaMask": "🦊", "Discord": "🗨️",
    "Steam": "🎮", "Epic Games": "🕹️", "PlayStation": "🎮", "Xbox": "🎮",
    "Twitch": "📺", "Reddit": "👽", "Yahoo": "🟣", "ProtonMail": "🔐",
    "LinkedIn": "💼", "Indeed": "📋", "Upwork": "🧑‍💻", "Fiverr": "💻",
    "Airbnb": "🏠", "Booking.com": "🛏️", "Uber": "🚗", "Bolt": "🚖",
    "Careem": "🚗", "Swiggy": "🍔", "Zomato": "🍽️", "Foodpanda": "🍱",
    "McDonald's": "🍟", "KFC": "🍗", "Shein": "👗", "OnlyFans": "🔞",
    "Tinder": "🔥", "Bumble": "🐝", "Signal": "🔐", "Viber": "📞",
    "Line": "💬", "WeChat": "💬", "VK": "🌐", "Unknown": "❓",
}

# ─────────────────────────────────────────────────────────────
#  GLOBAL BROWSER STATE
#  All declared here at module level so there are zero
#  "used before global declaration" errors anywhere.
# ─────────────────────────────────────────────────────────────
_playwright   = None   # playwright instance
_browser_ctx  = None   # persistent browser context
_csrf_token   = ""     # last known CSRF token
_is_logged_in = False  # whether we have a valid session
_fail_count   = 0      # consecutive login failures


# ─────────────────────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def escape_md(text: str) -> str:
    """Escape all MarkdownV2 special characters."""
    return re.sub(r'([_*\[\]()~`>#+=|{}.!\-\\])', r'\\\1', str(text))


def read_json(path: str, default):
    """Read a JSON file safely, returning default if missing or corrupt."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: str, data) -> None:
    """Write data to a JSON file, creating directories as needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_chats() -> list:
    data = read_json(CHATS_FILE, None)
    if data is None:
        write_json(CHATS_FILE, INITIAL_CHATS)
        return list(INITIAL_CHATS)
    return data


def save_chats(chats: list) -> None:
    write_json(CHATS_FILE, chats)


def load_seen() -> set:
    return set(read_json(STATE_FILE, []))


def mark_seen(uid: str) -> None:
    seen = load_seen()
    seen.add(uid)
    # Keep only the last 5000 entries so the file never grows unbounded
    trimmed = list(seen)[-5000:]
    write_json(STATE_FILE, trimmed)


def detect_service(sms_text: str) -> str:
    lower = sms_text.lower()
    for name, keywords in SERVICE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return name
    return "Unknown"


def extract_code(sms_text: str) -> str:
    # Try dashed format first: 123-456
    m = re.search(r'\b(\d{3}-\d{3})\b', sms_text)
    if m:
        return m.group(1)
    # Then plain 4-8 digit number
    m = re.search(r'\b(\d{4,8})\b', sms_text)
    return m.group(1) if m else "N/A"


def get_flag(country: str) -> str:
    flag = COUNTRY_FLAGS.get(country)
    if flag:
        return flag
    # Try title-cased version as fallback
    flag = COUNTRY_FLAGS.get(country.title())
    return flag if flag else "🏴‍☠️"


def is_admin(user_id) -> bool:
    return str(user_id) in ADMIN_IDS


# ─────────────────────────────────────────────────────────────
#  BROWSER MANAGEMENT
# ─────────────────────────────────────────────────────────────
async def launch_browser() -> None:
    """Start Playwright and open a persistent Chromium browser context."""
    global _playwright, _browser_ctx

    log.info("Launching Chromium browser …")
    _playwright = await async_playwright().start()
    _browser_ctx = await _playwright.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-extensions",
        ],
        ignore_https_errors=True,
        java_script_enabled=True,
        bypass_csp=True,
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="America/New_York",
    )

    # Inject stealth script to hide automation fingerprints
    await _browser_ctx.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins',   {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
    """)
    log.info("Browser ready.")


async def close_browser() -> None:
    """Cleanly close browser and playwright."""
    global _playwright, _browser_ctx
    if _browser_ctx:
        try:
            await _browser_ctx.close()
        except Exception:
            pass
        _browser_ctx = None
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None


# ─────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────
async def do_login() -> bool:
    """
    Open a real browser page, navigate to the login form,
    fill credentials, submit, and confirm we landed on the dashboard.
    Returns True on success, False on failure.
    """
    global _csrf_token, _is_logged_in, _fail_count

    # Make sure browser is running
    if _browser_ctx is None:
        await launch_browser()

    log.info("Logging in to iVAS SMS …")
    page = await _browser_ctx.new_page()

    try:
        # Go to login page
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

        # Wait up to 30 s for Cloudflare challenge to pass
        for attempt in range(6):
            email_input = await page.query_selector('input[name="email"]')
            if email_input:
                break
            log.info("  Cloudflare challenge — waiting 5s … (%d/6)", attempt + 1)
            await asyncio.sleep(5)
        else:
            log.warning("  Login form never appeared — Cloudflare blocked us.")
            _fail_count += 1
            _is_logged_in = False
            return False

        # Type credentials with realistic delays so CF bot-score stays low
        await page.fill('input[name="email"]', "")
        await page.type('input[name="email"]', IVAS_EMAIL, delay=70)
        await asyncio.sleep(0.5)

        await page.fill('input[name="password"]', "")
        await page.type('input[name="password"]', IVAS_PASSWORD, delay=55)
        await asyncio.sleep(0.4)

        # Click submit
        await page.click('button[type="submit"]')

        # Wait for redirect away from the login page
        try:
            await page.wait_for_url(
                lambda url: "login" not in url,
                timeout=25_000,
            )
        except Exception:
            body = await page.inner_text("body")
            if "invalid" in body.lower() or "credentials" in body.lower():
                log.error("  Wrong credentials — check IVAS_EMAIL / IVAS_PASSWORD.")
            else:
                log.warning("  Redirect never happened after submit.")
            _fail_count += 1
            _is_logged_in = False
            return False

        # Extract CSRF token from dashboard meta tag
        token = await page.evaluate(
            'document.querySelector(\'meta[name="csrf-token"]\')?.content ?? ""'
        )
        if token:
            _csrf_token = token
            log.info("  Login OK. CSRF: %s…", _csrf_token[:12])
        else:
            log.warning("  Logged in but no CSRF token found on dashboard.")

        _fail_count   = 0
        _is_logged_in = True
        return True

    except Exception as exc:
        log.error("  Login exception: %s", exc)
        _fail_count   += 1
        _is_logged_in  = False
        return False

    finally:
        await page.close()


async def refresh_csrf() -> str:
    """
    Navigate to the portal page in a background page to grab
    a fresh CSRF token without disrupting anything else.
    Returns the token string (may be empty on failure).
    """
    global _csrf_token, _is_logged_in

    if _browser_ctx is None:
        return ""

    page = await _browser_ctx.new_page()
    try:
        await page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=30_000)

        # If we got redirected back to login, session has expired
        if "login" in page.url:
            log.warning("  Session expired (redirected to login).")
            _is_logged_in = False
            _csrf_token   = ""
            return ""

        token = await page.evaluate(
            'document.querySelector(\'meta[name="csrf-token"]\')?.content ?? ""'
        )
        if token:
            _csrf_token = token

        return _csrf_token

    except Exception as exc:
        log.error("  refresh_csrf error: %s", exc)
        return _csrf_token

    finally:
        await page.close()


# ─────────────────────────────────────────────────────────────
#  SMS FETCHING
# ─────────────────────────────────────────────────────────────
async def fetch_sms() -> list:
    """
    Use the browser's authenticated session to POST to the iVAS API
    and return a list of SMS message dicts.
    All global variables are declared at the TOP of this function.
    """
    global _csrf_token, _is_logged_in

    # Guard: if not logged in or browser not ready, return empty
    if not _is_logged_in or _browser_ctx is None:
        return []

    # Make sure we have a CSRF token
    token = _csrf_token
    if not token:
        log.info("  No CSRF token cached — refreshing …")
        token = await refresh_csrf()
    if not token:
        log.warning("  Still no CSRF token — skipping this cycle.")
        return []

    today    = datetime.utcnow()
    from_str = (today - timedelta(days=1)).strftime("%m/%d/%Y")
    to_str   = today.strftime("%m/%d/%Y")

    try:
        # ── Step 1: Get the list of country/group IDs ──
        resp = await _browser_ctx.request.post(
            SMS_URL,
            form={"from": from_str, "to": to_str, "_token": token},
        )

        # Handle session expiry
        if resp.status == 419:
            log.warning("  CSRF expired (419) — refreshing …")
            _csrf_token = ""
            await refresh_csrf()
            return []

        if not resp.ok:
            log.warning("  SMS endpoint returned HTTP %d", resp.status)
            return []

        soup       = BeautifulSoup(await resp.text(), "html.parser")
        group_divs = soup.find_all("div", {"class": "pointer"})
        if not group_divs:
            return []

        # Parse group IDs from onclick attributes
        group_ids = []
        for div in group_divs:
            onclick = div.get("onclick", "")
            m = re.search(r"getDetials\('(.+?)'\)", onclick)
            if m:
                group_ids.append(m.group(1))

        messages = []

        # ── Step 2: For each group, get phone numbers ──
        for gid in group_ids:
            try:
                num_resp = await _browser_ctx.request.post(
                    NUMBERS_URL,
                    form={
                        "start":  from_str,
                        "end":    to_str,
                        "range":  gid,
                        "_token": token,
                    },
                )
                if not num_resp.ok:
                    continue

                num_soup    = BeautifulSoup(await num_resp.text(), "html.parser")
                number_divs = num_soup.select("div[onclick*='getDetialsNumber']")

                # ── Step 3: For each number, get SMS messages ──
                for ndiv in number_divs:
                    phone = ndiv.text.strip()
                    if not phone:
                        continue

                    sms_resp = await _browser_ctx.request.post(
                        SMS_DETAIL,
                        form={
                            "start":  from_str,
                            "end":    to_str,
                            "Number": phone,
                            "Range":  gid,
                            "_token": token,
                        },
                    )
                    if not sms_resp.ok:
                        continue

                    sms_soup  = BeautifulSoup(await sms_resp.text(), "html.parser")
                    sms_cards = sms_soup.find_all("div", class_="card-body")

                    for card in sms_cards:
                        p = card.find("p", class_="mb-0")
                        if not p:
                            continue

                        sms_text = p.get_text(separator="\n").strip()
                        if not sms_text:
                            continue

                        # Derive country name from group id
                        m2      = re.match(r"([a-zA-Z\s]+)", gid)
                        country = m2.group(1).strip() if m2 else gid.strip()

                        service = detect_service(sms_text)
                        code    = extract_code(sms_text)
                        flag    = get_flag(country)
                        emoji   = SERVICE_EMOJIS.get(service, "❓")

                        messages.append({
                            "id":      f"{phone}|{sms_text[:80]}",
                            "time":    datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                            "number":  phone,
                            "country": country,
                            "flag":    flag,
                            "service": service,
                            "emoji":   emoji,
                            "code":    code,
                            "sms":     sms_text,
                        })

            except Exception as group_err:
                log.error("  Error in group %s: %s", gid, group_err)
                continue

        return messages

    except Exception as exc:
        log.error("  fetch_sms error: %s", exc)
        traceback.print_exc()
        return []


# ─────────────────────────────────────────────────────────────
#  TELEGRAM: SEND OTP MESSAGE
# ─────────────────────────────────────────────────────────────
async def send_otp(bot, chat_id: str, msg: dict) -> None:
    """Send a formatted OTP message to a Telegram chat."""

    text = (
        f"🔔 *New OTP Received*\n\n"
        f"📞 *Number:* `{escape_md(msg['number'])}`\n"
        f"🔑 *Code:* `{escape_md(msg['code'])}`\n"
        f"🏆 *Service:* {msg['emoji']} {escape_md(msg['service'])}\n"
        f"🌎 *Country:* {escape_md(msg['country'])} {msg['flag']}\n"
        f"⏳ *Time:* {escape_md(msg['time'])}\n\n"
        f"💬 *Message:*\n{escape_md(msg['sms'])}"
    )

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=BUTTONS,
        )
    except RetryAfter as e:
        # Telegram rate limit — wait and retry once
        await asyncio.sleep(e.retry_after + 1)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="MarkdownV2",
                reply_markup=BUTTONS,
            )
        except Exception:
            pass
    except Exception:
        # MarkdownV2 parse error — fall back to plain text
        try:
            plain = (
                f"New OTP Received\n\n"
                f"Number:  {msg['number']}\n"
                f"Code:    {msg['code']}\n"
                f"Service: {msg['service']}\n"
                f"Country: {msg['country']} {msg['flag']}\n"
                f"Time:    {msg['time']}\n\n"
                f"Message:\n{msg['sms']}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=plain,
                reply_markup=BUTTONS,
            )
        except Exception as fallback_err:
            log.error("  Could not send to %s: %s", chat_id, fallback_err)


# ─────────────────────────────────────────────────────────────
#  MAIN POLLING LOOP
# ─────────────────────────────────────────────────────────────
async def poll_loop(bot) -> None:
    """
    The heart of the bot. Runs forever:
      1. Make sure we are logged in.
      2. Fetch SMS messages.
      3. Send any new ones to all registered Telegram chats.
      4. Sleep, then repeat.
    """
    global _fail_count, _is_logged_in

    log.info("Starting poll loop …")

    # Initial login — try up to 3 times before giving up temporarily
    for attempt in range(1, 4):
        if await do_login():
            break
        wait = 30 * attempt
        log.warning("Login attempt %d/3 failed — waiting %ds …", attempt, wait)
        await asyncio.sleep(wait)
    else:
        log.error("Could not log in after 3 attempts. Will keep retrying in the loop.")

    # ── Endless polling ──
    while True:
        try:
            now = datetime.utcnow().strftime("%H:%M:%S")
            log.info("[%s] Polling SMS …", now)

            # Re-login if needed
            if not _is_logged_in or _fail_count >= 3:
                log.info("Session gone — re-logging in …")
                success = await do_login()
                if not success:
                    backoff = min(60 * max(_fail_count, 1), 300)
                    log.warning("Re-login failed — backing off %ds.", backoff)
                    await asyncio.sleep(backoff)
                    continue

            # Fetch messages
            messages = await fetch_sms()

            if not messages:
                log.info("  No messages found this cycle.")
            else:
                seen      = load_seen()
                chats     = load_chats()
                new_count = 0

                for msg in reversed(messages):   # oldest first
                    if msg["id"] in seen:
                        continue
                    new_count += 1
                    log.info(
                        "  → New OTP | %s | %s | code=%s",
                        msg["number"], msg["service"], msg["code"],
                    )
                    for cid in chats:
                        await send_otp(bot, cid, msg)
                    mark_seen(msg["id"])

                if new_count:
                    log.info("  Dispatched %d new OTP(s).", new_count)
                else:
                    log.info("  All messages already seen.")

        except Exception as exc:
            log.error("poll_loop unhandled error: %s", exc)
            traceback.print_exc()

        # Wait before next cycle
        await asyncio.sleep(POLL_INTERVAL)


# ─────────────────────────────────────────────────────────────
#  TELEGRAM COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.message.from_user.id
    if is_admin(uid):
        await update.message.reply_text(
            "Welcome Admin\\!\n\n"
            "`/add_chat <id>` — Add a chat ID\n"
            "`/remove_chat <id>` — Remove a chat ID\n"
            "`/list_chats` — Show all chats\n"
            "`/status` — Live bot status",
            parse_mode="MarkdownV2",
            reply_markup=BUTTONS,
        )
    else:
        await update.message.reply_text(
            "You are not authorized to use this bot\\.",
            parse_mode="MarkdownV2",
            reply_markup=BUTTONS,
        )


async def cmd_add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        return await update.message.reply_text("Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /add\\_chat \\<chat\\_id\\>", parse_mode="MarkdownV2")

    cid   = context.args[0]
    chats = load_chats()
    if cid in chats:
        return await update.message.reply_text(
            f"`{escape_md(cid)}` is already registered\\.", parse_mode="MarkdownV2"
        )
    chats.append(cid)
    save_chats(chats)
    await update.message.reply_text(f"✅ Added `{escape_md(cid)}`\\.", parse_mode="MarkdownV2")


async def cmd_remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        return await update.message.reply_text("Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /remove\\_chat \\<chat\\_id\\>", parse_mode="MarkdownV2")

    cid   = context.args[0]
    chats = load_chats()
    if cid not in chats:
        return await update.message.reply_text(
            f"`{escape_md(cid)}` not found\\.", parse_mode="MarkdownV2"
        )
    chats.remove(cid)
    save_chats(chats)
    await update.message.reply_text(f"✅ Removed `{escape_md(cid)}`\\.", parse_mode="MarkdownV2")


async def cmd_list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        return await update.message.reply_text("Admins only.")
    chats = load_chats()
    if not chats:
        return await update.message.reply_text("No chats registered yet.")
    lines = "\n".join(f"• `{escape_md(c)}`" for c in chats)
    await update.message.reply_text(
        f"📜 *Registered Chats:*\n\n{lines}", parse_mode="MarkdownV2"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        return

    browser = "✅ Running" if _browser_ctx else "❌ Down"
    session = "✅ Active"  if _is_logged_in else "❌ Logged out"
    csrf    = "✅ Present" if _csrf_token   else "❌ Missing"

    await update.message.reply_text(
        f"*Bot Status*\n\n"
        f"Browser: {browser}\n"
        f"Session: {session}\n"
        f"CSRF:    {csrf}\n"
        f"Fails:   {_fail_count}\n"
        f"Chats:   {len(load_chats())}\n"
        f"Seen:    {len(load_seen())} IDs\n\n"
        f"Email: `{escape_md(IVAS_EMAIL)}`",
        parse_mode="MarkdownV2",
    )


# ─────────────────────────────────────────────────────────────
#  TELEGRAM ERROR HANDLER
# ─────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, Conflict):
        # Two instances of the bot running simultaneously (Railway rolling deploy)
        log.warning("Telegram Conflict — waiting 30s for old instance to die …")
        await asyncio.sleep(30)
    elif isinstance(err, (TimedOut, NetworkError)):
        log.warning("Telegram network error (will auto-recover): %s", err)
    else:
        log.error("Unhandled Telegram error: %s", err)


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
async def main() -> None:
    log.info("=" * 55)
    log.info("iVAS SMS → Telegram Bot")
    log.info("Email : %s", IVAS_EMAIL)
    log.info("Admin : %s", ADMIN_IDS)
    log.info("Chats : %s", load_chats())
    log.info("=" * 55)

    # Start the browser
    await launch_browser()

    # Build the Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Register commands
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("add_chat",    cmd_add_chat))
    app.add_handler(CommandHandler("remove_chat", cmd_remove_chat))
    app.add_handler(CommandHandler("list_chats",  cmd_list_chats))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_error_handler(error_handler)

    # Run everything
    async with app:
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message"],
        )
        log.info("Bot is live. Polling SMS every %ds.", POLL_INTERVAL)
        try:
            await poll_loop(app.bot)
        finally:
            await app.updater.stop()
            await app.stop()
            await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
