import numpy as np
import pandas as pd
import streamlit as st

from finsense.data import DISCRETIONARY, INVESTMENT, inr

# ============================================================
# MONEY PERSONALITY
# ------------------------------------------------------------
# Behavioural traits measured from *when* and *how* someone
# spends, not just how much. Each trait has a strength (0–1)
# computed from a measurable signal, and the evidence sentence
# quotes that signal so the label is never a black box.
# ============================================================

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PHASES = ["1st–7th", "8th–14th", "15th–21st", "22nd–end"]


def _clamp(x):
    return float(np.clip(x, 0, 1)) if x == x else 0.0


@st.cache_data
def daily_spend(df):
    ex = df[df["Type"] == "Expense"]
    days = pd.date_range(df["Date"].min().normalize(), df["Date"].max().normalize(), freq="D")
    daily = ex.groupby(ex["Date"].dt.normalize())["Amount"].sum().reindex(days, fill_value=0)
    out = daily.rename("Spend").to_frame()
    out["DOW"] = out.index.dayofweek
    out["Day"] = out.index.day
    out["Phase"] = np.minimum((out["Day"] - 1) // 7, 3)
    return out


def heatmap(df):
    daily = daily_spend(df)
    grid = daily.pivot_table(index="Phase", columns="DOW", values="Spend", aggfunc="mean")
    grid = grid.reindex(index=range(4), columns=range(7))
    grid.index = PHASES
    grid.columns = DOW
    return grid


@st.cache_data
def traits(df):
    ex = df[df["Type"] == "Expense"]
    inc = df[df["Type"] == "Income"]
    daily = daily_spend(df)
    total_spend = ex["Amount"].sum()
    found = []

    # --- Weekend vs weekday --------------------------------------------
    weekend = daily.loc[daily["DOW"] >= 5, "Spend"].mean()
    weekday = daily.loc[daily["DOW"] < 5, "Spend"].mean()
    if weekday > 0:
        ratio = weekend / weekday
        if ratio >= 1:
            found.append({
                "name": "Weekend Splurger", "icon": "🎉", "tone": "watch",
                "strength": _clamp((ratio - 1) / 0.6),
                "evidence": f"An average weekend day costs {inr(weekend)} vs {inr(weekday)} on weekdays ({ratio:.2f}×).",
                "nudge": "Plan one no-spend weekend day each week.",
            })
        else:
            found.append({
                "name": "Weekday Spender", "icon": "💼", "tone": "neutral",
                "strength": _clamp((1 - ratio) / 0.4),
                "evidence": f"Weekdays average {inr(weekday)} a day vs {inr(weekend)} at weekends.",
                "nudge": "Check commute, lunches and convenience buys — that's where weekday money goes.",
            })

    # --- Payday effect ---------------------------------------------------
    if len(inc) >= 3:
        pay_days = np.sort(inc["Date"].dt.normalize().unique())
        idx = np.searchsorted(pay_days, ex["Date"].dt.normalize().values, side="right") - 1
        has_pay = idx >= 0
        since = (ex["Date"].dt.normalize().values[has_pay] - pay_days[idx[has_pay]]).astype("timedelta64[D]").astype(int)
        amounts = ex["Amount"].values[has_pay]
        if amounts.sum() > 0:
            window_share = amounts[since <= 6].sum() / amounts.sum()
            all_days = daily.index.values
            didx = np.searchsorted(pay_days, all_days, side="right") - 1
            dsince = (all_days[didx >= 0] - pay_days[didx[didx >= 0]]).astype("timedelta64[D]").astype(int)
            expected = (dsince <= 6).mean() if len(dsince) else 0
            if expected > 0:
                lift = window_share / expected
                found.append({
                    "name": "Payday Spender", "icon": "💸", "tone": "watch",
                    "strength": _clamp((lift - 1) / 0.8),
                    "evidence": f"{window_share * 100:.0f}% of spending lands in the 7 days after income arrives "
                                f"(you'd expect {expected * 100:.0f}% if it were spread evenly).",
                    "nudge": "Move savings out on payday, before the spending window opens.",
                })

    # --- Month-end juggling ------------------------------------------------
    signed = np.where(df["Type"] == "Income", df["Amount"], -df["Amount"])
    # Net each day first: salary and a purchase on the same date shouldn't
    # count as "ran out" just because of row order within the day.
    flows = pd.Series(signed, index=df["Date"].dt.normalize()).groupby(level=0).sum()
    squeezed = 0
    months = 0
    for _, month in flows.groupby(flows.index.to_period("M")):
        months += 1
        if month.cumsum().min() < 0:
            squeezed += 1
    if months:
        share = squeezed / months
        found.append({
            "name": "Month-End Juggler", "icon": "⏳", "tone": "watch",
            "strength": _clamp((share - 0.25) / 0.5),
            "evidence": f"In {squeezed} of {months} months, spending ran ahead of that month's income at some point.",
            "nudge": "Keep a one-month buffer so bills never wait on the next salary.",
        })

    # --- Lifestyle share ----------------------------------------------------
    if total_spend > 0:
        disc = ex.loc[ex["Category"].isin(DISCRETIONARY), "Amount"].sum() / total_spend
        found.append({
            "name": "Lifestyle Lover", "icon": "🛍️", "tone": "watch",
            "strength": _clamp((disc - 0.30) / 0.30),
            "evidence": f"{disc * 100:.0f}% of spending goes on wants — shopping, eating out, travel, entertainment.",
            "nudge": "Try the 50/30/20 split: cap wants at 30% of take-home pay.",
        })

    # --- Volatility ---------------------------------------------------------
    monthly_exp = ex.groupby(ex["Date"].dt.to_period("M"))["Amount"].sum()
    if len(monthly_exp) >= 3 and monthly_exp.mean() > 0:
        cv = monthly_exp.std() / monthly_exp.mean()
        found.append({
            "name": "Rollercoaster Spender", "icon": "🎢", "tone": "watch",
            "strength": _clamp((cv - 0.20) / 0.50),
            "evidence": f"Monthly spending swings by {cv * 100:.0f}% around its average "
                        f"(from {inr(monthly_exp.min())} to {inr(monthly_exp.max())}).",
            "nudge": "Smooth lumpy costs with a sinking fund you top up every month.",
        })

    # --- Big tickets ----------------------------------------------------------
    if len(ex) >= 20:
        top = ex["Amount"].nlargest(max(1, len(ex) // 10)).sum() / total_spend
        found.append({
            "name": "Big-Ticket Buyer", "icon": "💎", "tone": "neutral",
            "strength": _clamp((top - 0.25) / 0.30),
            "evidence": f"Your largest 10% of purchases make up {top * 100:.0f}% of everything you spend.",
            "nudge": "Add a 48-hour cooling-off rule for anything above your usual range.",
        })

    # --- Festive season (Oct–Nov, Diwali) -------------------------------------
    by_month = ex.groupby(ex["Date"].dt.month)["Amount"].sum()
    if ex["Date"].dt.to_period("M").nunique() >= 12 and by_month.sum() > 0:
        festive_total = by_month.reindex([10, 11], fill_value=0).sum()
        festive = festive_total / by_month.sum()
        lift = festive / (2 / 12)
        festive_years = max(1, ex.loc[ex["Date"].dt.month.isin([10, 11]), "Date"].dt.year.nunique())
        monthly_set_aside = festive_total / festive_years / 4
        found.append({
            "name": "Festive Season Spender", "icon": "🪔", "tone": "neutral",
            "strength": _clamp((lift - 1) / 0.5),
            "evidence": f"October–November takes {festive * 100:.0f}% of your yearly spend "
                        f"({lift:.2f}× an average two-month stretch).",
            "nudge": f"Start a festive fund in July — about {inr(monthly_set_aside)} a month "
                     "covers a typical Oct–Nov without a credit-card hangover.",
        })

    # --- Investing habit --------------------------------------------------------
    if total_spend > 0:
        invest = ex.loc[ex["Category"].isin(INVESTMENT), "Amount"].sum() / total_spend
        if invest > 0:
            found.append({
                "name": "Future Builder", "icon": "🌱", "tone": "positive",
                "strength": _clamp(invest / 0.20),
                "evidence": f"{invest * 100:.0f}% of your outflow goes into investments.",
                "nudge": "Keep it automatic — a monthly SIP removes the decision entirely.",
            })

    found.sort(key=lambda t: t["strength"], reverse=True)
    return found


def archetype(found):
    strong = [t for t in found if t["strength"] >= 0.35]
    if not strong:
        return {
            "name": "The Balanced Planner", "icon": "⚖️",
            "line": "No single habit dominates your spending — your patterns are steady and spread out.",
        }
    lead = strong[0]
    second = strong[1]["name"] if len(strong) > 1 else None
    line = lead["evidence"]
    if second:
        line += f" You also show signs of being a {second}."
    return {"name": f"The {lead['name']}", "icon": lead["icon"], "line": line}
