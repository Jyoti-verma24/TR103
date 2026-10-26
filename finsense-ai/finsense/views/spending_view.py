import numpy as np
import pandas as pd
import streamlit as st

from finsense import charts, data, theme
from finsense.data import inr
from finsense.theme import esc
from finsense.views.common import require_data


def _category_table(cat_matrix):
    recent = cat_matrix.tail(6).mean()
    prior = cat_matrix.iloc[-12:-6].mean() if len(cat_matrix) >= 12 else pd.Series(np.nan, index=cat_matrix.columns)
    total = cat_matrix.sum()
    table = pd.DataFrame({
        "Total": total,
        "Share": total / total.sum() * 100,
        "Per month": cat_matrix.mean(),
        "Last 6 mo vs prior 6": np.where(prior > 0, (recent - prior) / prior * 100, np.nan),
    })
    return table.sort_values("Total", ascending=False)


def render():
    df = require_data()
    monthly = data.monthly_summary(df)
    cat_matrix = data.category_matrix(df)

    theme.hero("Spending", "Categories, months and every transaction",
               "Where the money goes, how that's shifting, and a searchable ledger.")

    table = _category_table(cat_matrix)
    rising = table["Last 6 mo vs prior 6"].dropna()
    if len(rising):
        up, down = rising.idxmax(), rising.idxmin()
        if rising[up] > 5:
            theme.insight(f"<b>{esc(up)}</b> is your fastest-growing category — up "
                          f"<b>{rising[up]:.0f}%</b> over the last six months.", "warn")
        if rising[down] < -5:
            theme.insight(f"<b>{esc(down)}</b> is shrinking — down <b>{abs(rising[down]):.0f}%</b> "
                          f"over the last six months.", "good")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("#### Top categories over time")
        st.caption("3-month rolling average.")
        charts.show(charts.category_trend(cat_matrix))
    with right:
        st.markdown("#### Category breakdown")
        st.dataframe(
            table, width="stretch",
            column_config={
                "Total": st.column_config.NumberColumn(format="₹%.0f"),
                "Share": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "Per month": st.column_config.NumberColumn(format="₹%.0f"),
                "Last 6 mo vs prior 6": st.column_config.NumberColumn(format="%+.0f%%"),
            },
        )

    st.markdown("#### Month by month")
    best = monthly.loc[monthly["Savings"].idxmax()]
    worst = monthly.loc[monthly["Savings"].idxmin()]
    theme.stat_cards([
        ("Best month", best["Month"], inr(best["Savings"], sign=True), "good"),
        ("Toughest month", worst["Month"], inr(worst["Savings"], sign=True), "bad"),
        ("Months in surplus", f"{(monthly['Savings'] > 0).sum()} / {len(monthly)}", "", "neutral"),
        ("Avg monthly spend", inr(monthly["Expense"].mean()), "", "neutral"),
    ])
    st.dataframe(
        monthly[["Month", "Income", "Expense", "Savings", "Savings_Rate"]].iloc[::-1],
        hide_index=True, width="stretch",
        column_config={
            "Income": st.column_config.NumberColumn(format="₹%.0f"),
            "Expense": st.column_config.NumberColumn(format="₹%.0f"),
            "Savings": st.column_config.NumberColumn("Net", format="₹%.0f"),
            "Savings_Rate": st.column_config.NumberColumn("Savings rate", format="%.1f%%"),
        },
    )

    st.markdown("#### Transaction explorer")
    f1, f2, f3 = st.columns([2, 2, 3])
    with f1:
        kinds = st.multiselect("Type", ["Income", "Expense"], default=["Income", "Expense"])
    with f2:
        cats = st.multiselect("Category", sorted(df["Category"].unique()))
    with f3:
        query = st.text_input("Search description")

    view = df[df["Type"].isin(kinds)]
    if cats:
        view = view[view["Category"].isin(cats)]
    if query:
        view = view[view["Description"].str.contains(query, case=False, na=False, regex=False)]

    st.caption(f"{len(view):,} transactions · {inr(view['Amount'].sum())}")
    st.dataframe(
        view.sort_values("Date", ascending=False), hide_index=True, width="stretch",
        column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f"),
                       "Date": st.column_config.DateColumn(format="DD MMM YYYY")},
    )
