import streamlit as st

from finsense import auth, theme
from finsense.theme import (
    BLUE, COVER, COVER_DARK, GOLD, GOLD_SOFT, HAND, INK, LEATHER, LINE, PAGE, PAPER, RED, RED_SOFT, RULED, SERIF,
    SOFT, TYPE, logo,
)

MODES = ["Log in", "Create account"]

CSS = f"""
<style>
.block-container {{ max-width: 1180px; padding-top: 1.4rem; }}

/* Left: the passbook cover */
.l-cover {{ position:relative; min-height:640px; border-radius:6px 12px 12px 6px; background-color:{COVER};
  background-image:{LEATHER}; border-left:14px solid {COVER_DARK}; box-shadow:0 30px 50px -30px rgba(0,0,0,.7);
  padding:44px 40px 34px; display:flex; flex-direction:column; align-items:center; text-align:center; gap:10px; }}
.l-cover .frame {{ position:absolute; inset:16px; border:1.5px solid rgba(201,165,78,.55); border-radius:4px; pointer-events:none; }}
.l-cover .foil {{ color:{GOLD}; font:700 2rem {SERIF}; letter-spacing:.16em; margin-top:8px; }}
.l-cover .foil2 {{ color:{GOLD_SOFT}; font:400 .78rem {TYPE}; letter-spacing:.3em; }}
.l-cover .rule {{ width:60%; border-top:1px solid rgba(201,165,78,.6); margin:18px 0 10px; }}
.l-cover h1 {{ color:#F4EBD0 !important; font:700 clamp(1.7rem, 2.8vw, 2.3rem)/1.25 {SERIF} !important; margin:6px 0 0; padding:0; }}
.l-cover p {{ color:{GOLD_SOFT}; line-height:1.7; margin:12px auto 0; max-width:380px; }}
.l-privileges {{ margin-top:22px; display:grid; gap:10px; text-align:left; }}
.l-privileges div {{ color:{GOLD_SOFT}; font:400 .86rem {TYPE}; letter-spacing:.04em; }}
.l-privileges b {{ color:{GOLD}; margin-right:8px; }}
.l-holder {{ margin-top:30px; width:100%; text-align:left; color:{GOLD_SOFT}; font:400 .74rem {TYPE}; letter-spacing:.16em; }}
.l-holder span {{ display:block; border-bottom:1px dotted {GOLD}; height:30px; margin-top:4px;
  font:600 1.5rem {HAND}; letter-spacing:0; color:#F4EBD0; }}
@media (max-width: 900px) {{ .l-cover {{ display:none; }} .l-mobile-logo {{ display:flex !important; }} }}

.l-mobile-logo {{ display:none; justify-content:center; align-items:center; gap:10px; margin-bottom:16px;
  color:{INK} !important; text-decoration:none !important; font:700 1.3rem {SERIF}; }}
.l-back {{ display:inline-flex; align-items:center; gap:6px; padding:7px 14px; border:1px solid {INK}; border-radius:3px;
  font:700 .78rem {TYPE}; letter-spacing:.1em; text-transform:uppercase; color:{INK} !important;
  text-decoration:none !important; background:{PAGE}; }}
.l-back:hover {{ background:{PAPER}; }}

/* Folder index tabs */
.st-key-auth_mode [data-testid="stButtonGroup"] > div {{ display:grid !important; grid-template-columns:1fr 1fr; gap:6px; }}
.st-key-auth_mode button {{ height:44px; border-radius:6px 6px 0 0 !important; border:1px solid {LINE} !important;
  border-bottom:0 !important; background:#E2DDCB !important; width:100%;
  font:700 .8rem {TYPE} !important; letter-spacing:.14em; text-transform:uppercase; color:{SOFT} !important; }}
.st-key-auth_mode button[aria-checked="true"] {{ background:{PAGE} !important; color:{INK} !important; height:48px;
  margin-top:-4px; box-shadow:0 -2px 0 {COVER} inset; }}
.st-key-auth_mode {{ margin-bottom:-17px; position:relative; z-index:1; }}

/* The form sheet */
.st-key-auth_card {{ background-color:{PAGE}; background-image:{RULED}; border:1px solid {LINE}; border-radius:0 0 4px 4px;
  padding:18px 26px 22px 64px; box-shadow:0 18px 34px -26px rgba(30,36,48,.6); }}
.st-key-auth_card [data-testid="stForm"] {{ border:0; padding:0; }}
.st-key-auth_card label p {{ font:700 .72rem {TYPE} !important; letter-spacing:.16em; text-transform:uppercase; color:{SOFT}; }}
.st-key-auth_card [data-testid="stTextInputRootElement"] {{ border:0 !important; border-bottom:1.5px solid {INK} !important;
  border-radius:0; background:transparent !important; }}
.st-key-auth_card [data-testid="stTextInputRootElement"] > div, .st-key-auth_card input {{ background:transparent !important; }}
.st-key-auth_card [data-testid="stTextInputRootElement"]:focus-within {{ border-bottom-color:{BLUE} !important; }}
.st-key-auth_card input {{ font:600 1.45rem {HAND} !important; color:{BLUE} !important; height:44px; padding-left:2px; }}
.st-key-auth_card input::placeholder {{ font:400 .9rem {TYPE}; color:{SOFT}; opacity:.6; }}
.st-key-auth_card [data-testid="stFormSubmitButton"] button {{ height:52px; font-size:1rem; letter-spacing:.04em; }}
.l-error {{ margin-top:14px; padding:10px 14px; border:2px solid {RED}; color:{RED}; background:{RED_SOFT};
  font:700 .9rem {TYPE}; text-align:center; transform:rotate(-.6deg); }}
.l-hint {{ text-align:center; color:{BLUE}; font:600 1.15rem {HAND}; margin-top:10px; }}
.l-fine {{ text-align:center; color:{SOFT}; font:400 .74rem {TYPE}; letter-spacing:.06em; margin-top:16px; }}
</style>
"""


def _cover():
    privileges = ["Every score shows its working", "Odd entries circled, with the reason", "Your statement never leaves this computer"]
    theme.html(f"""
    <div class="l-cover"><span class="frame"></span>
      {logo(84, on_cover=True)}
      <div class="foil">FINSENSE</div>
      <div class="foil2">SAVINGS ACCOUNT PASSBOOK</div>
      <div class="rule"></div>
      <h1>Your money, finally explained.</h1>
      <p>One upload and you'll know your health score, the entries that don't look like you,
        and what next year holds if you change one habit.</p>
      <div class="l-privileges">{"".join(f'<div><b>✦</b>{t}</div>' for t in privileges)}</div>
      <div class="l-holder">NAME OF ACCOUNT HOLDER<span>&nbsp;</span></div>
    </div>""")


def _error(message):
    theme.html(f'<div class="l-error">{theme.esc(message)}</div>')


def _heading(form_no, title, sub):
    theme.html(f'<div class="pb-printhead"><span>{form_no}</span><span>FinSense</span></div>'
               f'<h2 style="margin:12px 0 0;padding:0;font:700 1.7rem {SERIF}">{title}</h2>'
               f'<p style="color:{SOFT};margin:2px 0 6px;line-height:32px">{sub}</p>')


def _login_form():
    _heading("Counter · existing account holders", "Open your passbook", "Pick up where you left off.")
    with st.form("login_form", border=False):
        email = st.text_input("Email", placeholder="you@example.com", autocomplete="email")
        password = st.text_input("Password", type="password", placeholder="your password",
                                 autocomplete="current-password")
        submitted = st.form_submit_button("Open my passbook", width="stretch")
    if submitted:
        user, err = auth.authenticate(email, password)
        if err:
            _error(err)
            if not err.startswith("Too many"):
                theme.html('<div class="l-hint">No passbook yet, or made one before an update? '
                           'Use the “Create account” tab above.</div>')
        else:
            auth.sign_in(user)
            st.rerun()


def _signup_form():
    _heading("Form A-1 · account opening", "Open a new passbook",
             "Takes under a minute. No bank details, no KYC.")
    with st.form("signup_form", border=False):
        name = st.text_input("Your name", placeholder="e.g. Priya Sharma", autocomplete="name")
        email = st.text_input("Email", placeholder="you@example.com", autocomplete="email")
        password = st.text_input("Password", type="password", placeholder=f"at least {auth.MIN_PASSWORD} characters",
                                 autocomplete="new-password")
        confirm = st.text_input("Confirm password", type="password", placeholder="type it again",
                                autocomplete="new-password")
        submitted = st.form_submit_button("Open my passbook", width="stretch")
    if submitted:
        user, err = auth.register(name, email, password, confirm)
        if err:
            _error(err)
        else:
            auth.sign_in(user)
            st.session_state.just_joined = True
            st.rerun()


def render():
    theme.html(CSS)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = MODES[1] if st.query_params.get("mode") == "signup" else MODES[0]

    left, right = st.columns([1, 1.05], gap="large")
    with left:
        _cover()
    with right:
        theme.html(f'<a class="l-mobile-logo" href="./" target="_self">{logo(40)}FinSense</a>')
        theme.html('<div style="margin:4px 0 26px"><a class="l-back" href="./" target="_self">&larr; Back to home</a></div>')
        mode = st.segmented_control("Choose", MODES, key="auth_mode", required=True, width="stretch",
                                    label_visibility="collapsed")
        with st.container(key="auth_card"):
            if mode == MODES[1]:
                _signup_form()
            else:
                _login_form()
        theme.html('<div class="l-fine">Passwords are stored only as a salted hash on this computer.</div>')
