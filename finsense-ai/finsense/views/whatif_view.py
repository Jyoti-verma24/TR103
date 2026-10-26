import streamlit as st

from finsense import charts, data, forecast, health, theme
from finsense.data import inr
from finsense.theme import esc
from finsense.views.common import require_data


def render():
    df = require_data()
    monthly = data.monthly_summary(df)
    cat_matrix = data.category_matrix(df)

    theme.hero(
        "What-if lab",
        "Change a habit, watch your future move",
        "Adjust spending and income below. FinSense simulates 3,000 possible futures from your "
        "own month-to-month ups and downs and shows the likely range — not a single guess.",
    )

    if len(monthly) < 3:
        st.info("The simulator needs at least 3 months of history.")
        return

    controls, results = st.columns([1, 2], gap="large")

    with controls:
        with st.container(border=True):
            st.markdown("**Income**")
            income_change = st.slider("Change in income", -30, 50, 0, 5, format="%d%%")
            extra_income = st.number_input("New monthly side income (₹)", 0, step=1000)

            st.markdown("**Spending by category**")
            top_cats = cat_matrix.sum().sort_values(ascending=False).head(6).index
            changes = {}
            for cat in top_cats:
                avg = cat_matrix[cat].mean()
                changes[cat] = st.slider(f"{cat} · avg {inr(avg)}/mo", -100, 50, 0, 5,
                                         format="%d%%", key=f"cut_{cat}")
            extra_expense = st.number_input("New monthly commitment, e.g. EMI (₹)", 0, step=1000)

            st.markdown("**Goal**")
            horizon = st.select_slider("Look ahead", [6, 12, 18, 24, 36], value=12,
                                       format_func=lambda m: f"{m} months")
            start_balance = st.number_input("Savings you have today (₹)", 0, step=5000)
            goal = st.number_input("Savings goal (₹)", 0, value=100000, step=10000)

    scenario_monthly = forecast.apply_scenario(
        monthly, cat_matrix, changes, income_change, extra_expense, extra_income
    )
    base_sim = forecast.simulate(monthly, horizon, start_balance)
    scen_sim = forecast.simulate(scenario_monthly, horizon, start_balance)
    base_score = health.compute_health(monthly)["score"]
    scen_score = health.compute_health(scenario_monthly)["score"]
    base_odds, base_month = forecast.goal_odds(base_sim, goal)
    scen_odds, scen_month = forecast.goal_odds(scen_sim, goal)

    monthly_gain = (scenario_monthly["Savings"] - monthly["Savings"]).mean()
    base_end = base_sim["balance"]["P50"].iloc[-1]
    scen_end = scen_sim["balance"]["P50"].iloc[-1]

    with results:
        theme.stat_cards([
            ("Extra per month", inr(monthly_gain, sign=True), "vs your current habits",
             "good" if monthly_gain >= 0 else "bad"),
            (f"Likely balance in {horizon} mo", inr(scen_end, sign=True),
             f"was {inr(base_end, sign=True)}", "good" if scen_end >= base_end else "bad"),
            ("Health score", f"{scen_score}/100", f"was {base_score}/100",
             "good" if scen_score > base_score else "neutral" if scen_score == base_score else "bad"),
            ("Chance of hitting goal", f"{scen_odds[-1] * 100:.0f}%", f"was {base_odds[-1] * 100:.0f}%",
             "good" if scen_odds[-1] >= base_odds[-1] else "bad"),
        ])

        st.markdown("#### Projected savings balance")
        st.caption("Solid line = most likely path. Shaded band = 80% of simulated futures land here.")
        charts.show(charts.fan(base_sim["balance"], scen_sim["balance"], goal or None))

        changed = {k: v for k, v in changes.items() if v}
        if not changed and not (income_change or extra_income or extra_expense):
            theme.insight("Move a slider to build a scenario — the violet band will show its future.", "info")
        else:
            biggest = max(
                changed.items(),
                key=lambda kv: abs(cat_matrix[kv[0]].mean() * kv[1] / 100),
                default=None,
            )
            if biggest:
                cat, change = biggest
                freed = -cat_matrix[cat].mean() * change / 100
                theme.insight(
                    f"Your biggest lever is <b>{esc(cat)}</b>: a {change:+d}% change moves "
                    f"<b>{inr(freed, sign=True)}</b> a month — {inr(freed * 12, sign=True)} a year.",
                    "good" if freed > 0 else "warn",
                )
            if scen_month:
                was = f" (currently {base_month})" if base_month else " (unreachable on current habits)"
                theme.insight(f"You'd most likely reach <b>{inr(goal)}</b> by <b>{scen_month}</b>{was}.", "good")
            elif goal:
                theme.insight(f"Even with this scenario, the likely path doesn't reach {inr(goal)} "
                              f"within {horizon} months. Try a bigger change or a longer horizon.", "warn")

            risk = scen_sim["p_deficit_month"].mean() * 100
            theme.insight(f"In this scenario, an average future month has a <b>{risk:.0f}%</b> chance "
                          f"of ending in deficit (was {base_sim['p_deficit_month'].mean() * 100:.0f}%).",
                          "warn" if risk > 30 else "good")

    with st.expander("How the simulation works"):
        st.markdown(
            "1. Monthly income and spending are fitted with a **damped trend** over the last 24 months, "
            "so a short-term rise doesn't extrapolate forever.\n"
            "2. Each simulated month adds a **residual drawn from your own history** — your real "
            "month-to-month volatility, not a textbook bell curve.\n"
            "3. 3,000 futures are simulated; the chart shows the 10th, 50th and 90th percentiles.\n"
            "4. Scenarios rewrite your history *as if* you'd always had the new habit, then re-run the "
            "same simulation and the same health score — so before/after is a fair comparison.\n\n"
            "This is a planning tool, not financial advice."
        )
