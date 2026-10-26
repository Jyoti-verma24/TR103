import os
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


# ============================================================
# FINSENSE AI - ISOLATION FOREST ANOMALY DETECTION
# ============================================================

print("\n" + "=" * 70)
print("FINSENSE AI - ISOLATION FOREST ANOMALY DETECTION")
print("=" * 70)


# ------------------------------------------------------------
# 1. Load Dataset
# ------------------------------------------------------------

DATA_PATH = "datasets/raw/creditcard.csv"

df = pd.read_csv(DATA_PATH)

print("\nOriginal Dataset Shape:")
print(df.shape)


# ------------------------------------------------------------
# 2. Remove Duplicate Transactions
# ------------------------------------------------------------

duplicates = df.duplicated().sum()

print("\nDuplicate Transactions:", duplicates)

df = df.drop_duplicates().reset_index(drop=True)

print("Dataset Shape After Removing Duplicates:")
print(df.shape)


# ------------------------------------------------------------
# 3. Separate Features and Target
# ------------------------------------------------------------

X = df.drop("Class", axis=1)
y = df["Class"]


# ------------------------------------------------------------
# 4. Scale Features
# ------------------------------------------------------------

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

print("\nFeature Shape:")
print(X_scaled.shape)


# ------------------------------------------------------------
# 5. Train Isolation Forest
# ------------------------------------------------------------

print("\nTraining Isolation Forest...")

model = IsolationForest(
    n_estimators=200,
    contamination=0.0017,
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled)
# ============================================================
# SAVE ISOLATION FOREST MODEL + SCALER
# ============================================================

os.makedirs("models", exist_ok=True)

joblib.dump(
    model,
    "models/isolation_forest.pkl"
)

joblib.dump(
    scaler,
    "models/isolation_scaler.pkl"
)

print("\nIsolation Forest model saved successfully!")
print("models/isolation_forest.pkl")

print("\nIsolation Forest scaler saved successfully!")
print("models/isolation_scaler.pkl")

# ------------------------------------------------------------
# 6. Predict Anomalies
# ------------------------------------------------------------

predictions = model.predict(X_scaled)

# Isolation Forest:
#  1  = normal
# -1  = anomaly

anomaly_prediction = np.where(predictions == -1, 1, 0)


# ------------------------------------------------------------
# 7. Anomaly Score
# ------------------------------------------------------------

anomaly_score = -model.decision_function(X_scaled)

# Normalize score between 0 and 100

anomaly_score_normalized = (
    (anomaly_score - anomaly_score.min())
    /
    (anomaly_score.max() - anomaly_score.min())
) * 100


# ------------------------------------------------------------
# 8. Evaluation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ISOLATION FOREST RESULTS")
print("=" * 70)

print("\nActual Fraud Distribution:")
print(y.value_counts())

print("\nDetected Anomalies:")
print(pd.Series(anomaly_prediction).value_counts())


print("\nClassification Report:")

print(
    classification_report(
        y,
        anomaly_prediction,
        target_names=["Normal", "Fraud"],
        zero_division=0
    )
)


print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y,
        anomaly_prediction
    )
)


# ------------------------------------------------------------
# 9. ROC-AUC
# ------------------------------------------------------------

try:

    roc_auc = roc_auc_score(
        y,
        anomaly_score_normalized
    )

    print("\nROC-AUC Score:")
    print(round(roc_auc, 4))

except Exception as e:

    print("\nROC-AUC could not be calculated.")
    print(e)


# ------------------------------------------------------------
# 10. Add Results to Dataset
# ------------------------------------------------------------

df["anomaly_score"] = anomaly_score_normalized

df["anomaly_prediction"] = anomaly_prediction


# ------------------------------------------------------------
# 11. Risk Level
# ------------------------------------------------------------

def classify_risk(score):

    if score >= 80:
        return "HIGH"

    elif score >= 50:
        return "MEDIUM"

    else:
        return "LOW"


df["anomaly_risk"] = df["anomaly_score"].apply(
    classify_risk
)


# ------------------------------------------------------------
# 12. Show Most Suspicious Transactions
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TOP 10 MOST SUSPICIOUS TRANSACTIONS")
print("=" * 70)

top_anomalies = df.sort_values(
    "anomaly_score",
    ascending=False
).head(10)

print(
    top_anomalies[
        [
            "Amount",
            "Class",
            "anomaly_score",
            "anomaly_prediction",
            "anomaly_risk"
        ]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# 13. Save Results
# ------------------------------------------------------------

OUTPUT_PATH = "datasets/processed/anomaly_detection_results.csv"

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nResults saved successfully!")

print("\nOutput:")
print(OUTPUT_PATH)