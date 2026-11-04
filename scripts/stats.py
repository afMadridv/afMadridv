"""Generates assets/estadisticas.svg from the public GitHub REST API."""
import datetime
import json
import os
import re
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

USER = "afMadridv"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
W = 860
FACE, LIGHT, SHADOW, DARK = "#c6c6c6", "#ffffff", "#808080", "#1b1b1b"
TA, TB, ACCENT, PANEL, TEXT, SOFT = "#7a0f0f", "#d63a3a", "#fa4040", "#0b0b0b", "#d4d4d4", "#8a8a8a"
BLOCKS = 22


def api(path):
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "afMadridv-readme-stats")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def search_count(kind, query):
    return api(f"/search/{kind}?per_page=1&q=" + urllib.parse.quote(query))["total_count"]


def collect():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    # The profile repo only holds this README and its generator.
    own = [r for r in repos if not r["fork"] and r["name"] != USER]
    langs = {}
    for r in own:
        for lang, size in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[lang] = langs.get(lang, 0) + size
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    return {
        "rows": [
            ("Repositorios", user["public_repos"]),
            ("Commits", search_count("commits", f"author:{USER}")),
            ("Pull requests", search_count("issues", f"author:{USER} type:pr")),
            ("Estrellas", sum(r["stargazers_count"] for r in own)),
            ("Seguidores", user["followers"]),
        ],
        "langs": [(name, size / total) for name, size in top],
    }


def bevel(x, y, w, h, fill=FACE, inset=False):
    tl, br = (SHADOW, LIGHT) if inset else (LIGHT, DARK)
    tl2, br2 = (DARK, FACE) if inset else (FACE, SHADOW)
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
            f'<path d="M{x} {y+h}V{y}H{x+w}" stroke="{tl}" fill="none"/>'
            f'<path d="M{x} {y+h-0.5}H{x+w-0.5}V{y}" stroke="{br}" fill="none"/>'
            f'<path d="M{x+1.5} {y+h-1.5}V{y+1.5}H{x+w-1.5}" stroke="{tl2}" fill="none"/>'
            f'<path d="M{x+1.5} {y+h-1.5}H{x+w-1.5}V{y+1.5}" stroke="{br2}" fill="none"/>')


def title_buttons(x, y):
    out = bevel(x, y, 16, 14) + f'<rect x="{x+4}" y="{y+9}" width="6" height="2" fill="#000"/>'
    out += bevel(x + 18, y, 16, 14)
    out += f'<rect x="{x+21.5}" y="{y+2.5}" width="8" height="8" fill="none" stroke="#000"/>'
    out += f'<rect x="{x+21}" y="{y+2}" width="9" height="2" fill="#000"/>'
    out += bevel(x + 38, y, 16, 14)
    out += f'<path d="M{x+42} {y+3}l7 7M{x+49} {y+3}l-7 7" stroke="#000" stroke-width="1.6"/>'
    return out


def render(data, fonts):
    h = 260
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    b = bevel(0, 0, W, h)
    b += (f'<defs><linearGradient id="tb" x1="0" x2="1"><stop offset="0" stop-color="{TA}"/>'
          f'<stop offset="1" stop-color="{TB}"/></linearGradient></defs>')
    b += f'<rect x="4" y="4" width="{W-8}" height="22" fill="url(#tb)"/>'
    b += '<rect x="9" y="8" width="12" height="14" fill="#fff" stroke="#000"/>'
    b += '<path d="M12 12h6M12 15h6M12 18h4" stroke="#1d4fa8"/>'
    b += '<text x="28" y="20" font-size="13" font-weight="700" fill="#fff">Estadisticas.exe</text>'
    b += title_buttons(W - 62, 8)
    b += bevel(6, 30, W - 12, h - 62, fill=PANEL, inset=True)

    b += f'<text x="26" y="62" class="sk" font-size="16" fill="{ACCENT}" letter-spacing="1.5">ACTIVIDAD</text>'
    y = 92
    for label, value in data["rows"]:
        b += f'<text x="26" y="{y}" font-size="14" fill="{TEXT}">{escape(label)}</text>'
        b += f'<text x="290" y="{y}" font-size="14" font-weight="700" fill="#fff" text-anchor="end">{value:,}</text>'
        y += 28

    b += f'<text x="330" y="62" class="sk" font-size="16" fill="{ACCENT}" letter-spacing="1.5">LENGUAJES</text>'
    y = 92
    for name, share in data["langs"]:
        filled = max(1, round(share * BLOCKS))
        b += f'<text x="330" y="{y}" font-size="13" fill="{TEXT}">{escape(name[:12])}</text>'
        b += f'<rect x="440.5" y="{y-12.5}" width="{BLOCKS*14+5}" height="15" fill="none" stroke="{FACE}"/>'
        b += "".join(f'<rect x="{443+i*14}" y="{y-10}" width="11" height="10" fill="{ACCENT}"/>' for i in range(filled))
        b += f'<text x="{W-24}" y="{y}" font-size="12" fill="{SOFT}" text-anchor="end">{share*100:.1f}%</text>'
        y += 24

    b += bevel(6, h - 28, W - 12, 22, inset=True)
    b += f'<text x="14" y="{h-13}" font-size="12" fill="#222">Actividad pública · actualizado {today}</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
            f'{fonts}{b}</svg>')


def main():
    # Reuses the fonts already embedded in the other windows.
    with open(os.path.join(ASSETS, "taskbar.svg"), encoding="utf-8") as f:
        fonts = re.search(r"<style>.*?</style>", f.read(), re.S).group(0)
    svg = render(collect(), fonts)
    with open(os.path.join(ASSETS, "estadisticas.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
