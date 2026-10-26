import pandas as pd

# ============================================================
# LOAD FEATURE-ENGINEERED DATA
# ============================================================

df = pd.read_csv(
    "datasets/processed/finance_engineered.csv"
)

print("Dataset loaded successfully!")
print("Shape:", df.shape)


# ============================================================
# 1. SAVINGS SCORE
# ============================================================

def savings_score(rate):

    rate = max(0, min(rate, 0.40))

    return (rate / 0.40) * 100


df["savings_score"] = df["savings_rate"].apply(
    savings_score
)


# ============================================================
# 2. DEBT MANAGEMENT SCORE
# ============================================================

def debt_score(ratio):

    if ratio <= 0.10:
        return 100

    elif ratio <= 0.20:
        return 90

    elif ratio <= 0.30:
        return 75

    elif ratio <= 0.40:
        return 60

    elif ratio <= 0.50:
        return 40

    else:
        return 20


df["debt_score"] = df["debt_to_income_ratio"].apply(
    debt_score
)


# ============================================================
# 3. EMERGENCY FUND SCORE
# ============================================================

def emergency_score(months):

    if months >= 6:
        return 100

    elif months >= 5:
        return 90

    elif months >= 4:
        return 80

    elif months >= 3:
        return 70

    elif months >= 2:
        return 50

    elif months >= 1:
        return 30

    else:
        return 10


df["emergency_score"] = df[
    "emergency_fund_coverage"
].apply(emergency_score)


# ============================================================
# 4. BUDGET SCORE
# ============================================================

def budget_score(utilization):

    if utilization <= 0.70:
        return 100

    elif utilization <= 0.80:
        return 90

    elif utilization <= 0.90:
        return 80

    elif utilization <= 1.00:
        return 70

    elif utilization <= 1.10:
        return 50

    else:
        return 25


df["budget_score"] = df[
    "budget_utilization"
].apply(budget_score)


# ============================================================
# 5. CREDIT SCORE
# ============================================================

def credit_score_normalized(score):

    score = max(300, min(score, 850))

    return ((score - 300) / (850 - 300)) * 100


df["credit_score_component"] = df[
    "credit_score"
].apply(credit_score_normalized)


# ============================================================
# 6. INVESTMENT SCORE
# ============================================================

def investment_score(ratio):

    ratio = max(0, min(ratio, 0.30))

    return (ratio / 0.30) * 100


df["investment_score"] = df[
    "investment_ratio"
].apply(investment_score)


# ============================================================
# 7. CASH FLOW SCORE
# ============================================================

def cash_flow_score(row):

    income = row["monthly_income"]
    cash_flow = row["net_cash_flow"]

    if income <= 0:
        return 0

    ratio = cash_flow / income

    if ratio >= 0.30:
        return 100

    elif ratio >= 0.20:
        return 90

    elif ratio >= 0.10:
        return 80

    elif ratio >= 0:
        return 65

    elif ratio >= -0.10:
        return 40

    else:
        return 20


df["cash_flow_score"] = df.apply(
    cash_flow_score,
    axis=1
)


# ============================================================
# 8. FINAL FINANCIAL HEALTH SCORE
# ============================================================

df["financial_health_score"] = (

    df["savings_score"] * 0.25

    + df["debt_score"] * 0.20

    + df["emergency_score"] * 0.15

    + df["budget_score"] * 0.15

    + df["credit_score_component"] * 0.10

    + df["investment_score"] * 0.10

    + df["cash_flow_score"] * 0.05

)


# ============================================================
# 9. HEALTH CATEGORY
# ============================================================

def health_category(score):

    if score >= 80:
        return "Excellent"

    elif score >= 65:
        return "Good"

    elif score >= 50:
        return "Moderate"

    elif score >= 35:
        return "Needs Improvement"

    else:
        return "Critical"


df["health_category"] = df[
    "financial_health_score"
].apply(health_category)


# ============================================================
# 10. SAVE FINAL DATASET
# ============================================================

df.to_csv(
    "datasets/processed/finance_health_scored.csv",
    index=False
)


# ============================================================
# 11. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 60)
print("FINANCIAL HEALTH SCORE ENGINE")
print("=" * 60)

print("\nAverage Health Score:")
print(
    round(
        df["financial_health_score"].mean(),
        2
    )
)

print("\nHealth Category Distribution:")
print(
    df["health_category"].value_counts()
)

print("\nSample Results:")

print(
    df[
        [
            "user_id",
            "financial_health_score",
            "health_category",
            "financial_risk",
            "financial_personality"
        ]
    ].head(10)
)

print("\nFinal dataset saved successfully!")