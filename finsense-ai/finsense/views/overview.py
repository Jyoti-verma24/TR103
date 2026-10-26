import streamlit as st

from finsense import anomaly, charts, data, forecast, health, personality, theme
from finsense.data import inr
from finsense.theme import esc
from finsense.views.common import link, require_data


def _amount(x):
    return inr(x, 2).replace("₹", "")


def _statement(df, scanned, entries=12):
    """The last few entries as passbook rows, with a running balance and the radar's circles."""
    notes = {}
    if "Radar_Score" in scanned and scanned["Radar_Score"].notna().any():
        flagged = anomaly.flag(scanned, 3)
        for r in flagged[flagged["Flagged"]].itertuples():
            if r.Dup_Gap == r.Dup_Gap:
                notes[r.TxnID] = "charged twice?"
            elif r.Ratio >= 1.5:
                notes[r.TxnID] = f"{r.Ratio:.1f}× your usual"
            else:
                notes[r.TxnID] = "unusual for you"

    signed = df["Amount"].where(df["Type"] == "Income", -df["Amount"])
    page = df.assign(Balance=signed.cumsum()).tail(entries)
    rows = []
    for r in page.itertuples():
        desc = str(r.Description).strip()
        rows.append({
            "date": r.Date.strftime("%d-%m-%y"),
            "particulars": f"{r.Category} · {desc[:28]}" if desc else r.Category,
            "withdrawal": _amount(r.Amount) if r.Type == "Expense" else "",
            "deposit": _amount(r.Amount) if r.Type == "Income" else "",
            "balance": _amount(r.Balance),
            "flag": notes.get(r.TxnID),
        })
    shown = set(page["TxnID"])
    elsewhere = sum(1 for t in notes if t not in shown)
    return rows, ("Balance c/f", _amount(page["Balance"].iloc[-1])), elsewhere


def render():
    df = require_data()
    stats = data.headline_stats(df)
    monthly = data.monthly_summary(df)
    score = health.compute_health(monthly)

    theme.hero(
        f"Overview · {stats['start'].strftime('%b %Y')} – {stats['end'].strftime('%b %Y')}",
        "Your money, at a glance",
        f"{stats['transactions']:,} transactions across {stats['months']} months.",
    )

    net_tone = "good" if stats["savings"] >= 0 else "bad"
    theme.stat_cards([
        ("Money in", inr(stats["income"]), f"{inr(stats['income'] / stats['months'])} / month avg", "info"),
        ("Money out", inr(stats["expense"]), f"{inr(stats['expense'] / stats['months'])} / month avg", "bad"),
        ("Net", inr(stats["savings"], sign=True),
         f"savings rate {data.pct(stats['savings_rate'])}", net_tone),
        ("Health score", f"{score['score']}/100", score["grade"], theme.score_tone(score["score"])),
    ])

    scanned = anomaly.scan(df)
    st.markdown("#### Latest entries")
    st.caption("Your most recent transactions, printed passbook-style. Entries the radar finds unusual are circled.")
    rows, total, circled_elsewhere = _statement(df, scanned)
    theme.html(theme.ledger(rows, total))
    if circled_elsewhere:
        theme.insight(f"The radar circled <b>{circled_elsewhere} more entries</b> on earlier pages — "
                      "open the Anomaly radar to see them all.", "bad")

    left, right = st.columns([2, 1], gap="large")
    with left:
        st.markdown("#### Cash flow by month")
        charts.show(charts.cashflow(monthly))
    with right:
        st.markdown("#### Where it goes")
        charts.show(charts.category_donut(stats["by_category"]))

    st.markdown("#### A few things we spotted")

    leak = score["biggest_leak"]
    theme.insight(
        f"Your health score is <b>{score['score']}/100 ({esc(score['grade'])})</b>. "
        f"The biggest leak is <b>{esc(leak['name'])}</b> — {esc(leak['value'])}, "
        f"costing {leak['lost']:.0f} points.",
        theme.score_tone(score["score"]),
    )

    if "Radar_Score" in scanned and scanned["Radar_Score"].notna().any():
        flagged = anomaly.flag(scanned, 3)
        flagged = flagged[flagged["Flagged"]].sort_values("Radar_Score", ascending=False)
        if len(flagged):
            top = flagged.iloc[0]
            theme.insight(
                f"The radar flagged <b>{len(flagged)} unusual expenses</b>. Most unusual: "
                f"{esc(top['Category'])} {inr(top['Amount'])} on {top['Date']:%d %b %Y} — "
                f"{esc(top['Reasons'][0])}.",
                "bad",
            )

    found = personality.traits(df)
    persona = personality.archetype(found)
    theme.insight(f"Your money personality: <b>{esc(persona['name'])}</b>. "
                  f"{esc(persona['line'])}", "info")

    if len(monthly) >= 3:
        sim = forecast.simulate(monthly, horizon=12)
        mid = sim["balance"]["P50"].iloc[-1]
        p_def = sim["p_deficit_month"][0] * 100
        theme.insight(
            f"If nothing changes, the likely net position 12 months from now is "
            f"<b>{inr(mid, sign=True)}</b>, and there's a <b>{p_def:.0f}% chance</b> next month "
            f"ends in deficit.",
            "good" if mid >= 0 else "warn",
        )

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        link("health", "Explain my score", icon=":material/favorite:")
    with c2:
        link("radar", "Open the radar", icon=":material/radar:")
    with c3:
        link("whatif", "Try a what-if", icon=":material/tune:")
    with c4:
        link("persona", "See my personality", icon=":material/fingerprint:")
