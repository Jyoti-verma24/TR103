"""FinSense AI — run with:  streamlit run app.py"""

import streamlit as st

from finsense import auth, theme
from finsense.views import (
    common,
    data_view,
    fraud_lab_view,
    health_view,
    home_view,
    login_view,
    overview,
    personality_view,
    radar_view,
    report_view,
    spending_view,
    whatif_view,
)

st.set_page_config(page_title="FinSense AI", page_icon=":material/menu_book:", layout="wide")
theme.inject()

# ------------------------------------------------------------
# Signed out: only the home page and the login page exist.
# ------------------------------------------------------------
user = auth.current_user()
if user is None:
    st.navigation(
        [
            st.Page(home_view.render, title="FinSense — your money journal", url_path="home", default=True),
            st.Page(login_view.render, title="Log in · FinSense", url_path="login"),
        ],
        position="hidden",
    ).run()
    st.stop()

# The login form's ?mode=signup has done its job once you're in.
if st.query_params:
    st.query_params.clear()

pages = {
    "home": st.Page(home_view.render, title="Home", icon=":material/home:", url_path="home"),
    "data": st.Page(data_view.render, title="Your data", icon=":material/upload_file:", url_path="data"),
    "overview": st.Page(overview.render, title="Overview", icon=":material/auto_stories:", url_path="overview", default=True),
    "health": st.Page(health_view.render, title="Health score", icon=":material/favorite:", url_path="health"),
    "radar": st.Page(radar_view.render, title="Anomaly radar", icon=":material/radar:", url_path="radar"),
    "whatif": st.Page(whatif_view.render, title="What-if lab", icon=":material/tune:", url_path="what-if"),
    "persona": st.Page(personality_view.render, title="Money personality", icon=":material/fingerprint:", url_path="personality"),
    "spending": st.Page(spending_view.render, title="Spending", icon=":material/receipt_long:", url_path="spending"),
    "report": st.Page(report_view.render, title="Report", icon=":material/description:", url_path="report"),
    "fraud": st.Page(fraud_lab_view.render, title="Fraud lab", icon=":material/policy:", url_path="fraud-lab"),
}
common.PAGES.clear()
common.PAGES.update(pages)

nav = st.navigation({
    "Start": [pages["home"], pages["data"], pages["overview"]],
    "Understand": [pages["health"], pages["persona"], pages["spending"]],
    "Protect & plan": [pages["radar"], pages["whatif"]],
    "More": [pages["report"], pages["fraud"]],
})

with st.sidebar:
    theme.html(
        f'<div style="text-align:center;padding:4px 0 10px;border-bottom:1px solid rgba(201,165,78,.35)">'
        f'{theme.logo(54, on_cover=True)}'
        f'<div style="font:700 1.35rem {theme.SERIF};color:{theme.GOLD};letter-spacing:.06em;margin-top:6px">FINSENSE</div>'
        f'<div style="font:400 .7rem {theme.TYPE};letter-spacing:.22em;color:{theme.GOLD_SOFT}">SAVINGS PASSBOOK</div></div>'
    )
    source = st.session_state.get("data_source")
    if source:
        st.caption(f"Reading from **{source}**")
    st.divider()
    theme.html(f'<div style="font:400 .72rem {theme.TYPE};letter-spacing:.14em">NAME OF ACCOUNT HOLDER</div>'
               f'<div style="font:600 1.4rem {theme.HAND};color:#fff;margin:2px 0">{theme.esc(user["name"])}</div>'
               f'<div style="font-size:.8rem;opacity:.8;margin-bottom:10px">{theme.esc(user["email"])}</div>')
    if st.button("Log out", icon=":material/logout:", key="sidebar_logout", width="stretch"):
        auth.sign_out()
        st.rerun()

# ------------------------------------------------------------
# Top bar on every signed-in page: always a way home and a way out.
# ------------------------------------------------------------
with st.container(key="topbar"):
    brand, who, home, out = st.columns([2.4, 1.5, .9, 1.1], vertical_alignment="center", gap="small")
    with brand:
        theme.html(
            f'<div class="t-brand">{theme.logo(32)}<b>FinSense</b>'
            f'<span class="t-crumb">· Page: {theme.esc(nav.title)}</span></div>'
        )
    with who:
        theme.html(f'<div class="t-who">A/c holder<br><span>{theme.esc(user["name"])}</span></div>')
    with home:
        if nav.url_path != "home":
            st.page_link(pages["home"], label="Home", icon=":material/home:")
    with out:
        if st.button("Log out", icon=":material/logout:", key="topbar_logout", width="stretch"):
            auth.sign_out()
            st.rerun()

if st.session_state.pop("just_joined", False):
    st.toast(f"Welcome, {user['name'].split()[0]}! Start by loading your statement or the sample data.")

nav.run()
