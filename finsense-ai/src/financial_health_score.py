import pandas as pd
import numpy as np

# ============================================================
# FINSENSE AI - FINANCIAL HEALTH SCORE
# ============================================================

# 1. LOAD MONTHLY FEATURES
monthly = pd.read_csv(
    "datasets/processed/monthly_summary.csv"
)

print("\n" + "=" * 70)
print("             FINSENSE AI - FINANCIAL HEALTH SCORE")
print("=" * 70)


# ============================================================
# 2. SAVINGS SCORE
# ============================================================

def calculate_savings_score(rate):
    if rate >= 20:
        return 30
    elif rate >= 10:
        return 20
    elif rate >= 0:
        return 10
    else:
        return 0


monthly["Savings_Score"] = (
    monthly["Savings_Rate"]
    .apply(calculate_savings_score)
)


# ============================================================
# 3. EXPENSE SCORE
# ============================================================

def calculate_expense_score(ratio):
    if ratio <= 80:
        return 30
    elif ratio <= 100:
        return 20
    elif ratio <= 120:
        return 10
    else:
        return 0


monthly["Expense_Score"] = (
    monthly["Expense_to_Income_Ratio"]
    .apply(calculate_expense_score)
)


# ============================================================
# 4. INCOME STABILITY SCORE
# ============================================================

income_mean = monthly["Total_Income"].mean()
income_std = monthly["Total_Income"].std()

# Coefficient of variation
if income_mean > 0:
    income_cv = income_std / income_mean
else:
    income_cv = 999


if income_cv <= 0.30:
    income_stability_score = 20
elif income_cv <= 0.60:
    income_stability_score = 15
elif income_cv <= 1.00:
    income_stability_score = 10
else:
    income_stability_score = 5


monthly["Income_Stability_Score"] = income_stability_score


# ============================================================
# 5. SPENDING CONSISTENCY SCORE
# ============================================================

expense_mean = monthly["Total_Expense"].mean()
expense_std = monthly["Total_Expense"].std()

if expense_mean > 0:
    expense_cv = expense_std / expense_mean
else:
    expense_cv = 999


if expense_cv <= 0.30:
    spending_score = 20
elif expense_cv <= 0.60:
    spending_score = 15
elif expense_cv <= 1.00:
    spending_score = 10
else:
    spending_score = 5


monthly["Spending_Consistency_Score"] = spending_score


# ============================================================
# 6. TOTAL FINANCIAL HEALTH SCORE
# ============================================================

monthly["Financial_Health_Score"] = (
    monthly["Savings_Score"]
    + monthly["Expense_Score"]
    + monthly["Income_Stability_Score"]
    + monthly["Spending_Consistency_Score"]
)


# ============================================================
# 7. HEALTH CATEGORY
# ============================================================

def health_category(score):

    if score >= 80:
        return "Excellent"

    elif score >= 60:
        return "Good"

    elif score >= 40:
        return "Needs Improvement"

    else:
        return "Poor"


monthly["Health_Category"] = (
    monthly["Financial_Health_Score"]
    .apply(health_category)
)


# ============================================================
# 8. DISPLAY MONTHLY RESULTS
# ============================================================

print("\nMONTHLY FINANCIAL HEALTH")

print(
    monthly[
        [
            "Year",
            "Month",
            "Total_Income",
            "Total_Expense",
            "Savings",
            "Savings_Rate",
            "Expense_to_Income_Ratio",
            "Financial_Health_Score",
            "Health_Category"
        ]
    ].to_string(index=False)
)


# ============================================================
# 9. OVERALL SCORE
# ============================================================

overall_score = monthly[
    "Financial_Health_Score"
].mean()

overall_category = health_category(
    overall_score
)


print("\n" + "=" * 70)
print("              OVERALL FINANCIAL HEALTH")
print("=" * 70)

print(
    f"\nOverall Financial Health Score : "
    f"{overall_score:.2f} / 100"
)

print(
    f"Overall Financial Category     : "
    f"{overall_category}"
)


# ============================================================
# 10. BEST AND WORST MONTH
# ============================================================

best_month = monthly.loc[
    monthly["Financial_Health_Score"].idxmax()
]

worst_month = monthly.loc[
    monthly["Financial_Health_Score"].idxmin()
]


print("\nBest Financial Month:")
print(
    f"{int(best_month['Year'])}-"
    f"{int(best_month['Month']):02d}"
)

print(
    f"Score: "
    f"{best_month['Financial_Health_Score']}"
)


print("\nWorst Financial Month:")
print(
    f"{int(worst_month['Year'])}-"
    f"{int(worst_month['Month']):02d}"
)

print(
    f"Score: "
    f"{worst_month['Financial_Health_Score']}"
)


# ============================================================
# 11. SAVE RESULTS
# ============================================================

monthly.to_csv(
    "datasets/processed/financial_health_scores.csv",
    index=False
)


print("\nFinancial health scores saved successfully.")

print("\nFINANCIAL HEALTH SCORE COMPLETED SUCCESSFULLY!")