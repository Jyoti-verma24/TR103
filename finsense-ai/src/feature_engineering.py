import pandas as pd
import numpy as np

# ============================================================
# FINSENSE AI - FEATURE ENGINEERING
# ============================================================

# 1. LOAD DATASET
df = pd.read_csv("datasets/raw/Personal_Finance_Dataset.csv")

print("\n" + "=" * 70)
print("           FINSENSE AI - FEATURE ENGINEERING")
print("=" * 70)

# ============================================================
# 2. CONVERT DATE
# ============================================================

df["Date"] = pd.to_datetime(df["Date"])

print("\nDate converted successfully.")

# ============================================================
# 3. CREATE DATE FEATURES
# ============================================================

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Month_Name"] = df["Date"].dt.month_name()
df["Day"] = df["Date"].dt.day
df["Day_of_Week"] = df["Date"].dt.day_name()

print("\nDate features created.")

# ============================================================
# 4. SEPARATE INCOME AND EXPENSE
# ============================================================

df["Income"] = np.where(
    df["Type"] == "Income",
    df["Amount"],
    0
)

df["Expense"] = np.where(
    df["Type"] == "Expense",
    df["Amount"],
    0
)

print("\nIncome and Expense columns created.")

# ============================================================
# 5. MONTHLY SUMMARY
# ============================================================

monthly_summary = (
    df.groupby(["Year", "Month"])
    .agg(
        Total_Income=("Income", "sum"),
        Total_Expense=("Expense", "sum"),
        Transaction_Count=("Amount", "count")
    )
    .reset_index()
)

# ============================================================
# 6. MONTHLY SAVINGS
# ============================================================

monthly_summary["Savings"] = (
    monthly_summary["Total_Income"]
    - monthly_summary["Total_Expense"]
)

# ============================================================
# 7. SAVINGS RATE
# ============================================================

monthly_summary["Savings_Rate"] = np.where(
    monthly_summary["Total_Income"] > 0,
    (monthly_summary["Savings"] /
     monthly_summary["Total_Income"]) * 100,
    0
)

# ============================================================
# 8. EXPENSE TO INCOME RATIO
# ============================================================

monthly_summary["Expense_to_Income_Ratio"] = np.where(
    monthly_summary["Total_Income"] > 0,
    (monthly_summary["Total_Expense"] /
     monthly_summary["Total_Income"]) * 100,
    0
)

# ============================================================
# 9. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("MONTHLY FINANCIAL SUMMARY")
print("=" * 70)

print(monthly_summary)

# ============================================================
# 10. OVERALL FINANCIAL FEATURES
# ============================================================

total_income = df["Income"].sum()
total_expense = df["Expense"].sum()
total_savings = total_income - total_expense

if total_income > 0:
    savings_rate = (total_savings / total_income) * 100
    expense_income_ratio = (total_expense / total_income) * 100
else:
    savings_rate = 0
    expense_income_ratio = 0

print("\n" + "=" * 70)
print("OVERALL FINANCIAL FEATURES")
print("=" * 70)

print(f"\nTotal Income              : ₹{total_income:,.2f}")
print(f"Total Expense             : ₹{total_expense:,.2f}")
print(f"Total Savings             : ₹{total_savings:,.2f}")
print(f"Savings Rate              : {savings_rate:.2f}%")
print(f"Expense-to-Income Ratio   : {expense_income_ratio:.2f}%")
print(f"Total Transactions        : {len(df)}")

# ============================================================
# 11. SAVE PROCESSED DATA
# ============================================================

import os

os.makedirs("datasets/processed", exist_ok=True)

df.to_csv(
    "datasets/processed/finance_features.csv",
    index=False
)

monthly_summary.to_csv(
    "datasets/processed/monthly_summary.csv",
    index=False
)

print("\nProcessed files saved successfully.")

print("\nFEATURE ENGINEERING COMPLETED SUCCESSFULLY!")