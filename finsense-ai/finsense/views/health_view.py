import streamlit as st

from finsense import charts, data, health, theme
from finsense.theme import esc
from finsense.views.common import require_data


def render():
    df = require_data()
    monthly = data.monthly_summary(df)
    score = health.compute_health(monthly)
    tone = theme.score_tone(score["score"])

    theme.hero(
        "Health check",
        "How healthy is your money?",
        "Six everyday habits, each worth a few points, adding up to 100. "
        "Each card below shows what was measured and how to win the points back.",
    )

    leak = score["biggest_leak"]
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown(
            f'<div class="pb-page pb-score rise">'
            f'{theme.stamp(score["score"], score["grade"], tone)}'
            f'<div><div class="pb-eyebrow" style="color:{theme.TONE_COLOR[tone]}">Out of 100</div>'
            f'<div style="font-size:1.5rem;font-weight:600;margin-top:4px">{esc(score["grade"])}</div>'
            f'<div style="color:{theme.SOFT};margin-top:6px;line-height:1.6">'
            f'Most points were lost on <b style="color:{theme.INK}">{esc(leak["name"].lower())}</b> '
            f'(−{leak["lost"]:.0f}).</div></div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("#### From a perfect 100 down to yours")
        charts.show(charts.score_waterfall(score))

    st.markdown("#### The six habits")
    cols = st.columns(3)
    for i, c in enumerate(score["components"]):
        share = c["points"] / c["max"]
        c_tone = "good" if share >= 0.8 else "info" if share >= 0.5 else "warn" if share >= 0.25 else "bad"
        with cols[i % 3]:
            st.markdown(
                f'<div class="pb-page pb-card rise" style="animation-delay:{i * 40}ms">'
                f'<div class="pb-eyebrow" style="color:{theme.TONE_COLOR[c_tone]}">Habit {i + 1:02d}</div>'
                f'<div class="title" style="margin-top:4px">{esc(c["name"])}</div>'
                f'<div style="font-size:1.6rem;font-weight:600;margin-top:6px">{c["points"]:.0f}'
                f'<span style="color:{theme.SOFT};font-size:1rem;font-weight:500"> / {c["max"]}</span></div>'
                f'{theme.bar(share, c_tone)}'
                f'<div class="body">{esc(c["value"])}</div>'
                f'<div class="hint">{esc(c["target"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### Month by month")
    st.caption("A quick per-month score from that month's savings rate and spend ratio, "
               "with a 3-month trend line to show which way you're heading.")
    charts.show(charts.pulse_line(health.monthly_pulse(monthly)))

    st.markdown("#### Where to start")
    st.caption("Ordered by how many points each fix is worth.")
    plan = sorted(score["components"], key=lambda c: c["lost"], reverse=True)
    for c in plan[:3]:
        if c["lost"] < 1:
            continue
        theme.insight(f"<b>{esc(c['name'])}: up to {c['lost']:.0f} points back</b><br>{esc(c['tip'])}", "info")
