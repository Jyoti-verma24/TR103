import os

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import roc_auc_score

from finsense import charts, fraud, payments_fraud, theme
from finsense.views import payments_fraud_view
from finsense.fraud import FEATURES


@st.cache_resource
def load_model(path):
    return joblib.load(path)


@st.cache_data
def score(raw, _model, _scaler):
    X = raw[FEATURES].apply(pd.to_numeric, errors="coerce")
    valid = X.notna().all(axis=1)
    X, results = X[valid], raw[valid].copy()
    results.insert(0, "Payment", np.arange(1, len(results) + 1))
    if X.empty:
        return results.assign(Probability=[])
    # The forest was trained on standardised features (src/anomaly_detection.py),
    # so inputs must go through the same scaler or Time/Amount are on the wrong scale.
    if _scaler is not None:
        X = pd.DataFrame(_scaler.transform(X), columns=FEATURES, index=X.index)
    results["Probability"] = _model.predict_proba(X)[:, 1]
    return results


def _when(time_seconds):
    day = int(time_seconds // 86400) + 1
    return f"Day {day} · {int(fraud.hour_of(time_seconds)):02d}:{int(time_seconds // 60 % 60):02d}"


def _payment_card(row, ref, threshold, labelled):
    label, tone = fraud.verdict(row["Probability"], threshold)
    reasons = fraud.explain(row, ref) if ref else []
    with st.container(border=True):
        a, b = st.columns([4, 1])
        with a:
            truth = ""
            if labelled:
                actual = int(row["Class"]) == 1
                if actual:
                    note = "confirmed fraud"
                elif row["Probability"] >= threshold:
                    note = "actually genuine (false alarm)"
                else:
                    note = "actually genuine"
                truth = f" · <b style='color:{theme.RED if actual else theme.GREEN}'>{note}</b>"
            st.markdown(
                f"**Payment #{int(row['Payment'])}** · €{row['Amount']:,.2f} · {_when(row['Time'])}{truth}",
                unsafe_allow_html=True,
            )
            if reasons:
                theme.pills(reasons, tone)
            else:
                st.caption("Every key signal sits inside the normal range for genuine payments — "
                           "nothing stands out on its own.")
        with b:
            st.metric(label, f"{row['Probability'] * 100:.0f}%")


def render():
    theme.hero(
        "Fraud lab",
        "Why does this payment look like fraud?",
        "Upload a file of payments. Each one gets a fraud score, and every flagged payment "
        "comes with the reasons behind it.",
        tone="bad",
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        uploaded = st.file_uploader("Payments CSV", type=["csv"], key="fraud_csv")
    with c2:
        threshold = st.slider("Flag when fraud probability is at least", 0.10, 0.90, 0.50, 0.05,
                              help="Lower = catch more fraud, but more genuine payments get flagged too.")

    if uploaded is None:
        theme.insight(
            "<b>Two kinds of file work here.</b><br>"
            "<b>Mobile payments</b> (PaySim format: step, type, amount and balances) — explained in plain "
            "words, e.g. <i>\"emptied the sender's account\"</i>. Try "
            "<code>sample_data/payments_fraud_test.csv</code>.<br>"
            "<b>Card payments</b> (Kaggle format: Time, V1–V28, Amount) — the bank has anonymised these "
            "columns, so reasons can only name the signal, not what it means. Try "
            "<code>sample_data/card_fraud_test.csv</code>.",
            "info",
        )
        return

    raw = pd.read_csv(uploaded)
    if all(c in raw.columns for c in payments_fraud.REQUIRED):
        payments_fraud_view.render_payments(raw, threshold)
    elif all(c in raw.columns for c in FEATURES):
        render_card(raw, threshold)
    else:
        st.error("This file doesn't match either format. Mobile payments need: "
                 + ", ".join(payments_fraud.REQUIRED) + ". Card payments need: Time, V1–V28, Amount.")


def render_card(raw, threshold):
    if not os.path.exists(fraud.MODEL_PATH):
        st.error("Card model not found. Train it with src/anomaly_detection.py first.")
        return

    model = load_model(fraud.MODEL_PATH)
    scaler = load_model(fraud.SCALER_PATH) if os.path.exists(fraud.SCALER_PATH) else None
    ref = fraud.load_reference()
    if scaler is None:
        st.warning("Scaler file missing — scores will be less accurate. Re-run src/anomaly_detection.py.")
    if ref is None:
        st.warning("Reference profile missing — flags will show without reasons. Re-run src/anomaly_detection.py.")

    st.caption("Card payments: V1–V28 are anonymised by the bank for privacy, so the reasons below name the "
               "signal and how extreme it is, but not what it means in real life.")

    results = score(raw, model, scaler)
    if results.empty:
        st.error("No valid rows to score.")
        return

    proba = results["Probability"].values
    hit = proba >= threshold
    labelled = "Class" in results and results["Class"].nunique() == 2
    truth = results["Class"].astype(int).values == 1 if labelled else None

    cards = [
        ("Payments checked", f"{len(results):,}", "", "neutral"),
        ("Flagged", f"{int(hit.sum()):,}", f"at {threshold:.0%} or above", "bad" if hit.any() else "good"),
        ("Very likely fraud", f"{int((proba >= 0.8).sum()):,}", "80% or above", "bad"),
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
        flagged = results[hit].sort_values("Probability", ascending=False)
        if flagged.empty:
            st.success("Nothing reaches the threshold.")
        else:
            st.caption(f"Showing the top {min(len(flagged), 25)} of {len(flagged)} flagged payments, "
                       "most suspicious first.")
        for _, row in flagged.head(25).iterrows():
            _payment_card(row, ref, threshold, labelled)

    with tabs[1]:
        if not labelled:
            st.info("This needs a `Class` column with the true answers (1 = fraud).")
        else:
            missed_rows = results[truth & ~hit].sort_values("Probability", ascending=False)
            st.caption("Frauds the model scored below your threshold. These usually look like ordinary "
                       "payments — often a tiny 'test' charge before the real theft.")
            if missed_rows.empty:
                st.success("No frauds were missed at this threshold.")
            for _, row in missed_rows.iterrows():
                _payment_card(row, ref, threshold, labelled)

    with tabs[2]:
        default = int(results.loc[results["Probability"].idxmax(), "Payment"])
        pick = st.number_input("Payment number", 1, len(results), default)
        row = results[results["Payment"] == pick].iloc[0]
        _payment_card(row, ref, threshold, labelled)
        if ref:
            top = [f for f in ref["importance"].index if f not in ("Time", "Amount")][:8]
            st.markdown("##### This payment vs normal")
            st.caption("The shaded band is where 98% of genuine payments fall. A diamond far outside the "
                       "band, close to the ✕ (typical fraud), is what makes the model suspicious.")
            charts.show(charts.payment_profile(fraud.feature_profile(row, ref, top)))

    with tabs[3]:
        if ref:
            left, right = st.columns(2)
            with left:
                st.markdown("##### Signals the model relies on most")
                charts.show(charts.importance_bars(ref["importance"]))
            with right:
                st.markdown("##### When fraud happens")
                st.caption("Genuine spending sleeps at night; fraud doesn't.")
                charts.show(charts.hour_profile(ref["genuine_hour_share"], ref["fraud_hour_share"]))
        st.markdown("##### How confident the model is")
        st.caption("Most payments score near 0%. Fraud piles up on the right. The dashed line is your slider.")
        charts.show(charts.probability_histogram(proba, truth.astype(int) if labelled else None, threshold))

    export = results.assign(Verdict=[fraud.verdict(p, threshold)[0] for p in proba])
    if ref:
        export["Reasons"] = ["; ".join(fraud.explain(r, ref)) if h else ""
                             for (_, r), h in zip(results.iterrows(), hit)]
    st.download_button("Download all scores with reasons (CSV)", export.to_csv(index=False).encode("utf-8"),
                       "finsense_fraud_scores.csv", "text/csv")
