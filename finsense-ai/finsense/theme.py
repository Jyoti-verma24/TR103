import html as _html
import re

import streamlit as st

# ============================================================
# DESIGN TOKENS — "Savings Passbook"
# Modelled on an Indian bank passbook: security paper with blue
# rules and a red margin, a bottle-green cover with gold foil,
# entries typed like a dot-matrix printer, violet rubber stamps,
# and the teller's handwritten notes in fountain-pen blue.
#   blue  = money in / primary     red    = money out / alerts
#   green = healthy / the cover    ochre  = watch / goals
#   violet = stamps, and anything predicted or inferred
# ============================================================

PAPER = "#ECE8DA"        # the desk the passbook lies on
PAGE = "#FBF9F1"         # passbook page
INK = "#1E2430"          # printed text
SOFT = "#5A6170"         # secondary print
LINE = "#D6D0BE"         # page edges, dividers
RULE = "#CBD6E8"         # blue ruled lines
MARGIN = "#E2A39B"       # red margin line

BLUE, BLUE_SOFT = "#1F3A93", "#E3E9F7"
RED, RED_SOFT = "#B3261E", "#F7E1DE"
GREEN, GREEN_SOFT = "#1E5A43", "#DDEDE4"
OCHRE, OCHRE_SOFT = "#94650E", "#F6ECD3"
VIOLET, VIOLET_SOFT = "#5B3E96", "#ECE5F6"

COVER, COVER_DARK = "#1C4A3A", "#143529"
GOLD, GOLD_SOFT = "#C9A54E", "#E9D9A6"

TONES = {
    "good": (GREEN, GREEN_SOFT),
    "bad": (RED, RED_SOFT),
    "warn": (OCHRE, OCHRE_SOFT),
    "info": (BLUE, BLUE_SOFT),
    "plum": (VIOLET, VIOLET_SOFT),
    "neutral": (SOFT, "#ECE9DF"),
}
TONE_COLOR = {k: v[0] for k, v in TONES.items()}

SERIF = "'Libre Caslon Text', Georgia, serif"
SANS = "'Source Sans 3', system-ui, sans-serif"
TYPE = "'Courier Prime', 'Courier New', monospace"
HAND = "'Caveat', cursive"

# Ruled page: blue lines every 32px plus the red margin line.
RULED = (
    f"linear-gradient(to right, transparent 46px, {MARGIN} 46px, {MARGIN} 47.5px, transparent 47.5px),"
    f"repeating-linear-gradient(to bottom, transparent 0 31px, {RULE} 31px 32px)"
)
LEATHER = (
    "repeating-linear-gradient(45deg, rgba(255,255,255,.025) 0 2px, transparent 2px 5px),"
    "repeating-linear-gradient(-45deg, rgba(0,0,0,.05) 0 2px, transparent 2px 6px)"
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Source+Sans+3:wght@400;600;700&family=Courier+Prime:wght@400;700&family=Caveat:wght@500;700&display=swap');

.stApp {{
  background-color: {PAPER};
  background-image:
    repeating-linear-gradient(45deg, rgba(31,58,147,.028) 0 1px, transparent 1px 7px),
    repeating-linear-gradient(-45deg, rgba(31,58,147,.028) 0 1px, transparent 1px 7px);
}}
/* Leave spans alone: Streamlit's Material icons are spans with their own font. */
html, body, .stApp, p, li, label, input, textarea, td, th, button {{ font-family: {SANS}; }}
h1, h2, h3, h4 {{ font-family: {SERIF} !important; font-weight: 700 !important; color: {INK}; letter-spacing: -.005em; }}
h4 {{ margin-top: 1.8rem !important; font-size: 1.25rem !important; }}
.block-container {{ padding-top: 1.6rem; max-width: 1140px; }}
[data-testid="stHeader"] {{ background: transparent; }}

/* ---------- Sidebar = the passbook cover ---------- */
[data-testid="stSidebar"] {{ background-color: {COVER}; background-image: {LEATHER}; border-right: 3px solid {COVER_DARK}; }}
[data-testid="stSidebar"] * {{ color: {GOLD_SOFT}; }}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{ border-radius: 3px; }}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {{ background: rgba(255,255,255,.07); }}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
  background: rgba(201,165,78,.18); box-shadow: inset 3px 0 0 {GOLD}; }}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {{ color: {GOLD_SOFT} !important; }}
[data-testid="stSidebar"] [data-testid="stNavSectionHeader"], [data-testid="stSidebar"] header {{
  font-family: {TYPE} !important; text-transform: uppercase; letter-spacing: .16em; color: {GOLD} !important; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(201,165,78,.3); }}
[data-testid="stSidebar"] button {{ background: transparent; border: 1.5px solid {GOLD}; border-radius: 3px; }}
[data-testid="stSidebar"] button:hover {{ background: rgba(201,165,78,.15); border-color: {GOLD}; }}

/* ---------- Buttons & inputs ---------- */
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button {{ border-radius: 3px; font-weight: 600; }}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {{
  background: {COVER}; color: {GOLD_SOFT}; border: 1px solid {COVER_DARK};
  box-shadow: 0 2px 0 {COVER_DARK}; }}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {{
  background: {COVER_DARK}; color: #fff; border-color: {COVER_DARK}; }}

/* ---------- Paper ---------- */
.pb-page {{
  position: relative; background: {PAGE}; border: 1px solid {LINE}; border-radius: 4px;
  box-shadow: 0 1px 0 #fff inset, 0 12px 26px -20px rgba(30,36,48,.55);
}}
.pb-sheet {{ background-color: {PAGE}; background-image: {RULED}; }}
.pb-type {{ font-family: {TYPE}; }}
.pb-hand {{ font-family: {HAND}; }}
.pb-eyebrow {{ font: 700 .74rem {TYPE}; letter-spacing: .18em; text-transform: uppercase; }}
.pb-printhead {{ display: flex; justify-content: space-between; gap: 12px; font: 400 .74rem {TYPE};
  letter-spacing: .14em; text-transform: uppercase; color: {SOFT}; padding-bottom: 8px;
  border-bottom: 3px double {INK}; }}

.pb-hero {{ padding: 18px 30px 26px 66px; margin: 6px 0 28px; }}
.pb-hero h1 {{ font-size: 2.1rem; line-height: 1.25; margin: 14px 0 0; padding: 0; }}
.pb-hero p {{ color: {SOFT}; font-size: 1.04rem; line-height: 2rem; margin: 2px 0 0; max-width: 680px; }}

.pb-stats {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); margin: 4px 0 20px; }}
.pb-stat {{ padding: 12px 16px 14px; border-top: 3px double {INK}; }}
.pb-stat .label {{ font: 700 .72rem {TYPE}; letter-spacing: .14em; text-transform: uppercase; color: {SOFT}; }}
.pb-stat .value {{ font: 700 1.55rem {TYPE}; color: {INK}; margin-top: 6px; line-height: 1.2; }}
.pb-stat .foot {{ font-size: .86rem; margin-top: 4px; }}

/* A note the teller wrote in the margin, in fountain-pen ink. */
.pb-note {{ background-color: {PAGE}; background-image: {RULED}; border: 1px solid {LINE}; border-radius: 4px;
  padding: 2px 18px 0 62px; margin: 12px 0; color: var(--ink); font: 500 1.32rem/32px {HAND}; }}
.pb-note b {{ font-weight: 700; text-decoration: underline wavy var(--ink-40); text-underline-offset: 5px; }}

.pb-pill {{ display: inline-block; padding: 2px 9px; border: 1.5px solid var(--ink); border-radius: 3px;
  color: var(--ink); font: 700 .74rem {TYPE}; letter-spacing: .06em; text-transform: uppercase;
  margin: 4px 8px 4px 0; background: var(--soft-bg); transform: rotate(-.6deg); }}
.pb-pill:nth-child(even) {{ transform: rotate(.5deg); }}

.pb-bar {{ height: 10px; border: 1px solid var(--ink-40); background: {PAGE}; margin: 10px 0 4px; padding: 1px; }}
.pb-bar > span {{ display: block; height: 100%;
  background: repeating-linear-gradient(-45deg, var(--ink) 0 3px, var(--ink-70) 3px 6px); }}

.pb-card {{ padding: 16px 20px 18px; margin-bottom: 16px; }}
.pb-card .title {{ font: 700 1.12rem {SERIF}; color: {INK}; margin-top: 4px; }}
.pb-card .body {{ color: {INK}; font-size: .96rem; margin-top: 8px; line-height: 1.6; }}
.pb-card .hint {{ color: {BLUE}; font: 500 1.18rem/1.35 {HAND}; margin-top: 8px; }}

.pb-score {{ display: flex; gap: 22px; align-items: center; padding: 22px 26px; }}

/* ---------- The ledger ---------- */
.pb-ledger-wrap {{ padding: 16px 20px 10px 62px; overflow-x: auto;
  background-image: linear-gradient(to right, transparent 46px, {MARGIN} 46px, {MARGIN} 47.5px, transparent 47.5px) !important; }}
table.pb-ledger {{ width: 100%; border-collapse: collapse; font-family: {TYPE}; font-size: .92rem; border: 0; }}
.pb-page table, .pb-page th, .pb-page td, .pb-page tr {{ border-left: 0 !important; border-right: 0 !important;
  background: transparent !important; }}
.pb-page table {{ border-top: 0; border-bottom: 0; }}
.pb-ledger th {{ text-align: left; font-weight: 700; font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
  color: {SOFT}; border-top: 3px double {INK}; border-bottom: 1px solid {INK}; padding: 8px 8px; white-space: nowrap; }}
.pb-ledger td {{ height: 32px; padding: 0 8px; border-bottom: 1px solid {RULE}; white-space: nowrap; color: {INK}; }}
.pb-ledger td.num, .pb-ledger th.num {{ text-align: right; }}
.pb-ledger td.dr {{ color: {RED}; }}
.pb-ledger td.cr {{ color: {BLUE}; }}
.pb-ledger td.part {{ white-space: normal; min-width: 180px; }}
.pb-ledger tr.total td {{ border-top: 1px solid {INK}; border-bottom: 3px double {INK}; font-weight: 700; }}
.pb-circled {{ position: relative; display: inline-block; padding: 0 6px; }}
.pb-circled::after {{ content: ""; position: absolute; inset: -5px -4px; border: 2px solid {RED}; border-radius: 50%;
  transform: rotate(-4deg); opacity: .85; }}
.pb-flagnote {{ font: 700 1.1rem {HAND}; color: {RED}; margin-left: 10px; }}

/* ---------- Top bar = the passbook's printed header ---------- */
.st-key-topbar {{ background: {PAGE}; border: 1px solid {LINE}; border-radius: 4px; padding: 6px 8px 6px 16px;
  margin-bottom: 20px; box-shadow: 0 10px 22px -20px rgba(30,36,48,.6); border-bottom: 3px double {INK}; }}
.t-brand {{ display: flex; align-items: center; gap: 10px; }}
.t-brand b {{ font: 700 1.12rem {SERIF}; color: {INK}; }}
.t-crumb {{ font: 400 .78rem {TYPE}; letter-spacing: .12em; text-transform: uppercase; color: {SOFT};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.t-who span {{ font: 600 1.15rem {HAND}; letter-spacing: 0; text-transform: none; color: {BLUE}; }}
.t-who {{ font: 400 .66rem/1.2 {TYPE}; letter-spacing: .12em; text-transform: uppercase; color: {SOFT}; text-align: right;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.st-key-topbar [data-testid="stPageLink"] a {{ justify-content: center; border-radius: 3px; height: 38px; padding: 0 14px;
  border: 1px solid {LINE}; background: {PAGE}; }}
.st-key-topbar button, .st-key-topbar a {{ white-space: nowrap; }}
.st-key-topbar button {{ border-radius: 3px; background: {COVER}; border: 1px solid {COVER_DARK}; min-height: 38px; height: 38px; }}
.st-key-topbar button:hover {{ background: {COVER_DARK}; border-color: {COVER_DARK}; }}
.st-key-topbar button * {{ color: {GOLD_SOFT} !important; }}
@media (max-width: 640px) {{ .t-crumb, .t-who {{ display: none; }} }}

@keyframes stamp-in {{
  0%   {{ opacity: 0; transform: scale(1.7) rotate(-26deg); }}
  60%  {{ opacity: .95; transform: scale(.94) rotate(-9deg); }}
  100% {{ opacity: .9; transform: scale(1) rotate(-11deg); }}
}}
.stamp-in {{ animation: stamp-in .45s cubic-bezier(.2,.8,.3,1.2) both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
.rise {{ animation: rise .4s ease-out both; }}
@media (prefers-reduced-motion: reduce) {{ .stamp-in, .rise {{ animation: none !important; }} }}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text):
    return _html.escape(str(text))


def html(markup):
    """Render a block of HTML. Newlines and indentation collapse to single spaces so
    Markdown never mistakes indented lines for code blocks."""
    st.markdown(re.sub(r"\s*\n\s*", " ", markup), unsafe_allow_html=True)


def _vars(tone):
    ink, soft = TONES[tone]
    return f"--ink:{ink};--soft-bg:{soft};--ink-40:{ink}66;--ink-70:{ink}B3"


def hero(eyebrow, title, sub="", tone="info"):
    """A passbook page header: printed strip, then the page title."""
    html(
        f'<header class="pb-page pb-sheet pb-hero rise">'
        f'<div class="pb-printhead"><span>FinSense savings passbook</span><span>{esc(eyebrow)}</span></div>'
        f'<h1>{esc(title)}</h1>'
        + (f'<p>{esc(sub)}</p>' if sub else "")
        + "</header>"
    )


def stat_cards(cards):
    """cards: list of (label, value, foot, tone)."""
    parts = "".join(
        f'<div class="pb-page pb-stat"><div class="label">{esc(label)}</div>'
        f'<div class="value">{esc(value)}</div>'
        f'<div class="foot" style="color:{TONE_COLOR.get(tone, SOFT)}">{esc(foot)}</div></div>'
        for label, value, foot, tone in cards
    )
    html(f'<div class="pb-stats">{parts}</div>')


def insight(text_html, tone="info"):
    """A handwritten margin note. text_html may contain <b>; callers escape data."""
    html(f'<div class="pb-note" style="{_vars(tone)}">{text_html}</div>')


def pills(items, tone="info"):
    html("".join(f'<span class="pb-pill" style="{_vars(tone)}">{esc(i)}</span>' for i in items))


def bar(fraction, tone="info"):
    width = max(0, min(100, fraction * 100))
    return f'<div class="pb-bar" style="{_vars(tone)}"><span style="width:{width:.0f}%"></span></div>'


def stamp(score, label, tone="plum", size=132, sub="out of 100"):
    """A round rubber stamp: uneven ink (SVG turbulence), score typed in the middle."""
    color = TONE_COLOR[tone]
    uid = re.sub(r"\W", "", f"{label}{score}{size}")
    text = f"{label.upper()} ✦ FINSENSE ✦ {label.upper()} ✦ FINSENSE ✦ "
    return (
        f'<svg viewBox="0 0 100 100" width="{size}" height="{size}" class="stamp-in" '
        f'style="flex-shrink:0;transform:rotate(-11deg)" role="img" aria-label="{esc(label)}: {score} {esc(sub)}">'
        f'<defs><filter id="ink{uid}"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/>'
        f'<feDisplacementMap in="SourceGraphic" scale="2.2"/></filter>'
        f'<path id="arc{uid}" d="M50 50 m-35 0 a35 35 0 1 1 70 0 a35 35 0 1 1 -70 0"/></defs>'
        f'<g filter="url(#ink{uid})" fill="none" stroke="{color}" opacity=".9">'
        f'<circle cx="50" cy="50" r="46" stroke-width="3.2"/><circle cx="50" cy="50" r="42" stroke-width="1"/>'
        f'<circle cx="50" cy="50" r="27" stroke-width="1.4"/>'
        f'<text font-size="7.4" font-weight="700" letter-spacing="1.4" fill="{color}" stroke="none" '
        f'font-family="Courier Prime, monospace"><textPath href="#arc{uid}">{esc(text)}</textPath></text>'
        f'<text x="50" y="55" text-anchor="middle" font-size="20" font-weight="700" fill="{color}" stroke="none" '
        f'font-family="Courier Prime, monospace">{score}</text>'
        f'<text x="50" y="66" text-anchor="middle" font-size="5.6" letter-spacing=".8" fill="{color}" stroke="none" '
        f'font-family="Courier Prime, monospace">{esc(sub.upper())}</text></g></svg>'
    )


def score_tone(score):
    if score >= 80:
        return "good"
    if score >= 60:
        return "info"
    if score >= 40:
        return "warn"
    return "bad"


def ledger(rows, total=None):
    """A passbook statement. rows: dicts with date, particulars, withdrawal, deposit, balance,
    and optional flag (a short handwritten note). Amounts are pre-formatted strings."""
    body = []
    for r in rows:
        flag = r.get("flag")
        dr = r.get("withdrawal") or ""
        if flag and dr:
            dr = f'<span class="pb-circled">{dr}</span>'
        note = f'<span class="pb-flagnote">← {esc(flag)}</span>' if flag else ""
        body.append(
            f'<tr><td>{esc(r["date"])}</td><td class="part">{esc(r["particulars"])}{note}</td>'
            f'<td class="num dr">{dr}</td><td class="num cr">{r.get("deposit") or ""}</td>'
            f'<td class="num">{r.get("balance", "")}</td></tr>'
        )
    if total:
        body.append(f'<tr class="total"><td></td><td>{esc(total[0])}</td><td></td><td></td>'
                    f'<td class="num">{total[1]}</td></tr>')
    return (
        '<div class="pb-page pb-sheet pb-ledger-wrap"><table class="pb-ledger"><thead><tr>'
        '<th>Date</th><th>Particulars</th><th class="num">Withdrawals</th><th class="num">Deposits</th>'
        '<th class="num">Balance</th></tr></thead><tbody>' + "".join(body) + "</tbody></table></div>"
    )


def logo(size=40, on_cover=False):
    """The FinSense seal: a gold-rimmed roundel with a rupee and a rising line."""
    rim = GOLD if on_cover else COVER
    fill = COVER if on_cover else PAGE
    mark = GOLD_SOFT if on_cover else COVER
    return (
        f'<svg viewBox="0 0 48 48" width="{size}" height="{size}" role="img" aria-label="FinSense seal">'
        f'<circle cx="24" cy="24" r="21.5" fill="{fill}" stroke="{rim}" stroke-width="2.4"/>'
        f'<circle cx="24" cy="24" r="17.5" fill="none" stroke="{rim}" stroke-width="1" stroke-dasharray="2 2.2"/>'
        f'<path d="M17 16h14M17 21h14M21.5 16c5 0 5 9 0 9H18l9 8" fill="none" stroke="{mark}" stroke-width="2.4" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


# Simple line icons (24×24, stroke = currentColor).
ICONS = {
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/><path d="M8 12h2l1.2-2.4L13 14l1.2-2H16"/>',
    "radar": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18 6"/><circle cx="16" cy="14.5" r="1.2" fill="currentColor"/>',
    "sliders": '<path d="M5 6h9M18 6h1M5 12h3M12 12h7M5 18h11M20 18h-1"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    "person": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c.8-3.6 3.6-5.5 7-5.5s6.2 1.9 7 5.5"/><path d="M16.5 4.5 18 3M19 7h1.8"/>',
    "receipt": '<path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    "shield": '<path d="M12 3 5 6v5c0 4.4 3 8 7 10 4-2 7-5.6 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
    "upload": '<path d="M12 15V4M8 8l4-4 4 4"/><path d="M5 15v4h14v-4"/>',
    "book": '<path d="M4 5.5C6.5 4 9.5 4 12 5.5 14.5 4 17.5 4 20 5.5V19c-2.5-1.5-5.5-1.5-8 0-2.5-1.5-5.5-1.5-8 0z"/><path d="M12 5.5V19"/>',
    "check": '<path d="M5 12.5 10 17l9-10"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
}


def icon(name, size=24, color="currentColor"):
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{ICONS[name]}</svg>'
    )
