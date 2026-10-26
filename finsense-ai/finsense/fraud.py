import os

import joblib
import numpy as np
import pandas as pd

from finsense.data import BASE_DIR

# ============================================================
# CARD FRAUD — EXPLANATIONS
# ------------------------------------------------------------
# The Random Forest only outputs a probability. To say *why* a
# payment looks like fraud we compare each of its values with a
# reference profile of genuine and fraudulent payments built from
# the training split (models/fraud_reference.pkl):
#   • how extreme is this value among genuine payments?
#   • is it extreme in the direction fraud usually goes?
#   • how much does the model rely on that feature?
# Plus two human-readable signals: amount and hour of day.
# ============================================================

FEATURES = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_fraud.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "random_forest_scaler.pkl")
REFERENCE_PATH = os.path.join(MODELS_DIR, "fraud_reference.pkl")
PCTS = [0.1, 1, 5, 25, 50, 75, 95, 99, 99.9]
GRID = np.linspace(0, 100, 2001)


def hour_of(time_seconds):
    """The dataset's Time is seconds since the first transaction (two days, starting at midnight)."""
    return (np.asarray(time_seconds) // 3600 % 24).astype(int)


def build_reference(X_train, y_train, model):
    genuine = X_train[y_train == 0]
    fraud = X_train[y_train == 1]
    hours = pd.Series(hour_of(genuine["Time"])).value_counts(normalize=True).reindex(range(24), fill_value=0)
    return {
        # 2,001 quantiles per feature: enough for percentile lookups, a few KB on disk.
        "genuine_grid": {f: np.percentile(genuine[f].values, GRID) for f in FEATURES},
        "genuine_pcts": genuine[FEATURES].quantile([p / 100 for p in PCTS]),
        "fraud_median": fraud[FEATURES].median(),
        "genuine_median": genuine[FEATURES].median(),
        "importance": pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False),
        "genuine_hour_share": hours,
        "fraud_hour_share": pd.Series(hour_of(fraud["Time"])).value_counts(normalize=True)
        .reindex(range(24), fill_value=0),
    }


def load_reference():
    return joblib.load(REFERENCE_PATH) if os.path.exists(REFERENCE_PATH) else None


def _genuine_percentile(ref, feature, value):
    return float(np.interp(value, ref["genuine_grid"][feature], GRID))


def explain(row, ref, top_n=4):
    """Return a list of plain-language reasons for one transaction (raw, unscaled values)."""
    reasons = []
    importance = ref["importance"]
    rank = {f: i + 1 for i, f in enumerate(importance.index)}

    # --- anonymised bank signals --------------------------------------------
    scored = []
    for f in importance.index[:12]:
        if f in ("Time", "Amount"):
            continue
        value = row[f]
        pct = _genuine_percentile(ref, f, value)
        fraud_side = np.sign(ref["fraud_median"][f] - ref["genuine_median"][f])
        towards_fraud = np.sign(value - ref["genuine_median"][f]) == fraud_side
        if not towards_fraud:
            continue
        extremeness = pct if fraud_side > 0 else 100 - pct
        if extremeness >= 99:
            scored.append((importance[f] * extremeness, f, value, extremeness, fraud_side))

    for _, f, value, extremeness, side in sorted(scored, reverse=True)[:top_n]:
        word = "higher" if side > 0 else "lower"
        share = max(round(extremeness, 1), 99.0) if extremeness < 99.95 else 99.9
        reasons.append(
            f"Signal {f} is {value:.1f} — {word} than {share:g}% of genuine payments "
            f"(the model's #{rank[f]} fraud signal)"
        )

    # --- amount ---------------------------------------------------------------
    amount = row["Amount"]
    amt_pct = _genuine_percentile(ref, "Amount", amount)
    if amount <= 1.0:
        reasons.append(f"Tiny amount (€{amount:.2f}) — fraudsters often test a card with a small charge first")
    elif amt_pct >= 99:
        reasons.append(f"Large amount (€{amount:,.2f}) — bigger than {amt_pct:.0f}% of genuine payments")

    # --- hour of day ------------------------------------------------------------
    hour = int(hour_of(row["Time"]))
    g_share = ref["genuine_hour_share"][hour] * 100
    f_share = ref["fraud_hour_share"][hour] * 100
    if g_share < 2.5 and f_share > g_share * 1.5:
        reasons.append(
            f"Made around {hour:02d}:00 — only {g_share:.1f}% of genuine payments happen in this hour, "
            f"vs {f_share:.1f}% of frauds"
        )

    return reasons


def verdict(probability, threshold):
    if probability >= 0.8:
        return "Very likely fraud", "bad"
    if probability >= threshold:
        return "Suspicious", "warn"
    if probability >= threshold / 2:
        return "Borderline", "info"
    return "Looks genuine", "good"


def feature_profile(row, ref, features):
    """For the lookup chart: genuine p1/p50/p99, fraud median and this value per feature."""
    p = ref["genuine_pcts"]
    return pd.DataFrame({
        "Feature": features,
        "Genuine low": [p.loc[0.01, f] for f in features],
        "Genuine typical": [p.loc[0.5, f] for f in features],
        "Genuine high": [p.loc[0.99, f] for f in features],
        "Fraud typical": [ref["fraud_median"][f] for f in features],
        "This payment": [row[f] for f in features],
    })
