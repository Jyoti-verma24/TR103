import pandas as pd


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    "datasets/processed/finance_health_scored.csv"
)


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

def generate_recommendations(row):

    recommendations = []

    # --------------------------------------------------------
    # EMERGENCY FUND
    # --------------------------------------------------------

    if row["emergency_fund_coverage"] < 1:

        recommendations.append({
            "priority": "CRITICAL",
            "area": "Emergency Fund",
            "message":
                "Your emergency fund covers less than "
                "one month of expenses.",
            "action":
                "Start building an emergency fund "
                "covering at least 3 months of expenses."
        })

    elif row["emergency_fund_coverage"] < 3:

        recommendations.append({
            "priority": "HIGH",
            "area": "Emergency Fund",
            "message":
                "Your emergency fund is below the "
                "recommended 3-month buffer.",
            "action":
                "Gradually increase your emergency "
                "fund to cover at least 3 months."
        })


    # --------------------------------------------------------
    # DEBT
    # --------------------------------------------------------

    if row["debt_to_income_ratio"] > 0.50:

        recommendations.append({
            "priority": "CRITICAL",
            "area": "Debt",
            "message":
                "More than 50% of your income is "
                "associated with debt obligations.",
            "action":
                "Prioritize reducing high-interest "
                "debt and avoid taking unnecessary loans."
        })

    elif row["debt_to_income_ratio"] > 0.30:

        recommendations.append({
            "priority": "HIGH",
            "area": "Debt",
            "message":
                "Your debt-to-income ratio is relatively high.",
            "action":
                "Focus on reducing outstanding debt "
                "before increasing discretionary spending."
        })


    # --------------------------------------------------------
    # SAVINGS
    # --------------------------------------------------------

    if row["savings_rate"] < 0.10:

        recommendations.append({
            "priority": "HIGH",
            "area": "Savings",
            "message":
                "Your savings rate is below 10%.",
            "action":
                "Set aside a fixed percentage of income "
                "before making discretionary purchases."
        })

    elif row["savings_rate"] < 0.20:

        recommendations.append({
            "priority": "MEDIUM",
            "area": "Savings",
            "message":
                "Your savings rate could be improved.",
            "action":
                "Try gradually increasing your savings "
                "toward 20% of income."
        })


    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    if row["budget_utilization"] > 1.10:

        recommendations.append({
            "priority": "CRITICAL",
            "area": "Budget",
            "message":
                "Your spending significantly exceeds "
                "your budget.",
            "action":
                "Review discretionary expenses and "
                "reduce non-essential spending."
        })

    elif row["budget_utilization"] > 1.00:

        recommendations.append({
            "priority": "HIGH",
            "area": "Budget",
            "message":
                "You are spending more than your budget.",
            "action":
                "Review your largest spending categories "
                "and adjust your monthly budget."
        })


    # --------------------------------------------------------
    # INVESTMENT
    # --------------------------------------------------------

    if row["investment_ratio"] < 0.05:

        recommendations.append({
            "priority": "MEDIUM",
            "area": "Investment",
            "message":
                "Very little of your income is being invested.",
            "action":
                "After establishing an emergency fund, "
                "consider a consistent long-term investment plan."
        })


    # --------------------------------------------------------
    # POSITIVE FEEDBACK
    # --------------------------------------------------------

    if len(recommendations) == 0:

        recommendations.append({
            "priority": "LOW",
            "area": "Overall",
            "message":
                "Your financial indicators are generally healthy.",
            "action":
                "Continue monitoring spending, saving and investing."
        })


    return recommendations


# ============================================================
# GENERATE RECOMMENDATIONS FOR USERS
# ============================================================

print("\n" + "=" * 70)
print("FINSENSE AI - PERSONALIZED FINANCIAL ADVICE")
print("=" * 70)


# Show recommendations for first 5 users

for index, row in df.head(5).iterrows():

    print("\n")
    print("-" * 70)

    print(
        "User ID:",
        row["user_id"]
    )

    print(
        "Health Score:",
        round(
            row["financial_health_score"],
            2
        )
    )

    print(
        "Health Category:",
        row["health_category"]
    )

    recommendations = generate_recommendations(row)

    print("\nRecommendations:")

    for rec in recommendations:

        print(
            f"[{rec['priority']}] "
            f"{rec['area']}"
        )

        print(
            "Why:",
            rec["message"]
        )

        print(
            "Action:",
            rec["action"]
        )


print("\n" + "=" * 70)
print("Recommendation Engine Completed!")
print("=" * 70)