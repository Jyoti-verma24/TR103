import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import roc_auc_score

from finsense import charts, payments_fraud as pf, theme
from finsense.data import inr
from finsense.theme import esc

FRIENDLY = {
    "is_transfer": "Is a transfer",
    "log_amount": "Amount",
    "oldbalanceOrg": "Sender's balance before",
    "newbalanceOrig": "Sender's balance after",
    "oldbalanceDest": "Receiver's balance before",
    "newbalanceDest": "Receiver's balance after",
    "drain_ratio": "Share of balance sent",
    "exact_drain": "Sent the entire balance",
    "receiver_stays_zero": "Money never arrived",
    "hour": "Hour of day",
    "is_night": "Night-time",
}


@st.cache_resource
def _load():
    return pf.load()


def _when(step):
    return f"Day {int(pf.day_of(step))}, {int(pf.hour_of(step)):02d}:00"


def _payment_card(row, ref, threshold, labelled):
    label, tone = pf.verdict(row["Probability"], threshold)
    with st.container(border=True):
        a, b = st.columns([4, 1])
        with a:
            who = ""
            if "nameOrig" in row and "nameDest" in row:
                who = f" · {esc(row['nameOrig'])} → {esc(row['nameDest'])}"
            truth = ""
            if labelled:
                actual = int(row["isFraud"]) == 1
                if actual:
                    note = "confirmed fraud"
                elif row["Probability"] >= threshold:
                    note = "actually genuine (false alarm)"
                else:
                    note = "actually genuine"
                truth = f" · <b style='color:{theme.RED if actual else theme.GREEN}'>{note}</b>"
            st.markdown(
                f"**Payment #{int(row['Payment'])}** · {esc(row['type'].replace('_', ' ').title())} · "
                f"{inr(row['amount'])} · {_when(row['step'])}{who}{truth}",
                unsafe_allow_html=True,
            )
            reasons = pf.explain(row, ref)
            if row["Probability"] >= threshold / 2 and reasons:
                for r in reasons:
                    theme.insight(esc(r), tone)
            else:
                ok = pf.reassurances(row, ref)
                if ok:
                    theme.pills(ok, "good")
                elif reasons:
                    st.caption(reasons[0])
        with b:
            st.metric(label, f"{row['Probability'] * 100:.0f}%")


def _balance_story(row):
    sent = row["amount"]
    sender_change = row["newbalanceOrig"] - row["oldbalanceOrg"]
    receiver_change = row["newbalanceDest"] - row["oldbalanceDest"]
    table = pd.DataFrame({
        "": ["Sender", "Receiver"],
        "Before": [inr(row["oldbalanceOrg"]), inr(row["oldbalanceDest"])],
        "After": [inr(row["newbalanceOrig"]), inr(row["newbalanceDest"])],
        "Change": [inr(sender_change, sign=True), inr(receiver_change, sign=True)],
    })
    st.dataframe(table, hide_index=True, width="stretch")
    if row["type"] in pf.RISKY_TYPES and receiver_change == 0 and sent > 0:
        theme.insight(f"The payment says <b>{inr(sent)}</b> was sent, but the receiver's balance "
                      f"<b>didn't change at all</b>. The money went somewhere it can't be traced.", "bad")
    if row["oldbalanceOrg"] > 0 and abs(sent - row["oldbalanceOrg"]) < 1:
        theme.insight(f"The sender had exactly <b>{inr(row['oldbalanceOrg'])}</b> and all of it was sent. "
                      "Real people almost never send their entire balance down to the last rupee.", "bad")


def render_payments(raw, threshold):
    model, ref = _load()
    if model is None:
        st.error("Payment fraud model not found. Train it with `python src/train_paysim_fraud.py`.")
        return

    df = raw.copy()
    for c in pf.REQUIRED[2:] + ["step"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=pf.REQUIRED).reset_index(drop=True)
    df.insert(0, "Payment", np.arange(1, len(df) + 1))
    df["Probability"] = pf.score(df, model)

    proba = df["Probability"].values
    hit = proba >= threshold
    labelled = "isFraud" in df and df["isFraud"].nunique() == 2
    truth = df["isFraud"].astype(int).values == 1 if labelled else None

    cards = [
        ("Payments checked", f"{len(df):,}", f"{int(df['type'].isin(pf.RISKY_TYPES).sum()):,} transfers/cash-outs",
         "neutral"),
        ("Flagged", f"{int(hit.sum()):,}", f"at {threshold:.0%} or above", "bad" if hit.any() else "good"),
        ("Money in flagged payments", inr(df.loc[hit, "amount"].sum()), "", "bad"),
    ]
    if labelled:
        cards.append(("ROC-AUC on this file", f"{roc_auc_score(truth, proba):.3f}", "1.0 = perfect ranking", "info"))
    theme.stat_cards(cards)

    if labelled:
        caught, missed = int((truth & hit).sum()), int((truth & ~hit).sum())
        false_alarms = int((~truth & hit).sum())
        theme.insight(
            f"This file includes the real answers, so we can grade the model. It <b>caught {caught} of "
            f"{caught + missed} frauds</b> and missed {missed}. It wrongly flagged <b>{false_alarms} genuine "
            f"payment{'s' if false_alarms != 1 else ''}</b> out of {int((~truth).sum()):,}.",
            "info",
        )

    tabs = st.tabs(["Flagged payments", "Missed frauds", "Look up a payment", "How the model decides"])

    with tabs[0]:
        flagged = df[hit].sort_values("Probability", ascending=False)
        if flagged.empty:
            st.success("Nothing reaches the threshold.")
        else:
            st.caption(f"Showing the top {min(len(flagged), 25)} of {len(flagged)} flagged payments, "
                       "most suspicious first.")
        for _, row in flagged.head(25).iterrows():
            _payment_card(row, ref, threshold, labelled)

    with tabs[1]:
        if not labelled:
            st.info("This needs an `isFraud` column with the true answers (1 = fraud).")
        else:
            missed_rows = df[truth & ~hit].sort_values("Probability", ascending=False)
            if missed_rows.empty:
                st.success("No frauds were missed at this threshold.")
            for _, row in missed_rows.iterrows():
                _payment_card(row, ref, threshold, labelled)

    with tabs[2]:
        default = int(df.loc[df["Probability"].idxmax(), "Payment"])
        pick = st.number_input("Payment number", 1, len(df), default)
        row = df[df["Payment"] == pick].iloc[0]
        _payment_card(row, ref, threshold, labelled)
        st.markdown("##### Follow the money")
        _balance_story(row)

    with tabs[3]:
        st.markdown("##### The patterns behind fraud in this data")
        st.caption("Measured on the training data: how often each pattern appears in fraud vs genuine payments.")
        rates = pd.DataFrame(
            [(pf.SIGNALS_LABELS[k], f, g) for k, (f, g) in ref["rates"].items()],
            columns=["Pattern", "In frauds", "In genuine payments"],
        )
        st.dataframe(
            rates, hide_index=True, width="stretch",
            column_config={
                "In frauds": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "In genuine payments": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            },
        )
        left, right = st.columns(2)
        with left:
            st.markdown("##### What the model leans on")
            charts.show(charts.importance_bars(ref["importance"].rename(index=FRIENDLY)))
        with right:
            st.markdown("##### When fraud happens")
            st.caption("Genuine payments sleep at night; fraud doesn't.")
            charts.show(charts.hour_profile(ref["genuine_hour_share"], ref["fraud_hour_share"]))
        theme.insight(
            "<b>A note on accuracy.</b> PaySim is a simulator built from real mobile-money logs, and its "
            "fraudsters follow one very consistent script (empty the account, move it, cash it out), so the "
            "model scores almost perfectly here. Real fraud is messier; expect lower numbers on real bank data.",
            "warn",
        )

    export = df.assign(Verdict=[pf.verdict(p, threshold)[0] for p in proba],
                       Reasons=["; ".join(pf.explain(r, ref)) for _, r in df.iterrows()])
    st.download_button("Download all scores with reasons (CSV)", export.to_csv(index=False).encode("utf-8"),
                       "finsense_payment_fraud_scores.csv", "text/csv")
