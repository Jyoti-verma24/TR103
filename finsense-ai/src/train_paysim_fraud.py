"""Train the explainable mobile-payment fraud model on PaySim.

Run from the project root:  python src/train_paysim_fraud.py
Writes models/paysim_fraud.pkl, models/paysim_reference.pkl and
sample_data/payments_fraud_test.csv (held-out rows only).
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finsense import payments_fraud as pf  # noqa: E402

DATA = "datasets/raw/paysim.csv"
NUMERIC = ["step", "type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest", "isFraud"]

print("=" * 70)
print("FINSENSE AI - EXPLAINABLE PAYMENT FRAUD (PaySim)")
print("=" * 70)

df = pd.read_csv(DATA, usecols=NUMERIC)
print("All transactions:", len(df))

# Fraud only happens on TRANSFER and CASH_OUT, so that's all the model needs to learn.
risky = df[df["type"].isin(pf.RISKY_TYPES)]
fraud = risky[risky["isFraud"] == 1]
genuine = risky[risky["isFraud"] == 0].sample(400_000, random_state=42)
data = pd.concat([fraud, genuine])
print(f"Training pool: {len(fraud):,} frauds + {len(genuine):,} genuine")

train, test = train_test_split(data, test_size=0.20, random_state=42, stratify=data["isFraud"])

model = RandomForestClassifier(
    n_estimators=200, max_depth=14, min_samples_leaf=2,
    class_weight="balanced_subsample", random_state=42, n_jobs=-1,
)
model.fit(pf.features(train), train["isFraud"])

proba = model.predict_proba(pf.features(test))[:, 1]
pred = (proba >= 0.5).astype(int)
print("\nROC-AUC:", round(roc_auc_score(test["isFraud"], proba), 4))
print(classification_report(test["isFraud"], pred, digits=4))
print(confusion_matrix(test["isFraud"], pred))

os.makedirs("models", exist_ok=True)
joblib.dump(model, pf.MODEL_PATH)
joblib.dump(pf.build_reference(train, model), pf.REFERENCE_PATH)
print("\nSaved", pf.MODEL_PATH, "and", pf.REFERENCE_PATH)

# ------------------------------------------------------------
# Test file: held-out transfers/cash-outs + some everyday payments
# (PAYMENT / CASH_IN / DEBIT are never fraud and never trained on).
# ------------------------------------------------------------
pick = pd.concat([
    test[test["isFraud"] == 0].sample(2_600, random_state=7),
    test[test["isFraud"] == 1].sample(150, random_state=7),
    df[~df["type"].isin(pf.RISKY_TYPES)].sample(400, random_state=7),
])
wanted = set(pick.index)

# Second pass to fetch the full rows (with account names) for just those indices.
rows = []
for chunk in pd.read_csv(DATA, chunksize=500_000):
    rows.append(chunk[chunk.index.isin(wanted)])
sample = pd.concat(rows).drop(columns=["isFlaggedFraud"]).sample(frac=1, random_state=7).sort_values("step")
os.makedirs("sample_data", exist_ok=True)
sample.to_csv("sample_data/payments_fraud_test.csv", index=False)
print(f"Saved sample_data/payments_fraud_test.csv ({len(sample):,} rows, {int(sample['isFraud'].sum())} frauds)")
