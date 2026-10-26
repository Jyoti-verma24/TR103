import pandas as pd
import streamlit as st

from finsense import data, theme
from finsense.views.common import link


def render():
    theme.hero(
        "Step 1 · Your data",
        "Bring your transactions",
        "FinSense runs entirely on this machine — nothing you upload leaves the app. "
        "Export a statement from your bank or expense tracker as CSV and drop it below.",
    )

    left, right = st.columns([3, 2], gap="large")

    with left:
        uploaded = st.file_uploader("Transaction CSV", type=["csv"])
        # Only ingest a file once, so the sample button isn't overridden on rerun.
        if uploaded is not None and st.session_state.get("ingested_file") != uploaded.file_id:
            st.session_state.ingested_file = uploaded.file_id
            try:
                df, notes = data.clean_transactions(pd.read_csv(uploaded))
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Couldn't read that file: {e}")
            else:
                data.set_data(df, uploaded.name)
                for note in notes:
                    st.warning(note)
                st.success(f"Loaded {len(df):,} transactions from **{uploaded.name}**.")

        st.markdown("**No CSV handy?**")
        if st.button("Use the sample dataset (2020–2024, 1,500 transactions)"):
            data.set_data(data.load_sample(), "Sample dataset")
            st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("**Expected columns**")
            st.dataframe(
                pd.DataFrame({
                    "Date": ["2026-01-01", "2026-01-03", "2026-01-05"],
                    "Category": ["Salary", "Rent", "Food & Drink"],
                    "Amount": [50000, 15000, 2500],
                    "Type": ["Income", "Expense", "Expense"],
                }),
                hide_index=True,
                width="stretch",
            )
            st.caption("An optional `Description` column is shown in the radar and explorer.")

    df = data.get_data()
    if df is None:
        return

    st.divider()
    stats = data.headline_stats(df)
    theme.stat_cards([
        ("Source", st.session_state.get("data_source", "—"), "", "neutral"),
        ("Transactions", f"{stats['transactions']:,}", f"{stats['months']} months", "neutral"),
        ("Covers", stats["start"].strftime("%d %b %Y"), f"to {stats['end'].strftime('%d %b %Y')}", "neutral"),
        ("Categories", f"{df['Category'].nunique()}", f"top spend: {stats['top_category']}", "neutral"),
    ])
    st.dataframe(df.tail(10), hide_index=True, width="stretch")
    link("overview", "Continue to your overview →")
