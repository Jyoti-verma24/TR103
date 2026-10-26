import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import IsolationForest

from finsense.data import inr

# ============================================================
# PERSONAL ANOMALY RADAR
# ------------------------------------------------------------
# Learns what "normal" looks like for *this* person — per
# category amounts, which weekdays they usually spend on, how
# often each category recurs, how busy a typical day is — then
# scores every expense against that baseline.
#
# Two signals are blended:
#   • Isolation Forest over behavioural features (how hard is
#     this transaction to "explain" given the rest?)
#   • Robust z-score of the amount within its own category
#     (median/MAD, so one huge outlier can't hide others)
#
# Each flagged transaction carries plain-language reasons that
# come straight from the features, so the user sees *why*.
# ============================================================

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _percentile_rank(values):
    return pd.Series(values).rank(pct=True).values * 100


@st.cache_data
def build_features(df):
    ex = df[df["Type"] == "Expense"].copy().sort_values("Date").reset_index(drop=True)
    if ex.empty:
        return ex

    grp = ex.groupby("Category")["Amount"]
    ex["Cat_Median"] = grp.transform("median")
    mad = grp.transform(lambda s: (s - s.median()).abs().median())
    ex["Cat_MAD"] = mad.replace(0, np.nan).fillna(ex["Cat_Median"] * 0.25 + 1)
    ex["Robust_Z"] = (ex["Amount"] - ex["Cat_Median"]) / (1.4826 * ex["Cat_MAD"])
    ex["Ratio"] = ex["Amount"] / ex["Cat_Median"].replace(0, np.nan)
    ex["Cat_Pctile"] = grp.rank(pct=True) * 100
    ex["Cat_Count"] = grp.transform("count")
    ex["Cat_Share"] = ex["Cat_Count"] / len(ex)

    # Running maximum per category → was this a new record?
    ex["Prev_Cat_Max"] = grp.transform(lambda s: s.cummax().shift(1))
    ex["Is_Record"] = (ex["Prev_Cat_Max"].notna()) & (ex["Amount"] > ex["Prev_Cat_Max"])

    # Weekday habits
    ex["DOW"] = ex["Date"].dt.dayofweek
    dow_counts = ex.groupby(["Category", "DOW"])["Amount"].transform("count")
    ex["Cat_DOW_Share"] = dow_counts / ex["Cat_Count"]

    # Recurrence: days since the previous expense in the same category
    ex["Gap_Days"] = ex.groupby("Category")["Date"].diff().dt.days
    ex["Gap_P90"] = ex.groupby("Category")["Gap_Days"].transform(lambda s: s.quantile(0.9))

    # How busy was the day overall?
    day = ex.groupby(ex["Date"].dt.normalize())["Amount"]
    ex["Day_Total"] = day.transform("sum")
    ex["Day_Count"] = day.transform("count")

    # Same category + same amount within 3 days → possible double charge
    ex["Amt_Key"] = ex["Amount"].round(0)
    prev_same = ex.groupby(["Category", "Amt_Key"])["Date"].diff().dt.days
    ex["Dup_Gap"] = prev_same.where(prev_same <= 3)

    return ex


@st.cache_data
def scan(df):
    ex = build_features(df)
    if len(ex) < 20:
        return ex.assign(Radar_Score=np.nan)

    features = pd.DataFrame({
        "log_amount": np.log1p(ex["Amount"]),
        "robust_z": ex["Robust_Z"].clip(-10, 10),
        "ratio": ex["Ratio"].fillna(1).clip(0, 20),
        "log_day_total": np.log1p(ex["Day_Total"]),
        "day_count": ex["Day_Count"],
        "log_gap": np.log1p(ex["Gap_Days"].fillna(ex["Gap_Days"].median())),
        "dow_share": ex["Cat_DOW_Share"],
        "cat_share": ex["Cat_Share"],
    })

    model = IsolationForest(n_estimators=300, contamination="auto", random_state=42)
    model.fit(features)
    iso = -model.score_samples(features)

    ex["Model_Score"] = _percentile_rank(iso)
    ex["Amount_Score"] = _percentile_rank(ex["Robust_Z"].clip(lower=0))
    ex["Radar_Score"] = (0.6 * ex["Model_Score"] + 0.4 * ex["Amount_Score"]).round(1)
    ex["Reasons"] = [_reasons(row, ex) for row in ex.itertuples(index=False)]
    return ex


def _reasons(row, ex):
    reasons = []
    cat = row.Category

    if row.Dup_Gap == row.Dup_Gap:  # not NaN
        days = int(row.Dup_Gap)
        when = "the same day" if days == 0 else f"{days} day{'s' if days > 1 else ''} earlier"
        reasons.append(f"Possible duplicate — same {cat} amount charged {when}")

    if row.Ratio >= 1.5:
        reasons.append(f"{row.Ratio:.1f}× your typical {cat} spend ({inr(row.Cat_Median)})")
    elif row.Cat_Pctile >= 95:
        reasons.append(f"In your top 5% of {cat} purchases")

    if row.Is_Record:
        reasons.append(f"Your biggest {cat} purchase up to that point")

    if row.Day_Count >= max(3, ex["Day_Count"].quantile(0.97)):
        reasons.append(f"Busy day — {int(row.Day_Count)} expenses totalling {inr(row.Day_Total)}")
    elif row.Day_Total >= ex["Day_Total"].quantile(0.97):
        reasons.append(f"Heavy day — {inr(row.Day_Total)} spent in total")

    if row.Cat_Count >= 20 and row.Cat_DOW_Share < 0.08:
        reasons.append(f"You rarely spend on {cat} on a {DOW[row.DOW]}")

    if row.Gap_Days == row.Gap_Days and row.Gap_Days >= 30 and row.Gap_Days >= row.Gap_P90:
        reasons.append(f"First {cat} spend in {int(row.Gap_Days)} days")

    if not reasons:
        reasons.append("Unusual mix of amount, timing and category for you")
    return reasons


def flag(scanned, top_percent):
    """Flag the top N% by radar score, plus every likely duplicate."""
    cutoff = np.percentile(scanned["Radar_Score"], 100 - top_percent)
    flagged = (scanned["Radar_Score"] >= cutoff) | scanned["Dup_Gap"].notna()
    return scanned.assign(Flagged=flagged)


def normal_ranges(df):
    ex = df[df["Type"] == "Expense"]
    out = ex.groupby("Category")["Amount"].describe(percentiles=[0.1, 0.5, 0.9])
    return out[["count", "10%", "50%", "90%", "max"]].sort_values("50%", ascending=False)
