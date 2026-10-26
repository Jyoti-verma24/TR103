import os

import numpy as np
import pandas as pd
import streamlit as st

# ============================================================
# PATHS & SCHEMA
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(BASE_DIR, "datasets", "raw", "Personal_Finance_Dataset.csv")
DEMO_PATH = os.path.join(BASE_DIR, "sample_data", "demo_transactions.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "random_forest_fraud.pkl")

REQUIRED_COLUMNS = ["Date", "Category", "Amount", "Type"]
VALID_TYPES = ["Income", "Expense"]

# Categories treated as "wants" vs "needs" for personality traits.
DISCRETIONARY = {"Shopping", "Entertainment", "Travel", "Food & Drink"}
ESSENTIAL = {"Rent", "Utilities", "Health & Fitness", "Groceries", "Insurance", "EMI"}
INVESTMENT = {"Investment", "Investments", "SIP", "Savings"}


# ============================================================
# FORMATTING
# ============================================================

def inr(value, decimals=0, sign=False):
    """Format a number as rupees with Indian digit grouping (₹1,20,000)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"

    negative = value < 0
    text = f"{abs(value):.{decimals}f}"
    whole, _, frac = text.partition(".")

    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])

    body = f"₹{whole}" + (f".{frac}" if frac else "")

    if negative:
        return f"−{body}"
    return f"+{body}" if sign and value > 0 else body


def pct(value, decimals=1, sign=False):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return f"{value:+.{decimals}f}%" if sign else f"{value:.{decimals}f}%"


# ============================================================
# LOADING & CLEANING
# ============================================================

def clean_transactions(raw):
    """Validate and normalise an uploaded transaction frame.

    Returns (clean_df, notes). Raises ValueError for unusable input.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}."
        )

    notes = []
    df = raw.copy()

    if "Transaction Description" in df.columns and "Description" not in df.columns:
        df = df.rename(columns={"Transaction Description": "Description"})
    if "Description" not in df.columns:
        df["Description"] = ""

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").abs()
    df["Type"] = df["Type"].astype(str).str.strip().str.title()
    df["Category"] = df["Category"].fillna("Other").astype(str).str.strip()

    before = len(df)
    df = df.dropna(subset=["Date", "Amount"])
    if len(df) < before:
        notes.append(f"Dropped {before - len(df):,} row(s) with an unreadable date or amount.")

    invalid = ~df["Type"].isin(VALID_TYPES)
    if invalid.any():
        notes.append(f"Dropped {int(invalid.sum()):,} row(s) whose Type wasn't Income or Expense.")
        df = df[~invalid]

    if df.empty:
        raise ValueError("No valid Income/Expense transactions found.")

    df = df.sort_values("Date").reset_index(drop=True)
    df["TxnID"] = np.arange(1, len(df) + 1)
    return df[["TxnID", "Date", "Description", "Category", "Amount", "Type"]], notes


@st.cache_data
def load_sample():
    return clean_transactions(pd.read_csv(SAMPLE_PATH))[0]


@st.cache_data
def load_demo():
    return clean_transactions(pd.read_csv(DEMO_PATH))[0]


# ============================================================
# AGGREGATES
# ============================================================

@st.cache_data
def monthly_summary(df):
    """One row per calendar month with Income, Expense, Savings and ratios.

    Months with no transactions inside the covered range are kept as zeros
    so trend and volatility maths isn't skewed by gaps.
    """
    period = df["Date"].dt.to_period("M")
    monthly = (
        df.assign(Period=period)
        .pivot_table(index="Period", columns="Type", values="Amount", aggfunc="sum", fill_value=0)
    )
    full_range = pd.period_range(period.min(), period.max(), freq="M")
    monthly = monthly.reindex(full_range, fill_value=0)
    monthly.index.name = "Period"

    for col in VALID_TYPES:
        if col not in monthly.columns:
            monthly[col] = 0.0

    monthly = monthly[VALID_TYPES].astype(float)
    monthly["Savings"] = monthly["Income"] - monthly["Expense"]
    monthly["Savings_Rate"] = np.where(
        monthly["Income"] > 0, monthly["Savings"] / monthly["Income"] * 100, np.nan
    )
    monthly = monthly.reset_index()
    monthly["Month"] = monthly["Period"].dt.strftime("%b %Y")
    return monthly


@st.cache_data
def category_matrix(df):
    """Monthly expense per category (rows = months, columns = categories)."""
    expenses = df[df["Type"] == "Expense"]
    period = df["Date"].dt.to_period("M")
    matrix = (
        expenses.assign(Period=expenses["Date"].dt.to_period("M"))
        .pivot_table(index="Period", columns="Category", values="Amount", aggfunc="sum", fill_value=0)
    )
    full_range = pd.period_range(period.min(), period.max(), freq="M")
    return matrix.reindex(full_range, fill_value=0)


@st.cache_data
def headline_stats(df):
    income = df.loc[df["Type"] == "Income", "Amount"].sum()
    expense = df.loc[df["Type"] == "Expense", "Amount"].sum()
    savings = income - expense
    by_category = (
        df[df["Type"] == "Expense"].groupby("Category")["Amount"].sum().sort_values(ascending=False)
    )
    months = df["Date"].dt.to_period("M").nunique()
    return {
        "income": income,
        "expense": expense,
        "savings": savings,
        "savings_rate": savings / income * 100 if income > 0 else np.nan,
        "expense_ratio": expense / income * 100 if income > 0 else np.nan,
        "by_category": by_category,
        "top_category": by_category.index[0] if len(by_category) else "—",
        "months": months,
        "transactions": len(df),
        "start": df["Date"].min(),
        "end": df["Date"].max(),
    }


def get_data():
    return st.session_state.get("finance_df")


def set_data(df, source):
    st.session_state.finance_df = df
    st.session_state.data_source = source
