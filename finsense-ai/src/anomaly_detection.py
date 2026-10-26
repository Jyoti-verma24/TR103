import os
import joblib

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)


# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv(
    "datasets/raw/creditcard.csv"
)

print("=" * 70)
print("FINSENSE AI - ML ANOMALY DETECTION")
print("=" * 70)

print("\nOriginal Dataset Shape:")
print(df.shape)


# ============================================================
# 2. REMOVE DUPLICATES
# ============================================================

duplicates = df.duplicated().sum()

print("\nDuplicate Transactions:", duplicates)

df = df.drop_duplicates()

print("Dataset Shape After Removing Duplicates:")
print(df.shape)


# ============================================================
# 3. CHECK TARGET DISTRIBUTION
# ============================================================

print("\nFraud Distribution:")
print(df["Class"].value_counts())

print("\nFraud Percentage:")
print(
    df["Class"].value_counts(normalize=True) * 100
)


# ============================================================
# 4. SEPARATE FEATURES AND TARGET
# ============================================================

X = df.drop("Class", axis=1)

y = df["Class"]


print("\nFeature Shape:")
print(X.shape)

print("\nTarget Shape:")
print(y.shape)


# ============================================================
# 5. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining Samples:")
print(X_train.shape)

print("\nTesting Samples:")
print(X_test.shape)


print("\nFraud Distribution in Training Data:")
print(y_train.value_counts())

print("\nFraud Distribution in Testing Data:")
print(y_test.value_counts())


# ============================================================
# 6. SCALE TRANSACTION AMOUNT
# ============================================================

scaler = StandardScaler()

X_train = X_train.copy()
X_test = X_test.copy()

numeric_columns = X_train.columns

X_train[numeric_columns] = scaler.fit_transform(
    X_train[numeric_columns]
)

X_test[numeric_columns] = scaler.transform(
    X_test[numeric_columns]
)

# ============================================================
# 7. BASELINE LOGISTIC REGRESSION
# ============================================================

print("\n" + "=" * 70)
print("BASELINE LOGISTIC REGRESSION")
print("=" * 70)

model = LogisticRegression(
    max_iter=3000,
    class_weight="balanced",
    random_state=42
)

model.fit(
    X_train,
    y_train
)


# ============================================================
# 8. PREDICTIONS
# ============================================================

y_pred = model.predict(X_test)

y_probability = model.predict_proba(
    X_test
)[:, 1]


# ============================================================
# 9. EVALUATION
# ============================================================

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        digits=4
    )
)


print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# ============================================================
# 10. ROC-AUC
# ============================================================

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

print("\nROC-AUC Score:")
print(round(roc_auc, 4))

from sklearn.metrics import precision_score, recall_score, f1_score


print("\n" + "=" * 70)
print("FRAUD DETECTION THRESHOLD ANALYSIS")
print("=" * 70)

thresholds = [
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90
]

print(
    "\nThreshold | Precision | Recall | F1 Score"
)

print("-" * 50)

for threshold in thresholds:

    predictions = (
        y_probability >= threshold
    ).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    print(
        f"{threshold:9.2f} | "
        f"{precision:9.4f} | "
        f"{recall:6.4f} | "
        f"{f1:8.4f}"
    )

print("\n" + "=" * 70)
print("BASELINE MODEL COMPLETED")
print("=" * 70)
# ============================================================
# RANDOM FOREST
# ============================================================

from sklearn.ensemble import RandomForestClassifier


print("\n" + "=" * 70)
print("RANDOM FOREST FRAUD DETECTION")
print("=" * 70)


rf_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    min_samples_leaf=2,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1
)


print("\nTraining Random Forest...")

rf_model.fit(
    X_train,
    y_train
)


# Predictions
rf_pred = rf_model.predict(X_test)

rf_probability = rf_model.predict_proba(
    X_test
)[:, 1]


# Classification report
print("\nClassification Report:")

print(
    classification_report(
        y_test,
        rf_pred,
        digits=4
    )
)


# Confusion matrix
print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_test,
        rf_pred
    )
)


# ROC-AUC
rf_auc = roc_auc_score(
    y_test,
    rf_probability
)

print("\nROC-AUC Score:")

print(round(rf_auc, 4))
# ============================================================
# RANDOM FOREST THRESHOLD ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("RANDOM FOREST THRESHOLD ANALYSIS")
print("=" * 70)

print(
    "\nThreshold | Precision | Recall | F1 Score"
)

print("-" * 50)

rf_threshold_results = []

for threshold in thresholds:

    predictions = (
        rf_probability >= threshold
    ).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    rf_threshold_results.append(
        (
            threshold,
            precision,
            recall,
            f1
        )
    )

    print(
        f"{threshold:9.2f} | "
        f"{precision:9.4f} | "
        f"{recall:6.4f} | "
        f"{f1:8.4f}"
    )
# ============================================================
# SAVE RANDOM FOREST MODEL
# ============================================================

os.makedirs("models", exist_ok=True)

joblib.dump(
    rf_model,
    "models/random_forest_fraud.pkl"
)

print("\nRandom Forest model saved successfully!")
print("models/random_forest_fraud.pkl")

# The forest was trained on scaled features — save the scaler so the app can reuse it.
joblib.dump(
    scaler,
    "models/random_forest_scaler.pkl"
)
print("models/random_forest_scaler.pkl")
# Reference profile of genuine vs fraud payments, used by the app to explain
# *why* a payment was flagged. Built from the unscaled training split.
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finsense.fraud import build_reference

X_train_raw, _, y_train_raw, _ = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
joblib.dump(
    build_reference(X_train_raw, y_train_raw, rf_model),
    "models/fraud_reference.pkl"
)
print("models/fraud_reference.pkl")
