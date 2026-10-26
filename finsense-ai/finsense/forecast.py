import numpy as np
import pandas as pd

# ============================================================
# MONTE CARLO CASH-FLOW FORECAST
# ------------------------------------------------------------
# Instead of one straight line, we simulate thousands of
# possible futures:
#   1. Fit a robust (Theil–Sen), damped trend to recent monthly
#      income and expenses — one-off spikes don't bend it, and
#      damping stops a short trend running away.
#   2. Each simulated month = trend + a residual drawn from the
#      person's own history (their real month-to-month noise).
#   3. Report the 10th / 50th / 90th percentile paths and the
#      probability of hitting a savings goal.
# ============================================================

N_SIMS = 3000
LOOKBACK = 24
DAMPING = 0.85


def _trend_and_residuals(values):
    y = np.asarray(values, dtype=float)[-LOOKBACK:]
    x = np.arange(len(y))
    # Theil–Sen (median of pairwise slopes) so a one-off spike — a laptop,
    # a wedding month — can't drag the whole trend line with it.
    if len(y) >= 3:
        i, j = np.triu_indices(len(y), k=1)
        slope = np.median((y[j] - y[i]) / (j - i))
        intercept = np.median(y - slope * x)
    else:
        slope, intercept = 0.0, np.median(y)
    fitted = intercept + slope * x
    # Start from where the person is now (median of the last 6 months), and
    # trust the slope less when there's little history — 12 months of data
    # can't tell a real trend from one festive season.
    level = np.median(y[-6:])
    slope *= len(y) / (len(y) + 24)
    return level, slope, y - fitted


def _project(values, horizon, rng):
    last, slope, residuals = _trend_and_residuals(values)
    damp = np.cumsum(DAMPING ** np.arange(1, horizon + 1))
    trend = last + slope * damp
    noise = rng.choice(residuals, size=(N_SIMS, horizon), replace=True)
    return np.clip(trend + noise, 0, None)


def simulate(monthly, horizon=12, start_balance=0.0, seed=7):
    rng = np.random.default_rng(seed)
    income = _project(monthly["Income"].values, horizon, rng)
    expense = _project(monthly["Expense"].values, horizon, rng)
    savings = income - expense
    balance = start_balance + np.cumsum(savings, axis=1)

    last_period = monthly["Period"].iloc[-1]
    labels = [(last_period + i).strftime("%b %Y") for i in range(1, horizon + 1)]

    def bands(arr):
        p10, p50, p90 = np.percentile(arr, [10, 50, 90], axis=0)
        return pd.DataFrame({"Month": labels, "P10": p10, "P50": p50, "P90": p90})

    return {
        "labels": labels,
        "income": bands(income),
        "expense": bands(expense),
        "savings": bands(savings),
        "balance": bands(balance),
        "balance_paths": balance,
        "p_deficit_month": (savings < 0).mean(axis=0),
    }


def goal_odds(sim, goal):
    """Probability the balance reaches `goal` by each month, and the median
    month it's first reached (None if the median path never gets there)."""
    reached = sim["balance_paths"] >= goal
    by_month = reached.mean(axis=0)
    hit_any = reached.any(axis=1)
    first = np.where(hit_any, reached.argmax(axis=1), np.inf)
    median_first = np.median(first)
    month = None if np.isinf(median_first) else sim["labels"][int(median_first)]
    return by_month, month


def apply_scenario(monthly, cat_matrix, category_change, income_change=0.0,
                   extra_expense=0.0, extra_income=0.0):
    """Re-write history as if the person had followed the scenario all along.

    category_change: {category: percent change, e.g. -20}
    """
    adjusted = monthly.copy()
    delta = pd.Series(0.0, index=cat_matrix.index)
    for cat, change in category_change.items():
        if change and cat in cat_matrix.columns:
            delta += cat_matrix[cat] * change / 100

    adjusted["Expense"] = (
        adjusted["Expense"].values + delta.reindex(adjusted["Period"]).fillna(0).values + extra_expense
    ).clip(min=0)
    adjusted["Income"] = (adjusted["Income"] * (1 + income_change / 100) + extra_income).clip(lower=0)
    adjusted["Savings"] = adjusted["Income"] - adjusted["Expense"]
    adjusted["Savings_Rate"] = np.where(
        adjusted["Income"] > 0, adjusted["Savings"] / adjusted["Income"] * 100, np.nan
    )
    return adjusted
