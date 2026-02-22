#!/usr/bin/env python3
import sys
import time
import random
import requests
import os
import subprocess
from datetime import datetime
from sites import SITES as RAW_SITES

# =========================
# CONFIG BASICA
# =========================

TIMEOUT = 12
MIN_DELAY = 1.5
MAX_DELAY = 3.5

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# =========================
# PROXIES / TOR
# =========================

USE_TOR = False
USE_GEONODE = False
PROXIES_LIST = []

GEONODE_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"


def init_geonode_proxies():
    """Carga proxies HTTP(S) desde Geonode."""
    global PROXIES_LIST
    PROXIES_LIST = []
    try:
        resp = requests.get(GEONODE_URL, timeout=10)
        data = resp.json()
        proxies = []
        for item in data.get("data", []):
            protocols = item.get("protocols") or []
            if "http" in protocols or "https" in protocols:
                ip = item.get("ip")
                port = item.get("port")
                if ip and port:
                    proxies.append(f"http://{ip}:{port}")
        PROXIES_LIST = proxies
    except Exception as e:
        print(f"[*] Error cargando proxies de Geonode: {e}")
        PROXIES_LIST = []


def pick_proxy_dict():
    """Devuelve dict de proxies para requests o None."""
    if USE_TOR:
        return {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }
    if USE_GEONODE and PROXIES_LIST:
        proxy = random.choice(PROXIES_LIST)
        return {"http": proxy, "https": proxy}
    return None


# =========================
# SITES (DEDUP)
# =========================

def build_site_list():
    """Deduplica por slug para evitar sitios repetidos."""
    seen = set()
    sites = []
    for s in RAW_SITES:
        slug = s.get("slug") or s.get("name")
        if not slug:
            continue
        if slug in seen:
            continue
        seen.add(slug)
        sites.append(s)
    return sites


SITES = build_site_list()

# =========================
# CATEGORIAS + PESOS
# =========================

SLUG_CATEGORY = {
    # seguridad / hacking
    "hackthebox": "security",
    "tryhackme": "security",
    "hackerone": "security",
    "bugcrowd": "security",
    "pentesterlab": "security",
    "vulnhub": "security",
    "openbugbounty": "security",
    "picoctf": "security",
    "infosec_exchange": "security",

    # dev / code
    "github": "dev",
    "gitlab": "dev",
    "bitbucket": "dev",
    "gist": "dev",
    "sourceforge": "dev",
    "codepen": "dev",
    "replit": "dev",
    "devto": "dev",
    "hashnode": "dev",
    "hackerrank": "dev",
    "leetcode": "dev",
    "codewars": "dev",
    "freecodecamp": "dev",
    "kaggle": "dev",
    "npm": "dev",
    "pypi": "dev",
    "dockerhub": "dev",
    "glitch": "dev",
    "exercism": "dev",
    "codeberg": "dev",

    # social / general
    "twitter": "social",
    "facebook": "social",
    "instagram": "social",
    "reddit": "social",
    "pinterest": "social",
    "snapchat": "social",
    "tumblr": "social",
    "mastodon": "social",
    "bluesky": "social",
    "quora": "social",
    "telegram": "social",
    "vk": "social",
    "tiktok": "social",
    "mixfm": "social",
    "alwatanvoice": "social",
    "paldf": "social",
    "steam_group": "social",

    # gaming
    "twitch": "gaming",
    "kick": "gaming",
    "steam": "gaming",
    "itchio": "gaming",
    "speedrun": "gaming",
    "retroachievements": "gaming",
    "gog": "gaming",
    "psn": "gaming",
    "xbox": "gaming",
    "chesscom": "gaming",
    "lichess": "gaming",

    # profesional / negocio
    "linkedin_personal": "business",
    "linkedin_company": "business",
    "behance": "business",
    "dribbble": "business",
    "crunchbase": "business",
    "wellfound": "business",
    "polywork": "business",
    "contra": "business",
    "fiverr": "business",
    "producthunt": "business",

    # creativo / media / musica
    "youtube": "creative",
    "artstation": "creative",
    "deviantart": "creative",
    "flickr": "creative",
    "soundcloud": "creative",
    "bandcamp": "creative",
    "spotify": "creative",
    "apple_music": "creative",
    "lastfm": "creative",
    "fivehundredpx": "creative",
    "vimeo": "creative",
    "audible": "creative",
    "apple_podcasts": "creative",

    # soporte / donaciones
    "patreon": "creator",
    "buymeacoffee": "creator",

    # otros
    "tripadvisor": "other",
    "gamefaqs": "other",
    "alltrails": "other",
    "eksi_sozluk": "other",
}

CATEGORY_WEIGHT = {
    "security": 1.3,
    "dev": 1.2,
    "business": 1.2,
    "social": 1.0,
    "creative": 1.0,
    "creator": 1.0,
    "gaming": 0.9,
    "other": 1.0,
}


def get_category_and_weight(slug: str):
    cat = SLUG_CATEGORY.get(slug, "other")
    w = CATEGORY_WEIGHT.get(cat, 1.0)
    return cat, w


def compute_score(slug: str, status: str):
    """Devuelve (score 0-100, category)."""
    if status == "EXISTS_HIGH":
        base = 70
    elif status == "EXISTS_WEAK":
        base = 30
    else:
        return 0, "other"

    cat, w = get_category_and_weight(slug)
    score = int(base * w)
    if score > 100:
        score = 100
    return score, cat


# =========================
# PERFILES (SUBSET DE SITES)
# =========================

CORE_SLUGS = {
    "github",
    "gitlab",
    "twitter",
    "instagram",
    "facebook",
    "linkedin_personal",
    "linkedin_company",
    "reddit",
}


def get_sites_for_profile(profile_name: str):
    """Devuelve lista de sitios segun el perfil."""
    raw_profile = (profile_name or "all").lower()
    profile = raw_profile.lstrip("-")  # soporta --dev, --security, etc.

    if profile in ("all", "full"):
        return SITES, profile

    if profile == "core":
        subset = [s for s in SITES if (s.get("slug") or s.get("name")) in CORE_SLUGS]
        if not subset:
            subset = SITES
        return subset, profile

    if profile in CATEGORY_WEIGHT.keys():
        subset = []
        for s in SITES:
            slug = s.get("slug") or s.get("name")
            cat = SLUG_CATEGORY.get(slug, "other")
            if cat == profile:
                subset.append(s)
        if not subset:
            subset = SITES
        return subset, profile

    print(f"[*] Perfil desconocido '{raw_profile}', usando 'all'.")
    return SITES, "all"


# =========================
# CLASIFICACION DE RESULTADO
# =========================

def normalize_text(text):
    return (text or "").strip().lower()


def classify_result(site, status_code, body_text, username, final_url):
    """Devuelve: ('NOT_FOUND' | 'EXISTS_HIGH' | 'EXISTS_WEAK', motivo)."""
    text = normalize_text(body_text)
    user_l = (username or "").lower()
    url_l = (final_url or "").lower()

    not_found_markers = [m.lower() for m in site.get("not_found_markers", [])]
    positive_markers = [m.lower() for m in site.get("positive_markers", [])]

    for marker in not_found_markers:
        if marker and marker in text:
            return "NOT_FOUND", f'matched not_found marker "{marker}"'

    if status_code in (404, 410):
        return "NOT_FOUND", f"HTTP {status_code}"

    if user_l and (user_l not in text and user_l not in url_l):
        return "NOT_FOUND", "username not present in page or url"

    for marker in positive_markers:
        if marker and marker in text:
            return "EXISTS_HIGH", f'matched positive marker "{marker}"'

    if status_code == 200:
        return "EXISTS_WEAK", "HTTP 200 with username present"

    return "EXISTS_WEAK", f"HTTP {status_code} with username present"


# =========================
# REQUEST + CHEQUEO
# =========================

def pick_user_agent():
    return random.choice(USER_AGENTS)


def check_site(username, site):
    slug = site.get("slug") or site.get("name", "unknown")
    display_name = site.get("name", slug)
    template = site.get("url")
    if not template:
        reason = "missing url template"
        print(f"[{slug}] ERROR   -> <no-url> :: {reason}")
        return {
            "username": username,
            "site": slug,
            "name": display_name,
            "status": "ERROR",
            "reason": reason,
            "url": "",
            "http_status": 0,
            "score": 0,
            "category": "other",
        }

    url = template.format(username=username)

    headers = {
        "User-Agent": pick_user_agent(),
        "Accept-Language": "en-US,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    proxies = pick_proxy_dict()

    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT,
            allow_redirects=True,
            proxies=proxies,
        )
        status_code = resp.status_code
        text = resp.text
        final_url = resp.url
    except requests.RequestException as e:
        reason = f"request error: {type(e).__name__}"
        print(f"[{slug}] ERROR   -> {url} :: {reason}")
        return {
            "username": username,
            "site": slug,
            "name": display_name,
            "status": "ERROR",
            "reason": reason,
            "url": url,
            "http_status": 0,
            "score": 0,
            "category": "other",
        }

    status, reason = classify_result(site, status_code, text, username, final_url)
    score, category = compute_score(slug, status)

    if status == "NOT_FOUND":
        print(f"[{slug}] MISS    -> {final_url} :: {reason}")
    elif status == "EXISTS_HIGH":
        print(f"[{slug}] HIT *   -> {final_url} :: {reason} :: score={score}")
    elif status == "EXISTS_WEAK":
        print(f"[{slug}] HIT (?) -> {final_url} :: {reason} :: score={score}")
    else:
        print(f"[{slug}] {status} -> {final_url} :: {reason} :: score={score}")

    return {
        "username": username,
        "site": slug,
        "name": display_name,
        "status": status,
        "reason": reason,
        "url": final_url,
        "http_status": status_code,
        "score": score,
        "category": category,
    }


# =========================
# REPORTING (CONSOLE)
# =========================

def build_summary(results):
    hits_high = [r for r in results if r["status"] == "EXISTS_HIGH"]
    hits_weak = [r for r in results if r["status"] == "EXISTS_WEAK"]
    misses = [r for r in results if r["status"] == "NOT_FOUND"]
    errors = [r for r in results if r["status"] == "ERROR"]

    return {
        "hits_high": hits_high,
        "hits_weak": hits_weak,
        "misses": misses,
        "errors": errors,
    }


def print_summary(label, profile, results):
    summary = build_summary(results)
    hits_all = [r for r in results if r["score"] > 0]
    hits_sorted = sorted(hits_all, key=lambda r: r["score"], reverse=True)

    max_score = max((r["score"] for r in hits_all), default=0)
    avg_score = 0
    if hits_all:
        avg_score = int(sum(r["score"] for r in hits_all) / len(hits_all))

    print("\n================ SUMMARY ================")
    print(f"Target   : {label}")
    print(f"Profile  : {profile}")
    print(f"HITS_HIGH: {len(summary['hits_high'])}")
    print(f"HITS_WEAK: {len(summary['hits_weak'])}")
    print(f"NOT_FOUND: {len(summary['misses'])}")
    print(f"ERRORS   : {len(summary['errors'])}")
    print(f"\nGlobal max score : {max_score}")
    print(f"Average score    : {avg_score}")

    if hits_sorted:
        print("\n--- TOP MATCHES (by score) ---")
        for r in hits_sorted[:20]:
            print(
                f"[{r['score']:3}] {r['category']:9} "
                f"{r['site']:15} ({r['username']}) -> {r['url']}"
            )


# =========================
# REPORT HTML (AGRUPADO POR USERNAME)
# =========================

def html_escape(s):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def save_html_report(label, profile, results, file_tag=None):
    summary_global = build_summary(results)
    hits_all = [r for r in results if r["score"] > 0]
    max_score = max((r["score"] for r in hits_all), default=0)
    avg_score = 0
    if hits_all:
        avg_score = int(sum(r["score"] for r in hits_all) / len(hits_all))

    errors_count = len(summary_global["errors"])
    misses_count = len(summary_global["misses"])

    # orden de usernames segun aparecen
    username_order = []
    for r in results:
        u = r.get("username")
        if u and u not in username_order:
            username_order.append(u)

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    fname_ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if file_tag is None:
        file_tag = label

    safe_tag = "".join(c for c in file_tag if c.isalnum() or c in ("-", "_"))
    if not safe_tag:
        safe_tag = "target"

    filename = f"tyke_report_{safe_tag}_{fname_ts}.html"

    # directorio propio de tyke
    report_root = os.path.expanduser("~/tyke_reports")
    out_path = None

    sections_html = []

    for uname in username_order:
        u_results_all = [r for r in results if r.get("username") == uname]
        u_hits = [r for r in u_results_all if r["score"] > 0]
        u_hits_sorted = sorted(u_hits, key=lambda r: r["score"], reverse=True)

        u_summary = build_summary(u_results_all)
        u_hits_count = len(u_hits_sorted)
        u_max_score = max((r["score"] for r in u_hits_sorted), default=0)
        u_avg_score = 0
        if u_hits_sorted:
            u_avg_score = int(sum(r["score"] for r in u_hits_sorted) / len(u_hits_sorted))

        row_html = []
        for r in u_hits_sorted:
            score = r["score"]
            cat = r["category"]
            site_name = r.get("name", r["site"])
            url = r["url"]
            status = r["status"]
            reason = r["reason"]

            if score >= 80:
                score_class = "high"
            elif score >= 50:
                score_class = "med"
            else:
                score_class = "low"

            row_html.append(
                f"<tr>"
                f"<td class='score {score_class}'>{score}</td>"
                f"<td>{html_escape(cat)}</td>"
                f"<td>{html_escape(site_name)}</td>"
                f"<td class='url-col'><a href='{html_escape(url)}' target='_blank' rel='noopener'>{html_escape(url)}</a></td>"
                f"<td>{html_escape(status)}</td>"
                f"<td>{html_escape(reason)}</td>"
                f"</tr>"
            )

        if not row_html:
            row_html.append("<tr><td colspan='6'>No hits with score &gt; 0 for this username.</td></tr>")

        sections_html.append(f"""
<section class="u-block">
  <h2>Username: {html_escape(uname)}</h2>
  <div class="u-stats small">
    <span>Hits: <b>{u_hits_count}</b></span> &nbsp;|&nbsp;
    <span>Max score: <b>{u_max_score}</b></span> &nbsp;|&nbsp;
    <span>Avg score: <b>{u_avg_score}</b></span> &nbsp;|&nbsp;
    <span>Errors: <b>{len(u_summary['errors'])}</b></span> &nbsp;|&nbsp;
    <span>Misses: <b>{len(u_summary['misses'])}</b></span>
  </div>
  <table>
    <thead>
      <tr>
        <th>Score</th>
        <th>Category</th>
        <th>Site</th>
        <th class="url-col">URL</th>
        <th>Status</th>
        <th>Reason</th>
      </tr>
    </thead>
    <tbody>
      {''.join(row_html)}
    </tbody>
  </table>
</section>
""")

    hits_count_global = len(hits_all)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Tyke - Username OSINT Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0b0b0f;
    color: #f5f5f5;
    margin: 0;
    padding: 0;
}}
header {{
    padding: 12px 16px;
    background: linear-gradient(90deg, #141422, #191933);
    border-bottom: 1px solid #252545;
}}
h1 {{
    font-size: 1.1rem;
    margin: 0 0 4px 0;
}}
.small {{
    font-size: 0.8rem;
    opacity: 0.8;
}}
.stats {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
}}
.stat-card {{
    background: #151525;
    border-radius: 8px;
    padding: 8px 10px;
    min-width: 90px;
    border: 1px solid #26264a;
    font-size: 0.8rem;
}}
.stat-label {{
    opacity: 0.7;
}}
.stat-value {{
    font-weight: 600;
    margin-top: 2px;
}}
main {{
    padding: 10px 8px 18px 8px;
}}
.u-block {{
    margin-top: 18px;
}}
.u-block h2 {{
    font-size: 0.95rem;
    margin: 0 0 4px 0;
}}
.u-stats {{
    margin-bottom: 6px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
}}
th, td {{
    padding: 6px 5px;
    border-bottom: 1px solid #252545;
    vertical-align: top;
}}
th {{
    text-align: left;
    background: #151525;
    position: sticky;
    top: 0;
    z-index: 2;
}}
tr:nth-child(even) td {{
    background: #10101b;
}}
.score {{
    text-align: center;
    font-weight: 600;
    border-radius: 4px;
}}
.score.high {{
    color: #a6ffb0;
}}
.score.med {{
    color: #ffe08a;
}}
.score.low {{
    color: #ff9f9f;
}}
.url-col {{
    word-break: break-all;
}}
@media (max-width: 700px) {{
    /* en movil escondemos Category, Status, Reason */
    th:nth-child(2), td:nth-child(2),
    th:nth-child(5), td:nth-child(5),
    th:nth-child(6), td:nth-child(6) {{
        display: none;
    }}
}}
</style>
</head>
<body>
<header>
  <h1>Tyke - Username OSINT Report</h1>
  <div class="small">
    Targets: <b>{html_escape(label)}</b> &nbsp;|&nbsp;
    Profile: <b>{html_escape(profile)}</b> &nbsp;|&nbsp;
    Generated: {html_escape(ts)}
  </div>
  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Total hits</div>
      <div class="stat-value">{hits_count_global}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Global max score</div>
      <div class="stat-value">{max_score}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Global avg score</div>
      <div class="stat-value">{avg_score}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Errors</div>
      <div class="stat-value">{errors_count}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Misses</div>
      <div class="stat-value">{misses_count}</div>
    </div>
  </div>
</header>
<main>
  {''.join(sections_html) if sections_html else "<p>No hits with score &gt; 0.</p>"}
</main>
</body>
</html>
"""

    try:
        os.makedirs(report_root, exist_ok=True)
        out_path = os.path.join(report_root, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        out_path = os.path.abspath(filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

    return out_path


# =========================
# ABRIR REPORTE CON SERVIDOR LOCAL
# =========================

def open_report_via_termux(report_path):
    answer = input("¿Abrir reporte en navegador con servidor local (http.server)? [y/N]: ").strip().lower()
    if answer != "y":
        return

    filename = os.path.basename(report_path)
    root_dir = os.path.dirname(report_path)

    try:
        port = 8765
        print(f"[*] Iniciando servidor local en http://127.0.0.1:{port}/ ...")
        subprocess.Popen(
            ["python3", "-m", "http.server", str(port)],
            cwd=root_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"Cuando termines, puedes matar el servidor con:")
        print(f"  pkill -f \"http.server {port}\"")
        url = f"http://127.0.0.1:{port}/{filename}"
    except Exception as e:
        print(f"[!] No se pudo iniciar http.server: {e}")
        url = f"file://{os.path.abspath(report_path)}"

    print(f"Abriendo: {url}")
    exit_code = os.system(f'termux-open-url "{url}"')
    if exit_code != 0:
        print("[!] No pude ejecutar termux-open-url. ¿Tienes instalada la app Termux:API y el paquete termux-api?")


# =========================
# MAIN
# =========================

def main():
    args = sys.argv[1:]
    if not args:
        print("Uso:")
        print("  python3 tyke.py <username1> [username2 ...] [profile] [--geonode] [--tor]")
        print("")
        print("Profiles:")
        print("  all/full  -> todos (default)")
        print("  core      -> GitHub, X, IG, FB, LinkedIn, Reddit")
        print("  security  -> plataformas hacking/CTF/bug bounty")
        print("  dev       -> plataformas de desarrollo/codigo")
        print("  social    -> redes sociales generales")
        print("  creative  -> arte/musica/video")
        print("  business  -> LinkedIn/portfolio/negocios")
        print("  gaming    -> Twitch/Steam/PSN/Xbox/etc.")
        sys.exit(1)

    flags = [a for a in args if a.startswith("--")]
    positional = [a for a in args if not a.startswith("--")]

    known_profiles = {"all", "full", "core", "security", "dev", "social", "creative", "business", "gaming"}

    profile_arg = "all"
    usernames = []

    if positional:
        last = positional[-1].lower()
        if last in known_profiles:
            profile_arg = last
            usernames = positional[:-1]
        else:
            usernames = positional

    usernames = [u.strip() for u in usernames if u.strip()]
    if not usernames:
        print("Debes pasar al menos un username (o mas).")
        sys.exit(1)

    global USE_GEONODE, USE_TOR
    USE_GEONODE = "--geonode" in flags
    USE_TOR = "--tor" in flags

    if USE_TOR:
        print("[*] Usando Tor (socks5h://127.0.0.1:9050). Asegurate de que Tor esta corriendo (ej. `tor` o `termux-services`).")
        if USE_GEONODE:
            print("[*] Aviso: Tor tiene prioridad, se ignoraran los proxies de Geonode.")
    elif USE_GEONODE:
        print("[*] Cargando proxies desde Geonode...")
        init_geonode_proxies()
        print(f"[*] Proxies cargados: {len(PROXIES_LIST)}")

    sites, effective_profile = get_sites_for_profile(profile_arg)

    print(f"[*] Profile efectivo: {effective_profile}")
    print(f"[*] Total sitios a comprobar (despues de filtro): {len(sites)}\n")

    all_results = []

    for username in usernames:
        print("\n" + "=" * 50)
        print(f"== Buscando username: {username} ==")
        print("=" * 50 + "\n")

        results_user = []
        for idx, site in enumerate(sites, start=1):
            print(f"\n[{idx}/{len(sites)}] Comprobando {site.get('name', site.get('slug', 'site'))}...")
            res = check_site(username, site)
            results_user.append(res)
            all_results.append(res)
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        print_summary(username, effective_profile, results_user)

    if len(usernames) > 1:
        label_global = " / ".join(usernames)
        print("\n" + "=" * 50)
        print("== RESUMEN GLOBAL (todos los usernames) ==")
        print("=" * 50 + "\n")
        print_summary(label_global, effective_profile, all_results)
    else:
        label_global = usernames[0]

    if len(usernames) <= 3:
        label_for_header = ", ".join(usernames)
    else:
        label_for_header = ", ".join(usernames[:3]) + f" ... (+{len(usernames)-3} mas)"

    if len(usernames) == 1:
        file_tag = usernames[0]
    else:
        file_tag = f"{usernames[0]}+{len(usernames)-1}"

    report_path = save_html_report(label_for_header, effective_profile, all_results, file_tag=file_tag)
    print(f"\nReporte combinado guardado en: {report_path}")

    open_report_via_termux(report_path)


if __name__ == "__main__":
    main()
