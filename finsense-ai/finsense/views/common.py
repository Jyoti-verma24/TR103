import streamlit as st

from finsense import data, theme

# Filled in by app.py on every run so views can link to each other.
PAGES = {}


def link(key, label, icon=None):
    if key in PAGES:
        st.page_link(PAGES[key], label=label, icon=icon)


def require_data():
    """Return the active transactions, or stop the page with a friendly prompt."""
    df = data.get_data()
    if df is not None:
        return df

    user = st.session_state.get("user") or {}
    first = (user.get("name") or "there").split()[0]
    theme.hero("Your journal is empty", f"Welcome, {first}. Let's add some numbers.",
               "Pick one to get started. You can switch to your own statement any time from Your data.")

    options = [
        ("upload", theme.BLUE, theme.BLUE_SOFT, "Your own statement",
         "Export a CSV from your bank or expense app — date, category, amount, type."),
        ("book", theme.OCHRE, theme.OCHRE_SOFT, "A demo year",
         "One year for a salaried person in Bangalore, with a few surprises hidden in it."),
        ("receipt", theme.VIOLET, theme.VIOLET_SOFT, "Five years of sample data",
         "A larger synthetic history — good for seeing long-term trends."),
    ]
    cols = st.columns(3, gap="medium")
    for col, (ic, ink, soft, title, text) in zip(cols, options):
        with col:
            theme.html(f"""
            <div class="pb-page pb-card rise" style="min-height:190px">
              <span style="width:48px;height:48px;border-radius:15px;display:grid;place-items:center;
                background:{soft};color:{ink}">{theme.icon(ic, 24)}</span>
              <div class="title" style="margin-top:14px">{title}</div>
              <div class="hint">{text}</div>
            </div>""")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        link("data", "Upload my CSV", icon=":material/upload_file:")
    with c2:
        if st.button("Load the demo year", type="primary", width="stretch"):
            data.set_data(data.load_demo(), "Demo year (Bangalore, 2025)")
            st.rerun()
    with c3:
        if st.button("Load 5 years of sample data", width="stretch"):
            data.set_data(data.load_sample(), "Sample dataset")
            st.rerun()
    st.stop()
