import streamlit as st

from finsense import anomaly, charts, theme
from finsense.data import inr
from finsense.theme import esc
from finsense.views.common import require_data


def render():
    df = require_data()

    theme.hero(
        "Anomaly radar",
        "Spending that doesn't look like you",
        "The radar learns your normal — typical amounts per category, the days you usually spend, "
        "how often things recur — and flags what breaks the pattern, with the reasons why.",
    )

    scanned = anomaly.scan(df)
    if "Radar_Score" not in scanned or scanned["Radar_Score"].isna().all():
        st.info("The radar needs at least 20 expense transactions to learn your patterns.")
        return

    if "dismissed" not in st.session_state:
        st.session_state.dismissed = set()

    c1, c2 = st.columns([1, 2])
    with c1:
        top_pct = st.slider("Sensitivity — flag the top % most unusual", 1, 10, 3)
    with c2:
        cats = sorted(scanned["Category"].unique())
        chosen = st.multiselect("Categories", cats, default=cats)

    result = anomaly.flag(scanned, top_pct)
    result = result[result["Category"].isin(chosen)]
    result.loc[result["TxnID"].isin(st.session_state.dismissed), "Flagged"] = False
    flagged = result[result["Flagged"]].sort_values("Radar_Score", ascending=False)

    theme.stat_cards([
        ("Expenses scanned", f"{len(result):,}", "", "neutral"),
        ("Flagged", f"{len(flagged):,}", f"{len(flagged) / max(len(result), 1) * 100:.1f}% of expenses", "bad"),
        ("Possible duplicates", f"{int(flagged['Dup_Gap'].notna().sum())}", "same amount within 3 days", "warn"),
        ("Flagged value", inr(flagged["Amount"].sum()), "worth a second look", "warn"),
    ])

    st.markdown("#### Timeline")
    st.caption("Hover a red diamond to see why it was flagged.")
    charts.show(charts.radar_timeline(result))

    st.markdown("#### Flagged transactions")
    if flagged.empty:
        st.success("Nothing unusual at this sensitivity.")
    for row in flagged.head(20).itertuples():
        with st.container(border=True):
            a, b, c = st.columns([3, 1, 1])
            with a:
                desc = f" · {esc(row.Description)}" if row.Description else ""
                st.markdown(
                    f"**{esc(row.Category)}** · {inr(row.Amount)} · "
                    f"{row.Date:%a %d %b %Y}<span style='color:{theme.SOFT}'>{desc}</span>",
                    unsafe_allow_html=True,
                )
                theme.pills(row.Reasons, "bad" if row.Radar_Score >= 95 else "warn")
            with b:
                st.metric("Radar score", f"{row.Radar_Score:.0f}")
            with c:
                st.write("")
                if st.button("Looks fine", key=f"ok_{row.TxnID}", help="Hide this from the flagged list"):
                    st.session_state.dismissed.add(row.TxnID)
                    st.rerun()

    if st.session_state.dismissed:
        if st.button(f"Restore {len(st.session_state.dismissed)} dismissed"):
            st.session_state.dismissed = set()
            st.rerun()

    if not flagged.empty:
        export = flagged[["TxnID", "Date", "Description", "Category", "Amount", "Radar_Score"]].copy()
        export["Reasons"] = flagged["Reasons"].apply("; ".join)
        st.download_button("Download flagged list (CSV)", export.to_csv(index=False).encode("utf-8"),
                           "finsense_flagged.csv", "text/csv")

    st.markdown("#### Your normal, per category")
    ranges = anomaly.normal_ranges(df)
    st.dataframe(
        ranges.rename(columns={"count": "Purchases", "10%": "Low end", "50%": "Typical",
                               "90%": "High end", "max": "Largest"}),
        width="stretch",
        column_config={k: st.column_config.NumberColumn(format="₹%.0f")
                       for k in ["Low end", "Typical", "High end", "Largest"]},
    )

    with st.expander("How the radar works"):
        st.markdown(
            "- **Behaviour model** — an Isolation Forest is trained on *your* expenses using eight "
            "features: amount, how far it sits from your category median, the weekday, how often you "
            "spend in that category, the gap since your last purchase there, and how busy that day was.\n"
            "- **Amount check** — a robust z-score (median and MAD) per category, so a single huge "
            "purchase can't mask others.\n"
            "- **Radar score** — 60% behaviour model + 40% amount check, as a percentile (0–100).\n"
            "- **Reasons** come straight from the features, so every flag is explainable.\n"
            "- Same category + same amount within 3 days is always flagged as a possible duplicate charge."
        )
