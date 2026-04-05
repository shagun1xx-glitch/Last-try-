import re
import json
import os
import asyncio
import traceback
import logging
import sys
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError, RetryAfter

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

BOT_TOKEN     = "8729407620:AAFj37OrvH03YFHNS_p2KgtFWLIakrNQwNY"
IVAS_EMAIL    = "shagunkumar060q@gmail.com"
IVAS_PASSWORD = "Sh@gun1234567890"
ADMIN_IDS     = ["8544485437"]
INITIAL_CHATS = ["-1003887159426"]

LOGIN_URL    = "https://www.ivasms.com/login"
PORTAL_URL   = "https://www.ivasms.com/portal/sms/received"
SMS_URL      = "https://www.ivasms.com/portal/sms/received/getsms"
NUMBERS_URL  = "https://www.ivasms.com/portal/sms/received/getsms/number"
SMS_DETAIL   = "https://www.ivasms.com/portal/sms/received/getsms/number/sms"

DATA_DIR     = "/data" if os.path.isdir("/data") else "."
STATE_FILE   = os.path.join(DATA_DIR, "seen.json")
CHATS_FILE   = os.path.join(DATA_DIR, "chats.json")
COOKIES_FILE = os.path.join(DATA_DIR, "cookies.json")
DEBUG_SS     = os.path.join(DATA_DIR, "debug.png")
DEBUG_HTML   = os.path.join(DATA_DIR, "debug.html")

POLL_SECS = 30

BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 NUMBER CHANNEL", url="https://t.me/kitenumber")],
    [InlineKeyboardButton("📡 BACKUP CHANNEL",  url="https://t.me/auroratechinc")],
    [InlineKeyboardButton("🔑 OTP GROUP",        url="https://t.me/afrixotpgc")],
    [InlineKeyboardButton("👨‍💻 CONTACT DEV",     url="https://t.me/jaden_afrix")],
])

COUNTRY_FLAGS = {
    "Afghanistan":"🇦🇫","Albania":"🇦🇱","Algeria":"🇩🇿","Angola":"🇦🇴","Argentina":"🇦🇷",
    "Armenia":"🇦🇲","Australia":"🇦🇺","Austria":"🇦🇹","Azerbaijan":"🇦🇿","Bahrain":"🇧🇭",
    "Bangladesh":"🇧🇩","Belarus":"🇧🇾","Belgium":"🇧🇪","Benin":"🇧🇯","Bolivia":"🇧🇴",
    "Brazil":"🇧🇷","Bulgaria":"🇧🇬","Cambodia":"🇰🇭","Cameroon":"🇨🇲","Canada":"🇨🇦",
    "Chad":"🇹🇩","Chile":"🇨🇱","China":"🇨🇳","Colombia":"🇨🇴","Congo":"🇨🇬",
    "Croatia":"🇭🇷","Cuba":"🇨🇺","Cyprus":"🇨🇾","Czech Republic":"🇨🇿","Denmark":"🇩🇰",
    "Egypt":"🇪🇬","Estonia":"🇪🇪","Ethiopia":"🇪🇹","Finland":"🇫🇮","France":"🇫🇷",
    "Gabon":"🇬🇦","Gambia":"🇬🇲","Georgia":"🇬🇪","Germany":"🇩🇪","Ghana":"🇬🇭",
    "Greece":"🇬🇷","Guatemala":"🇬🇹","Guinea":"🇬🇳","Haiti":"🇭🇹","Honduras":"🇭🇳",
    "Hong Kong":"🇭🇰","Hungary":"🇭🇺","Iceland":"🇮🇸","India":"🇮🇳","Indonesia":"🇮🇩",
    "Iran":"🇮🇷","Iraq":"🇮🇶","Ireland":"🇮🇪","Israel":"🇮🇱","Italy":"🇮🇹",
    "Ivory Coast":"🇨🇮","IVORY COAST":"🇨🇮","Jamaica":"🇯🇲","Japan":"🇯🇵","Jordan":"🇯🇴",
    "Kazakhstan":"🇰🇿","Kenya":"🇰🇪","Kuwait":"🇰🇼","Kyrgyzstan":"🇰🇬","Laos":"🇱🇦",
    "Latvia":"🇱🇻","Lebanon":"🇱🇧","Liberia":"🇱🇷","Libya":"🇱🇾","Lithuania":"🇱🇹",
    "Luxembourg":"🇱🇺","Madagascar":"🇲🇬","Malaysia":"🇲🇾","Mali":"🇲🇱","Malta":"🇲🇹",
    "Mexico":"🇲🇽","Moldova":"🇲🇩","Monaco":"🇲🇨","Mongolia":"🇲🇳","Montenegro":"🇲🇪",
    "Morocco":"🇲🇦","Mozambique":"🇲🇿","Myanmar":"🇲🇲","Namibia":"🇳🇦","Nepal":"🇳🇵",
    "Netherlands":"🇳🇱","New Zealand":"🇳🇿","Nicaragua":"🇳🇮","Niger":"🇳🇪","Nigeria":"🇳🇬",
    "North Korea":"🇰🇵","North Macedonia":"🇲🇰","Norway":"🇳🇴","Oman":"🇴🇲","Pakistan":"🇵🇰",
    "Panama":"🇵🇦","Paraguay":"🇵🇾","Peru":"🇵🇪","Philippines":"🇵🇭","Poland":"🇵🇱",
    "Portugal":"🇵🇹","Qatar":"🇶🇦","Romania":"🇷🇴","Russia":"🇷🇺","Rwanda":"🇷🇼",
    "Saudi Arabia":"🇸🇦","Senegal":"🇸🇳","Serbia":"🇷🇸","Sierra Leone":"🇸🇱",
    "Singapore":"🇸🇬","Slovakia":"🇸🇰","Slovenia":"🇸🇮","Somalia":"🇸🇴",
    "South Africa":"🇿🇦","South Korea":"🇰🇷","Spain":"🇪🇸","Sri Lanka":"🇱🇰",
    "Sudan":"🇸🇩","Sweden":"🇸🇪","Switzerland":"🇨🇭","Syria":"🇸🇾","Taiwan":"🇹🇼",
    "Tajikistan":"🇹🇯","Tanzania":"🇹🇿","Thailand":"🇹🇭","Togo":"🇹🇬","TOGO":"🇹🇬",
    "Tunisia":"🇹🇳","Turkey":"🇹🇷","Turkmenistan":"🇹🇲","Uganda":"🇺🇬","Ukraine":"🇺🇦",
    "United Arab Emirates":"🇦🇪","United Kingdom":"🇬🇧","United States":"🇺🇸",
    "Uruguay":"🇺🇾","Uzbekistan":"🇺🇿","Venezuela":"🇻🇪","Vietnam":"🇻🇳",
    "Yemen":"🇾🇪","Zambia":"🇿🇲","Zimbabwe":"🇿🇼",
}

SERVICE_KEYWORDS = {
    "Facebook":    ["facebook"],
    "Google":      ["google","gmail"],
    "WhatsApp":    ["whatsapp"],
    "Telegram":    ["telegram"],
    "Instagram":   ["instagram"],
    "Amazon":      ["amazon"],
    "Netflix":     ["netflix"],
    "LinkedIn":    ["linkedin"],
    "Microsoft":   ["microsoft","outlook","live.com"],
    "Apple":       ["apple","icloud"],
    "Twitter":     ["twitter","x.com"],
    "Snapchat":    ["snapchat"],
    "TikTok":      ["tiktok"],
    "Discord":     ["discord"],
    "Signal":      ["signal"],
    "Viber":       ["viber"],
    "IMO":         ["imo"],
    "PayPal":      ["paypal"],
    "Binance":     ["binance"],
    "Uber":        ["uber"],
    "Bolt":        ["bolt"],
    "Airbnb":      ["airbnb"],
    "Yahoo":       ["yahoo"],
    "Steam":       ["steam"],
    "Foodpanda":   ["foodpanda"],
    "Messenger":   ["messenger","meta"],
    "YouTube":     ["youtube"],
    "eBay":        ["ebay"],
    "AliExpress":  ["aliexpress"],
    "Alibaba":     ["alibaba"],
    "Flipkart":    ["flipkart"],
    "Skype":       ["skype"],
    "Spotify":     ["spotify"],
    "Stripe":      ["stripe"],
    "Cash App":    ["cash app","cashapp"],
    "Venmo":       ["venmo"],
    "Zelle":       ["zelle"],
    "Wise":        ["wise","transferwise"],
    "Coinbase":    ["coinbase"],
    "KuCoin":      ["kucoin"],
    "Bybit":       ["bybit"],
    "OKX":         ["okx"],
    "Huobi":       ["huobi"],
    "Kraken":      ["kraken"],
    "MetaMask":    ["metamask"],
    "Epic Games":  ["epic games","epicgames"],
    "PlayStation": ["playstation","psn"],
    "Xbox":        ["xbox"],
    "Twitch":      ["twitch"],
    "Reddit":      ["reddit"],
    "ProtonMail":  ["protonmail","proton"],
    "Zoho":        ["zoho"],
    "Indeed":      ["indeed"],
    "Upwork":      ["upwork"],
    "Fiverr":      ["fiverr"],
    "Booking.com": ["booking.com"],
    "Careem":      ["careem"],
    "Swiggy":      ["swiggy"],
    "Zomato":      ["zomato"],
    "McDonald's":  ["mcdonalds","mcdonald's"],
    "KFC":         ["kfc"],
    "Shein":       ["shein"],
    "OnlyFans":    ["onlyfans"],
    "Tinder":      ["tinder"],
    "Bumble":      ["bumble"],
    "Line":        ["line app","line:"],
    "WeChat":      ["wechat"],
    "VK":          ["vk.com","vkontakte"],
}

SERVICE_EMOJIS = {
    "Telegram":"📩","WhatsApp":"🟢","Facebook":"📘","Instagram":"📸","Messenger":"💬",
    "Google":"🔍","YouTube":"▶️","Twitter":"🐦","TikTok":"🎵","Snapchat":"👻",
    "Amazon":"🛒","eBay":"📦","AliExpress":"📦","Alibaba":"🏭","Flipkart":"📦",
    "Microsoft":"🪟","Outlook":"📧","Skype":"📞","Netflix":"🎬","Spotify":"🎶",
    "Apple":"🍏","PayPal":"💰","Stripe":"💳","Cash App":"💵","Venmo":"💸",
    "Zelle":"🏦","Wise":"🌐","Binance":"🪙","Coinbase":"🪙","KuCoin":"🪙",
    "Bybit":"📈","OKX":"🟠","Huobi":"🔥","Kraken":"🐙","MetaMask":"🦊",
    "Discord":"🗨️","Steam":"🎮","Epic Games":"🕹️","PlayStation":"🎮","Xbox":"🎮",
    "Twitch":"📺","Reddit":"👽","Yahoo":"🟣","ProtonMail":"🔐","LinkedIn":"💼",
    "Indeed":"📋","Upwork":"🧑‍💻","Fiverr":"💻","Airbnb":"🏠","Booking.com":"🛏️",
    "Uber":"🚗","Bolt":"🚖","Careem":"🚗","Swiggy":"🍔","Zomato":"🍽️",
    "Foodpanda":"🍱","McDonald's":"🍟","KFC":"🍗","Shein":"👗","OnlyFans":"🔞",
    "Tinder":"🔥","Bumble":"🐝","Signal":"🔐","Viber":"📞","Line":"💬",
    "WeChat":"💬","VK":"🌐","Unknown":"❓",
}

_pw           = None
_browser      = None
_bcontext     = None
_curl_session = None
_csrf         = ""
_logged_in    = False
_fail_count   = 0
_login_method = "none"

EXTRA_STEALTH_JS = """
    (() => {
        const NOOP = () => {};
        const RND  = () => Math.floor(Math.random() * 1000);

        Object.defineProperty(navigator, 'webdriver',           {get: () => undefined, configurable: true});
        Object.defineProperty(navigator, 'plugins',             {get: () => [1,2,3,4,5], configurable: true});
        Object.defineProperty(navigator, 'languages',           {get: () => ['en-US','en'], configurable: true});
        Object.defineProperty(navigator, 'platform',            {get: () => 'Win32', configurable: true});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8, configurable: true});
        Object.defineProperty(navigator, 'deviceMemory',        {get: () => 8, configurable: true});
        Object.defineProperty(navigator, 'maxTouchPoints',      {get: () => 0, configurable: true});
        Object.defineProperty(navigator, 'vendor',              {get: () => 'Google Inc.', configurable: true});
        Object.defineProperty(navigator, 'appVersion',          {get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', configurable: true});

        Object.defineProperty(screen, 'colorDepth',  {get: () => 24, configurable: true});
        Object.defineProperty(screen, 'pixelDepth',  {get: () => 24, configurable: true});
        Object.defineProperty(screen, 'width',       {get: () => 1280, configurable: true});
        Object.defineProperty(screen, 'height',      {get: () => 800, configurable: true});
        Object.defineProperty(screen, 'availWidth',  {get: () => 1280, configurable: true});
        Object.defineProperty(screen, 'availHeight', {get: () => 760, configurable: true});

        window.chrome = {
            app: {isInstalled: false, InstallState: {DISABLED:'a',INSTALLED:'b',NOT_INSTALLED:'c'}, RunningState: {CANNOT_RUN:'a',READY_TO_RUN:'b',RUNNING:'c'}},
            runtime: {
                PlatformOs: {MAC:'mac',WIN:'win',ANDROID:'android',CROS:'cros',LINUX:'linux',OPENBSD:'openbsd'},
                PlatformArch: {ARM:'arm',X86_32:'x86-32',X86_64:'x86-64'},
                PlatformNaclArch: {ARM:'arm',X86_32:'x86-32',X86_64:'x86-64'},
                RequestUpdateCheckStatus: {THROTTLED:'throttled',NO_UPDATE:'no_update',UPDATE_AVAILABLE:'update_available'},
                OnInstalledReason: {INSTALL:'install',UPDATE:'update',CHROME_UPDATE:'chrome_update',SHARED_MODULE_UPDATE:'shared_module_update'},
                OnRestartRequiredReason: {APP_UPDATE:'app_update',OS_UPDATE:'os_update',PERIODIC:'periodic'},
                connect:         NOOP,
                sendMessage:     NOOP,
                id:              undefined,
                onMessage:       {addListener: NOOP, removeListener: NOOP},
                onConnect:       {addListener: NOOP, removeListener: NOOP},
                onInstalled:     {addListener: NOOP, removeListener: NOOP},
            },
            loadTimes:  NOOP,
            csi:        NOOP,
        };

        window.outerHeight = 900;
        window.outerWidth  = 1440;
        window.innerHeight = 800;
        window.innerWidth  = 1280;
        window.screenX    = 0;
        window.screenY    = 0;

        try {
            const origQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
            window.navigator.permissions.__proto__.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : origQuery(parameters);
        } catch(e) {}

        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            const ctx = originalGetContext.call(this, type, ...args);
            if (type === '2d' && ctx) {
                const originalGetImageData = ctx.getImageData.bind(ctx);
                ctx.getImageData = function(x, y, w, h) {
                    const data = originalGetImageData(x, y, w, h);
                    for (let i = 0; i < data.data.length; i += 100) {
                        data.data[i] = data.data[i] ^ (RND() & 1);
                    }
                    return data;
                };
            }
            return ctx;
        };

        Object.defineProperty(HTMLElement.prototype, 'offsetParent', {
            get() { return this.parentElement; }
        });
    })();
"""


def esc(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+=|{}.!\-\\])', r'\\\1', str(text))

def rj(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def wj(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_chats():
    d = rj(CHATS_FILE, None)
    if d is None:
        wj(CHATS_FILE, INITIAL_CHATS)
        return list(INITIAL_CHATS)
    return d

def save_chats(chats):
    wj(CHATS_FILE, chats)

def load_seen():
    return set(rj(STATE_FILE, []))

def mark_seen(uid):
    seen = load_seen()
    seen.add(uid)
    wj(STATE_FILE, list(seen)[-5000:])

def save_cookies(cookies: list):
    wj(COOKIES_FILE, cookies)
    log.info("[COOKIES] Saved %d cookies.", len(cookies))

def load_cookies() -> list:
    return rj(COOKIES_FILE, [])

def detect_service(text):
    lower = text.lower()
    for name, kws in SERVICE_KEYWORDS.items():
        if any(k in lower for k in kws):
            return name
    return "Unknown"

def extract_code(text):
    m = re.search(r'\b(\d{3}-\d{3})\b', text)
    if m:
        return m.group(1)
    m = re.search(r'\b(\d{4,8})\b', text)
    return m.group(1) if m else "N/A"

def get_flag(country):
    return COUNTRY_FLAGS.get(country) or COUNTRY_FLAGS.get(country.title()) or "🏴‍☠️"

def is_admin(uid):
    return str(uid) in ADMIN_IDS

async def save_debug(page):
    try:
        await page.screenshot(path=DEBUG_SS, full_page=True)
        log.info("[DEBUG] Screenshot saved.")
    except Exception:
        pass
    try:
        html = await page.content()
        with open(DEBUG_HTML, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass

async def human_mouse_move(page):
    try:
        for _ in range(3):
            x = 200 + (hash(str(_)) % 400)
            y = 200 + (hash(str(_ * 7)) % 200)
            await page.mouse.move(x, y)
            await asyncio.sleep(0.15)
    except Exception:
        pass

async def human_type(page, selector: str, text: str, min_delay=45, max_delay=110):
    await page.click(selector)
    await page.fill(selector, "")
    await asyncio.sleep(0.3)
    for ch in text:
        delay = min_delay + (abs(hash(ch)) % (max_delay - min_delay))
        await page.keyboard.type(ch, delay=delay)
    await asyncio.sleep(0.4)


async def start_browser():
    global _pw, _browser, _bcontext
    log.info("[PW] Starting Chromium ...")
    _pw = await async_playwright().start()
    _browser = await _pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process,AutomationControlled",
            "--disable-web-security",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-popup-blocking",
            "--disable-default-apps",
            "--window-size=1280,800",
            "--start-maximized",
            "--ignore-certificate-errors",
            "--allow-running-insecure-content",
            "--disable-ipc-flooding-protection",
        ],
    )
    _bcontext = await _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="America/New_York",
        ignore_https_errors=True,
        java_script_enabled=True,
        color_scheme="light",
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        permissions=["notifications"],
    )
    await _bcontext.add_init_script(EXTRA_STEALTH_JS)
    log.info("[PW] Browser ready. Stealth: %s", "playwright-stealth" if STEALTH_AVAILABLE else "manual-only")

async def stop_browser():
    global _pw, _browser, _bcontext
    for obj in (_bcontext, _browser, _pw):
        if obj:
            try:
                await obj.close()
            except Exception:
                pass
    _pw = _browser = _bcontext = None


async def _wait_for_turnstile_token(page, timeout_secs=25) -> bool:
    log.info("[TURNSTILE] Waiting up to %ds for token ...", timeout_secs)
    deadline = asyncio.get_event_loop().time() + timeout_secs
    while asyncio.get_event_loop().time() < deadline:
        token = await page.evaluate("""
            () => {
                const byName = document.querySelector('[name="cf-turnstile-response"]');
                if (byName && byName.value) return byName.value;
                const byId = document.querySelector('#cf-turnstile-response');
                if (byId && byId.value) return byId.value;
                const textareas = document.querySelectorAll('textarea');
                for (const ta of textareas) {
                    if (ta.name && ta.name.includes('turnstile') && ta.value) return ta.value;
                }
                return '';
            }
        """)
        if token:
            log.info("[TURNSTILE] Token received! Length=%d", len(token))
            return True
        await asyncio.sleep(0.8)
    return False


async def _solve_turnstile(page) -> bool:
    log.info("[TURNSTILE] Looking for Cloudflare iframe ...")

    iframe_appeared = False
    for i in range(12):
        frames_with_cf = [f for f in page.frames if "challenges.cloudflare.com" in (f.url or "")]
        if frames_with_cf:
            iframe_appeared = True
            log.info("[TURNSTILE] CF iframe found after %ds (url: %s)", i * 2, frames_with_cf[0].url[:70])
            break
        try:
            fl = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
            ct = await fl.locator('body').count()
            if ct > 0:
                iframe_appeared = True
                break
        except Exception:
            pass
        await asyncio.sleep(2)

    if not iframe_appeared:
        log.info("[TURNSTILE] No CF iframe found — may be invisible/auto-passed or not present.")
        return True

    await asyncio.sleep(1.5)

    clicked = False
    selectors_to_try = [
        'label.ctp-checkbox-label',
        'input[type="checkbox"]',
        '.cb-lb',
        'span.mark',
        'div[class*="check"]',
        'div[class*="checkbox"]',
        'label',
        'div[class*="widget"]',
        'body',
    ]

    fl = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
    for sel in selectors_to_try:
        try:
            loc = fl.locator(sel).first
            ct  = await loc.count()
            if ct == 0:
                continue
            await loc.click(timeout=4000, force=True)
            log.info("[TURNSTILE] Clicked selector: %s", sel)
            clicked = True
            break
        except Exception as e:
            log.info("[TURNSTILE] Selector %s failed: %s", sel, str(e)[:60])
            continue

    if not clicked:
        for frame in page.frames:
            if "challenges.cloudflare.com" not in (frame.url or ""):
                continue
            for sel in ['label', 'input', 'div', 'body']:
                try:
                    el = await frame.query_selector(sel)
                    if el:
                        await el.click(force=True)
                        log.info("[TURNSTILE] Frame fallback clicked: %s", sel)
                        clicked = True
                        break
                except Exception:
                    continue
            if clicked:
                break

    if not clicked:
        log.warning("[TURNSTILE] Could not click any element — trying mouse click on iframe position.")
        try:
            iframe_el = page.locator('iframe[src*="challenges.cloudflare.com"]').first
            box = await iframe_el.bounding_box()
            if box:
                cx = box['x'] + box['width'] / 2
                cy = box['y'] + box['height'] / 2
                await page.mouse.move(cx - 20, cy - 10)
                await asyncio.sleep(0.3)
                await page.mouse.click(cx, cy)
                log.info("[TURNSTILE] Mouse-clicked iframe at (%d, %d)", cx, cy)
                clicked = True
        except Exception as e:
            log.warning("[TURNSTILE] Mouse click failed: %s", e)

    passed = await _wait_for_turnstile_token(page, timeout_secs=22)

    if passed:
        log.info("[TURNSTILE] CHALLENGE PASSED!")
        return True

    log.warning("[TURNSTILE] Token not received. Turnstile may be managed/invisible or still processing.")
    return False


async def _pw_login() -> bool:
    global _csrf, _logged_in, _fail_count, _login_method

    if _bcontext is None:
        await start_browser()

    log.info("[PW] Starting login sequence ...")
    page = await _bcontext.new_page()

    try:
        if STEALTH_AVAILABLE:
            await stealth_async(page)
            log.info("[PW] playwright-stealth applied.")

        saved = load_cookies()
        if saved:
            await _bcontext.add_cookies(saved)
            log.info("[PW] Injected %d saved cookies.", len(saved))

        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(2)
        log.info("[PW] Page loaded: %s", page.url)

        if "login" not in page.url.lower():
            log.info("[PW] Cookies still valid — already logged in at: %s", page.url)
            token = await page.evaluate(
                'document.querySelector(\'meta[name="csrf-token"]\')?.content ?? ""'
            )
            if token:
                _csrf = token
                _fail_count   = 0
                _logged_in    = True
                _login_method = "playwright"
                cookies = await _bcontext.cookies()
                save_cookies(cookies)
                return True

        log.info("[PW] STEP 1 — Waiting for Cloudflare Turnstile to appear ...")
        await human_mouse_move(page)

        turnstile_ok = await _solve_turnstile(page)
        if not turnstile_ok:
            log.warning("[PW] Turnstile may not be fully solved. Proceeding anyway ...")

        await asyncio.sleep(1)

        email_sel = 'input[name="email"]'
        email_visible = False
        for i in range(10):
            el = await page.query_selector(email_sel)
            if el and await el.is_visible():
                email_visible = True
                log.info("[PW] Login form visible after %ds.", i * 2)
                break
            await asyncio.sleep(2)

        if not email_visible:
            log.warning("[PW] Email field never appeared.")
            await save_debug(page)
            _fail_count += 1
            return False

        await human_mouse_move(page)
        await asyncio.sleep(0.5)

        log.info("[PW] STEP 2 — Typing email ...")
        await human_type(page, email_sel, IVAS_EMAIL, 50, 100)

        log.info("[PW] STEP 3 — Typing password ...")
        await human_type(page, 'input[name="password"]', IVAS_PASSWORD, 45, 95)

        pw_check = await page.evaluate(
            'document.querySelector("input[name=\'password\']")?.value ?? ""'
        )
        if not pw_check:
            log.warning("[PW] Password field cleared by page JS — refilling forcefully.")
            await page.evaluate(
                f'document.querySelector("input[name=\'password\']").value = "{IVAS_PASSWORD}"'
            )
            await asyncio.sleep(0.3)

        log.info("[PW] STEP 4 — Clicking submit button ...")
        await human_mouse_move(page)
        await asyncio.sleep(0.5)

        submit_clicked = False
        for btn_selector in [
            'button[type="submit"]',
            'button.btn-primary',
            'button.btn-login',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
        ]:
            try:
                el = page.locator(btn_selector).first
                ct = await el.count()
                if ct > 0 and await el.is_visible():
                    await el.click(timeout=5000)
                    log.info("[PW] Clicked submit: %s", btn_selector)
                    submit_clicked = True
                    break
            except Exception:
                continue

        if not submit_clicked:
            log.info("[PW] No submit button found — trying JS click ...")
            try:
                await page.evaluate("""
                    () => {
                        const btn = document.querySelector('button[type="submit"]')
                                 || document.querySelector('button.btn-primary')
                                 || document.querySelector('button');
                        if (btn) btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    }
                """)
                submit_clicked = True
                log.info("[PW] JS click dispatched.")
            except Exception as e:
                log.warning("[PW] JS click failed: %s", e)

        if not submit_clicked:
            await page.focus('input[name="password"]')
            await page.keyboard.press("Enter")
            log.info("[PW] Pressed Enter as last resort.")

        log.info("[PW] STEP 5 — Waiting for redirect away from /login ...")
        redirected = False
        try:
            await page.wait_for_function(
                "() => !window.location.href.includes('/login')",
                timeout=20_000,
            )
            redirected = True
            log.info("[PW] Redirected to: %s", page.url)
        except Exception:
            pass

        if not redirected:
            log.info("[PW] No redirect yet — pressing Enter in password field ...")
            await page.focus('input[name="password"]')
            await page.keyboard.press("Enter")
            try:
                await page.wait_for_function(
                    "() => !window.location.href.includes('/login')",
                    timeout=15_000,
                )
                redirected = True
                log.info("[PW] Redirected after Enter: %s", page.url)
            except Exception:
                pass

        if not redirected:
            body_text = ""
            try:
                body_text = (await page.inner_text("body"))[:600]
            except Exception:
                pass
            log.warning("[PW] Still on login after all attempts. URL: %s", page.url)
            log.warning("[PW] Page content: %s", body_text[:300])
            await save_debug(page)
            _fail_count += 1
            _logged_in = False
            return False

        await page.wait_for_load_state("domcontentloaded", timeout=15_000)

        token = await page.evaluate(
            'document.querySelector(\'meta[name="csrf-token"]\')?.content ?? ""'
        )
        if token:
            _csrf = token
            log.info("[PW] CSRF token: %s...", _csrf[:16])
        else:
            log.warning("[PW] No CSRF token on dashboard — will refresh next cycle.")

        cookies = await _bcontext.cookies()
        save_cookies(cookies)

        _fail_count   = 0
        _logged_in    = True
        _login_method = "playwright"
        log.info("[PW] LOGIN SUCCESS ✅")
        return True

    except Exception as exc:
        log.error("[PW] Unexpected exception: %s", exc)
        traceback.print_exc()
        try:
            await save_debug(page)
        except Exception:
            pass
        _fail_count += 1
        _logged_in = False
        return False
    finally:
        await page.close()


async def _cookie_login() -> bool:
    global _csrf, _logged_in, _login_method, _curl_session

    cookies = load_cookies()
    if not cookies:
        log.info("[COOKIE] No saved cookies.")
        return False

    log.info("[COOKIE] Testing %d saved cookies ...", len(cookies))

    try:
        if _curl_session:
            try:
                await _curl_session.close()
            except Exception:
                pass

        _curl_session = AsyncSession(
            impersonate="chrome124",
            timeout=20,
            verify=True,
            allow_redirects=True,
        )

        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie":          cookie_header,
        }

        r = await _curl_session.get(PORTAL_URL, headers=headers)

        if "login" in str(r.url).lower():
            log.info("[COOKIE] Cookies expired — redirected to login.")
            return False

        if r.status_code != 200:
            log.info("[COOKIE] Status %d — cookies invalid.", r.status_code)
            return False

        soup = BeautifulSoup(r.text, "html.parser")
        meta = soup.find("meta", {"name": "csrf-token"})
        if not meta:
            log.warning("[COOKIE] No CSRF on portal page — cookies stale.")
            return False

        _csrf         = meta.get("content", "")
        _logged_in    = True
        _login_method = "curl"
        log.info("[COOKIE] Logged in via saved cookies. CSRF: %s...", _csrf[:16])
        return True

    except Exception as e:
        log.error("[COOKIE] Exception: %s", e)
        return False


async def _curl_login() -> bool:
    global _csrf, _logged_in, _fail_count, _curl_session, _login_method

    log.info("[CURL] Attempting curl_cffi login ...")

    try:
        if _curl_session:
            try:
                await _curl_session.close()
            except Exception:
                pass

        _curl_session = AsyncSession(
            impersonate="chrome124",
            timeout=30,
            verify=True,
            allow_redirects=True,
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.9",
            "Accept-Encoding":           "gzip, deflate, br",
            "Cache-Control":             "no-cache",
            "Sec-Ch-Ua":                 '"Chromium";v="124","Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile":          "?0",
            "Sec-Ch-Ua-Platform":        '"Windows"',
            "Sec-Fetch-Dest":            "document",
            "Sec-Fetch-Mode":            "navigate",
            "Sec-Fetch-Site":            "none",
            "Upgrade-Insecure-Requests": "1",
        }

        r = await _curl_session.get(LOGIN_URL, headers=headers)
        log.info("[CURL] GET login: HTTP %d", r.status_code)

        if r.status_code not in (200, 302):
            log.warning("[CURL] CF blocking — status %d.", r.status_code)
            _fail_count += 1
            return False

        soup  = BeautifulSoup(r.text, "html.parser")
        field = soup.find("input", {"name": "_token"})
        if not field:
            log.warning("[CURL] CSRF field missing — CF blocking without JS.")
            _fail_count += 1
            return False

        csrf_token = field.get("value", "")
        log.info("[CURL] CSRF: %s...", csrf_token[:16])

        await asyncio.sleep(1.5)

        post_headers = {
            **headers,
            "Sec-Fetch-Site": "same-origin",
            "Referer":        LOGIN_URL,
            "Content-Type":   "application/x-www-form-urlencoded",
        }
        resp = await _curl_session.post(
            LOGIN_URL,
            data={
                "email":    IVAS_EMAIL,
                "password": IVAS_PASSWORD,
                "_token":   csrf_token,
            },
            headers=post_headers,
        )
        log.info("[CURL] POST: HTTP %d, URL: %s", resp.status_code, str(resp.url)[:70])

        if "login" in str(resp.url).lower():
            log.warning("[CURL] Still on login — CF Turnstile blocked POST.")
            _fail_count += 1
            _logged_in = False
            return False

        dash = BeautifulSoup(resp.text, "html.parser")
        meta = dash.find("meta", {"name": "csrf-token"})
        if meta:
            _csrf = meta.get("content", "")
            log.info("[CURL] Dashboard CSRF: %s...", _csrf[:16])
        else:
            _csrf = csrf_token

        _fail_count   = 0
        _logged_in    = True
        _login_method = "curl"
        log.info("[CURL] LOGIN SUCCESS ✅")
        return True

    except Exception as exc:
        log.error("[CURL] Exception: %s", exc)
        _fail_count += 1
        _logged_in = False
        return False


async def do_login() -> bool:
    global _logged_in

    try:
        if await _cookie_login():
            return True
    except Exception as e:
        log.error("Cookie login crashed: %s", e)

    log.info("Cookies failed → Playwright ...")
    try:
        if await _pw_login():
            return True
    except Exception as e:
        log.error("PW login crashed: %s", e)

    log.info("Playwright failed → curl_cffi ...")
    try:
        if await _curl_login():
            return True
    except Exception as e:
        log.error("CURL login crashed: %s", e)

    log.error("All login strategies failed.")
    _logged_in = False
    return False


async def refresh_csrf() -> str:
    global _csrf, _logged_in

    if _login_method == "playwright" and _bcontext:
        page = await _bcontext.new_page()
        try:
            await page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=30_000)
            if "login" in page.url:
                _csrf = ""
                _logged_in = False
                return ""
            token = await page.evaluate(
                'document.querySelector(\'meta[name="csrf-token"]\')?.content ?? ""'
            )
            if token:
                _csrf = token
            return _csrf
        except Exception:
            return _csrf
        finally:
            await page.close()

    elif _login_method == "curl" and _curl_session:
        try:
            cookies = load_cookies()
            cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            hdrs = {"Cookie": cookie_header} if cookie_header else {}
            r = await _curl_session.get(PORTAL_URL, headers=hdrs)
            if "login" in str(r.url).lower():
                _csrf = ""
                _logged_in = False
                return ""
            soup = BeautifulSoup(r.text, "html.parser")
            meta = soup.find("meta", {"name": "csrf-token"})
            if meta:
                _csrf = meta.get("content", "")
            return _csrf
        except Exception:
            return _csrf

    return _csrf


async def _post(url, payload):
    if _login_method == "playwright" and _bcontext:
        r      = await _bcontext.request.post(url, form=payload)
        status = r.status
        text   = await r.text()
        return status, text, str(r.url)
    elif _login_method == "curl" and _curl_session:
        cookies = load_cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        hdrs = {"Cookie": cookie_header} if cookie_header else {}
        r = await _curl_session.post(url, data=payload, headers=hdrs)
        return r.status_code, r.text, str(r.url)
    return 0, "", ""


async def fetch_sms() -> list:
    global _csrf, _logged_in

    if not _logged_in:
        return []

    token = _csrf
    if not token:
        log.info("No CSRF — refreshing ...")
        token = await refresh_csrf()
    if not token:
        log.warning("Still no CSRF — skipping cycle.")
        return []

    today    = datetime.utcnow()
    from_str = (today - timedelta(days=1)).strftime("%m/%d/%Y")
    to_str   = today.strftime("%m/%d/%Y")

    try:
        status, text, url = await _post(
            SMS_URL,
            {"from": from_str, "to": to_str, "_token": token},
        )

        if status == 419:
            log.warning("CSRF expired (419).")
            _csrf = ""
            _logged_in = False
            return []

        if "login" in url.lower():
            log.warning("Session expired — redirected to login.")
            _logged_in = False
            return []

        if status != 200:
            log.warning("SMS endpoint HTTP %d.", status)
            return []

        soup       = BeautifulSoup(text, "html.parser")
        group_divs = soup.find_all("div", {"class": "pointer"})
        if not group_divs:
            return []

        group_ids = []
        for div in group_divs:
            m = re.search(r"getDetials\('(.+?)'\)", div.get("onclick", ""))
            if m:
                group_ids.append(m.group(1))

        messages = []

        for gid in group_ids:
            try:
                ns, nt, _ = await _post(
                    NUMBERS_URL,
                    {"start": from_str, "end": to_str, "range": gid, "_token": token},
                )
                if ns != 200:
                    continue

                for ndiv in BeautifulSoup(nt, "html.parser").select("div[onclick*='getDetialsNumber']"):
                    phone = ndiv.text.strip()
                    if not phone:
                        continue

                    ss, st, _ = await _post(
                        SMS_DETAIL,
                        {"start": from_str, "end": to_str,
                         "Number": phone, "Range": gid, "_token": token},
                    )
                    if ss != 200:
                        continue

                    for card in BeautifulSoup(st, "html.parser").find_all("div", class_="card-body"):
                        p = card.find("p", class_="mb-0")
                        if not p:
                            continue
                        sms = p.get_text(separator="\n").strip()
                        if not sms:
                            continue

                        m2      = re.match(r"([a-zA-Z\s]+)", gid)
                        country = m2.group(1).strip() if m2 else gid.strip()
                        svc     = detect_service(sms)

                        messages.append({
                            "id":      f"{phone}|{sms[:80]}",
                            "time":    datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                            "number":  phone,
                            "country": country,
                            "flag":    get_flag(country),
                            "service": svc,
                            "emoji":   SERVICE_EMOJIS.get(svc, "❓"),
                            "code":    extract_code(sms),
                            "sms":     sms,
                        })
            except Exception as e:
                log.error("Group %s error: %s", gid, e)
                continue

        return messages

    except Exception as e:
        log.error("fetch_sms error: %s", e)
        traceback.print_exc()
        return []


async def send_otp(bot, chat_id, msg):
    text = (
        f"🔔 *New OTP Received*\n\n"
        f"📞 *Number:* `{esc(msg['number'])}`\n"
        f"🔑 *Code:* `{esc(msg['code'])}`\n"
        f"🏆 *Service:* {msg['emoji']} {esc(msg['service'])}\n"
        f"🌎 *Country:* {esc(msg['country'])} {msg['flag']}\n"
        f"⏳ *Time:* {esc(msg['time'])}\n\n"
        f"💬 *Message:*\n{esc(msg['sms'])}"
    )
    try:
        await bot.send_message(
            chat_id=chat_id, text=text,
            parse_mode="MarkdownV2", reply_markup=BUTTONS,
        )
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 1)
        try:
            await bot.send_message(
                chat_id=chat_id, text=text,
                parse_mode="MarkdownV2", reply_markup=BUTTONS,
            )
        except Exception:
            pass
    except Exception:
        try:
            plain = (
                f"New OTP\n\nNumber: {msg['number']}\nCode: {msg['code']}\n"
                f"Service: {msg['service']}\nCountry: {msg['country']} {msg['flag']}\n"
                f"Time: {msg['time']}\n\nMessage:\n{msg['sms']}"
            )
            await bot.send_message(chat_id=chat_id, text=plain, reply_markup=BUTTONS)
        except Exception as e2:
            log.error("Send failed %s: %s", chat_id, e2)


async def poll_loop(bot):
    global _fail_count, _logged_in

    log.info("Starting poll loop ...")

    for attempt in range(1, 4):
        if await do_login():
            break
        wait = 30 * attempt
        log.warning("Attempt %d/3 failed — retrying in %ds ...", attempt, wait)
        await asyncio.sleep(wait)
    else:
        log.error("All 3 initial login attempts failed. Retrying indefinitely ...")

    while True:
        try:
            log.info("[%s] Polling ...", datetime.utcnow().strftime("%H:%M:%S"))

            if not _logged_in or _fail_count >= 3:
                log.info("Re-login needed ...")
                _fail_count = 0
                ok = await do_login()
                if not ok:
                    log.warning("Re-login failed — waiting 120s.")
                    await asyncio.sleep(120)
                    continue

            messages = await fetch_sms()

            if not messages:
                log.info("  No messages this cycle.")
            else:
                seen      = load_seen()
                chats     = load_chats()
                new_count = 0
                for msg in reversed(messages):
                    if msg["id"] in seen:
                        continue
                    new_count += 1
                    log.info("  -> %s | %s | %s", msg["number"], msg["service"], msg["code"])
                    for cid in chats:
                        await send_otp(bot, cid, msg)
                    mark_seen(msg["id"])
                if new_count:
                    log.info("  Sent %d new OTP(s).", new_count)
                else:
                    log.info("  All already seen.")

        except Exception as e:
            log.error("poll_loop error: %s", e)
            traceback.print_exc()

        await asyncio.sleep(POLL_SECS)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if is_admin(uid):
        await update.message.reply_text(
            "Welcome Admin\\!\n\n"
            "`/status` — Live bot status\n"
            "`/debug` — Browser screenshot \\+ HTML\n"
            "`/relogin` — Force re\\-login now\n"
            "`/add_chat <id>` — Add chat\n"
            "`/remove_chat <id>` — Remove chat\n"
            "`/list_chats` — List chats",
            parse_mode="MarkdownV2",
            reply_markup=BUTTONS,
        )
    else:
        await update.message.reply_text("Not authorized.", reply_markup=BUTTONS)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    pw  = "✅" if _bcontext     else "❌"
    cur = "✅" if _curl_session else "❌"
    ses = "✅ Logged in" if _logged_in else "❌ Logged out"
    csr = "✅" if _csrf else "❌"
    ck  = len(load_cookies())
    sth = "✅ playwright-stealth" if STEALTH_AVAILABLE else "⚠️ manual-only"
    await update.message.reply_text(
        f"*Bot Status*\n\n"
        f"Playwright: {pw}\n"
        f"curl\\_cffi: {cur}\n"
        f"Session: {ses}\n"
        f"CSRF: {csr}\n"
        f"Stealth: {sth}\n"
        f"Method: `{esc(_login_method)}`\n"
        f"Fails: {_fail_count}\n"
        f"Cookies: {ck} saved\n"
        f"Chats: {len(load_chats())}\n"
        f"Seen: {len(load_seen())} IDs\n\n"
        f"Email: `{esc(IVAS_EMAIL)}`",
        parse_mode="MarkdownV2",
    )


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    sent = False
    if os.path.exists(DEBUG_SS):
        try:
            await update.message.reply_photo(
                photo=open(DEBUG_SS, "rb"),
                caption="Last browser screenshot at login failure.",
            )
            sent = True
        except Exception as e:
            await update.message.reply_text(f"Screenshot error: {e}")

    if os.path.exists(DEBUG_HTML):
        try:
            with open(DEBUG_HTML, encoding="utf-8") as f:
                snippet = f.read(1500)
            await update.message.reply_text(
                f"HTML snippet:\n```\n{snippet[:1000]}\n```",
                parse_mode="MarkdownV2",
            )
            sent = True
        except Exception:
            pass

    if not sent:
        await update.message.reply_text("No debug data yet.")


async def cmd_relogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    global _fail_count, _logged_in
    _fail_count = 0
    _logged_in  = False
    await update.message.reply_text("Triggering re-login now ...")
    ok = await do_login()
    if ok:
        await update.message.reply_text(
            f"✅ Re-login succeeded via `{esc(_login_method)}`\\.",
            parse_mode="MarkdownV2",
        )
    else:
        await update.message.reply_text(
            "❌ Re-login failed\\. Send /debug to see what browser saw\\.",
            parse_mode="MarkdownV2",
        )


async def cmd_add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if not context.args:
        return await update.message.reply_text("Usage: /add\\_chat \\<id\\>", parse_mode="MarkdownV2")
    cid   = context.args[0]
    chats = load_chats()
    if cid in chats:
        return await update.message.reply_text("Already registered.")
    chats.append(cid)
    save_chats(chats)
    await update.message.reply_text(f"✅ Added `{esc(cid)}`\\.", parse_mode="MarkdownV2")


async def cmd_remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    if not context.args:
        return await update.message.reply_text("Usage: /remove\\_chat \\<id\\>", parse_mode="MarkdownV2")
    cid   = context.args[0]
    chats = load_chats()
    if cid not in chats:
        return await update.message.reply_text("Not found.")
    chats.remove(cid)
    save_chats(chats)
    await update.message.reply_text(f"✅ Removed `{esc(cid)}`\\.", parse_mode="MarkdownV2")


async def cmd_list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return
    chats = load_chats()
    if not chats:
        return await update.message.reply_text("No chats registered.")
    lines = "\n".join(f"• `{esc(c)}`" for c in chats)
    await update.message.reply_text(
        f"📜 *Registered Chats:*\n\n{lines}", parse_mode="MarkdownV2"
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, Conflict):
        log.warning("Telegram Conflict — waiting 30s ...")
        await asyncio.sleep(30)
    elif isinstance(err, (TimedOut, NetworkError)):
        log.warning("Telegram network hiccup: %s", err)
    else:
        log.error("Telegram error: %s", err)


async def main():
    log.info("=" * 55)
    log.info("iVAS SMS Bot v10 — Turnstile-First Login")
    log.info("Email  : %s", IVAS_EMAIL)
    log.info("Admins : %s", ADMIN_IDS)
    log.info("Stealth: %s", "playwright-stealth ACTIVE" if STEALTH_AVAILABLE else "manual JS only")
    log.info("Chats  : %s", load_chats())
    log.info("=" * 55)

    await start_browser()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("debug",       cmd_debug))
    app.add_handler(CommandHandler("relogin",     cmd_relogin))
    app.add_handler(CommandHandler("add_chat",    cmd_add_chat))
    app.add_handler(CommandHandler("remove_chat", cmd_remove_chat))
    app.add_handler(CommandHandler("list_chats",  cmd_list_chats))
    app.add_error_handler(error_handler)

    async with app:
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message"],
        )
        log.info("Bot online. Polling every %ds.", POLL_SECS)
        try:
            await poll_loop(app.bot)
        finally:
            await app.updater.stop()
            await app.stop()
            await stop_browser()
            if _curl_session:
                try:
                    await _curl_session.close()
                except Exception:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
