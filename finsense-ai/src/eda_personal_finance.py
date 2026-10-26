import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# 1. LOAD DATASET
# --------------------------------------------------

df = pd.read_csv("datasets/raw/Personal_Finance_Dataset.csv")

print("\n" + "=" * 70)
print("           FINSENSE AI - PERSONAL FINANCE EDA")
print("=" * 70)


# --------------------------------------------------
# 2. BASIC INFORMATION
# --------------------------------------------------

print("\nDataset Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

print("\nMissing Values:")
print(df.isnull().sum())


# --------------------------------------------------
# 3. BASIC STATISTICS
# --------------------------------------------------

print("\nNumerical Statistics:")
print(df.describe())


# --------------------------------------------------
# 4. INCOME VS EXPENSE
# --------------------------------------------------

print("\nTransaction Type:")
print(df["Type"].value_counts())

# Total income
income = df[df["Type"] == "Income"]["Amount"].sum()

# Only expense transactions
expense_df = df[df["Type"] == "Expense"]

# Total expense
total_expense = expense_df["Amount"].sum()

# Savings
savings = income - total_expense

print("\nTotal Income  :", income)
print("Total Expense :", total_expense)
print("Savings       :", savings)


# --------------------------------------------------
# 5. EXPENSE BY CATEGORY
# --------------------------------------------------

expense_category = (
    expense_df.groupby("Category")["Amount"]
    .sum()
    .sort_values(ascending=False)
)

print("\nExpense by Category:")
print(expense_category)


# --------------------------------------------------
# 6. TOP SPENDING CATEGORY
# --------------------------------------------------

print("\nHighest Spending Category:")
print(expense_category.idxmax())

print("\nHighest Spending Amount:")
print(expense_category.max())


# --------------------------------------------------
# 7. VISUALIZATION 1
# --------------------------------------------------

plt.figure(figsize=(8, 5))

sns.countplot(
    data=df,
    x="Type"
)

plt.title("Income vs Expense Transactions")
plt.xlabel("Transaction Type")
plt.ylabel("Number of Transactions")

plt.tight_layout()
plt.show()


# --------------------------------------------------
# 8. VISUALIZATION 2
# --------------------------------------------------

plt.figure(figsize=(10, 6))

expense_category.plot(kind="bar")

plt.title("Expense by Category")
plt.xlabel("Category")
plt.ylabel("Total Amount")

plt.xticks(rotation=45)

plt.tight_layout()
plt.show()


# --------------------------------------------------
# 9. VISUALIZATION 3
# --------------------------------------------------

plt.figure(figsize=(8, 6))

sns.boxplot(
    data=df,
    x="Type",
    y="Amount"
)

plt.title("Transaction Amount Distribution")
plt.xlabel("Transaction Type")
plt.ylabel("Amount")

plt.tight_layout()
plt.show()


# --------------------------------------------------
# 10. COMPLETION
# --------------------------------------------------

print("\nEDA COMPLETED SUCCESSFULLY!")