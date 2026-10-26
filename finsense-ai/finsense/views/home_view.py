import streamlit as st

from finsense import auth, theme
from finsense.theme import (
    BLUE, COVER, COVER_DARK, GOLD, GOLD_SOFT, GREEN, HAND, INK, LEATHER, LINE, OCHRE, PAGE, RED, SERIF,
    SOFT, TYPE, VIOLET, logo,
)
from finsense.views import common

CSS = f"""
<style>
.block-container {{ max-width: 1180px; padding-top: 1rem; }}
.h-nav {{ display:flex; align-items:center; justify-content:space-between; gap:12px; background:{PAGE};
  border:1px solid {LINE}; border-bottom:3px double {INK}; border-radius:4px; padding:8px 10px 8px 14px; }}
.h-brand, .h-brand:hover {{ display:flex; align-items:center; gap:10px; text-decoration:none !important; color:{INK} !important; }}
.h-brand b {{ font:700 1.3rem {SERIF}; }}
.h-brand small {{ display:block; font:400 .68rem {TYPE}; letter-spacing:.2em; color:{SOFT}; text-transform:uppercase; }}
.h-actions {{ display:flex; gap:8px; align-items:center; }}
.h-btn {{ display:inline-flex; align-items:center; gap:8px; height:42px; padding:0 18px; border-radius:3px;
  font-weight:700; font-size:.95rem; text-decoration:none !important; white-space:nowrap; transition:transform .15s ease; }}
.h-btn:hover {{ transform:translateY(-1px); }}
.h-btn-ink {{ background:{COVER}; color:{GOLD_SOFT} !important; border:1px solid {COVER_DARK}; box-shadow:0 2px 0 {COVER_DARK}; }}
.h-btn-ghost {{ color:{INK} !important; border:1.5px solid {INK}; background:{PAGE}; }}
.h-btn-lg {{ height:52px; padding:0 24px; font-size:1.02rem; }}
@media (max-width: 600px) {{
  .h-brand small, .h-nav .h-btn-ghost {{ display:none; }}
  .h-nav .h-btn {{ height:38px; padding:0 12px; font-size:.86rem; }}
}}

.h-hero {{ margin:52px 0 0; }}
.h-hero h1 {{ font:700 clamp(2.4rem, 5vw, 3.9rem)/1.08 {SERIF} !important; margin:14px 0 0; padding:0; letter-spacing:-.015em; }}
.h-hero h1 .pen {{ display:inline-block; font:700 1.12em/1 {HAND}; color:{BLUE}; transform:rotate(-2.5deg); }}
.h-lead {{ color:{SOFT}; font-size:1.12rem; line-height:1.8; margin:22px 0 0 !important; max-width:560px; }}
.h-ctas {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:30px; }}

/* The passbook illustration: cover behind, open page in front */
.h-book {{ position:relative; max-width:460px; margin:40px auto 70px; height:470px; }}
.h-cover {{ position:absolute; inset:10px 30px 30px 40px; background-color:{COVER}; background-image:{LEATHER};
  border-radius:6px 10px 10px 6px; transform:rotate(-7deg); box-shadow:0 26px 40px -24px rgba(0,0,0,.6);
  border-left:10px solid {COVER_DARK}; display:flex; flex-direction:column; align-items:center; padding-top:34px; }}
.h-cover .foil {{ color:{GOLD}; font:700 1.25rem {SERIF}; letter-spacing:.14em; margin-top:10px; }}
.h-cover .foil2 {{ color:{GOLD_SOFT}; font:400 .7rem {TYPE}; letter-spacing:.24em; }}
.h-open {{ position:absolute; left:0; right:20px; top:70px; padding:14px 18px 14px 58px; transform:rotate(1.5deg); }}
.h-open table {{ width:100%; border-collapse:collapse; font:400 .82rem {TYPE}; }}
.h-open th {{ text-align:left; font-size:.62rem; letter-spacing:.12em; color:{SOFT}; border-bottom:1px solid {INK}; padding:4px 4px; }}
.h-open td {{ height:32px; padding:0 4px; white-space:nowrap; }}
.h-open .r {{ text-align:right; }}
.h-open .bal td {{ border-top:1px solid {INK}; border-bottom:3px double {INK}; font-weight:700; }}
.h-stamp {{ position:absolute; right:-44px; bottom:-64px; }}
@media (max-width: 600px) {{
  .h-book {{ width:460px; max-width:none; transform:scale(.7); transform-origin:top left; height:340px; margin:20px 0 70px; }}
  .h-stamp {{ right:-10px; }}
}}
.h-penote {{ font:700 1.3rem {HAND}; color:{RED}; transform:rotate(-2deg); margin:6px 0 0 118px; }}

.h-terms {{ display:flex; flex-wrap:wrap; justify-content:center; gap:8px 26px; margin:70px 0 0; padding:14px 10px;
  border-top:3px double {INK}; border-bottom:1px solid {INK}; font:400 .82rem {TYPE}; letter-spacing:.06em; color:{SOFT}; }}
.h-terms b {{ color:{GREEN}; }}

.h-section {{ margin:80px 0 0; }}
.h-head {{ text-align:center; max-width:660px; margin:0 auto 30px; }}
.h-head h2 {{ font:700 clamp(1.8rem, 3.2vw, 2.5rem) {SERIF} !important; margin:10px 0 0; padding:0; }}
.h-head p {{ color:{SOFT}; line-height:1.7; margin-top:10px; }}

/* Contents page */
.h-toc {{ padding:0 28px 32px 66px; }}
.h-toc .pb-printhead {{ height:64px; box-sizing:border-box; padding:38px 0 0; }}
.h-toc-row {{ padding:0; }}
.h-toc-line {{ display:flex; align-items:baseline; gap:10px; height:32px; line-height:32px; }}
.h-toc-no {{ font:700 .9rem {TYPE}; color:{SOFT}; width:30px; flex-shrink:0; }}
.h-toc-title {{ font:700 1.18rem {SERIF}; color:{INK}; white-space:nowrap; }}
.h-toc-dots {{ flex:1; border-bottom:2px dotted {SOFT}; transform:translateY(-4px); min-width:20px; }}
.h-toc-page {{ font:400 .8rem {TYPE}; color:{SOFT}; white-space:nowrap; }}
.h-toc-desc {{ margin:0 0 0 40px; color:{SOFT}; font-size:.98rem; line-height:32px; }}
.h-toc-eg {{ margin:0 0 0 40px; font:600 1.2rem/32px {HAND}; color:{BLUE}; }}

/* Deposit slips */
.h-slips {{ display:grid; gap:20px; }}
@media (min-width: 860px) {{ .h-slips {{ grid-template-columns:repeat(3, 1fr); }} }}
.h-slip {{ padding:22px 22px 20px;
  background-image:radial-gradient(circle at 8px -2px, {LINE} 4px, transparent 4.5px); background-size:16px 10px;
  background-repeat:repeat-x; background-color:{PAGE}; }}
.h-slip .no {{ font:700 .74rem {TYPE}; letter-spacing:.16em; color:{SOFT}; border-bottom:1px dashed {SOFT}; padding:10px 0 8px; }}
.h-slip h3 {{ font:700 1.15rem {SERIF} !important; margin:12px 0 0; padding:0; }}
.h-slip p {{ color:{SOFT}; line-height:1.65; margin:8px 0 0; font-size:.98rem; }}

/* Rubber-stamp privacy note */
.h-privacy {{ display:grid; gap:26px; align-items:center; padding:28px 32px; }}
@media (min-width: 860px) {{ .h-privacy {{ grid-template-columns: auto 1fr; }} }}
.h-rubber {{ display:inline-block; padding:12px 18px; border:3px double {VIOLET}; color:{VIOLET}; transform:rotate(-4deg);
  font:700 .9rem/1.5 {TYPE}; letter-spacing:.14em; text-align:center; opacity:.88; }}
.h-privacy h3 {{ font:700 1.3rem {SERIF} !important; margin:0; padding:0; }}
.h-privacy p {{ color:{SOFT}; line-height:1.7; margin:6px 0 0; }}

/* Closing band = the back cover */
.h-final {{ margin-top:80px; padding:46px 28px; text-align:center; border-radius:6px; background-color:{COVER};
  background-image:{LEATHER}; border-left:10px solid {COVER_DARK}; }}
.h-final .foil {{ color:{GOLD}; font:700 clamp(1.7rem, 3vw, 2.3rem) {SERIF}; letter-spacing:.04em; }}
.h-final p {{ color:{GOLD_SOFT}; margin:10px auto 0; max-width:520px; line-height:1.7; }}
.h-final .h-ctas {{ justify-content:center; }}
.h-final .h-btn-ink {{ background:{GOLD}; color:{COVER_DARK} !important; border-color:{GOLD}; box-shadow:0 2px 0 #8E7330; }}
.h-final .h-btn-ghost {{ background:transparent; color:{GOLD_SOFT} !important; border-color:{GOLD_SOFT}; }}
.h-foot {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px; font:400 .78rem {TYPE};
  letter-spacing:.06em; color:{SOFT}; margin:34px 0 10px; padding-top:14px; border-top:1px solid {INK}; }}

/* In-app buttons on the signed-in home page */
.st-key-cta_hero {{ margin-top:26px; }}
.st-key-cta_final {{ display:flex; align-items:center; margin-top:20px; }}
.st-key-cta_hero a, .st-key-cta_final a {{ background:{COVER}; border:1px solid {COVER_DARK}; border-radius:3px; height:52px;
  padding:0 24px; display:inline-flex !important; align-items:center; gap:8px; width:auto !important;
  box-shadow:0 2px 0 {COVER_DARK}; }}
.st-key-cta_hero a:hover, .st-key-cta_final a:hover {{ background:{COVER_DARK}; }}
.st-key-cta_hero a *, .st-key-cta_final a * {{ color:{GOLD_SOFT} !important; font-weight:700; font-size:1rem; }}
</style>
"""

CONTENTS = [
    ("Health check", "p. 1", "A score out of 100 from six everyday habits — and exactly where the points went.",
     "Safety runway: 1.2 months saved. Up to 12 points back."),
    ("Anomaly radar", "p. 2", "Learns what normal looks like for you, then circles the entries that don't fit.",
     "BESCOM ₹9,800 — 9.1× your usual electricity bill!"),
    ("What-if lab", "p. 3", "Move a slider and see next year change. Thousands of possible futures, not one guess.",
     "Food & shopping 30% less → ₹1 lakh by July, not November."),
    ("Money personality", "p. 4", "Weekend splurger or payday spender? Your habits, with the numbers behind them.",
     "Weekends cost you 2.2× a weekday."),
    ("Spending", "p. 5", "Which categories are creeping up, your best and toughest months, and the full ledger.",
     "Shopping up 327% in six months — mostly one laptop."),
    ("Fraud lab", "p. 6", "Scores payments for fraud and says why in plain words, not just a percentage.",
     "Emptied the sender's whole balance — seen in 98% of frauds."),
]

SLIPS = [
    ("Slip 01", "Bring your statement",
     "Export a CSV from your bank or expense app. We only need date, category, amount and type."),
    ("Slip 02", "We enter it in your passbook",
     "Score, odd entries, habits and a 12-month outlook — ready in seconds. No bank login, no forms."),
    ("Slip 03", "Read the teller's notes",
     "Every finding has the reason and one small thing to try. Take a one-page report home."),
]


def _book():
    rows = [
        ("01-12", "Salary · Acme Tech", "", "65,000.00", "65,000.00"),
        ("03-12", "Rent · Mr Sharma", "18,000.00", "", "47,000.00"),
        ("05-12", "HDFC MF SIP", "5,000.00", "", "42,000.00"),
        ("07-12", "Swiggy", '<span class="pb-circled">1,179.20</span>', "", "40,820.80"),
        ("10-12", "BESCOM electricity", "1,163.00", "", "39,657.80"),
    ]
    body = "".join(
        f'<tr><td>{d}</td><td>{p}</td><td class="r" style="color:{RED}">{w}</td>'
        f'<td class="r" style="color:{BLUE}">{c}</td><td class="r">{b}</td></tr>' for d, p, w, c, b in rows
    )
    return f"""
    <div class="h-book">
      <div class="h-cover">{logo(70, on_cover=True)}
        <div class="foil">FINSENSE</div><div class="foil2">SAVINGS PASSBOOK</div></div>
      <div class="pb-page pb-sheet h-open">
        <div class="pb-printhead"><span>A/c 0042 · Priya S.</span><span>Page 07</span></div>
        <table><thead><tr><th>Date</th><th>Particulars</th><th class="r">Dr</th><th class="r">Cr</th>
          <th class="r">Balance</th></tr></thead>
          <tbody>{body}<tr class="bal"><td></td><td>Balance c/f</td><td></td><td></td>
          <td class="r">39,657.80</td></tr></tbody></table>
        <div class="h-penote">↑ 2.1× your usual Swiggy order!</div>
        <div class="h-stamp">{theme.stamp(60, "Good", "plum", size=118)}</div>
      </div>
    </div>"""


def _cta(key, label):
    """A button that switches page inside the app (keeps you signed in)."""
    with st.container(key=key):
        st.page_link(common.PAGES["overview"], label=label, icon=":material/arrow_forward:")


def render():
    theme.html(CSS)
    user = auth.current_user()

    # Signed in, the app's own top bar (Home · Log out) replaces this strip.
    if user is None:
        theme.html(f"""
        <nav class="h-nav">
          <a class="h-brand" href="./" target="_self">{logo(40)}
            <span><b>FinSense</b><small>Savings passbook</small></span></a>
          <span class="h-actions">
            <a class="h-btn h-btn-ghost" href="./login" target="_self">Log in</a>
            <a class="h-btn h-btn-ink" href="./login?mode=signup" target="_self">Open a passbook</a>
          </span>
        </nav>""")

    left, right = st.columns([1.05, .95], gap="large", vertical_alignment="center")
    with left:
        eyebrow = (f"Welcome back, {theme.esc(user['name'].split()[0])}" if user
                   else "For every household that's asked “where did it all go?”")
        theme.html(f"""
        <div class="h-hero">
          <div class="pb-eyebrow" style="color:{BLUE}">{eyebrow}</div>
          <h1>Every rupee, entered — <span class="pen">and explained.</span></h1>
          <p class="h-lead">FinSense turns your bank statement into a passbook that reads you back:
            the habits behind your balance, the entries that don't look like you, and what next year
            holds if you change one thing.</p>
        </div>""")
        theme.pills(["Health score", "Odd-entry radar", "What-if planner", "Money personality", "Fraud check"], "info")
        if user:
            _cta("cta_hero", "Open my passbook")
        else:
            theme.html("""
            <div class="h-ctas">
              <a class="h-btn h-btn-ink h-btn-lg" href="./login?mode=signup" target="_self">Open a free passbook &rarr;</a>
              <a class="h-btn h-btn-ghost h-btn-lg" href="./login" target="_self">I already have one</a>
            </div>""")
    with right:
        theme.html(_book())

    theme.html("""
    <div class="h-terms">
      <span><b>✓</b> Amounts in rupees, Indian style (₹1,20,000)</span>
      <span><b>✓</b> Knows about Diwali spending</span>
      <span><b>✓</b> Runs on your own computer</span>
      <span><b>✓</b> Every number shows its working</span>
    </div>""")

    toc = "".join(f"""
      <div class="h-toc-row">
        <div class="h-toc-line"><span class="h-toc-no">{n:02d}</span><span class="h-toc-title">{title}</span>
          <span class="h-toc-dots"></span><span class="h-toc-page">{page}</span></div>
        <div class="h-toc-desc">{desc}</div>
        <div class="h-toc-eg">{eg}</div>
      </div>""" for n, (title, page, desc, eg) in enumerate(CONTENTS, 1))
    theme.html(f"""
    <section class="h-section">
      <div class="h-head"><div class="pb-eyebrow" style="color:{RED}">What's inside</div>
        <h2>Contents</h2>
        <p>Six ways to read your money. The handwritten notes are real findings from the demo file.</p></div>
      <div class="pb-page pb-sheet h-toc">
        <div class="pb-printhead"><span>FinSense savings passbook</span><span>Index</span></div>
        {toc}
      </div>
    </section>""")

    slips = "".join(f"""
      <div class="pb-page h-slip"><div class="no">{no} · Deposit slip</div>
        <h3>{title}</h3><p>{text}</p></div>""" for no, title, text in SLIPS)
    theme.html(f"""
    <section class="h-section">
      <div class="h-head"><div class="pb-eyebrow" style="color:{OCHRE}">How it works</div>
        <h2>Three slips, about two minutes</h2></div>
      <div class="h-slips">{slips}</div>
    </section>""")

    theme.html("""
    <section class="h-section">
      <div class="pb-page h-privacy">
        <span class="h-rubber">STATEMENT<br>NEVER LEAVES<br>THIS COMPUTER</span>
        <div><h3>Your statement stays with you</h3>
          <p>FinSense runs on your own computer. Your file is read in memory and never sent to a server,
            and we never ask for your bank login. Your password is stored only as a salted hash.</p></div>
      </div>
    </section>""")

    if user:
        theme.html(f"""
        <section class="h-final">{logo(56, on_cover=True)}
          <div class="foil" style="margin-top:10px">Your passbook is waiting</div>
          <p>Load a statement, or carry on with the entries you already have open.</p>
        </section>""")
        _cta("cta_final", "Back to my passbook")
    else:
        theme.html(f"""
        <section class="h-final">{logo(56, on_cover=True)}
          <div class="foil" style="margin-top:10px">Open your passbook</div>
          <p>Make an account, load your statement or our demo file, and read your first notes in under a minute.</p>
          <div class="h-ctas" style="margin-top:24px">
            <a class="h-btn h-btn-ink h-btn-lg" href="./login?mode=signup" target="_self">Open a free passbook</a>
            <a class="h-btn h-btn-ghost h-btn-lg" href="./login" target="_self">Log in</a>
          </div>
        </section>""")
    theme.html("""
    <footer class="h-foot"><span>FinSense · a savings passbook for Indian households</span>
      <span>Not financial advice — a clearer view of your own numbers.</span></footer>""")
