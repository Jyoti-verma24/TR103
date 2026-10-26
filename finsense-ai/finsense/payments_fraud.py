import os

import joblib
import numpy as np
import pandas as pd

from finsense.data import BASE_DIR, inr

# ============================================================
# MOBILE-PAYMENT FRAUD (PaySim) — EXPLAINABLE
# ------------------------------------------------------------
# Unlike the Kaggle card data (anonymised V1–V28), PaySim keeps
# real meanings: who paid, how much, and every balance before
# and after. So each flag can be explained in plain words, and
# every reason quotes how often that pattern shows up in fraud
# vs genuine payments — measured on the training data, not
# assumed.
# ============================================================

MODEL_PATH = os.path.join(BASE_DIR, "models", "paysim_fraud.pkl")
REFERENCE_PATH = os.path.join(BASE_DIR, "models", "paysim_reference.pkl")

REQUIRED = ["step", "type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
RISKY_TYPES = ["TRANSFER", "CASH_OUT"]  # in PaySim, fraud only ever happens on these two

FEATURES = [
    "is_transfer", "log_amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest",
    "drain_ratio", "exact_drain", "receiver_stays_zero", "hour", "is_night",
]


def hour_of(step):
    return np.asarray(step) % 24


def day_of(step):
    return (np.asarray(step) - 1) // 24 + 1


def features(df):
    out = pd.DataFrame(index=df.index)
    out["is_transfer"] = (df["type"] == "TRANSFER").astype(int)
    out["log_amount"] = np.log1p(df["amount"])
    for col in ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
        out[col] = df[col]
    out["drain_ratio"] = (df["amount"] / (df["oldbalanceOrg"] + 1)).clip(0, 10)
    out["exact_drain"] = ((df["oldbalanceOrg"] > 0) & ((df["amount"] - df["oldbalanceOrg"]).abs() < 1)).astype(int)
    out["receiver_stays_zero"] = ((df["oldbalanceDest"] == 0) & (df["newbalanceDest"] == 0)
                                  & (df["amount"] > 0)).astype(int)
    out["hour"] = hour_of(df["step"])
    out["is_night"] = (out["hour"] < 6).astype(int)
    return out[FEATURES]


# Each signal: a test on one payment, and how to say it in words.
SIGNALS = {
    "exact_drain": (
        lambda r: r["oldbalanceOrg"] > 0 and abs(r["amount"] - r["oldbalanceOrg"]) < 1,
        lambda r: f"Emptied the sender's account — sent {inr(r['amount'])}, their entire balance",
    ),
    "receiver_stays_zero": (
        lambda r: r["amount"] > 0 and r["oldbalanceDest"] == 0 and r["newbalanceDest"] == 0,
        lambda r: f"The {inr(r['amount'])} never showed up — the receiver's balance stayed at ₹0 before and after",
    ),
    "is_night": (
        lambda r: hour_of(r["step"]) < 6,
        lambda r: f"Made at {int(hour_of(r['step'])):02d}:00, in the middle of the night",
    ),
    "big_amount": (
        lambda r, ref=None: ref is not None and r["amount"] > ref["amount_p95"],
        lambda r: f"Unusually large — {inr(r['amount'])}",
    ),
    "is_transfer": (
        lambda r: r["type"] == "TRANSFER",
        lambda r: "A transfer to another person's account — fraudsters move money out before cashing it",
    ),
}


SIGNALS_LABELS = {
    "exact_drain": "Sent the sender's entire balance",
    "receiver_stays_zero": "Money never showed up at the receiver",
    "is_night": "Made between midnight and 6 am",
    "big_amount": "Larger than 95% of genuine payments",
    "is_transfer": "Transfer to another person (not cash-out)",
}


def _rate_mask(name, df, ref_amount_p95=None):
    if name == "exact_drain":
        return (df["oldbalanceOrg"] > 0) & ((df["amount"] - df["oldbalanceOrg"]).abs() < 1)
    if name == "receiver_stays_zero":
        return (df["amount"] > 0) & (df["oldbalanceDest"] == 0) & (df["newbalanceDest"] == 0)
    if name == "is_night":
        return hour_of(df["step"]) < 6
    if name == "big_amount":
        return df["amount"] > ref_amount_p95
    if name == "is_transfer":
        return df["type"] == "TRANSFER"
    raise KeyError(name)


def build_reference(train_df, model):
    """train_df: raw TRANSFER/CASH_OUT rows with isFraud."""
    fraud = train_df[train_df["isFraud"] == 1]
    genuine = train_df[train_df["isFraud"] == 0]
    p95 = genuine["amount"].quantile(0.95)
    rates = {}
    for name in SIGNALS:
        rates[name] = (
            _rate_mask(name, fraud, p95).mean() * 100,
            _rate_mask(name, genuine, p95).mean() * 100,
        )
    return {
        "amount_p95": p95,
        "rates": rates,
        "importance": pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False),
        "genuine_hour_share": pd.Series(hour_of(genuine["step"])).value_counts(normalize=True)
        .reindex(range(24), fill_value=0),
        "fraud_hour_share": pd.Series(hour_of(fraud["step"])).value_counts(normalize=True)
        .reindex(range(24), fill_value=0),
    }


def load():
    if not (os.path.exists(MODEL_PATH) and os.path.exists(REFERENCE_PATH)):
        return None, None
    return joblib.load(MODEL_PATH), joblib.load(REFERENCE_PATH)


def _fmt_rate(x):
    if x < 0.1:
        return "almost none"
    return f"{x:.1f}%" if x < 10 else f"{x:.0f}%"


def explain(row, ref):
    """Plain-language reasons, strongest first. Each quotes fraud vs genuine rates."""
    if row["type"] not in RISKY_TYPES:
        return [f"{row['type'].replace('_', ' ').title()} payments are never fraud in this data — "
                "fraud only happens on transfers and cash-outs"]

    found = []
    for name, (test, say) in SIGNALS.items():
        hit = test(row, ref) if name == "big_amount" else test(row)
        if not hit:
            continue
        fraud_rate, genuine_rate = ref["rates"][name]
        lift = fraud_rate / max(genuine_rate, 0.05)
        if lift < 1.5:
            continue
        found.append((lift, f"{say(row)}. Seen in {_fmt_rate(fraud_rate)} of frauds vs "
                            f"{_fmt_rate(genuine_rate)} of genuine payments."))
    return [text for _, text in sorted(found, reverse=True)]


def reassurances(row, ref):
    """For payments that look fine: the fraud patterns they *don't* show."""
    if row["type"] not in RISKY_TYPES:
        return []
    notes = []
    if not SIGNALS["exact_drain"][0](row):
        notes.append("Didn't empty the sender's account")
    if not SIGNALS["receiver_stays_zero"][0](row):
        notes.append("The money arrived at the receiver")
    if not SIGNALS["is_night"][0](row):
        notes.append("Made at a normal hour")
    return notes


def verdict(probability, threshold):
    if probability >= 0.8:
        return "Very likely fraud", "bad"
    if probability >= threshold:
        return "Suspicious", "warn"
    if probability >= threshold / 2:
        return "Borderline", "info"
    return "Looks genuine", "good"


def score(df, model):
    proba = np.zeros(len(df))
    risky = df["type"].isin(RISKY_TYPES).values
    if risky.any():
        proba[risky] = model.predict_proba(features(df[risky]))[:, 1]
    return proba
