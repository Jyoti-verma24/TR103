import streamlit as st

from finsense import charts, personality, theme
from finsense.theme import esc
from finsense.views.common import require_data

TONE = {"positive": "good", "neutral": "info", "watch": "warn"}


def _strength_label(s):
    if s >= 0.7:
        return "Strong"
    if s >= 0.35:
        return "Moderate"
    if s > 0.05:
        return "Mild"
    return "Not you"


def render():
    df = require_data()
    found = personality.traits(df)
    persona = personality.archetype(found)

    theme.hero(
        "Money personality",
        "How you spend, not just how much",
        "These habits come from when and how you spend. Each one shows the numbers behind it.",
        tone="plum",
    )

    theme.html(f"""
    <div class="pb-page pb-sheet rise" style="padding:0 28px 26px 66px;margin-bottom:8px">
      <div class="pb-printhead" style="padding-top:12px"><span>Teller's assessment</span><span>Based on your entries</span></div>
      <div style="display:inline-block;margin:26px 0 6px;padding:10px 20px;border:3px double {theme.VIOLET};
        color:{theme.VIOLET};transform:rotate(-2deg);opacity:.92">
        <div style="font:700 .72rem {theme.TYPE};letter-spacing:.2em">YOU ARE</div>
        <div style="font:700 1.9rem {theme.SERIF};text-transform:uppercase;letter-spacing:.04em">{esc(persona["name"])}</div>
      </div>
      <div style="font:500 1.3rem/32px {theme.HAND};color:{theme.BLUE};max-width:720px">{esc(persona["line"])}</div>
    </div>""")

    st.markdown("#### Your traits")
    cols = st.columns(2)
    for i, t in enumerate(found):
        tone = TONE[t["tone"]] if t["strength"] > 0.05 else "neutral"
        ink = theme.TONE_COLOR[tone]
        with cols[i % 2]:
            st.markdown(
                f'<div class="pb-page pb-card rise" style="animation-delay:{i * 40}ms">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                f'<span class="pb-eyebrow" style="color:{ink}">Trait {i + 1:02d}</span>'
                f'<span class="pb-pill" style="--ink:{ink};--soft-bg:{theme.TONES[tone][1]}">'
                f'{_strength_label(t["strength"])}</span></div>'
                f'<div class="title">{esc(t["name"])}</div>'
                f'{theme.bar(t["strength"], tone)}'
                f'<div class="body">{esc(t["evidence"])}</div>'
                f'<div class="hint">Try this: {esc(t["nudge"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### When your money moves")
    st.caption("Average spend per day, by weekday and by week of the month. Darker squares are your busier days.")
    charts.show(charts.heatmap(personality.heatmap(df)))
