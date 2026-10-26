import numpy as np
import pandas as pd

# ============================================================
# EXPLAINABLE FINANCIAL HEALTH SCORE
# ------------------------------------------------------------
# Six components that add up to 100. Every component reports
# the points earned, the points it could have earned, the raw
# measurement behind it, and one concrete way to win points back.
# The score is computed from the monthly summary so the What-If
# Lab can re-score a simulated future with the same function.
# ============================================================


def _clamp(x, lo=0.0, hi=1.0):
    if x is None or np.isnan(x):
        return lo
    return float(min(max(x, lo), hi))


def _cv(series):
    series = pd.Series(series, dtype=float)
    mean = series.mean()
    if len(series) < 2 or mean <= 0:
        return np.nan
    return series.std() / mean


def grade_for(score):
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Needs Work"
    return "At Risk"


def compute_health(monthly):
    income = monthly["Income"].sum()
    expense = monthly["Expense"].sum()
    savings = income - expense
    months = len(monthly)
    avg_expense = expense / months if months else 0

    savings_rate = savings / income * 100 if income > 0 else -100.0
    expense_ratio = expense / income * 100 if income > 0 else 200.0
    positive_share = (monthly["Savings"] > 0).mean() if months else 0
    income_cv = _cv(monthly["Income"])
    expense_cv = _cv(monthly["Expense"])
    runway = max(savings, 0) / avg_expense if avg_expense > 0 else 0

    components = [
        {
            "name": "Savings power",
            "max": 30,
            "points": 30 * _clamp(savings_rate / 20),
            "value": f"{savings_rate:.1f}% of income saved",
            "target": "Full marks at a 20% savings rate",
            "tip": (
                "Automate a transfer on payday so saving happens before spending."
                if savings_rate < 20
                else "You're at or above the 20% benchmark — keep it automated."
            ),
        },
        {
            "name": "Spending control",
            "max": 20,
            "points": 20 * _clamp((120 - expense_ratio) / 50),
            "value": f"{expense_ratio:.1f}% of income spent",
            "target": "Full marks at 70% or less, zero at 120%",
            "tip": "Set a monthly cap on your largest discretionary category.",
        },
        {
            "name": "Positive months",
            "max": 15,
            "points": 15 * _clamp(positive_share),
            "value": f"{positive_share * 100:.0f}% of months ended in surplus",
            "target": "Full marks when every month ends positive",
            "tip": "Delay big purchases to months where income has already landed.",
        },
        {
            "name": "Income stability",
            "max": 10,
            "points": 10 * _clamp(1 - (income_cv - 0.25) / 1.0) if not np.isnan(income_cv) else 0,
            "value": "—" if np.isnan(income_cv) else f"{income_cv * 100:.0f}% month-to-month variation",
            "target": "Full marks at 25% variation or less",
            "tip": "Irregular income? Budget on your lowest typical month, not the average.",
        },
        {
            "name": "Spending steadiness",
            "max": 10,
            "points": 10 * _clamp(1 - (expense_cv - 0.25) / 1.0) if not np.isnan(expense_cv) else 0,
            "value": "—" if np.isnan(expense_cv) else f"{expense_cv * 100:.0f}% month-to-month variation",
            "target": "Full marks at 25% variation or less",
            "tip": "Spread annual costs (insurance, fees) into a monthly sinking fund.",
        },
        {
            "name": "Safety runway",
            "max": 15,
            "points": 15 * _clamp(runway / 6),
            "value": f"{runway:.1f} months of expenses saved",
            "target": "Full marks at a 6-month emergency buffer",
            "tip": "Park surplus in a separate account until it covers 6 months of costs.",
        },
    ]

    for c in components:
        c["points"] = round(c["points"], 1)
        c["lost"] = round(c["max"] - c["points"], 1)

    total = round(sum(c["points"] for c in components))

    return {
        "score": total,
        "grade": grade_for(total),
        "components": components,
        "biggest_leak": max(components, key=lambda c: c["lost"]),
        "savings_rate": savings_rate,
        "expense_ratio": expense_ratio,
        "runway": runway,
    }


def monthly_pulse(monthly):
    """A simple per-month score (0–100) from that month's savings and spend
    ratio, smoothed over three months — shows the direction of travel."""
    rate = np.where(monthly["Income"] > 0, monthly["Savings"] / monthly["Income"] * 100, -100)
    ratio = np.where(monthly["Income"] > 0, monthly["Expense"] / monthly["Income"] * 100, 200)

    pulse = 60 * np.clip(rate / 20, 0, 1) + 40 * np.clip((120 - ratio) / 50, 0, 1)
    out = monthly[["Month"]].copy()
    out["Pulse"] = pulse
    out["Trend"] = pd.Series(pulse).rolling(3, min_periods=1).mean().values
    return out
